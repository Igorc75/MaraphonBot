# admin/admin_manager.py
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from db.database import SessionLocal
from db.models import AdminInvite, AdminInviteUsage, AdminSettings
from config import Config
from .decorators import admin_required
from .keyboards import ADMIN_KEYBOARD, BACK_TO_ADMIN_MANAGEMENT
from admin.auth import is_chat_admin
import asyncio
from utils.cleanup import delete_after_3s
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_invite_token(length=32) -> str:
    """Генерирует безопасный токен для инвайта"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_invite_link(bot_username: str, token: str) -> str:
    """Создает ссылку для приглашения"""
    return f"https://t.me/{bot_username}?start=admin_{token}"

async def show_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню управления администраторами - сразу список админов"""
    if not await is_chat_admin(update, context):
        return
    
    # Получаем список админов
    text, keyboard = await get_admins_list_with_actions(context)
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def get_admins_list_with_actions(context: ContextTypes.DEFAULT_TYPE):
    """Возвращает текст списка админов и клавиатуру действий"""
    try:
        # Получаем суперадминов из конфига
        super_admins = Config.ADMIN_IDS
        
        # Получаем администраторов из базы
        session = SessionLocal()
        db_admins = session.query(AdminSettings).all()
        session.close()
        
        # Формируем текст
        text = "👥 <b>Управление администраторами</b>\n\n"
        
        # Суперадмины (из .env)
        text += "<b>🔸 Суперадминистраторы (из .env):</b>\n"
        for i, admin_id in enumerate(super_admins, 1):
            try:
                user = await context.bot.get_chat(admin_id)
                name = user.first_name or user.username or f"ID: {admin_id}"
                text += f"{i}. 👑 {name} (ID: <code>{admin_id}</code>)\n"
            except:
                text += f"{i}. 👑 ID: <code>{admin_id}</code> (не найден в Telegram)\n"
        
        # Администраторы из базы
        text += "\n<b>🔹 Администраторы (добавленные):</b>\n"
        if db_admins:
            for i, admin in enumerate(db_admins, 1):
                try:
                    user = await context.bot.get_chat(admin.user_id)
                    name = user.first_name or user.username or f"ID: {admin.user_id}"
                    
                    # Проверяем, активен ли администратор
                    is_active = "✅" if admin.receive_csv is not None else "⚠️"
                    text += f"{i}. {is_active} {name} (ID: <code>{admin.user_id}</code>)\n"
                except:
                    text += f"{i}. ⚠️ ID: <code>{admin.user_id}</code> (не найден в Telegram)\n"
        else:
            text += "  📭 Нет добавленных администраторов\n"
        
        # Статистика
        total = len(super_admins) + len(db_admins)
        text += f"\n📊 <b>Всего администраторов:</b> {total}\n"
        
        # Клавиатура действий
        keyboard = []
        
        # Основные действия
        keyboard.append([
            InlineKeyboardButton("➕ Создать инвайт-ссылку", callback_data="admin_create_invite"),
            InlineKeyboardButton("📋 Активные инвайты", callback_data="admin_list_invites")
        ])
        
        # Кнопки удаления для каждого админа из базы
        if db_admins:
            for admin in db_admins:
                if admin.user_id not in Config.ADMIN_IDS:  # Не удаляем суперадминов
                    try:
                        user = await context.bot.get_chat(admin.user_id)
                        name = user.first_name or user.username[:15] or f"ID:{admin.user_id}"
                    except:
                        name = f"ID:{admin.user_id}"
                    
                    keyboard.append([
                        InlineKeyboardButton(
                            f"🗑️ Удалить {name}", 
                            callback_data=f"admin_delete_{admin.user_id}"
                        )
                    ])
        
        # Кнопка назад
        keyboard.append([InlineKeyboardButton("⬅️ Назад к настройкам", callback_data="admin_management_back")])
        
        return text, keyboard
        
    except Exception as e:
        logger.error(f"Ошибка получения списка админов: {e}")
        return f"❌ Ошибка: {str(e)}", [[InlineKeyboardButton("⬅️ Назад", callback_data="admin_management_back")]]

