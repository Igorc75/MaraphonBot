# check_intro_chat.py
from db.database import SessionLocal
from db.models import BotSettings

session = SessionLocal()
try:
    settings = session.query(BotSettings).filter_by(id=1).first()
    if settings:
        print(f"intro_chat_id = {settings.intro_chat_id} (тип: {type(settings.intro_chat_id)})")
    else:
        print("Запись BotSettings с id=1 не найдена")
finally:
    session.close()