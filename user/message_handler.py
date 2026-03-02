import re
import asyncio
from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ContextTypes
from db.database import SessionLocal
from db.models import User, Hashtag, Action, TopicRule, BotSettings
from config import Config
from utils.cleanup import delete_after, delete_after_3s, delete_after_5s
from utils.logger import log_hashtag_action, logger
from utils.hashtag_utils import normalize_hashtag


async def process_hashtag(session, tag, rules, msg, now, tz):
    """
    Обрабатывает один хештег.
    Возвращает (success, message, delete_seconds)
    """
    normalized_tag = normalize_hashtag(tag)
    valid_rule = None
    for rule in rules:
        if normalized_tag == rule.hashtag_prefix or normalized_tag.startswith(rule.hashtag_prefix + '_'):
            valid_rule = rule
            break
    if not valid_rule:
        return False, "❌ Хештег не найден", 3

    now_naive = now.replace(tzinfo=None)
    if valid_rule.start_datetime and now_naive < valid_rule.start_datetime:
        start_str = valid_rule.start_datetime.strftime("%d.%m.%Y %H:%M")
        return False, f"❌ Хештег начнёт работать с {start_str}", 3
    if valid_rule.end_datetime and now_naive > valid_rule.end_datetime:
        end_str = valid_rule.end_datetime.strftime("%d.%m.%Y %H:%M")
        return False, f"❌ Хештег завершён (активен до {end_str})", 3

    today_start = datetime.combine(now.date(), datetime.min.time())
    existing = session.query(Action).join(Hashtag, Action.hashtag_id == Hashtag.id).filter(
        Action.uid == msg.from_user.id,
        Hashtag.name_hashtag == normalized_tag,
        Action.datetime >= today_start
    ).first()
    if existing:
        return False, "❌ Вы уже отправляли этот хештег сегодня", 3

    hashtag_obj = session.query(Hashtag).filter_by(name_hashtag=normalized_tag).first()
    if not hashtag_obj:
        hashtag_obj = Hashtag(name_hashtag=normalized_tag)
        session.add(hashtag_obj)
        session.commit()

    action = Action(uid=msg.from_user.id, pid=msg.message_id, hashtag_id=hashtag_obj.id, datetime=now)
    session.add(action)
    session.commit()

    display_name = msg.from_user.username or f"uid @{msg.from_user.id}"
    log_hashtag_action(
        user_id=msg.from_user.id,
        username=msg.from_user.username,
        thread_id=msg.message_thread_id,
        hashtag=normalized_tag,
        status="принят",
        reason=""
    )
    return True, f"✅ {display_name} — принято! (+{valid_rule.point_value} баллов)", 5


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    text_content = (msg.text or msg.caption or "").strip()
    if not text_content:
        return

    tz = pytz.timezone(Config.TIMEZONE)
    now = datetime.now(tz)

    # Получаем настройки чата знакомства
    session = SessionLocal()
    try:
        bot_settings = session.query(BotSettings).filter_by(id=1).first()
        intro_chat_id = bot_settings.intro_chat_id if bot_settings else None
        intro_thread_id = bot_settings.intro_thread_id if bot_settings else None
    finally:
        session.close()

    logger.info(f"handle_message: chat_id={chat.id}, intro_chat_id={intro_chat_id}, "
                f"intro_thread_id={intro_thread_id}, thread_id={msg.message_thread_id}, "
                f"text={text_content[:50]}")

    # --------- 1️⃣ ПРОВЕРКА НА ЧАТ ЗНАКОМСТВА (ТОЛЬКО ДЛЯ ЗАДАННОЙ ТЕМЫ) ---------
    is_intro_chat = intro_chat_id is not None and chat.id == intro_chat_id
    is_intro_thread_match = (intro_thread_id is None or msg.message_thread_id == intro_thread_id)

    if is_intro_chat and is_intro_thread_match:
        # Это нужная тема в чате знакомства – обрабатываем регистрацию
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(uid=msg.from_user.id).first()
            if not user:
                user = User(uid=msg.from_user.id, username=msg.from_user.username, name="", fam="", city="")
                session.add(user)
            if msg.from_user.username:
                user.username = msg.from_user.username

            lines = [l.strip() for l in re.sub(r'[\u200b\r]+', '', text_content).split("\n") if l.strip()]
            if len(lines) >= 2:
                name_parts = lines[0].split(maxsplit=1)
                user.name = name_parts[0]
                user.fam = name_parts[1] if len(name_parts) > 1 else ""
                user.city = lines[1]
                session.commit()

                reply = await msg.reply_text(f"✅ Принято!\n{user.name} {user.fam}\nгород: {user.city}")
                asyncio.create_task(delete_after_5s(reply))
            else:
                reply = await msg.reply_text("❌ Неверный формат.\nПример:\nИмя Фамилия\nГород")
                asyncio.create_task(delete_after_3s(reply))
        finally:
            session.close()
        return  # Выходим, чтобы не обрабатывать хештеги

    # --------- 2️⃣ ЕСЛИ МЫ ДОШЛИ ДО СЮДА, ЗНАЧИТ, ЭТО НЕ РЕГИСТРАЦИЯ В ЧАТЕ ЗНАКОМСТВА ---------
    # Теперь обрабатываем хештеги, если они есть
    raw_hashtags = re.findall(r'#(\w+[\w_]*)', text_content)
    if not raw_hashtags:
        return

    # Определяем, есть ли правила для этого чата/темы
    is_allowed_chat = chat.id in Config.ALLOWED_CHAT_IDS
    has_thread = msg.message_thread_id is not None

    rules = []
    if is_allowed_chat and has_thread:
        session = SessionLocal()
        try:
            rules = session.query(TopicRule).filter_by(chat_id=chat.id, thread_id=msg.message_thread_id).all()
            logger.info(f"rules found: {len(rules)} for thread {msg.message_thread_id}")
            for r in rules:
                logger.info(f"rule: {r.hashtag_prefix} start={r.start_datetime} end={r.end_datetime}")
        finally:
            session.close()

    # Обрабатываем каждый хештег
    for raw_tag in raw_hashtags:
        tag = normalize_hashtag(raw_tag)
        if tag == "знакомство":
            continue

        if rules:
            session = SessionLocal()
            try:
                success, message, delete_sec = await process_hashtag(session, tag, rules, msg, now, tz)
                reply = await msg.reply_text(message)
                asyncio.create_task(delete_after(delete_sec, reply))
            finally:
                session.close()
        else:
            reply = await msg.reply_text(f"❌ Хештег #{tag} не найден")
            asyncio.create_task(delete_after_3s(reply))