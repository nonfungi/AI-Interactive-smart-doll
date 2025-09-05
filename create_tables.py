# create_tables.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base
from app.models import User, Child, Doll # Import all your models

# --- FIX: Use localhost to connect from the host machine ---
DATABASE_URL_LOCAL = "postgresql+asyncpg://doll_user:mysecretpassword@localhost:5433/doll_db"
engine = create_async_engine(DATABASE_URL_LOCAL)

async def init_models():
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_models())
