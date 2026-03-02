# test_callback.py
import sys
sys.path.append('.')

from telegram.ext import CallbackQueryHandler
from admin.settings import handle_settings_callback

# Проверяем паттерн обработчика
handler = CallbackQueryHandler(
    handle_settings_callback, 
    pattern="^(toggle_csv_setting|reset_settings|settings_back)$"
)

print(f"✅ Обработчик создан: {handler}")
print(f"📋 Паттерн: {handler.pattern}")

# Проверяем совпадение паттернов
test_data = [
    "toggle_csv_setting",
    "reset_settings", 
    "settings_back",
    "edit_topic_123",  # Не должен совпадать
    "delete_topic_123" # Не должен совпадать
]

for data in test_data:
    matches = handler.check_update({'data': data})
    print(f"  {data}: {'✅ совпадает' if matches else '❌ не совпадает'}")