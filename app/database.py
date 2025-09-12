# app/database.py
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Import the settings function instead of the settings object
from .config import get_settings

# These will hold the engine and session instances once they are created.
engine = None
AsyncSessionLocal = None

# The Base class that our SQLAlchemy models will inherit from
Base = declarative_base()

def initialize_db():
    """
    Initializes the database connection using the settings.
    This function is called during the application startup lifespan event.
    """
    global engine, AsyncSessionLocal
    
    settings = get_settings()
    db_url = settings.database_url
    
    # Ensure the driver is asyncpg for async operations
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # --- FIX: Robustly remove the 'sslmode' parameter ---
    # The asyncpg driver handles SSL automatically and does not accept 'sslmode'.
    # We parse the URL, remove the sslmode query parameter, and rebuild it.
    parsed_url = urlparse(db_url)
    query_params = parse_qs(parsed_url.query)
    query_params.pop('sslmode', None)  # Remove sslmode if it exists
    
    # Rebuild the URL without the sslmode parameter
    cleaned_query = urlencode(query_params, doseq=True)
    db_url_cleaned = urlunparse(parsed_url._replace(query=cleaned_query))

    print(f"Initializing database with cleaned URL: {db_url_cleaned}")
    engine = create_async_engine(db_url_cleaned, echo=False)
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

async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides a database session for a single request.
    """
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call initialize_db() first.")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

