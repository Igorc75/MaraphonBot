# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///maraphon.db")
    TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    ALLOWED_CHAT_IDS = [int(x.strip()) for x in os.getenv("ALLOWED_CHAT_IDS", "").split(",") if x.strip()]
    
    # Настройки времени
    DELETE_ERROR_AFTER = 3    # секунды для ошибок
    DELETE_SUCCESS_AFTER = 5  # секунды для успешных действий

# Валидация при импорте
if not Config.BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN не задан в .env")
if not Config.ALLOWED_CHAT_IDS:
    raise ValueError("❌ ALLOWED_CHAT_IDS не задан в .env")
if not Config.ADMIN_IDS:
    raise ValueError("❌ ADMIN_IDS не задан в .env")