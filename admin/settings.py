# admin/settings.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from telegram.ext import ContextTypes
from db.database import SessionLocal
from db.models import AdminSettings, BotSettings
from config import Config
from .keyboards import SETTINGS_SUBMENU, ADMIN_KEYBOARD
from utils.logger import log_admin_action
import asyncio
import re
from utils.auto_delete import reply_and_del, auto_delete_user_message


# ==================== ФУНКЦИИ РАБОТЫ С БД ====================

def get_admin_settings(user_id: int):
    """Получает настройки администратора, создает если нет"""
    session = SessionLocal()
    try:
        settings = session.query(AdminSettings).filter_by(user_id=user_id).first()
        
        if not settings:
            if user_id in Config.ADMIN_IDS:
                settings = AdminSettings(
                    user_id=user_id,
                    receive_csv=False
                )
                session.add(settings)
                session.commit()
                session.refresh(settings)
            else:
                return None
        
        return settings
    except Exception as e:
        log_admin_action(
            user_id=user_id,
            action="error_get_settings",
            details=f"Ошибка получения настроек: {str(e)}"
        )
        session.rollback()
        return None
    finally:
        session.close()

def update_admin_settings(user_id: int, receive_csv: bool = None):
    """Обновляет настройки администратора"""
    session = SessionLocal()
    try:
        settings = session.query(AdminSettings).filter_by(user_id=user_id).first()
        
        if not settings:
            if user_id in Config.ADMIN_IDS:
                settings = AdminSettings(user_id=user_id)
            else:
                return False
        
        if receive_csv is not None:
            settings.receive_csv = receive_csv
        
        session.add(settings)
        session.commit()
        return True
    except Exception as e:
        log_admin_action(
            user_id=user_id,
            action="error_update_settings",
            details=f"Ошибка обновления настроек: {str(e)}"
        )
        session.rollback()
        return False
    finally:
        session.close()

def get_admins_wanting_csv():
    """Возвращает список администраторов, которые хотят получать CSV"""
    session = SessionLocal()
    try:
        admins = session.query(AdminSettings).filter_by(receive_csv=True).all()
        admin_ids = [admin.user_id for admin in admins]
        return admin_ids
    except Exception as e:
        log_admin_action(
            user_id=0,
            action="error_get_csv_admins",
            details=f"Ошибка получения списка админов с CSV: {str(e)}"
        )
        return []
    finally:
        session.close()

# ==================== BOT SETTINGS ====================

def get_bot_settings() -> BotSettings:
    """Singleton-настройки бота (одна строка)"""
    session = SessionLocal()
    try:
        settings = session.query(BotSettings).filter_by(id=1).first()
        if not settings:
            settings = BotSettings(id=1, intro_chat_id=None, intro_thread_id=None)
            session.add(settings)
            session.commit()
            session.refresh(settings)
        return settings
    finally:
        session.close()

def set_intro_chat_id(intro_chat_id: int | None, intro_thread_id: int | None = None) -> bool:
    """Устанавливает ID чата и ID темы для знакомств"""
    session = SessionLocal()
    try:
        settings = session.query(BotSettings).filter_by(id=1).first()
        if not settings:
            settings = BotSettings(id=1)
        settings.intro_chat_id = intro_chat_id
        settings.intro_thread_id = intro_thread_id
        session.add(settings)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()

def parse_chat_id_from_link(text: str) -> tuple[int | None, int | None]:
    """
    Парсит ссылку вида:
    - https://t.me/c/1234567890/123  -> возвращает (-1001234567890, 123)
    - t.me/c/1234567890/123
    - -1001234567890 (числовой ID чата) -> возвращает (ID, None)
    """
    if not text:
        return None, None
    raw = text.strip()

    # Если это просто числовой ID (возможно с минусом)
    if re.fullmatch(r"-?\d{8,20}", raw):
        try:
            return int(raw), None
        except ValueError:
            return None, None

    # Ищем ссылку формата t.me/c/.../...
    m = re.search(r"(?:https?://)?t\.me/c/(\d{5,15})/(\d+)", raw)
    if not m:
        return None, None

    digits = m.group(1)   # часть ID чата (без -100)
    thread_id = int(m.group(2))

    # Формируем полный chat_id для супергруппы
    try:
        chat_id = -int(f"100{digits}")
        return chat_id, thread_id
    except ValueError:
        return None, None

# ==================== ОБРАБОТЧИКИ ТЕЛЕГРАМ ====================

