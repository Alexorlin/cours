from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Рядок підключення до PostgreSQL.

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:5374@localhost:5432/eds_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Створюємо фабрику сесій (для спілкування з БД)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас, від якого будуть успадковуватися всі наші моделі
Base = declarative_base()