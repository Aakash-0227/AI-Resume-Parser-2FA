
import os

from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool


# Load environment variables
load_dotenv()


# Read PostgreSQL database URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env file")


# Create asynchronous database engine
# NullPool prevents connection reuse across different event loops
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    poolclass=NullPool
)


# Create asynchronous session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# Base class for all database models
class Base(DeclarativeBase):
    pass


# Database dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
