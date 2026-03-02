# utils/stop_daemon.py 
import io
import csv
import pytz
from datetime import datetime, timedelta
from db.database import SessionLocal
from db.models import TopicRule, Action, User, Hashtag
from config import Config
from utils.hashtag_utils import match_hashtag_to_rule

class StopDaemon:
    """Демон для точной отправки СТОП сообщений секунда в секунду"""
    
    def __init__(self, application):
        self.application = application
        self.bot = application.bot
    
    def get_participants(self, rule, today_start):
        """
        Получает участников, попавших в окно действия хештега.
        Возвращает список кортежей:
        (first_name, last_name, username, uid, points, action_datetime)
        где username — строка с @ или пустая, uid — строковое представление ID.
        """
        session = SessionLocal()
        try:
            start_dt = rule.start_datetime or today_start
            end_dt = rule.end_datetime

            q = session.query(Action, Hashtag).join(Hashtag, Action.hashtag_id == Hashtag.id).filter(
                Action.datetime >= start_dt
            )
            if end_dt:
                q = q.filter(Action.datetime <= end_dt)

            actions = q.all()
            
            participants = []
            seen_uids = set()
            
            for action, hashtag in actions:
                if action.uid in seen_uids:
                    continue
                
                if not (hashtag and match_hashtag_to_rule(hashtag.name_hashtag, rule.hashtag_prefix)):
                    continue

                seen_uids.add(action.uid)

                user = session.query(User).filter_by(uid=action.uid).first()

                first_name = ""
                last_name = ""
                username = ""
                uid = str(action.uid)

                if user:
                    first_name = user.name or ""
                    last_name = user.fam or ""
                    if user.username:
                        username = f"@{user.username}"
                # если user нет, оставляем пустые имя/фамилию/username, uid уже есть

                points = rule.point_value
                participants.append((first_name, last_name, username, uid, points, action.datetime))
            
            # Сортируем по имени
            return sorted(participants, key=lambda x: (x[0], x[1]))
        finally:
            session.close()
    
    async def create_csv_file(self, rule, participants):
        """Создает CSV файл с отдельными колонками для имени, фамилии, username и uid"""
        if not participants:
            return None, "Нет участников"
        
        tz = pytz.timezone(Config.TIMEZONE)
        report_time = datetime.now(tz)
        
        csv_buffer = io.StringIO()
        csv_writer = csv.writer(csv_buffer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Заголовки с раздельными колонками для username и uid
        csv_writer.writerow([
            '№', 
            'Имя', 
            'Фамилия', 
            'Username', 
            'UID', 
            'Баллы', 
            'Хештег', 
            'Тема ID', 
            'Время действия', 
            'Время формирования отчета'
        ])
        
        for i, (first_name, last_name, username, uid, points, action_time) in enumerate(participants, 1):
            csv_writer.writerow([
                i,
                first_name,
                last_name,
                username,
                uid,
                points,
                rule.hashtag_prefix,
                rule.thread_id,
                action_time.strftime('%d.%m.%Y %H:%M:%S'),
                report_time.strftime('%d.%m.%Y %H:%M:%S')
            ])
        
        csv_content = csv_buffer.getvalue()
        csv_buffer.close()
        
        csv_bytes = csv_content.encode('utf-8')
        filename = f"results_{rule.hashtag_prefix}_{report_time.strftime('%Y%m%d_%H%M%S')}.csv"
        
        return csv_bytes, filename
    
    async def send_csv_to_admins(self, rule, participants):
        """Отправляет CSV файл администраторам, которые включили опцию"""
        try:
            from admin.settings import get_admins_wanting_csv
            
            admin_ids = get_admins_wanting_csv()
            
            if not admin_ids:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Нет администраторов с включенной опцией CSV")
                return
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Найдено администраторов для отправки CSV: {len(admin_ids)}")
            
            csv_bytes, filename = await self.create_csv_file(rule, participants)
            
            if not csv_bytes:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Нечего отправлять - нет участников")
                return
            
            success_count = 0
            for admin_id in admin_ids:
                try:
                    tz = pytz.timezone(Config.TIMEZONE)
                    stop_time = datetime.now(tz)
                    await self.bot.send_document(
                        chat_id=admin_id,
                        document=io.BytesIO(csv_bytes),
                        filename=filename,
                        caption=(
                            f"📊 Результаты по теме #{rule.hashtag_prefix}\n"
                            f"🔢 Тема ID: {rule.thread_id}\n"
                            f"👥 Участников: {len(participants)}\n"
                            f"⭐ Баллов за участие: {rule.point_value}\n"
                            f"⏰ Время СТОП: {stop_time.strftime('%d.%m.%Y %H:%M:%S')}"
                        )
                    )
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📤 CSV отправлен администратору {admin_id}")
                    success_count += 1
                    
                    # Текстовый отчёт оставляем как раньше (объединённый вид)
                    if participants:
                        report_text = f"📊 Отчет по теме #{rule.hashtag_prefix}:\n"
                        for i, (first_name, last_name, username, uid, points, action_time) in enumerate(participants, 1):
                            full_name = f"{first_name} {last_name}".strip()
                            identifier = username if username else f"uid @{uid}"
                            if full_name:
                                display = f"{full_name} ({identifier})"
                            else:
                                display = identifier
                            time_str = action_time.strftime('%H:%M')
                            report_text += f"{i}. {display} - {time_str} - {points}\n"
                        
                        report_text += f"\n✅ Всего: {len(participants)} участников"
                        
                        await self.bot.send_message(
                            chat_id=admin_id,
                            text=report_text
                        )
                    
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Ошибка отправки CSV администратору {admin_id}: {e}")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 CSV отправлен {success_count}/{len(admin_ids)} администраторам")
                    
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Ошибка при отправке CSV: {e}")

    async def send_stop_for_rule(self, rule):
        """Отправляет СТОП сообщение для одной темы (асинхронно)"""
        try:
            tz = pytz.timezone(Config.TIMEZONE)
            now = datetime.now(tz)
            today_start = datetime.combine(now.date(), datetime.min.time())
            
            participants = self.get_participants(rule, today_start)
            
            stop_header = "СТОП"
            
            if participants:
                participants_msg = "Список участников:\n"
                for i, (first_name, last_name, username, uid, points, action_time) in enumerate(participants, 1):
                    full_name = f"{first_name} {last_name}".strip()
                    identifier = username if username else f"uid @{uid}"
                    if full_name:
                        display = f"{full_name} ({identifier})"
                    else:
                        display = identifier
                    time_str = action_time.strftime('%H:%M')
                    participants_msg += f"{i}. {display} - {time_str} - {points}\n"
            else:
                participants_msg = "Список участников:\n\nНикто не успел."
            
            await self.bot.send_message(
                chat_id=Config.ALLOWED_CHAT_IDS[0],
                message_thread_id=rule.thread_id,
                text=stop_header
            )
            
            await self.bot.send_message(
                chat_id=Config.ALLOWED_CHAT_IDS[0],
                message_thread_id=rule.thread_id,
                text=participants_msg
            )
            
            await self.send_csv_to_admins(rule, participants)
            
            session = SessionLocal()
            try:
                rule_db = session.query(TopicRule).filter_by(id=rule.id).first()
                if rule_db:
                    rule_db.stop_sent = True
                    session.commit()
            finally:
                session.close()
            
            print(f"[{now.strftime('%H:%M:%S')}] 📤 STOP sent: #{rule.hashtag_prefix}")
            return True
                    
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ STOP error: {e}")
            return False
    
    async def check_and_send_stops(self, context=None):
        try:
            session = SessionLocal()
            tz = pytz.timezone(Config.TIMEZONE)
            now = datetime.now(tz)
            current_time = now.replace(tzinfo=None)
            
            time_start = current_time - timedelta(seconds=1)
            time_end = current_time + timedelta(seconds=1)
            
            rules = session.query(TopicRule).filter(
                TopicRule.chat_id == Config.ALLOWED_CHAT_IDS[0],
                TopicRule.end_datetime.isnot(None),
                TopicRule.end_datetime.between(time_start, time_end),
                TopicRule.stop_sent == False
            ).all()
            
            past_rules = session.query(TopicRule).filter(
                TopicRule.chat_id == Config.ALLOWED_CHAT_IDS[0],
                TopicRule.end_datetime.isnot(None),
                TopicRule.end_datetime < time_start,
                TopicRule.stop_sent == False
            ).all()
            
            all_rules = rules + past_rules

            eligible_rules = []
            for rule in all_rules:
                if rule.start_datetime and rule.start_datetime > current_time:
                    continue
                eligible_rules.append(rule)
            
            for rule in eligible_rules:
                await self.send_stop_for_rule(rule)
            
            session.close()
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Ошибка в демоне: {e}")
    
_stop_daemon_instance = None

def setup_stop_daemon(application):
    global _stop_daemon_instance
    try:
        _stop_daemon_instance = StopDaemon(application)
        application.job_queue.run_repeating(
            _stop_daemon_instance.check_and_send_stops,
            interval=1.0,
            first=0.0,
            name="stop_daemon"
        )
        return _stop_daemon_instance
    except Exception as e:
        print(f"❌ Ошибка запуска демона СТОП: {e}")
        return None

def get_stop_daemon():
    return _stop_daemon_instance