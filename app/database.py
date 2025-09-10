from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# --- FIX: Modify the database URL to use the asyncpg driver ---
# We replace "postgresql://" with "postgresql+asyncpg://"
# This tells SQLAlchemy to use the newly installed asyncpg library.
ASYNC_DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(ASYNC_DATABASE_URL)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()
