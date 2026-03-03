# admin/stats.py
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from utils.auto_delete import auto_delete_user_message
import asyncio

@auto_delete_user_message
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
    if not await is_chat_admin(update, context):
        return
    
    await update.message.reply_text(
        "📈 Статистика за сегодня:\n• Участников: 0\n• Хештегов: 0"
    )
    # Сообщение пользователя удалит декоратор auto_delete_user_message