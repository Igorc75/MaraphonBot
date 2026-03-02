# test_callback_real.py
import sys
sys.path.append('.')

from telegram import Update, CallbackQuery, Message, User, Chat
from telegram.ext import CallbackQueryHandler
from admin.settings import handle_settings_callback
import asyncio

# Создаем мок-объекты для тестирования
def create_mock_update(callback_data: str):
    """Создает mock update объект для тестирования"""
    # Создаем пользователя
    user = User(id=90299004, first_name="Test", is_bot=False)
    
    # Создаем чат
    chat = Chat(id=90299004, type="private")
    
    # Создаем сообщение
    message = Message(
        message_id=1,
        date=None,
        chat=chat,
        text="Test"
    )
    
    # Создаем callback query
    callback_query = CallbackQuery(
        id="test_callback_id",
        from_user=user,
        chat_instance="test_chat_instance",
        data=callback_data,
        message=message
    )
    
    # Создаем update
    update = Update(update_id=1, callback_query=callback_query)
    
    return update

# Тестируем
handler = CallbackQueryHandler(handle_settings_callback)

print(f"✅ Обработчик создан: {handler}")

# Проверяем, что handler принимает update
test_data = [
    "toggle_csv_setting",
    "reset_settings", 
    "settings_back",
]

print("\n🔍 Тестируем обработчик с реальными объектами:")
for data in test_data:
    update = create_mock_update(data)
    try:
        # Проверяем, принимает ли handler этот update
        check_result = handler.check_update(update)
        print(f"  {data}: {'✅ принимается' if check_result else '❌ не принимается'}")
    except Exception as e:
        print(f"  {data}: ❌ ошибка - {e}")