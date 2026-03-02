# init_db.py
from db.database import engine, Base
from db.models import (
    User, Hashtag, Action, TopicRule, 
    AdminSettings, AdminInvite, AdminInviteUsage
)
from config import Config

def init_database():
    """Инициализирует базу данных, создавая все таблицы"""
    try:
        # Создаем все таблицы
        Base.metadata.create_all(bind=engine)
        print("✅ Все таблицы созданы/уже существуют")
        
        # Проверяем администраторов
        if Config.ADMIN_IDS:
            print(f"📋 Суперадминистраторы из .env: {Config.ADMIN_IDS}")
        else:
            print("⚠️  ADMIN_IDS пустой в config.py")
        
        # Проверяем таблицы
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print("\n📊 Созданные таблицы:")
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            print(f"  - {table}: {len(columns)} колонок")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    init_database()