# utils/auto_delete.py
from telegram import Update, Message
from telegram.ext import ContextTypes
from functools import wraps

def auto_delete_user_message(func):
    """Декоратор - ОТКЛЮЧЕН, просто выполняет функцию"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        return await func(update, context, *args, **kwargs)
    return wrapper

async def reply_and_del(message: Message, text: str, delay: int = 3, **kwargs):
    """Просто отправляет сообщение без удаления"""
    return await message.reply_text(text, **kwargs)

async def send_and_del(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, delay: int = 3, **kwargs):
    """Просто отправляет сообщение без удаления"""
    return await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)