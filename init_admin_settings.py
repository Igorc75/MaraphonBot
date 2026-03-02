# init_admin_settings.py
from db.database import SessionLocal
from db.models import AdminSettings
from config import Config

def init_admin_settings():
    """Инициализирует настройки для всех администраторов"""
    session = SessionLocal()
    
    try:
        initialized = 0
        existing = 0
        
        for admin_id in Config.ADMIN_IDS:
            # Проверяем, существует ли уже запись
            settings = session.query(AdminSettings).filter_by(user_id=admin_id).first()
            
            if not settings:
                # Создаем новую запись
                settings = AdminSettings(
                    user_id=admin_id,
                    receive_csv=False  # По умолчанию выключено
                )
                session.add(settings)
                initialized += 1
                print(f"✅ Созданы настройки для администратора {admin_id}")
            else:
                existing += 1
                print(f"ℹ️  Настройки для администратора {admin_id} уже существуют")
        
        session.commit()
        print(f"\n📊 Итог: создано {initialized}, уже было {existing}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка при инициализации: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    if not Config.ADMIN_IDS:
        print("⚠️  Внимание: ADMIN_IDS пустой. Проверьте .env файл")
    else:
        print(f"📋 Найдено администраторов: {len(Config.ADMIN_IDS)}")
        init_admin_settings()