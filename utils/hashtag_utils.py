# utils/hashtag_utils.py
"""Утилиты для работы с хештегами - единая логика для всего проекта"""

def normalize_hashtag(hashtag: str) -> str:
    """
    Нормализует хештег: убирает #, приводит к нижнему регистру, обрезает пробелы.
    Используется везде в проекте для единообразия.
    
    Args:
        hashtag: Строка с хештегом (может быть с # или без)
    
    Returns:
        Нормализованный хештег без # в нижнем регистре
    """
    if not hashtag:
        return ""
    
    # Убираем пробелы
    hashtag = hashtag.strip()
    
    # Убираем # если есть в начале
    if hashtag.startswith('#'):
        hashtag = hashtag[1:].strip()
    
    # Приводим к нижнему регистру
    return hashtag.lower()

def validate_hashtag_prefix(hashtag: str) -> tuple[bool, str]:
    """
    Проверяет валидность префикса хештега для сохранения в БД.
    
    Args:
        hashtag: Хештег для проверки
        
    Returns:
        tuple: (is_valid, error_message)
    """
    hashtag = normalize_hashtag(hashtag)
    
    if not hashtag:
        return False, "Хештег не может быть пустым"
    
    if len(hashtag) > 100:
        return False, "Хештег слишком длинный (макс. 100 символов)"
    
    # Проверяем допустимые символы (буквы, цифры, подчеркивание, дефис)
    import re
    if not re.match(r'^[a-zа-яё0-9_-]+$', hashtag):
        return False, "Хештег содержит недопустимые символы. Допустимо: буквы, цифры, _, -"
    
    # Предупреждение, если хештег заканчивается на подчеркивание
    warning = ""
    if hashtag.endswith('_'):
        warning = "⚠️ Внимание: хештег заканчивается на подчеркивание! Это может повлиять на обработку хештегов пользователей."
    
    return True, warning

def extract_hashtags_from_text(text: str) -> list[str]:
    """
    Извлекает все хештеги из текста и нормализует их.
    
    Args:
        text: Текст для парсинга
        
    Returns:
        Список нормализованных хештегов
    """
    if not text:
        return []
    
    import re
    # Находим все слова, начинающиеся с #
    raw_hashtags = re.findall(r'#(\w+[\w_-]*)', text)
    
    # Нормализуем каждый хештег
    return [normalize_hashtag(tag) for tag in raw_hashtags]

def match_hashtag_to_rule(hashtag: str, rule_hashtag_prefix: str) -> bool:
    """
    Проверяет, соответствует ли хештег правилу.
    
    Args:
        hashtag: Нормализованный хештег
        rule_hashtag_prefix: Префикс хештега из правила
        
    Returns:
        True если хештег соответствует правилу
    """
    # Если хештег точно совпадает с префиксом
    if hashtag == rule_hashtag_prefix:
        return True
    
    # Если хештег начинается с префикса и заканчивается чем-то после подчеркивания
    # Пример: префикс="послевкусие", хештег="послевкусие_01"
    if hashtag.startswith(rule_hashtag_prefix + '_'):
        return True
    
    return False