# create_admin_table.py
from db.database import engine, Base
from db.models import AdminSettings, User, Hashtag, Action, TopicRule
from config import Config

def create_admin_settings_table():
    """Создает таблицу для настроек администратора"""
    try:
        # Создаем все таблицы, включая AdminSettings
        Base.metadata.create_all(bind=engine)
        print("✅ Все таблицы созданы/уже существуют")
        
        # Проверяем администраторов из config
        print(f"📋 Администраторы из config: {Config.ADMIN_IDS}")
        
        if not Config.ADMIN_IDS:
            print("⚠️  Внимание: ADMIN_IDS пустой в config.py")
            print(f"   Проверьте файл .env: ADMIN_IDS={Config.ADMIN_IDS}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        return False

if __name__ == "__main__":
    create_admin_settings_table()