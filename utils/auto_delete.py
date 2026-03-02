# utils/auto_delete.py
import asyncio
from telegram import Update, Message
from telegram.ext import ContextTypes
from functools import wraps

def auto_delete_user_message(func):
    """Декоратор для автоматического удаления сообщения пользователя через 3 секунды"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Выполняем функцию
        result = await func(update, context, *args, **kwargs)
        
        # Удаляем сообщение пользователя через 3 секунды
        if update and update.message:
            async def delete_user_msg():
                await asyncio.sleep(3)
                try:
                    await update.message.delete()
                except Exception as e:
                    print(f"Ошибка удаления сообщения пользователя: {e}")
            
            asyncio.create_task(delete_user_msg())
        
        return result
    return wrapper

async def reply_and_del(message: Message, text: str, delay: int = 3, **kwargs):
    """Отвечает на сообщение и удаляет через delay секунд"""
    sent = await message.reply_text(text, **kwargs)
    
    async def delete_later():
        await asyncio.sleep(delay)
        try:
            await sent.delete()
        except:
            pass
    
    asyncio.create_task(delete_later())
    return sent

async def send_and_del(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, delay: int = 3, **kwargs):
    """Отправляет сообщение и удаляет через delay секунд"""
    sent = await context.bot.send_message(chat_id=chat_id, text=text, **kwargs)
    
    async def delete_later():
        await asyncio.sleep(delay)
        try:
            await sent.delete()
        except:
            pass
    
    asyncio.create_task(delete_later())
    return sent