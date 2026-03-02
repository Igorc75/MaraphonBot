# utils/cleanup.py - должно быть так
import asyncio

async def delete_after(seconds: int, msg):
    """Удаляет сообщение через указанное количество секунд"""
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except Exception:
        pass

async def delete_after_5s(msg):
    """Удаляет сообщение через 5 секунд (успешные действия)"""
    await delete_after(5, msg)

async def delete_after_3s(msg):
    """Удаляет сообщение через 3 секунды (ошибки)"""
    await delete_after(3, msg)