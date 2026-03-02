# main.py
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, filters, CallbackQueryHandler
)
from config import Config

# Отключаем ВСЁ лишнее
import warnings
warnings.filterwarnings("ignore")
import logging

# Отключаем лишние логи, оставляем только INFO и выше для основного логгера
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# Включаем логирование для нашего бота
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Импорты
from admin.menu import admin_menu, show_topics_submenu
from admin.topics_list import list_topics
from admin.topic_add import request_topic_format, add_topic_single
from admin.topic_edit import (
    show_edit_topics, edit_topic_select, edit_topic_field, 
    edit_topic_value, edit_cancel, timeout_handler
)
from admin.topic_delete import (
    start_delete_topic, delete_topic_select, confirm_delete
)
from admin.stats import stats_handler
from admin.settings import (
    show_settings_panel,
    csv_settings_handler,
    handle_settings_callback,
    intro_chat_settings_handler,
)  # ← Используем show_settings_panel
from admin.admin_manager import show_admin_management, admin_management_callback, handle_invite_token
from admin.states import (
    EDIT_TOPIC_SELECT, EDIT_TOPIC_FIELD, EDIT_TOPIC_VALUE,
    DELETE_TOPIC_SELECT, DELETE_CONFIRM
)
from user.message_handler import handle_message
from utils.stop_daemon import setup_stop_daemon

# Новая функция для обработки команды /start с инвайтами
async def start_command(update, context):
    """Обработчик команды /start с поддержкой инвайт-токенов"""
    # Проверяем аргументы команды /start
    args = context.args
    
    if args and args[0].startswith('admin_'):
        # Пользователь перешел по инвайт-ссылке
        token = args[0].replace('admin_', '')  # Убираем префикс 'admin_'
        user_id = update.effective_user.id
        
        # Обрабатываем токен
        success, message = await handle_invite_token(user_id, token, context)
        
        # Отправляем результат пользователю
        await update.message.reply_text(message, parse_mode='HTML')
        
        # Если успешно добавлен как администратор, показываем админ-меню
        if success:
            await admin_menu(update, context)
    else:
        # Обычный запуск /start - показываем админ-меню
        await admin_menu(update, context)

def main():
    """Основная функция запуска бота"""
    # Проверка конфигурации
    if not Config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN не задан")
    if not Config.ALLOWED_CHAT_IDS:
        raise ValueError("ALLOWED_CHAT_IDS не задан")
    if not Config.ADMIN_IDS:
        raise ValueError("ADMIN_IDS не задан")
    
    # Создание приложения
    app = Application.builder().token(Config.BOT_TOKEN).build()

    # Запуск систем (БЕЗ ЛОГОВ О ЗАПУСКЕ)
    stop_daemon = setup_stop_daemon(app)
    if stop_daemon:
        print("✅ Демон точных СТОП запущен")
    else:
        print("❌ Демон СТОП не запустился")

    # ConversationHandler для редактирования тем
    edit_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✏️ Редактировать$"), show_edit_topics)],
        states={
            EDIT_TOPIC_SELECT: [
                CallbackQueryHandler(edit_topic_select, pattern=r"^edit_(topic_\d+|cancel)$")
            ],
            EDIT_TOPIC_FIELD: [
                CallbackQueryHandler(edit_topic_field, pattern=r"^edit_(field_.+|back|cancel)$")
            ],
            EDIT_TOPIC_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_topic_value)],
        },
        fallbacks=[
            CommandHandler("cancel", edit_cancel),
            MessageHandler(filters.Regex("^(⬅️ Назад|❌ Отмена)$"), edit_cancel),
            MessageHandler(filters.TEXT, timeout_handler)
        ],
        conversation_timeout=30,
        per_message=False,
        allow_reentry=True,
    )
    
    # ConversationHandler для удаления тем
    delete_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗑️ Удалить$"), start_delete_topic)],
        states={
            DELETE_TOPIC_SELECT: [
                CallbackQueryHandler(delete_topic_select, pattern=r"^(delete_topic_\d+|delete_cancel)$")
            ],
            DELETE_CONFIRM: [
                CallbackQueryHandler(confirm_delete, pattern=r"^(confirm_delete_\d+|confirm_cancel_\d+)$")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", lambda u, c: ConversationHandler.END),
            MessageHandler(filters.Regex("^⬅️ Назад$"), lambda u, c: ConversationHandler.END)
        ],
        per_message=False,
        allow_reentry=True,
    )
    
    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start_command))  # Используем новую функцию
    app.add_handler(CommandHandler("admin", admin_menu))
    
    # Главное меню
    app.add_handler(MessageHandler(filters.Regex("^📋 Темы$"), show_topics_submenu))
    app.add_handler(MessageHandler(filters.Regex("^📊 Статистика$"), stats_handler))
    
    # Настройки - показываем подменю
    app.add_handler(MessageHandler(filters.Regex("^⚙️ Настройка$"), show_settings_panel))
    
    # Подменю настроек
    app.add_handler(MessageHandler(filters.Regex("^📁 CSV отчеты$"), csv_settings_handler))
    app.add_handler(MessageHandler(filters.Regex("^👋 Чат знакомства$"), intro_chat_settings_handler))
    app.add_handler(MessageHandler(filters.Regex("^👥 Админы$"), show_admin_management))
    
    # Темы
    app.add_handler(MessageHandler(filters.Regex("^👁️ Список тем$"), list_topics))
    app.add_handler(MessageHandler(filters.Regex("^➕ Добавить$"), request_topic_format))
    app.add_handler(delete_conv)
    
    # Обработчик редактирования
    app.add_handler(edit_conv)
    
    # Навигация (исправленные регулярные выражения)
    app.add_handler(MessageHandler(filters.Regex("^(⬅️ Назад в меню|⬅️ Назад)$"), admin_menu))
    app.add_handler(MessageHandler(filters.Regex("^⬅️ Назад к настройкам$"), show_settings_panel))
    app.add_handler(MessageHandler(filters.Regex("^⬅️ Назад к управлению админами$"), show_admin_management))
    
    # Обработка добавления тем
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, add_topic_single))
    
    # Обработка сообщений в чатах (внутри handle_message есть строгая фильтрация по нужным chat_id)
    app.add_handler(MessageHandler((filters.TEXT | filters.CAPTION) & ~filters.COMMAND, handle_message))
    
    app.add_handler(CallbackQueryHandler(admin_management_callback, pattern="^admin_"))

    # Регистрируем обработчики callback для настроек, расписания и управления админами - ПОСЛЕДНИМ
    app.add_handler(CallbackQueryHandler(handle_settings_callback)) 
    
    

    # Чистый запуск
    print("=" * 60)
    print("🚀 Maraphon Bot запущен")
    print("👥 Система инвайт-ссылок для админов активирована")
    print("📅 СТОП будет отправляться секунда в секунду по окончанию времени")
    print("=" * 60)
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()