@auto_delete_user_message
async def show_settings_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает панель настроек администратора"""
    if update.effective_user.id not in Config.ADMIN_IDS:
        return
    
    log_admin_action(
        user_id=update.effective_user.id,
        action="settings_panel_opened",
        details="Открыта панель настроек"
    )
    
    from admin.menu import show_menu
    await show_menu(
        update,
        context,
        "⚙️ <b>Настройки бота</b>\n\nВыберите раздел:",
        SETTINGS_SUBMENU
    )

async def csv_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки '📁 CSV отчеты'"""
    if update.effective_user.id not in Config.ADMIN_IDS:
        return
    
    user_id = update.effective_user.id
    settings = get_admin_settings(user_id)
    
    if not settings:
        await reply_and_del(update.message,  # ← заменено на reply_and_del
            "❌ Не удалось загрузить настройки. Проверьте подключение к БД.",
            reply_markup=SETTINGS_SUBMENU
        )
        return
    
    # Сообщение с инлайн-кнопками - НЕ УДАЛЯЕМ (оставляем как есть)
    text = (
        "⚙️ <b>Настройки администратора</b>\n\n"
        f"🆔 Ваш ID: {user_id}\n"
        f"👤 Имя: {update.effective_user.first_name or ''} {update.effective_user.last_name or ''}\n"
        f"📛 Юзернейм: @{update.effective_user.username or 'не указан'}\n\n"
        f"📁 <b>Получать CSV файлы после СТОП:</b> {'✅ ВКЛ' if settings.receive_csv else '❌ ВЫКЛ'}\n\n"
        "Выберите опцию для изменения:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"CSV после СТОП: {'ВКЛ' if settings.receive_csv else 'ВЫКЛ'}",
                callback_data="toggle_csv_setting"
            )
        ],
        [
            InlineKeyboardButton("Назад к настройкам", callback_data="settings_back")
        ]
    ]
    
    await update.message.reply_text(  # ← оставляем обычный reply_text (с кнопками)
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def intro_chat_settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройка чата 'Знакомство'"""
    if update.effective_user.id not in Config.ADMIN_IDS or update.effective_chat.type != "private":
        return

    settings = get_bot_settings()
    intro_chat_id = settings.intro_chat_id
    intro_thread_id = settings.intro_thread_id

    if intro_chat_id:
        try:
            chat = await context.bot.get_chat(intro_chat_id)
            thread_info = f", тема {intro_thread_id}" if intro_thread_id else ""
            intro_text = f"{chat.title} (ID: {intro_chat_id}{thread_info})"
        except:
            intro_text = f"<code>{intro_chat_id}</code> (недоступен)"
    else:
        intro_text = "не задан"

    text = (
        f"👋 <b>Настройка чата знакомства</b>\n\n"
        f"Текущий чат: {intro_text}\n\n"
        f"📝 <b>Как настроить:</b>\n"
        f"1. Откройте нужный чат/тему в Telegram\n"
        f"2. Скопируйте ссылку на сообщение (например: https://t.me/c/3849962819/2)\n"
        f"3. Нажмите кнопку «Установить по ссылке» и отправьте ссылку\n\n"
        f"Или отправьте числовой ID чата (например -1001234567890)"
    )

    keyboard = [
        [InlineKeyboardButton("🔗 Установить по ссылке", callback_data="introchat_set")],
        [InlineKeyboardButton("🗑️ Сбросить", callback_data="introchat_reset")],
        [InlineKeyboardButton("⬅️ Назад к настройкам", callback_data="settings_back")]
    ]

    # Отправляем сообщение с инструкцией
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def handle_intro_chat_link_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Обрабатывает сообщение со ссылкой на чат знакомства, когда включён режим ожидания.
    Возвращает True, если сообщение было обработано (чтобы не парсить как тему).
    """
    if not context.user_data.get("awaiting_intro_chat_link"):
        return False
    context.user_data["awaiting_intro_chat_link"] = False

    text = update.message.text if update.message else ""
    intro_chat_id, intro_thread_id = parse_chat_id_from_link(text)

    if not intro_chat_id:
        await reply_and_del(update.message,
            "❌ Неверный формат.\n\nПример ссылки:\n"
            "<code>https://t.me/c/3849962819/2</code>\n\n"
            "Или пришлите числовой chat_id (например <code>-100...</code>).",
            parse_mode="HTML",
            reply_markup=SETTINGS_SUBMENU,
        )
        return True

    # Проверяем, что бот состоит в этом чате и чат доступен
    try:
        chat = await context.bot.get_chat(intro_chat_id)
        if chat.type not in ["group", "supergroup"]:
            await reply_and_del(update.message,
                "❌ Указанный чат не является группой или супергруппой.",
                reply_markup=SETTINGS_SUBMENU
            )
            return True
    except TelegramError as e:
        await reply_and_del(update.message,
            f"❌ Не удалось получить информацию о чате.\nОшибка: {e}",
            reply_markup=SETTINGS_SUBMENU
        )
        return True

    ok = set_intro_chat_id(intro_chat_id, intro_thread_id)
    if ok:
        thread_info = f", тема {intro_thread_id}" if intro_thread_id else ""
        await reply_and_del(update.message,
            f"✅ Чат знакомства установлен: {chat.title} (ID: {intro_chat_id}{thread_info})",
            parse_mode="HTML",
            reply_markup=SETTINGS_SUBMENU,
        )
    else:
        await reply_and_del(update.message,
            "❌ Не удалось сохранить настройку.",
            reply_markup=SETTINGS_SUBMENU
        )
    return True

async def handle_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает callback от настроек"""
    query = update.callback_query
    
    await query.answer()
    
    if query.data not in [
        "toggle_csv_setting",
        "settings_back",
        "settings_panel",
        "introchat_set",
        "introchat_reset",
    ]:
        return
    
    user_id = query.from_user.id
    
    if not query.message:
        return
    
    if query.data == "toggle_csv_setting":
        settings = get_admin_settings(user_id)
        if not settings:
            await reply_and_del(query.message, "❌ Ошибка: настройки не найдены")  # ← заменено
            return
        
        new_value = not settings.receive_csv
        success = update_admin_settings(user_id, receive_csv=new_value)
        
        if success:
            log_admin_action(
                user_id=user_id,
                action="csv_setting_toggled",
                details=f"CSV настройка изменена на: {new_value}"
            )
            
            # Обновляем текст сообщения (это inline сообщение с кнопками - НЕ УДАЛЯЕМ)
            text = (
                "⚙️ <b>Настройки администратора</b>\n\n"
                f"🆔 Ваш ID: {user_id}\n"
                f"👤 Имя: {query.from_user.first_name or ''} {query.from_user.last_name or ''}\n"
                f"📛 Юзернейм: @{query.from_user.username or 'не указан'}\n\n"
                f"📁 <b>Получать CSV файлы после СТОП:</b> {'✅ ВКЛ' if new_value else '❌ ВЫКЛ'}\n\n"
                "Выберите опцию для изменения:"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        f"CSV после СТОП: {'ВКЛ' if new_value else 'ВЫКЛ'}",
                        callback_data="toggle_csv_setting"
                    )
                ],
                [
                    InlineKeyboardButton("Назад к настройкам", callback_data="settings_back")
                ]
            ]
            
            await query.message.edit_text(  # ← edit_text оставляем как есть
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
        else:
            await reply_and_del(query.message, "❌ Ошибка при обновлении настроек")  # ← заменено
    
    elif query.data == "settings_back":
        # Удаляем текущее сообщение
        await query.message.delete()
        # Вызываем возврат в меню
        from admin.menu import admin_menu
        await admin_menu(update, context)

    elif query.data == "settings_panel":
        # НЕ ОТПРАВЛЯЕМ СООБЩЕНИЕ - только логируем
        log_admin_action(
            user_id=user_id,
            action="settings_panel_callback",
            details="Возврат к панели настроек"
        )

    elif query.data == "introchat_set":
        if query.message:
            context.user_data["awaiting_intro_chat_link"] = True
            # Отправляем сообщение с инструкцией
            await query.message.reply_text(
                "📝 <b>Настройка чата знакомства</b>\n\n"
                "Отправьте ссылку на сообщение в нужной теме:\n"
                "<code>https://t.me/c/3849962819/2</code>\n\n"
                "Или просто числовой ID чата:\n"
                "<code>-1001234567890</code>\n\n"
                "⏳ Ожидаю ссылку...",
                parse_mode='HTML'
            )
            # Логируем действие
            log_admin_action(
                user_id=user_id,
                action="introchat_set",
                details="Ожидание ссылки на чат знакомства"
            )

    elif query.data == "introchat_reset":
        set_intro_chat_id(None, None)
        if query.message:
            await reply_and_del(query.message,  # ← заменено
                "✅ Чат знакомства сброшен.",
                reply_markup=SETTINGS_SUBMENU
            )