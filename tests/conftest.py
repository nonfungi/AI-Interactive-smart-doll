# tests/conftest.py

import pytest
import sys
import os
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport # Import ASGITransport

# Set environment variables BEFORE importing the app
os.environ['DATABASE_URL'] = "postgresql+asyncpg://doll_user:mysecretpassword@localhost:5433/doll_db_test"
os.environ['QDRANT_URL'] = "http://localhost:6333"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import Base
from app.main import app, get_db 
from app.config import settings

# The test database URL is now read from the environment variable set above
engine_test = create_async_engine(settings.database_url, poolclass=NullPool)
AsyncSessionLocal_test = async_sessionmaker(engine_test, expire_on_commit=False)

# This function overrides the get_db dependency for tests
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal_test() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """
    Creates all tables in the test database before tests run,
    and drops them after tests are complete.
    """
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Creates an HTTP client for sending requests to the app in the test environment.
    """
    # --- FIX: Use ASGITransport to connect the client to the app ---
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
