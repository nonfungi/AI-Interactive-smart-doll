# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

# --- Import initializers and routers ---
from .database import initialize_db, engine
from .memory import initialize_memory_manager
from .routers import users, children, dolls, conversation, auth

# --- Lifespan event handler for application startup and shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown events.
    This is the correct place to initialize database connections,
    AI models, and other resources.
    """
    print("Server starting up...")
    
    try:
        # --- Initialize Database Connection ---
        # This will create the engine and tables if they don't exist.
        await initialize_db()
        print("Database tables checked/created successfully.")
        
        # --- Initialize Qdrant Memory Manager ---
        # This ensures the connection to Qdrant happens only after settings are loaded.
        initialize_memory_manager()
        print("Memory manager initialized successfully.")

    except Exception as e:
        print(f"FATAL ERROR DURING STARTUP: {e}")
        # Raising an exception here will prevent the app from starting
        # if the database or memory manager fails to initialize.
        raise RuntimeError("Could not initialize database or memory manager.") from e
    
    yield
    
    # --- Code here would run on shutdown ---
    print("Server shutting down...")
    if engine:
        await engine.dispose()
        print("Database connection pool closed.")

# --- Main FastAPI application instance ---
app = FastAPI(
    title="AI Interactive Smart Doll API",
    description="The core API for the smart storytelling toy.",
    version="1.0.0",
    lifespan=lifespan # The lifespan manager is attached to the app here.
)

# --- Register API routers ---
# Splitting routers into separate files keeps the main file clean.
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(children.router)
app.include_router(dolls.router)
app.include_router(conversation.router)

@app.get("/", tags=["Health Check"])
async def root():
    """A simple health check endpoint."""
    return {"status": "ok", "message": "Welcome to the AI Interactive Smart Doll API!"}

