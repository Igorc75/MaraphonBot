# admin/menu.py - УЛУЧШЕННАЯ ВЕРСИЯ
from telegram import Update
from telegram.ext import ContextTypes
from db.database import SessionLocal
from db.models import AdminSettings
from config import Config
from .keyboards import ADMIN_KEYBOARD, TOPICS_SUBMENU
from utils.logger import log_admin_action

async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, является ли пользователь администратором"""
    if not update.effective_user or not update.effective_chat:
        return False
    
    user_id = update.effective_user.id
    
    # 1. Суперадмины из конфига
    if user_id in Config.ADMIN_IDS:
        return True
    
    # 2. Админы из базы
    session = SessionLocal()
    try:
        admin_settings = session.query(AdminSettings).filter_by(user_id=user_id).first()
        if admin_settings:
            return True
    except Exception as e:
        print(f"Ошибка проверки админа в БД: {e}")
    finally:
        session.close()
    
    # 3. Админы чата (только для групп)
    if update.effective_chat.type in ["group", "supergroup"]:
        try:
            admins = await context.bot.get_chat_administrators(update.effective_chat.id)
            admin_ids = [admin.user.id for admin in admins]
            return user_id in admin_ids
        except Exception as e:
            print(f"Ошибка проверки админов чата: {e}")
    
    return False

async def send_message_safely(update, context, text, **kwargs):
    """Безопасная отправка сообщения"""
    try:
        if update.message:
            await update.message.reply_text(text, **kwargs)
        elif update.callback_query:
            if update.callback_query.message:
                await update.callback_query.message.reply_text(text, **kwargs)
            else:
                await update.effective_chat.send_message(text, **kwargs)
        else:
            await update.effective_chat.send_message(text, **kwargs)
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            **kwargs
        )

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню администратора"""
    if not await is_chat_admin(update, context):
        log_admin_action(
            user_id=update.effective_user.id,
            action="access_denied",
            details="Попытка доступа к админке"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❌ Доступ запрещён"
        )
        return
    
    log_admin_action(
        user_id=update.effective_user.id,
        action="menu_opened",
        details="Главное меню"
    )
    
    await send_message_safely(
        update=update,
        context=context,
        text="🔧 <b>Админка Maraphon</b>",
        reply_markup=ADMIN_KEYBOARD,
        parse_mode='HTML'
    )

async def show_topics_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подменю управления темами"""
    if not await is_chat_admin(update, context):
        return
    
    log_admin_action(
        user_id=update.effective_user.id,
        action="menu_opened",
        details="Подменю тем"
    )
    
    await send_message_safely(
        update=update,
        context=context,
        text="📋 <b>Управление темами</b>",
        reply_markup=TOPICS_SUBMENU,
        parse_mode='HTML'
    )