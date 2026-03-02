# db/models.py
from sqlalchemy import (
    Column, Integer, BigInteger, String, DateTime,
    Boolean, ForeignKey, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    uid = Column(BigInteger, unique=True, nullable=False)
    username = Column(String)
    name = Column(String)
    fam = Column(String)
    city = Column(String)
    datetime = Column(DateTime, default=func.now())

class Hashtag(Base):
    __tablename__ = "hashtags"
    id = Column(Integer, primary_key=True)
    name_hashtag = Column(String, unique=True, nullable=False)

class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True)
    uid = Column(BigInteger, ForeignKey("users.uid"), nullable=False)
    pid = Column(BigInteger, nullable=False)
    hashtag_id = Column(Integer, ForeignKey("hashtags.id"), nullable=False)
    datetime = Column(DateTime, default=func.now())

class TopicRule(Base):
    __tablename__ = "topic_rules"
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    thread_id = Column(BigInteger, nullable=False)
    hashtag_prefix = Column(String, nullable=False)
    start_datetime = Column(DateTime, nullable=True)
    end_datetime = Column(DateTime, nullable=True)
    point_value = Column(Integer, default=1)
    stop_sent = Column(Boolean, default=False)

class AdminSettings(Base):
    __tablename__ = "admin_settings"
    
    user_id = Column(BigInteger, primary_key=True)
    receive_csv = Column(Boolean, default=False)  # Получать CSV файлы
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# db/models.py - дополните
class AdminInvite(Base):
    __tablename__ = "admin_invites"
    
    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False, index=True)
    created_by = Column(BigInteger, nullable=False)  # ID администратора, создавшего ссылку
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)     # Время истечения
    max_uses = Column(Integer, default=1)            # Максимальное количество использований (1 для одноразовых)
    used_count = Column(Integer, default=0)          # Сколько раз использовано
    is_active = Column(Boolean, default=True)
    
    # Связь с пользователями, которые использовали токен
    used_by = relationship("AdminInviteUsage", back_populates="invite")

class AdminInviteUsage(Base):
    __tablename__ = "admin_invite_usage"
    
    id = Column(Integer, primary_key=True)
    invite_id = Column(Integer, ForeignKey("admin_invites.id"))
    used_by = Column(BigInteger, nullable=False)     # ID пользователя, который использовал токен
    used_at = Column(DateTime, default=func.now())
    
    invite = relationship("AdminInvite", back_populates="used_by")


# db/models.py (фрагмент с классом BotSettings)
class BotSettings(Base):
    __tablename__ = "bot_settings"

    id = Column(Integer, primary_key=True)  # всегда 1
    intro_chat_id = Column(BigInteger, nullable=True)
    intro_thread_id = Column(BigInteger, nullable=True)  # новое поле
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())