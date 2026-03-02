# utils/__init__.py
from .cleanup import delete_after_5s, delete_after_3s
from .logger import log_hashtag_action, log_admin_action, log_error
from .stop_daemon import setup_stop_daemon, get_stop_daemon, StopDaemon
from .utils import get_current_time, is_admin
from .user_utils import get_user_display_info
from .responses import reply_and_delete
from .hashtag_utils import normalize_hashtag, validate_hashtag_prefix, extract_hashtags_from_text, match_hashtag_to_rule
from .auto_delete import reply_and_del, send_and_del  # ← ЭТА СТРОКА ДОЛЖНА БЫТЬ

__all__ = [
    'delete_after_5s',
    'delete_after_3s',
    'log_hashtag_action',
    'log_admin_action',
    'log_error',
    'get_current_time',
    'is_admin',
    'get_user_display_info',
    'reply_and_delete',
    'setup_stop_daemon',
    'get_stop_daemon',
    'StopDaemon',
    'normalize_hashtag',
    'validate_hashtag_prefix',
    'extract_hashtags_from_text',
    'match_hashtag_to_rule',
    'reply_and_del',
    'send_and_del',
    'auto_delete_user_message',
    'clean_chat',
    'save_message',
]