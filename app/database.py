import urllib.parse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# --- FINAL FIX: Clean the database URL for full asyncpg compatibility ---
# Neon provides a URL with '?sslmode=require', which is a parameter for the psycopg2 driver.
# The asyncpg driver handles SSL/TLS automatically and does not accept the 'sslmode' parameter.
# This causes a TypeError. The solution is to parse the URL and remove any query parameters
# before passing it to the engine.

# Parse the original URL provided by the environment variable
parsed_url = urllib.parse.urlparse(settings.database_url)

# Create a new URL components tuple, but with an empty query string.
# This effectively removes '?sslmode=require' and any other potential parameters.
clean_url_components = parsed_url._replace(query="")

# Rebuild the URL as a string from the cleaned components
clean_url = urllib.parse.urlunparse(clean_url_components)

# Now, replace the scheme to tell SQLAlchemy to use the asyncpg driver
ASYNC_DATABASE_URL = clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)


# The engine is now created with a clean URL that asyncpg can understand.
engine = create_async_engine(ASYNC_DATABASE_URL)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

