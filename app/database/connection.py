import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import Base

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/database/sql_app.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

def init_db():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created and initialized.")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()