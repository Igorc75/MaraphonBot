# utils/utils.py - удаляем extract_hashtags
from datetime import datetime, timedelta
import pytz
from config import Config

def get_current_time():
    """Возвращает текущее время в московской зоне"""
    tz = pytz.timezone(Config.TIMEZONE)
    return datetime.now(tz)

def is_admin(user_id: int) -> bool:
    """Проверяет права администратора"""
    return user_id in Config.ADMIN_IDS

# УДАЛЯЕМ старую функцию extract_hashtags - теперь она в hashtag_utils.py