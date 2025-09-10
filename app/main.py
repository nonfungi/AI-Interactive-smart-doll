# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import AsyncSessionLocal, engine, Base
from .routers import users, children, dolls, conversation

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    On startup, it can be used to initialize resources like database connections.
    On shutdown, it can be used for cleanup.
    """
    print("Server starting up...")
    # You could add database table creation here if you wanted it to run on startup
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    yield
    print("Server shutting down...")

# --- App Initialization ---
app = FastAPI(
    title="AI Interactive Smart Doll API",
    description="The core API for the smart storytelling toy, now refactored for clarity and scalability.",
    version="0.2.0",
    lifespan=lifespan
)

# --- Include Routers ---
# By including routers, we keep the main file clean and delegate endpoint logic
# to specialized modules.
app.include_router(users.router)
app.include_router(children.router)
app.include_router(dolls.router)
app.include_router(conversation.router)


@app.get("/", tags=["Health Check"])
async def root():
    """
    A simple health check endpoint to confirm the API is running.
    """
    return {"status": "ok", "message": "Welcome to the AI Interactive Smart Doll API!"}
