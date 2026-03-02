# utils/chat_cleaner.py
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

async def clean_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет все сообщения бота и пользователя в чате"""
    chat_id = update.effective_chat.id
    
    # Удаляем сообщение, на которое нажали (если есть)
    if update.callback_query and update.callback_query.message:
        try:
            await update.callback_query.message.delete()
        except:
            pass
    
    # Удаляем сообщение пользователя (если есть)
    if update.message:
        try:
            await update.message.delete()
        except:
            pass
    
    # Удаляем сохраненные сообщения бота
    if 'bot_messages' in context.chat_data:
        for msg_id in context.chat_data['bot_messages']:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                pass
        context.chat_data['bot_messages'] = []

async def save_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int):
    """Сохраняет ID сообщения для последующего удаления"""
    if 'bot_messages' not in context.chat_data:
        context.chat_data['bot_messages'] = []
    context.chat_data['bot_messages'].append(message_id)
    
    # Ограничиваем список последними 50 сообщениями
    if len(context.chat_data['bot_messages']) > 50:
        context.chat_data['bot_messages'] = context.chat_data['bot_messages'][-50:]