# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

# --- Import initializers and modules ---
# Correct way: Import the database module itself, not the engine directly.
from . import database
from .memory import initialize_memory_manager
from .routers import users, children, dolls, conversation, auth
from .config import get_settings

# --- Lifespan Event Handler for Safe Startup and Shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    This is the core of the new architecture, ensuring all connections
    are established only after the app has started and settings are loaded.
    """
    print("Server starting up...")
    
    # Load settings once at the beginning
    settings = get_settings()
    
    # --- Establish Connections ---
    try:
        # Initialize the PostgreSQL database connection pool. This will set database.engine.
        database.initialize_db()
        
        # Connect and create database tables if they don't exist
        # Now, access the engine through the module to get the initialized instance.
        async with database.engine.begin() as conn:
            # Use conn.run_sync() to execute synchronous SQLAlchemy metadata operations
            # await conn.run_sync(database.Base.metadata.drop_all) # Uncomment for testing to clear tables
            await conn.run_sync(database.Base.metadata.create_all)
            print("Database tables checked/created successfully.")
        
        # Initialize the Qdrant client (MemoryManager)
        initialize_memory_manager()

    except Exception as e:
        # If any part of the startup fails, log a fatal error and stop the application.
        print(f"FATAL ERROR DURING STARTUP: {e}")
        raise RuntimeError("Could not initialize database or memory manager.") from e
    
    # --- Application is now running ---
    yield
    
    # --- Clean Up Connections on Shutdown ---
    print("Server shutting down...")
    await database.close_db_connection()


# --- Main FastAPI Application Instance ---
app = FastAPI(
    title="AI Interactive Smart Doll API",
    description="The core API for the smart storytelling toy.",
    version="1.0.0",
    lifespan=lifespan  # Connect the lifespan handler to the app
)

# --- Register API Routers ---
# These define the different sections of our API (users, children, etc.)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(children.router)
app.include_router(dolls.router)
app.include_router(conversation.router)

@app.get("/", tags=["Health Check"])
async def root():
    """A simple health check endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to the AI Interactive Smart Doll API!"}