@admin_required
async def create_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создает новую инвайт-ссылку"""
    logger.info("=" * 50)
    logger.info("ФУНКЦИЯ create_invite ВЫЗВАНА")
    
    # Проверяем тип update
    if update.callback_query:
        logger.info(f"Тип: callback_query, данные: {update.callback_query.data}")
        query = update.callback_query
        await query.answer()
        message = query.message
        user_id = query.from_user.id
    elif update.message:
        logger.info(f"Тип: message, текст: {update.message.text}")
        message = update.message
        user_id = update.message.from_user.id
    else:
        logger.error("Неизвестный тип update")
        return
    
    logger.info(f"User ID: {user_id}")
    
    session = SessionLocal()
    try:
        # Генерируем токен
        token = generate_invite_token()
        logger.info(f"Сгенерирован токен: {token}")
        
        # Создаем инвайт (действует 24 часа, одноразовый)
        expires_at = datetime.now() + timedelta(hours=24)
        invite = AdminInvite(
            token=token,
            created_by=user_id,
            expires_at=expires_at,
            max_uses=1,
            is_active=True
        )
        
        session.add(invite)
        session.commit()
        logger.info(f"Инвайт сохранен в БД с ID: {invite.id}")
        
        # Получаем username бота
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username
        logger.info(f"Bot username: {bot_username}")
        
        # Создаем ссылку
        invite_link = create_invite_link(bot_username, token)
        logger.info(f"Создана ссылка: {invite_link}")
        
        # Формируем сообщение
        text = (
            f"✅ <b>Инвайт-ссылка создана!</b>\n\n"
            f"🔗 <code>{invite_link}</code>\n\n"
            f"📊 <b>Информация:</b>\n"
            f"• Действует: 24 часа\n"
            f"• Одноразовая\n"
            f"• Создана: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"• Истекает: {expires_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📋 <b>Отправьте эту ссылку новому администратору.</b>\n"
            f"При переходе по ссылке пользователь будет добавлен в администраторы."
        )
        
        keyboard = [
            [InlineKeyboardButton("📋 К списку админов", callback_data="admin_list_refresh")],
            [InlineKeyboardButton("⬅️ Назад к настройкам", callback_data="admin_management_back")]
        ]
        
        # Отправляем сообщение
        try:
            if update.callback_query:
                # Пытаемся отредактировать существующее сообщение
                try:
                    await message.edit_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
                    logger.info("Сообщение отредактировано")
                except Exception as e:
                    logger.warning(f"Не удалось отредактировать: {e}")
                    # Отправляем новое сообщение
                    await message.reply_text(
                        text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
                    logger.info("Отправлено новое сообщение")
            else:
                # Просто отправляем новое сообщение
                await message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                logger.info("Отправлено новое сообщение (из message)")
            
            # Дополнительно отправляем ссылку в личные сообщения
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🔗 <b>Ваша инвайт-ссылка:</b>\n<code>{invite_link}</code>",
                    parse_mode='HTML'
                )
                logger.info("Ссылка отправлена в ЛС")
            except Exception as e:
                logger.warning(f"Не удалось отправить в ЛС: {e}")
            
            logger.info("✅ Инвайт-ссылка успешно создана и отправлена")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения: {e}")
        
    except Exception as e:
        logger.error(f"ОШИБКА создания инвайта: {e}", exc_info=True)
        session.rollback()
        
        error_text = f"❌ Ошибка: {str(e)}"
        try:
            if update.callback_query:
                await message.edit_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_management_back")]
                    ])
                )
            else:
                await message.reply_text(
                    error_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_management_back")]
                    ])
                )
        except:
            pass
    finally:
        session.close()
        logger.info("=" * 50)

async def list_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список активных инвайтов"""
    query = update.callback_query
    await query.answer()
    
    session = SessionLocal()
    try:
        invites = session.query(AdminInvite).filter_by(is_active=True).all()
        
        if not invites:
            await query.message.edit_text(
                "📭 <b>Нет активных инвайт-ссылок</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Создать инвайт", callback_data="admin_create_invite")],
                    [InlineKeyboardButton("⬅️ Назад к списку админов", callback_data="admin_list_refresh")]
                ]),
                parse_mode='HTML'
            )
            return
        
        # Получаем username бота для формирования ссылок
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username
        
        text = "📋 <b>Активные инвайт-ссылки:</b>\n\n"
        
        for invite in invites:
            status = "✅" if invite.is_active else "❌"
            expires_in = (invite.expires_at - datetime.now()).total_seconds() / 3600
            
            if expires_in <= 0:
                status = "⌛"
            
            invite_link = create_invite_link(bot_username, invite.token)
            
            text += f"{status} <b>Инвайт #{invite.id}</b>\n"
            text += f"   🔗 <code>{invite_link}</code>\n"
            text += f"   👤 Использован: {invite.used_count}/{invite.max_uses}\n"
            text += f"   ⏰ Истекает через: {expires_in:.1f} часов\n"
            text += f"   📅 Создан: {invite.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Создать новый инвайт", callback_data="admin_create_invite")],
            [InlineKeyboardButton("🗑️ Удалить истёкшие", callback_data="admin_cleanup_invites")],
            [InlineKeyboardButton("⬅️ Назад к списку админов", callback_data="admin_list_refresh")]
        ]
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения списка инвайтов: {e}")
        await query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_management_back")]
            ])
        )
    finally:
        session.close()

