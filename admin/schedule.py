# admin/schedule.py - ТОЛЬКО ТЕКСТОВОЕ РАСПИСАНИЕ
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from db.database import SessionLocal
from db.models import TopicRule
from config import Config
import pytz

async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки расписания"""
    if update.effective_user.id not in Config.ADMIN_IDS:
        return
    
    keyboard = [
        [
            InlineKeyboardButton("📅 Неделя", callback_data="schedule_week"),
            InlineKeyboardButton("📆 Месяц", callback_data="schedule_month")
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="schedule_back")]
    ]
    
    await update.message.reply_text(
        "📊 Выберите период для просмотра расписания:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback для расписания"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "schedule_back":
        # Используем импорт внутри функции чтобы избежать циклического импорта
        from admin.menu import admin_menu
        await admin_menu(update, context)
        return
    
    if query.data in ["schedule_week", "schedule_month"]:
        days = 7 if query.data == "schedule_week" else 30
        await send_schedule(update, context, days)

async def send_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE, days):
    """Отправляет текстовое расписание"""
    query = update.callback_query
    
    # Генерируем расписание
    session = SessionLocal()
    try:
        # Используем таймзону из конфига
        tz = pytz.timezone(Config.TIMEZONE)
        today = datetime.now(tz)
        end_date = today + timedelta(days=days)
        
        # Получаем правила
        rules = session.query(TopicRule).filter(
            TopicRule.chat_id == Config.ALLOWED_CHAT_IDS[0],
            TopicRule.start_datetime.isnot(None)
        ).order_by(TopicRule.start_datetime).all()
        
        if not rules:
            await query.message.edit_text(
                "📭 Нет запланированных тем на выбранный период",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад", callback_data="schedule_back")]
                ])
            )
            return
        
        # Фильтруем по периоду
        filtered_rules = [
            r for r in rules 
            if r.start_datetime and r.start_datetime.date() <= end_date.date()
        ]
        
        if not filtered_rules:
            await query.message.edit_text(
                f"📭 Нет тем на ближайшие {days} дней",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Назад", callback_data="schedule_back")]
                ])
            )
            return
        
        # Формируем красивое текстовое расписание
        schedule_text = await create_beautiful_schedule(filtered_rules, days, tz)
        
        # Клавиатура
        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="schedule_back")]]
        
        # Отправляем (разбиваем если длинное)
        if len(schedule_text) > 4000:
            parts = split_message(schedule_text, 4000)
            # Отправляем первое сообщение как новое, а не редактируем
            await query.message.delete()
            for i, part in enumerate(parts):
                if i == 0:
                    await update.effective_chat.send_message(
                        text=part,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode='HTML'
                    )
                else:
                    await update.effective_chat.send_message(
                        text=part,
                        parse_mode='HTML'
                    )
        else:
            await query.message.edit_text(
                schedule_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        
    except Exception as e:
        print(f"Ошибка при формировании расписания: {e}")
        await query.message.edit_text(
            f"❌ Ошибка при формировании расписания:\n{str(e)[:200]}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Назад", callback_data="schedule_back")]
            ])
        )
    finally:
        session.close()

async def create_beautiful_schedule(rules, days, tz):
    """Создает красивое текстовое расписание в HTML"""
    # Группируем по дням
    schedule_by_day = {}
    for rule in rules:
        if rule.start_datetime:
            day_key = rule.start_datetime.date()
            if day_key not in schedule_by_day:
                schedule_by_day[day_key] = []
            schedule_by_day[day_key].append(rule)
    
    # Эмодзи для дней недели
    day_emojis = ["🟢", "🔵", "🟡", "🟣", "🔴", "🟠", "⚪"]
    day_names = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
    month_names = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    
    # Формируем HTML
    html = f"<b>📅 РАСПИСАНИЕ ХЕШТЕГОВ НА {days} ДНЕЙ</b>\n\n"
    
    current_month = None
    # В БД времена хранятся как "московские" naive, поэтому сравниваем в naive
    now = datetime.now(tz).replace(tzinfo=None)
    
    for day_key in sorted(schedule_by_day.keys()):
        day_date = day_key
        weekday = day_date.weekday()
        
        # Заголовок месяца (если изменился)
        month_str = f"{month_names[day_date.month - 1]} {day_date.year}"
        if month_str != current_month:
            current_month = month_str
            html += f"<b>🗓️ {month_str.upper()}</b>\n\n"
        
        # День
        html += f"{day_emojis[weekday]} <b>{day_date.strftime('%d.%m.%Y')} ({day_names[weekday]})</b>\n"
        
        # События дня (сортируем по времени)
        day_rules = sorted(schedule_by_day[day_key], 
                          key=lambda x: x.start_datetime)
        
        for rule in day_rules:
            start_time = rule.start_datetime.strftime("%H:%M") if rule.start_datetime else "--:--"
            end_time = rule.end_datetime.strftime("%H:%M") if rule.end_datetime else "--:--"
            
            # Определяем статус
            if rule.stop_sent:
                status = "🔴"  # Завершено
            elif rule.start_datetime and rule.start_datetime > now:
                status = "🟡"  # Ожидает
            else:
                status = "🟢"  # Активно
            
            html += f"  {status} <code>{start_time}-{end_time}</code> <b>#{rule.hashtag_prefix}</b>\n"
            html += f"     👉 Тема: {rule.thread_id}, 🏆 Баллов: {rule.point_value}\n"
        
        html += "\n"
    
    # Статистика
    active = sum(1 for r in rules if not r.stop_sent)
    completed = sum(1 for r in rules if r.stop_sent)
    upcoming = sum(1 for r in rules if not r.stop_sent and r.start_datetime and r.start_datetime > now)
    
    html += f"{'═' * 20}\n"
    html += f"<b>📊 СТАТИСТИКА:</b>\n"
    html += f"• Всего тем: {len(rules)}\n"
    html += f"• 🟢 Активных сейчас: {active}\n"
    html += f"• 🟡 Ожидаемых: {upcoming}\n"
    html += f"• 🔴 Завершённых: {completed}\n"
    
    return html

def split_message(text, max_length):
    """Разбивает сообщение на части по переносу строк"""
    parts = []
    while len(text) > max_length:
        split_at = text[:max_length].rfind('\n')
        if split_at == -1:
            split_at = max_length
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    parts.append(text)
    return parts

# Для main.py
def get_schedule_handlers():
    """Возвращает обработчики для расписания"""
    return [
        CallbackQueryHandler(schedule_callback, pattern="^schedule_")
    ]