# admin/stats.py
from telegram import Update
from telegram.ext import ContextTypes
from config import Config

async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private" or update.effective_user.id not in Config.ADMIN_IDS:
        return
    await update.message.reply_text("📈 Статистика за сегодня:\n• Участников: 0\n• Хештегов: 0")