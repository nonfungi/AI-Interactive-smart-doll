import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI

# --- Import routers and database components ---
from .database import engine, Base
from .routers import users, children, dolls, conversation

# --- Lifespan Event Handler (for startup and shutdown events) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    On startup, it ensures that all necessary database tables are created.
    """
    print("Server starting up...")
    
    # --- NEW: Create database tables on startup ---
    async with engine.begin() as conn:
        # This command connects to the database and runs the SQL to create
        # all tables that are defined in models.py, but only if they don't already exist.
        await conn.run_sync(Base.metadata.create_all)
        print("Database tables checked/created successfully.")
        
    yield # The application runs here
    
    print("Server shutting down...")

# --- App Initialization ---
app = FastAPI(
    title="AI Interactive Smart Doll API",
    description="The core API for the smart storytelling toy.",
    version="0.1.0",
    lifespan=lifespan # Use the lifespan handler
)

# --- Include API Routers ---
# This makes the main file clean and organizes endpoints into separate files.
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(children.router, prefix="/children", tags=["Children"])
app.include_router(dolls.router, prefix="/dolls", tags=["Dolls"])
app.include_router(conversation.router, tags=["Conversation"])


@app.get("/", tags=["Health Check"])
async def root():
    """A simple health check endpoint to confirm the API is running."""
    return {"status": "ok", "message": "Welcome to the AI Interactive Smart Doll API!"}

# --- Main Execution Block (for local development) ---
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=True)

