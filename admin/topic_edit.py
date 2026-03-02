# admin/topic_edit.py
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from db.database import SessionLocal
from db.models import TopicRule
from config import Config
from utils.hashtag_utils import normalize_hashtag, validate_hashtag_prefix
from utils.cleanup import delete_after_3s
from .states import EDIT_TOPIC_SELECT, EDIT_TOPIC_FIELD, EDIT_TOPIC_VALUE
from .keyboards import TOPICS_SUBMENU, ADMIN_KEYBOARD
from .timeout_utils import (
    setup_timeout_job, reset_timeout_job, cleanup_timeout_job,
    timeout_callback, edit_cancel, timeout_handler, TIMEOUT_SECONDS
)
import asyncio

# ==================== ОСНОВНЫЕ ФУНКЦИИ РЕДАКТИРОВАНИЯ ====================

async def show_edit_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список тем для редактирования"""
    if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    session = SessionLocal()
    try:
        rules = session.query(TopicRule).filter_by(chat_id=Config.ALLOWED_CHAT_IDS[0]).all()
        if not rules:
            await update.message.reply_text("📭 Нет тем для редактирования", reply_markup=TOPICS_SUBMENU)
            return ConversationHandler.END
        
        keyboard = []
        for rule in rules:
            start_str = rule.start_datetime.strftime("%d.%m.%Y %H:%M") if rule.start_datetime else "—"
            end_str = rule.end_datetime.strftime("%d.%m.%Y %H:%M") if rule.end_datetime else "—"
            btn_text = f"#{rule.hashtag_prefix} (тема {rule.thread_id})"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"edit_topic_{rule.id}")])
        
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="edit_cancel")])
        
        await update.message.reply_text(
            "✏️ Выберите тему для редактирования:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return EDIT_TOPIC_SELECT
    finally:
        session.close()

async def edit_topic_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор темы для редактирования"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "edit_cancel":
        await query.message.edit_text("⏹️ Редактирование отменено")
        from .menu import show_topics_submenu
        await show_topics_submenu(update, context)
        return ConversationHandler.END
    
    topic_id = int(query.data.split("_")[2])
    context.user_data['editing_topic_id'] = topic_id
    
    # Устанавливаем таймаут
    await setup_timeout_job(update, context, TIMEOUT_SECONDS)
    
    # Показываем поля для редактирования
    keyboard = [
        [
            InlineKeyboardButton("📝 Хештег", callback_data="edit_field_hashtag"),
            InlineKeyboardButton("🕐 Начало", callback_data="edit_field_start_datetime"),
        ],
        [
            InlineKeyboardButton("🕐 Окончание", callback_data="edit_field_end_datetime"),
            InlineKeyboardButton("⭐ Балл", callback_data="edit_field_point_value"),
        ],
        [
            InlineKeyboardButton("⬅️ Назад", callback_data="edit_back"),
            InlineKeyboardButton("❌ Отмена", callback_data="edit_cancel"),
        ]
    ]
    
    session = SessionLocal()
    try:
        rule = session.query(TopicRule).filter_by(id=topic_id).first()
        if rule:
            start_str = rule.start_datetime.strftime("%d.%m.%Y %H:%M") if rule.start_datetime else "—"
            end_str = rule.end_datetime.strftime("%d.%m.%Y %H:%M") if rule.end_datetime else "—"
            
            text = (
                f"✏️ Редактирование темы:\n"
                f"• Хештег: #{rule.hashtag_prefix}\n"
                f"• Тема ID: {rule.thread_id}\n"
                f"• Начало: {start_str}\n"
                f"• Окончание: {end_str}\n"
                f"• Балл: {rule.point_value}\n\n"
                f"Выберите поле для редактирования:"
            )
            
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            return EDIT_TOPIC_FIELD
        else:
            await query.message.edit_text("❌ Тема не найдена")
            return ConversationHandler.END
    finally:
        session.close()

async def edit_topic_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор поля для редактирования"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "edit_back":
        # Возвращаемся к выбору темы
        await cleanup_timeout_job(context)
        return await show_edit_topics(update, context)
    
    if query.data == "edit_cancel":
        await cleanup_timeout_job(context)
        await query.message.edit_text("⏹️ Редактирование отменено")
        from .menu import show_topics_submenu
        await show_topics_submenu(update, context)
        return ConversationHandler.END
    
    # Извлекаем название поля
    field = query.data.replace("edit_field_", "")
    context.user_data['editing_field'] = field
    
    # Обновляем таймаут
    await reset_timeout_job(update, context, TIMEOUT_SECONDS)
    
    # Запрашиваем новое значение
    if field == "hashtag":
        prompt = "Введите новый хештег (без #):"
    elif field in ("start_datetime", "end_datetime"):
        prompt = "Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ\n(или отправьте 0, чтобы удалить время):"
    elif field == "point_value":
        prompt = "Введите новую стоимость балла (целое число ≥ 1):"
    else:
        prompt = f"Введите новое значение для {field}:"
    
    await query.message.edit_text(prompt)
    return EDIT_TOPIC_VALUE

async def edit_topic_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод нового значения для поля"""
    if update.effective_user.id not in Config.ADMIN_IDS:
        await cleanup_timeout_job(context)
        return ConversationHandler.END
    
    value = update.message.text.strip()
    field = context.user_data.get('editing_field')
    topic_id = context.user_data.get('editing_topic_id')
    
    if not field or not topic_id:
        await cleanup_timeout_job(context)
        await update.message.reply_text("❌ Ошибка сессии", reply_markup=TOPICS_SUBMENU)
        return ConversationHandler.END
    
    session = SessionLocal()
    try:
        rule = session.query(TopicRule).filter_by(id=topic_id).first()
        if not rule:
            await cleanup_timeout_job(context)
            await update.message.reply_text("❌ Тема не найдена", reply_markup=TOPICS_SUBMENU)
            return ConversationHandler.END
        
        if field == "hashtag":
            # Используем единую функцию нормализации
            prefix = normalize_hashtag(value)
            
            # Проверяем валидность хештега
            is_valid, warning = validate_hashtag_prefix(prefix)
            
            if not is_valid:
                await update.message.reply_text(f"❌ {warning}\n\nПопробуйте снова:")
                await reset_timeout_job(update, context, TIMEOUT_SECONDS)
                return EDIT_TOPIC_VALUE
            
            # Если есть предупреждение, показываем его
            if warning:
                warning_msg = await update.message.reply_text(f"⚠️ {warning}")
                asyncio.create_task(delete_after_3s(warning_msg))
            
            rule.hashtag_prefix = prefix
            msg_text = f"✅ Хештег изменён на #{prefix}"
        
        elif field in ("start_datetime", "end_datetime"):
            dt_value = None
            if value != "0":
                try:
                    dt_value = datetime.strptime(value, "%d.%m.%Y %H:%M")
                except ValueError:
                    await update.message.reply_text(
                        "❌ Неверный формат. Попробуйте снова:\n"
                        "Формат: `ДД.ММ.ГГГГ ЧЧ:ММ`\n"
                        "Или отправьте 0, чтобы удалить время:"
                    )
                    await reset_timeout_job(update, context, TIMEOUT_SECONDS)
                    return EDIT_TOPIC_VALUE
            setattr(rule, field, dt_value)
            msg_text = f"✅ {'Начало' if field == 'start_datetime' else 'Окончание'} установлено: {value if value != '0' else 'удалено'}"
        
        elif field == "point_value":
            try:
                points = int(value)
                if points < 1:
                    raise ValueError
                rule.point_value = points
                msg_text = f"✅ Стоимость балла установлена: {points}"
            except ValueError:
                await update.message.reply_text("❌ Введите целое число ≥ 1:")
                await reset_timeout_job(update, context, TIMEOUT_SECONDS)
                return EDIT_TOPIC_VALUE
        else:
            await cleanup_timeout_job(context)
            await update.message.reply_text("❌ Неизвестное поле", reply_markup=TOPICS_SUBMENU)
            return ConversationHandler.END
        
        session.commit()
        await cleanup_timeout_job(context)
        await update.message.reply_text(msg_text, reply_markup=TOPICS_SUBMENU)
        return ConversationHandler.END
    
    except Exception as e:
        session.rollback()
        await cleanup_timeout_job(context)
        await update.message.reply_text(f"❌ Ошибка: {e}", reply_markup=TOPICS_SUBMENU)
        return ConversationHandler.END
    finally:
        session.close()