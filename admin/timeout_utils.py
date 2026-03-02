# admin/timeout_utils.py
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from .keyboards import ADMIN_KEYBOARD
import asyncio

# ==================== КОНСТАНТЫ ТАЙМАУТА ====================
TIMEOUT_SECONDS = 30

# ==================== ФУНКЦИИ УПРАВЛЕНИЯ ТАЙМАУТАМИ ====================

async def setup_timeout_job(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                           timeout_seconds: int = TIMEOUT_SECONDS):
    """Устанавливает джобу для таймаута"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    # Удаляем предыдущий таймаут, если есть
    if 'timeout_job' in context.user_data:
        try:
            context.user_data['timeout_job'].schedule_removal()
        except:
            pass
    
    # Создаем новую джобу
    job = context.job_queue.run_once(
        timeout_callback,
        timeout_seconds,
        chat_id=chat_id,
        user_id=user_id,
        name=f"timeout_{user_id}",
        data={'chat_id': chat_id, 'user_id': user_id}
    )
    
    context.user_data['timeout_job'] = job
    context.user_data['last_activity'] = datetime.now().timestamp()

async def reset_timeout_job(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           timeout_seconds: int = TIMEOUT_SECONDS):
    """Сбрасывает таймаут при активности пользователя"""
    # Удаляем старую джобу
    if 'timeout_job' in context.user_data:
        try:
            context.user_data['timeout_job'].schedule_removal()
        except:
            pass
    
    # Создаем новую
    await setup_timeout_job(update, context, timeout_seconds)

async def cleanup_timeout_job(context: ContextTypes.DEFAULT_TYPE):
    """Очищает джобу таймаута"""
    if 'timeout_job' in context.user_data:
        try:
            context.user_data['timeout_job'].schedule_removal()
        except:
            pass
        del context.user_data['timeout_job']
    
    if 'last_activity' in context.user_data:
        del context.user_data['last_activity']

# ==================== КОЛЛБЭКИ И ОБРАБОТЧИКИ ====================

async def timeout_callback(context: ContextTypes.DEFAULT_TYPE):
    """Коллбэк при таймауте - возвращает в главное меню"""
    job = context.job
    chat_id = job.data.get('chat_id')
    user_id = job.data.get('user_id')
    
    try:
        # Отправляем сообщение о таймауте
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏰ Время на редактирование истекло. Возвращаю в главное меню.",
            reply_markup=ADMIN_KEYBOARD
        )
        
        # Очищаем данные
        if 'timeout_job' in context.user_data:
            del context.user_data['timeout_job']
        if 'last_activity' in context.user_data:
            del context.user_data['last_activity']
        
        # Завершаем ConversationHandler
        return ConversationHandler.END
    except Exception as e:
        print(f"Ошибка в timeout_callback: {e}")

async def edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена редактирования (для fallback) - возвращает в главное меню"""
    await cleanup_timeout_job(context)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            "❌ Редактирование отменено",
            reply_markup=ADMIN_KEYBOARD
        )
    elif update.message:
        await update.message.reply_text(
            "❌ Редактирование отменено",
            reply_markup=ADMIN_KEYBOARD
        )
    
    return ConversationHandler.END

async def timeout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для состояния таймаута в ConversationHandler"""
    await cleanup_timeout_job(context)
    
    if update.message:
        await update.message.reply_text(
            "⏰ Время на редактирование истекло. Возвращаю в главное меню.",
            reply_markup=ADMIN_KEYBOARD
        )
    
    return ConversationHandler.END