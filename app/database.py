# app/database.py
import re
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Import the settings function instead of the settings object
from .config import get_settings

# These will hold the engine and session instances once they are created.
# They are initialized as None at the global scope.
engine = None
AsyncSessionLocal = None

def initialize_db():
    """
    Initializes the database connection using the settings.
    This function is called during the application startup lifespan event,
    ensuring that settings are fully loaded before a connection is attempted.
    """
    global engine, AsyncSessionLocal
    
    # Get the loaded settings
    settings = get_settings()
    
    # Clean the database URL to be compatible with asyncpg driver
    db_url = settings.database_url
    if db_url.startswith("postgresql://"):
        # The asyncpg driver requires the dialect to be 'postgresql+asyncpg'
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Remove the sslmode query parameter if it exists, as it's not used by asyncpg
    db_url = re.sub(r"\?sslmode=require$", "", db_url)

    print(f"Initializing database with URL: {db_url}")
    engine = create_async_engine(db_url, echo=False)
    AsyncSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
    )

async def close_db_connection():
    """
    Closes the database connection pool gracefully.
    This is called during the application shutdown lifespan event.
    """
    if engine:
        print("Closing database connection pool.")
        await engine.dispose()

# The Base class that our SQLAlchemy models will inherit from
Base = declarative_base()

