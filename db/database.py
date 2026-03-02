# db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from .models import Base
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    "sqlite:///maraphon.db",
    connect_args={"check_same_thread": False},
    echo=False  # Включить для отладки SQL
)

Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_db_session():
    """Контекстный менеджер для сессий БД"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        session.close()