async def delete_admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает удаление администратора"""
    query = update.callback_query
    await query.answer()
    
    # Получаем ID админа для удаления
    admin_id = int(query.data.split("_")[2])
    
    # Проверяем, что не пытаемся удалить суперадмина из .env
    if admin_id in Config.ADMIN_IDS:
        await query.message.edit_text(
            "❌ <b>Нельзя удалить суперадминистратора (из .env)</b>\n\n"
            "Суперадминистраторы управляются через файл конфигурации.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад к списку админов", callback_data="admin_list_refresh")]
            ]),
            parse_mode='HTML'
        )
        return
    
    session = SessionLocal()
    try:
        # Ищем админа в базе
        admin = session.query(AdminSettings).filter_by(user_id=admin_id).first()
        
        if not admin:
            await query.message.edit_text(
                f"❌ Администратор с ID <code>{admin_id}</code> не найден в базе",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад к списку админов", callback_data="admin_list_refresh")]
                ]),
                parse_mode='HTML'
            )
            return
        
        # Запрашиваем подтверждение
        try:
            user = await context.bot.get_chat(admin_id)
            admin_name = user.first_name or user.username or f"ID: {admin_id}"
        except:
            admin_name = f"ID: {admin_id}"
        
        confirm_text = (
            f"⚠️ <b>Подтверждение удаления</b>\n\n"
            f"Вы действительно хотите удалить администратора?\n\n"
            f"👤 <b>{admin_name}</b>\n"
            f"🆔 ID: <code>{admin_id}</code>\n\n"
            f"Это действие нельзя отменить!"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, удалить", callback_data=f"admin_delete_confirm_{admin_id}"),
                InlineKeyboardButton("❌ Нет, отмена", callback_data="admin_list_refresh")
            ]
        ]
        
        await query.message.edit_text(
            confirm_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка при подготовке удаления: {e}")
        await query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_management_back")]
            ])
        )
    finally:
        session.close()

async def confirm_delete_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждает и выполняет удаление администратора"""
    query = update.callback_query
    await query.answer()
    
    admin_id = int(query.data.split("_")[3])
    
    session = SessionLocal()
    try:
        admin = session.query(AdminSettings).filter_by(user_id=admin_id).first()
        
        if admin:
            session.delete(admin)
            session.commit()
            
            # Показываем успешное сообщение
            try:
                user = await context.bot.get_chat(admin_id)
                admin_name = user.first_name or user.username or f"ID: {admin_id}"
            except:
                admin_name = f"ID: {admin_id}"
            
            success_text = (
                f"✅ <b>Администратор удален</b>\n\n"
                f"👤 {admin_name}\n"
                f"🆔 ID: <code>{admin_id}</code>\n\n"
                f"Теперь у этого пользователя нет доступа к админ-панели."
            )
            
            # Обновляем список админов
            text, keyboard = await get_admins_list_with_actions(context)
            
            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
            # Временное подтверждение
            msg = await query.message.reply_text("✅ Администратор успешно удален")
            asyncio.create_task(delete_after_3s(msg))
        else:
            await query.message.edit_text(
                "❌ Администратор не найден",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад к списку админов", callback_data="admin_list_refresh")]
                ])
            )
            
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка удаления администратора: {e}")
        await query.message.edit_text(
            f"❌ Ошибка при удалении: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_management_back")]
            ])
        )
    finally:
        session.close()

