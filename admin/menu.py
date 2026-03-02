# admin/menu.py
from telegram import Update
from telegram.ext import ContextTypes
from db.database import SessionLocal
from db.models import AdminSettings
from config import Config
from .keyboards import ADMIN_KEYBOARD, TOPICS_SUBMENU
from utils.logger import log_admin_action
from utils.auto_delete import auto_delete_user_message

async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, является ли пользователь администратором"""
    if not update.effective_user:
        return False
    
    user_id = update.effective_user.id
    
    # 1. Проверяем суперадминов из конфига
    if user_id in Config.ADMIN_IDS:
        return True
    
    # 2. Проверяем администраторов из базы данных
    session = SessionLocal()
    try:
        admin = session.query(AdminSettings).filter_by(user_id=user_id).first()
        if admin:
            return True
    except Exception as e:
        print(f"Ошибка проверки админа в БД: {e}")
    finally:
        session.close()
    
    return False

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, keyboard):
    """Показывает меню без удалений"""
    
    # Просто отправляем новое сообщение
    if update.callback_query:
        sent = await update.callback_query.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        await update.callback_query.answer()
    else:
        sent = await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

@auto_delete_user_message
async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главное меню администратора"""
    print(f"🔥 admin_menu вызвана от пользователя {update.effective_user.id}")
    
    if not await is_chat_admin(update, context):
        print(f"❌ Доступ запрещён для пользователя {update.effective_user.id}")
        return
    
    log_admin_action(
        user_id=update.effective_user.id,
        action="menu_opened",
        details="Главное меню"
    )
    
    await show_menu(
        update,
        context,
        "🔧 <b>Админка Марафон</b>\n\nВыберите действие:",
        ADMIN_KEYBOARD
    )

@auto_delete_user_message
async def show_topics_submenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подменю управления темами"""
    if not await is_chat_admin(update, context):
        return
    
    log_admin_action(
        user_id=update.effective_user.id,
        action="menu_opened",
        details="Подменю тем"
    )
    
    await show_menu(
        update,
        context,
        "📋 <b>Управление темами</b>\n\nВыберите действие:",
        TOPICS_SUBMENU
    )