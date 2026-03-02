# admin/decorators.py
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import Config
from .auth import is_chat_admin

def admin_required(func):
    """Декоратор для проверки прав администратора"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not await is_chat_admin(update, context):
            if update.message:
                await update.message.reply_text("❌ Доступ запрещён")
            elif update.callback_query:
                await update.callback_query.answer("❌ Доступ запрещён", show_alert=True)
            return
        return await func(update, context, *args, **kwargs)
    return wrapper