async def cleanup_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет истекшие инвайты"""
    query = update.callback_query
    await query.answer()
    
    session = SessionLocal()
    try:
        # Находим истекшие или использованные инвайты
        expired_invites = session.query(AdminInvite).filter(
            (AdminInvite.expires_at < datetime.now()) | 
            (AdminInvite.used_count >= AdminInvite.max_uses)
        ).all()
        
        deleted_count = 0
        for invite in expired_invites:
            session.delete(invite)
            deleted_count += 1
        
        session.commit()
        
        await query.message.edit_text(
            f"✅ Удалено {deleted_count} истёкших/использованных инвайтов",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📋 К списку инвайтов", callback_data="admin_list_invites")],
                [InlineKeyboardButton("⬅️ Назад к списку админов", callback_data="admin_list_refresh")]
            ])
        )
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка очистки инвайтов: {e}")
        await query.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="admin_management_back")]
            ])
        )
    finally:
        session.close()

async def refresh_admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновляет список админов"""
    query = update.callback_query
    await query.answer()
    
    text, keyboard = await get_admins_list_with_actions(context)
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def handle_invite_token(user_id: int, token: str, context: ContextTypes.DEFAULT_TYPE) -> Tuple[bool, str]:
    """Обрабатывает использование инвайт-токена"""
    session = SessionLocal()
    try:
        # Ищем токен
        invite = session.query(AdminInvite).filter_by(token=token, is_active=True).first()
        
        if not invite:
            return False, "❌ Инвайт-ссылка не найдена или неактивна"
        
        # Проверяем срок действия
        if invite.expires_at < datetime.now():
            invite.is_active = False
            session.commit()
            return False, "❌ Срок действия инвайт-ссылки истёк"
        
        # Проверяем лимит использований
        if invite.used_count >= invite.max_uses:
            invite.is_active = False
            session.commit()
            return False, "❌ Инвайт-ссылка уже использована"
        
        # Проверяем, не является ли пользователь уже администратором
        existing_admin = session.query(AdminSettings).filter_by(user_id=user_id).first()
        if existing_admin:
            return False, "⚠️ Вы уже являетесь администратором"
        
        # Проверяем, не входит ли пользователь в суперадмины
        if user_id in Config.ADMIN_IDS:
            return False, "⚠️ Вы уже являетесь суперадминистратором"
        
        # Создаем запись администратора
        admin_settings = AdminSettings(
            user_id=user_id,
            receive_csv=False  # По умолчанию не получает CSV
        )
        session.add(admin_settings)
        
        # Обновляем статистику использования инвайта
        invite.used_count += 1
        
        # Если достигнут лимит - деактивируем
        if invite.used_count >= invite.max_uses:
            invite.is_active = False
        
        # Записываем использование
        usage = AdminInviteUsage(
            invite_id=invite.id,
            used_by=user_id
        )
        session.add(usage)
        
        session.commit()
        
        return True, "✅ Вы успешно добавлены в администраторы!\n\n" \
                     "Теперь у вас есть доступ к админ-панели. Используйте команду /admin для входа."
        
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка обработки инвайт-токена: {e}")
        return False, f"❌ Ошибка: {str(e)}"
    finally:
        session.close()

async def admin_management_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает callback от меню управления администраторами"""
    print("\n" + "🔥"*50)
    print("🔥 admin_management_callback ВЫЗВАНА")
    
    query = update.callback_query
    
    if not query:
        print("❌ НЕТ QUERY В CALLBACK!")
        return
    
    print(f"📞 Данные callback: {query.data}")
    print(f"👤 От пользователя: {query.from_user.id}")
    print(f"💬 Текст сообщения: {query.message.text[:100] if query.message else 'Нет сообщения'}")
    print("🔥"*50 + "\n")
    
    await query.answer()
    
    # Логируем callback для отладки
    logger.info(f"admin_management_callback: получен callback с данными: {query.data}")
    
    if query.data == "admin_management_back":
        # Удаляем текущее сообщение
        await query.message.delete()
        # Вызываем возврат в меню
        from admin.menu import admin_menu
        await admin_menu(update, context)
        return
    
    elif query.data == "admin_list_refresh":
        logger.info("Вызвано обновление списка админов")
        await refresh_admin_list(update, context)
    
    elif query.data == "admin_create_invite":
        logger.info("=" * 50)
        logger.info("ПОЛУЧЕН ЗАПРОС НА СОЗДАНИЕ ИНВАЙТ-ССЫЛКИ")
        logger.info(f"От пользователя: {query.from_user.id}")
        logger.info("=" * 50)
        await create_invite(update, context)
    
    elif query.data == "admin_list_invites":
        logger.info("Вызван просмотр списка инвайтов")
        await list_invites(update, context)
    
    elif query.data.startswith("admin_delete_") and "confirm" not in query.data:
        logger.info(f"Вызвано удаление администратора: {query.data}")
        await delete_admin_handler(update, context)
    
    elif query.data.startswith("admin_delete_confirm_"):
        logger.info(f"Подтверждение удаления: {query.data}")
        await confirm_delete_admin(update, context)
    
    elif query.data == "admin_cleanup_invites":
        logger.info("Вызвана очистка инвайтов")
        await cleanup_invites(update, context)