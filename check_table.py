# check_table.py
from db.database import SessionLocal, engine
from sqlalchemy import inspect

def check_admin_table():
    """Проверяет, существует ли таблица admin_settings"""
    inspector = inspect(engine)
    
    tables = inspector.get_table_names()
    print(f"📋 Таблицы в базе данных: {tables}")
    
    if 'admin_settings' in tables:
        print("✅ Таблица admin_settings существует")
        
        # Проверяем структуру таблицы
        columns = inspector.get_columns('admin_settings')
        print("📝 Структура таблицы admin_settings:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # Проверяем есть ли записи
        session = SessionLocal()
        try:
            count = session.query(AdminSettings).count()
            print(f"📊 Записей в таблице: {count}")
            
            if count > 0:
                records = session.query(AdminSettings).limit(5).all()
                for record in records:
                    print(f"  👤 user_id: {record.user_id}, receive_csv: {record.receive_csv}")
        finally:
            session.close()
    else:
        print("❌ Таблица admin_settings не существует")

if __name__ == "__main__":
    check_admin_table()