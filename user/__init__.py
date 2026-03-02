# user/__init__.py
from .message_handler import handle_message, process_hashtag, normalize_hashtag

__all__ = [
    'handle_message',
    'process_hashtag', 
    'normalize_hashtag',
    'handle_registration'
]