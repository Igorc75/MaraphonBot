# utils/user_utils.py
from db.database import SessionLocal
from db.models import User

def get_user_display_info(user_id, rule_point_value=None, session=None):
    """
    Возвращает отображаемую информацию о пользователе с баллами
    Формат: Имя Фамилия (username/uid) - баллы
    
    Args:
        user_id: ID пользователя
        rule_point_value: Количество баллов (опционально)
        session: Сессия БД (опционально, создается если не передана)
    
    Returns:
        tuple: (display_name, points) или display_name если points не указаны
    """
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        user = session.query(User).filter_by(uid=user_id).first()
        
        if user:
            # Собираем имя/фамилию
            name_parts = []
            if user.name:
                name_parts.append(user.name)
            if user.fam:
                name_parts.append(user.fam)
            
            name_str = " ".join(name_parts) if name_parts else ""
            
            # Определяем идентификатор
            if user.username:
                identifier = f"@{user.username}"
            else:
                identifier = f"uid @{user_id}"
            
            # Формируем строку
            if name_str:
                display_name = f"{name_str} ({identifier})"
            else:
                display_name = identifier
        else:
            # Нет пользователя в базе
            display_name = f"uid @{user_id}"
        
        if rule_point_value is not None:
            return display_name, rule_point_value
        else:
            return display_name
    
    finally:
        if close_session:
            session.close()


def get_user_display_info_with_session(session, user_id, rule_point_value=None):
    """
    Альтернативная версия для использования с существующей сессией
    """
    return get_user_display_info(user_id, rule_point_value, session)