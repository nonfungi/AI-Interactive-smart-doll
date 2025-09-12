# app/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Import the settings GETTER function, not the settings object itself
from .config import get_settings

# Define the base class for declarative models
Base = declarative_base()

# We initialize these as None. They will be populated during the app's startup.
engine = None
AsyncSessionLocal = None

async def initialize_db():
    """
    Initializes the database engine and session maker.
    This function is called during the application's lifespan startup event.
    """
    global engine, AsyncSessionLocal
    
    settings = get_settings()
    
    # Clean the database URL for asyncpg compatibility
    # asyncpg does not recognize the 'sslmode' parameter, so we remove it.
    db_url = settings.database_url
    if db_url.startswith("postgresql://") and "?sslmode=require" in db_url:
        db_url = db_url.replace("?sslmode=require", "")

    # Create the asynchronous engine for SQLAlchemy
    engine = create_async_engine(db_url)

    # Create a configured "Session" class
    AsyncSessionLocal = sessionmaker(
        autocommit=False, 
        autoflush=False, 
        bind=engine, 
        class_=AsyncSession,
        expire_on_commit=False
    )

async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides a database session to the endpoints.
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database is not initialized. Call initialize_db() first.")
    
    async with AsyncSessionLocal() as session:
        yield session

