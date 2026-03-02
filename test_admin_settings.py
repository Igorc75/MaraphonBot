# test_admin_settings.py
from db.database import engine, Base
from db.models import AdminSettings

# Создаем таблицу если её нет
Base.metadata.create_all(bind=engine, tables=[AdminSettings.__table__])
print("✅ Таблица admin_settings готова")

# Проверяем администраторов из config
from config import Config
print(f"📋 Администраторы из config: {Config.ADMIN_IDS}")