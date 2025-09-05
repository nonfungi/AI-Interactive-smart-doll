# app/database.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# Create an asynchronous engine to connect to the database
engine = create_async_engine(settings.database_url)

# Create a class that our session-making factory will use
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# A base class for our declarative models
class Base(DeclarativeBase):
    pass