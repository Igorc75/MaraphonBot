# admin/keyboards.py
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
ADMIN_KEYBOARD = ReplyKeyboardMarkup(
    [["📋 Темы"], ["📊 Статистика"], ["⚙️ Настройка"]],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Выберите действие..."
)

# Подменю тем
TOPICS_SUBMENU = ReplyKeyboardMarkup(
    [
        ["👁️ Список тем", "➕ Добавить"],
        ["✏️ Редактировать", "🗑️ Удалить"],
        ["⬅️ Назад в меню"]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Действие с темами..."
)

# Подменю настроек
SETTINGS_SUBMENU = ReplyKeyboardMarkup(
    [
        ["📁 CSV отчеты", "👥 Админы"],
        ["👋 Чат знакомства"],
        ["⬅️ Назад в меню"]
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
    input_field_placeholder="Выберите настройку..."
)

# Клавиатура для возврата к настройкам
BACK_TO_SETTINGS = ReplyKeyboardMarkup(
    [["⬅️ Назад к настройкам"]],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Клавиатура для возврата к управлению админами
BACK_TO_ADMIN_MANAGEMENT = ReplyKeyboardMarkup(
    [["⬅️ Назад к управлению админами"]],
    resize_keyboard=True,
    one_time_keyboard=False
)