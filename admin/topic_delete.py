# admin/topic_delete.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from db.database import SessionLocal
from db.models import TopicRule
from config import Config
from .states import DELETE_TOPIC_SELECT, DELETE_CONFIRM
from .keyboards import TOPICS_SUBMENU
from utils.auto_delete import reply_and_del, auto_delete_user_message

@auto_delete_user_message
async def start_delete_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога удаления темы"""
    if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:
        return ConversationHandler.END
    
    session = SessionLocal()
    try:
        rules = session.query(TopicRule).filter_by(chat_id=Config.ALLOWED_CHAT_IDS[0]).all()
        if not rules:
            # Информация - удаляется через 3 сек
            await reply_and_del(update.message, "📭 Нет тем для удаления", reply_markup=TOPICS_SUBMENU)
            return ConversationHandler.END
        
        keyboard = [
            [InlineKeyboardButton(f"#{r.hashtag_prefix} (тема {r.thread_id})", callback_data=f"delete_topic_{r.id}")]
            for r in rules
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Отмена", callback_data="delete_cancel")])
        
        # Сообщение с инлайн-кнопками - НЕ УДАЛЯЕМ
        await update.message.reply_text(
            "🗑️ Выберите тему для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return DELETE_TOPIC_SELECT
    finally:
        session.close()

async def delete_topic_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор темы для удаления"""
    query = update.callback_query
    
    if not query:
        return ConversationHandler.END
    
    await query.answer()
    
    if query.data == "delete_cancel":
        # Удаляем сообщение с выбором темы
        await query.message.delete()
        # Вызываем возврат в меню тем
        from .menu import show_topics_submenu
        await show_topics_submenu(update, context)
        return ConversationHandler.END
    
    topic_id = int(query.data.split("_")[2])
    context.user_data['delete_topic_id'] = topic_id
    
    session = SessionLocal()
    try:
        rule = session.query(TopicRule).filter_by(id=topic_id).first()
        if not rule:
            if query.message:
                await query.message.edit_text("❌ Тема не найдена")
            else:
                await update.effective_chat.send_message("❌ Тема не найдена")
            return ConversationHandler.END
        
        start_str = rule.start_datetime.strftime("%d.%m.%Y %H:%M") if rule.start_datetime else "—"
        end_str = rule.end_datetime.strftime("%d.%m.%Y %H:%M") if rule.end_datetime else "—"
        
        text = (
            f"⚠️ Вы уверены, что хотите удалить тему?\n\n"
            f"• Хештег: #{rule.hashtag_prefix}\n"
            f"• ID темы: {rule.thread_id}\n"
            f"• Начало: {start_str}\n"
            f"• Окончание: {end_str}\n"
            f"• Балл: {rule.point_value}\n\n"
            f"Это действие нельзя отменить!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{topic_id}"),
                InlineKeyboardButton("❌ Нет, отмена", callback_data=f"confirm_cancel_{topic_id}")
            ]
        ]
        
        if query.message:
            # Сообщение с инлайн-кнопками - НЕ УДАЛЯЕМ
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.effective_chat.send_message(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        return DELETE_CONFIRM
    finally:
        session.close()

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления"""
    query = update.callback_query
    
    if not query:
        return ConversationHandler.END
    
    await query.answer()
    
    if "cancel" in query.data:
        if query.message:
            # Информация - удаляется через 3 сек
            await reply_and_del(query.message, "⏹️ Удаление отменено")
        else:
            await update.effective_chat.send_message("⏹️ Удаление отменено")
        
        from .menu import show_topics_submenu
        await show_topics_submenu(update, context)
        return ConversationHandler.END
    
    topic_id = int(query.data.split("_")[2])
    
    session = SessionLocal()
    try:
        rule = session.query(TopicRule).filter_by(id=topic_id).first()
        if not rule:
            if query.message:
                await query.message.edit_text("❌ Тема не найдена")
            else:
                await update.effective_chat.send_message("❌ Тема не найдена")
            return ConversationHandler.END
        
        hashtag = rule.hashtag_prefix
        thread_id = rule.thread_id
        
        session.delete(rule)
        session.commit()
        
        success_text = f"✅ Тема #{hashtag} (ID: {thread_id}) успешно удалена!"
        
        # Успех - удаляется через 3 сек
        await reply_and_del(query.message, success_text)
        
        # Возвращаемся в меню тем
        from .menu import show_topics_submenu
        await show_topics_submenu(update, context)
        
        return ConversationHandler.END
    except Exception as e:
        session.rollback()
        error_text = f"❌ Ошибка при удалении: {e}"
        # Ошибка - удаляется через 3 сек
        await reply_and_del(query.message, error_text)
        return ConversationHandler.END
    finally:
        session.close()