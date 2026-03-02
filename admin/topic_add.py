# admin/topic_add.py
import re
import asyncio
from datetime import datetime
import pytz
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes
from db.database import SessionLocal
from db.models import TopicRule
from config import Config
from utils.hashtag_utils import normalize_hashtag, validate_hashtag_prefix
from utils.auto_delete import reply_and_del, auto_delete_user_message
from .keyboards import ADMIN_KEYBOARD, TOPICS_SUBMENU

@auto_delete_user_message
async def request_topic_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    example = (
        "📋 Отправьте данные темы одним сообщением в формате:\n\n"
        "• Ссылка на тему: https://t.me/c/3849962819/2\n"
        "• Начало: 05.02.2026 11:00\n"
        "• Окончание: 05.02.2026 12:00\n"
        "• Балл: 10\n"
        "• Хештег: послевкусие_01"
    )
    await reply_and_del(update.message, example, reply_markup=ReplyKeyboardRemove())

@auto_delete_user_message
async def add_topic_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:
        return

    # Если админ сейчас вводит ссылку для чата знакомства — обрабатываем это, а не парсим тему
    try:
        from admin.settings import handle_intro_chat_link_message
        handled = await handle_intro_chat_link_message(update, context)
        if handled:
            return
    except Exception:
        # Не блокируем добавление темы, даже если что-то пошло не так в настройках
        pass
    
    text = update.message.text.strip()
    
    # Парсинг данных
    link_match = re.search(r'•\s*Ссылка на тему:\s*(https?://t\.me/c/(\d+)/(\d+))', text, re.IGNORECASE)
    start_match = re.search(r'•\s*Начало:\s*(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})', text, re.IGNORECASE)
    end_match = re.search(r'•\s*Окончание:\s*(\d{2}\.\d{2}\.\d{4} \d{2}:\d{2})', text, re.IGNORECASE)
    point_match = re.search(r'•\s*Балл:\s*(\d+)', text, re.IGNORECASE)
    hashtag_match = re.search(r'•\s*Хештег:\s*([^\n]+)', text, re.IGNORECASE)
    
    errors = []
    if not link_match:
        errors.append("❌ Не найдена ссылка на тему")
    else:
        chat_digits, thread_id = link_match.group(2), link_match.group(3)
        if Config.ALLOWED_CHAT_IDS:
            expected_digits = str(abs(Config.ALLOWED_CHAT_IDS[0]))[-10:]
            if chat_digits != expected_digits:
                errors.append(f"❌ Чат не совпадает! Ожидался: `{expected_digits}`")
            else:
                try:
                    thread_id = int(thread_id)
                except ValueError:
                    errors.append("❌ Неверный формат ID темы")
    
    tz = pytz.timezone(Config.TIMEZONE)
    
    if not start_match:
        errors.append("❌ Не указано время начала")
    else:
        try:
            start_datetime = datetime.strptime(start_match.group(1), "%d.%m.%Y %H:%M")
            start_datetime = tz.localize(start_datetime)
        except ValueError:
            errors.append("❌ Неверный формат даты начала (ожидается ДД.ММ.ГГГГ ЧЧ:ММ)")
    
    if not end_match:
        errors.append("❌ Не указано время окончания")
    else:
        try:
            end_datetime = datetime.strptime(end_match.group(1), "%d.%m.%Y %H:%M")
            end_datetime = tz.localize(end_datetime)
            
            if 'start_datetime' in locals() and end_datetime < start_datetime:
                errors.append("❌ Время окончания раньше начала")
        except ValueError:
            errors.append("❌ Неверный формат даты окончания (ожидается ДД.ММ.ГГГГ ЧЧ:ММ)")
    
    if not point_match:
        errors.append("❌ Не указана стоимость балла")
    else:
        try:
            point_value = int(point_match.group(1))
            if point_value < 1:
                errors.append("❌ Стоимость балла должна быть ≥ 1")
        except ValueError:
            errors.append("❌ Неверный формат балла")
    
    if not hashtag_match:
        errors.append("❌ Не указан хештег")
    else:
        hashtag_prefix = normalize_hashtag(hashtag_match.group(1))
        
        is_valid, error_msg = validate_hashtag_prefix(hashtag_prefix)
        
        if not is_valid:
            errors.append(f"❌ {error_msg}")
    
    if errors:
        error_text = "⚠️ Ошибки валидации:\n" + "\n".join(errors) + "\n\nПопробуйте снова:"
        # Ошибка - удаляется через 3 сек
        await reply_and_del(update.message, error_text, reply_markup=ReplyKeyboardRemove())
        return
    
    session = SessionLocal()
    try:
        # ПРОВЕРКА НА УНИКАЛЬНОСТЬ ХЕШТЕГА
        # Проверяем, существует ли уже такой хештег в этом чате
        existing_rule = session.query(TopicRule).filter_by(
            chat_id=Config.ALLOWED_CHAT_IDS[0],
            hashtag_prefix=hashtag_prefix
        ).first()
        
        if existing_rule:
            # Формируем информацию о существующей теме
            start_str = existing_rule.start_datetime.strftime("%d.%m.%Y %H:%M") if existing_rule.start_datetime else "—"
            end_str = existing_rule.end_datetime.strftime("%d.%m.%Y %H:%M") if existing_rule.end_datetime else "—"
            
            # Сообщение с инлайн-кнопками - НЕ УДАЛЯЕМ
            await update.message.reply_text(
                f"❌ Хештег #{hashtag_prefix} уже существует!\n\n"
                f"Информация о существующей теме:\n"
                f"• ID темы: {existing_rule.thread_id}\n"
                f"• Начало: {start_str}\n"
                f"• Окончание: {end_str}\n"
                f"• Балл: {existing_rule.point_value}\n"
                f"• Статус: {'СТОП отправлен' if existing_rule.stop_sent else 'активна'}\n\n"
                f"Используйте другой хештег.",
                reply_markup=TOPICS_SUBMENU
            )
            return
        
        # Если хештег уникален, создаем правило
        rule = TopicRule(
            chat_id=Config.ALLOWED_CHAT_IDS[0],
            thread_id=thread_id,
            hashtag_prefix=hashtag_prefix,
            start_datetime=start_datetime.replace(tzinfo=None) if start_datetime else None,
            end_datetime=end_datetime.replace(tzinfo=None) if end_datetime else None,
            point_value=point_value,
            stop_sent=False
        )
        session.add(rule)
        session.commit()
        
        response = (
            "✅ Тема успешно добавлена!\n\n"
            f"• Хештег: #{hashtag_prefix}\n"
            f"• Тема: {thread_id}\n"
            f"• Начало: {start_datetime.strftime('%d.%m.%Y %H:%M')}\n"
            f"• Окончание: {end_datetime.strftime('%d.%m.%Y %H:%M')}\n"
            f"• Балл: {point_value}"
        )
        # Успех - удаляется через 3 сек
        await reply_and_del(update.message, response, reply_markup=ADMIN_KEYBOARD)
    except Exception as e:
        session.rollback()
        # Ошибка - удаляется через 3 сек
        await reply_and_del(update.message, f"❌ Ошибка сохранения: {e}", reply_markup=TOPICS_SUBMENU)
    finally:
        session.close()