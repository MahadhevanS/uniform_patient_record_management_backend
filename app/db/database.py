from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
from typing import Generator

# The database URL is pulled from the settings object
SQLALCHEMY_DATABASE_URL = str(settings.DATABASE_URL)

# 1. Create the SQLAlchemy Engine
# The pool_pre_ping ensures connections are recycled properly in a web application
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)

# 2. Create a SessionLocal class
# This class will be used to create session objects for DB interactions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Create a Base class for ORM models
# All SQLAlchemy models (tables) will inherit from this Base class
Base = declarative_base()

# 4. Dependency for FastAPI Endpoints (Get Database Session)
def get_db() -> Generator:
    """
    A generator dependency to provide a database session to FastAPI endpoints.
    It ensures the session is always closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()