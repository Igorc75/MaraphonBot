# utils/logger.py
import logging
from datetime import datetime
from pathlib import Path

# Настройка логгера
logger = logging.getLogger("maraphon_bot")
logger.setLevel(logging.INFO)

# Создаем папку logs если её нет
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Форматтер
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Файловый обработчик
file_handler = logging.FileHandler(log_dir / "bot.log", encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Консольный обработчик (если нужно)
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)

def log_hashtag_action(
    user_id: int,
    username: str,
    thread_id: int,
    hashtag: str,
    status: str,
    reason: str = ""  # ← ОБЯЗАТЕЛЬНЫЙ параметр теперь
):
    """
    Логирует действие с хештегом
    
    Args:
        user_id: ID пользователя
        username: Имя пользователя
        thread_id: ID темы
        hashtag: Хештег
        status: "принят" или "отвергнут"
        reason: Причина (обязательно для "отвергнут")
    """
    display_name = f"@{username}" if username else f"user_{user_id}"
    
    if status == "принят":
        log_message = f"{display_name} | тема {thread_id} | #{hashtag} | ПРИНЯТ"
    elif status == "отвергнут":
        if not reason:
            reason = "причина не указана"
        log_message = f"{display_name} | тема {thread_id} | #{hashtag} | ОТВЕРГНУТ ({reason})"
    else:
        log_message = f"{display_name} | тема {thread_id} | #{hashtag} | {status.upper()}"
    
    logger.info(log_message)

def log_admin_action(user_id: int, action: str, details: str = ""):
    """Логирует действие администратора"""
    details_text = f" | {details}" if details else ""
    logger.info(f"ADMIN {user_id} | {action}{details_text}")

def log_error(error: Exception, context: str = ""):
    """Логирует ошибку"""
    context_text = f" [{context}]" if context else ""
    logger.error(f"{type(error).__name__}{context_text}: {error}")