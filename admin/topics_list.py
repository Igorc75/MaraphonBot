# admin/topics_list.py
from telegram import Update
from telegram.ext import ContextTypes
from db.database import SessionLocal
from db.models import TopicRule
from config import Config
from utils.auto_delete import auto_delete_user_message

@auto_delete_user_message
async def list_topics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:
        return
    
    session = SessionLocal()
    try:
        rules = session.query(TopicRule).filter_by(chat_id=Config.ALLOWED_CHAT_IDS[0]).all()
        if not rules:
            await update.message.reply_text("📭 Нет тем")
            return
        
        text = "📋 Темы:\n"
        for rule in rules:
            start_str = rule.start_datetime.strftime("%d.%m.%Y %H:%M") if rule.start_datetime else "—"
            end_str = rule.end_datetime.strftime("%d.%m.%Y %H:%M") if rule.end_datetime else "—"
            text += (
                f"• #{rule.hashtag_prefix} — тема {rule.thread_id}\n"
                f"  Начало: {start_str}\n"
                f"  Окончание: {end_str}\n"
                f"  Балл: {rule.point_value}\n\n"
            )
        await update.message.reply_text(text)
    finally:
        session.close()