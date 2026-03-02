# utils/chat_cleaner.py
from telegram import Update
from telegram.ext import ContextTypes

async def clean_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистка чата - ОТКЛЮЧЕНА"""
    pass

async def save_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
    """Сохранение сообщений - ОТКЛЮЧЕНО"""
    pass