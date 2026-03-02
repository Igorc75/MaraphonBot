# admin/auth.py - обновленная версия
from telegram.ext import ContextTypes
from telegram import Update
from config import Config
from db.database import SessionLocal
from db.models import AdminSettings

async def is_chat_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, является ли пользователь администратором"""
    if not update.effective_user or not update.effective_chat:
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
    except Exception:
        pass
    finally:
        session.close()
    
    # 3. Для суперчатов дополнительно проверяем права в чате
    if update.effective_chat.type in ["group", "supergroup"]:
        try:
            admins = await context.bot.get_chat_administrators(update.effective_chat.id)
            admin_ids = [admin.user.id for admin in admins]
            return user_id in admin_ids
        except Exception:
            return False
    
    return False