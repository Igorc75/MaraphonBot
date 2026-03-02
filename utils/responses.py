# utils/responses.py
import asyncio
from telegram import Message
from config import Config

async def reply_and_delete(msg: Message, text: str, is_error: bool = False, delete_after: int = None):
    """
    Отправляет сообщение и автоматически удаляет его
    
    Args:
        msg: Сообщение для ответа
        text: Текст ответа
        is_error: True для ошибок (удаление через 3 сек), False для успеха (через 5 сек)
        delete_after: Кастомное время удаления в секундах
    """
    response = await msg.reply_text(text)
    
    if delete_after is not None:
        delay = delete_after
    else:
        delay = Config.DELETE_ERROR_AFTER if is_error else Config.DELETE_SUCCESS_AFTER
    
    async def delete_later():
        await asyncio.sleep(delay)
        try:
            await response.delete()
        except Exception:
            pass
    
    asyncio.create_task(delete_later())
    return response