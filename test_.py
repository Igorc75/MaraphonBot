# test_callback_fixed.py
import sys
sys.path.append('.')

from telegram.ext import CallbackQueryHandler
from admin.settings import handle_settings_callback

# Создаем обработчик БЕЗ паттерна
handler = CallbackQueryHandler(handle_settings_callback)

print(f"✅ Обработчик создан: {handler}")
print(f"📋 Тип обработчика: {handler.__class__.__name__}")

# Тестовая функция для проверки check_update
def test_check_update(data_str):
    """Тестируем, как обработчик реагирует на данные"""
    # Создаем структуру, похожую на реальный callback
    update_dict = {
        'update_id': 123456,
        'callback_query': {
            'id': 'test_id',
            'from': {'id': 90299004, 'first_name': 'Test'},
            'message': {'message_id': 111, 'chat': {'id': 90299004}},
            'data': data_str
        }
    }
    
    try:
        # Метод check_update вернет либо объект для обработки, либо None
        result = handler.check_update(update_dict)
        return result is not None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

# Тестируем наши callback данные
test_data = [
    "toggle_csv_setting",
    "reset_settings", 
    "settings_back",
    "edit_topic_123",  # Должен быть пропущен
    "delete_topic_123" # Должен быть пропущен
]

print("\n🔍 Тестируем обработчик без паттерна:")
for data in test_data:
    matches = test_check_update(data)
    print(f"  {data}: {'✅ будет обработан' if matches else '❌ будет пропущен'}")