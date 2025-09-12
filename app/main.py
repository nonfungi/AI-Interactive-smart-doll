# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
# --- FIX: Import FileResponse to serve HTML files ---
from fastapi.responses import FileResponse
import os

# --- Import initializers and modules ---
from . import database
from .memory import initialize_memory_manager
from .routers import users, children, dolls, conversation, auth
from .config import get_settings

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting up...")
    settings = get_settings()
    
    try:
        database.initialize_db()
        async with database.engine.begin() as conn:
            await conn.run_sync(database.Base.metadata.create_all)
            print("Database tables checked/created successfully.")
        
        initialize_memory_manager()

    except Exception as e:
        print(f"FATAL ERROR DURING STARTUP: {e}")
        raise RuntimeError("Could not initialize services.") from e
    
    yield
    
    print("Server shutting down...")
    await database.close_db_connection()


# --- Main FastAPI Application Instance ---
app = FastAPI(
    title="AI Interactive Smart Doll API",
    description="The core API for the smart storytelling toy.",
    version="1.0.0",
    lifespan=lifespan
)

# --- Register API Routers ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(children.router)
app.include_router(dolls.router)
app.include_router(conversation.router)

# --- FIX: Serve the HTML Demo UI at the root URL ---
# Get the path to the templates directory
templates_dir = os.path.join(os.path.dirname(__file__), "templates")

@app.get("/", tags=["UI Demo"])
async def serve_demo_ui():
    """
    Serves the main HTML user interface for the live demo.
    """
    html_file_path = os.path.join(templates_dir, "demo.html")
    if os.path.exists(html_file_path):
        return FileResponse(html_file_path)
    return {"error": "demo.html not found"}
```

### نتیجه
با این تغییرات، هر کسی که به آدرس اصلی Space شما در هاگینگ فیس برود (مثلاً `https://your-username-your-space.hf.space/`)، مستقیماً با رابط کاربری دموی شما مواجه خواهد شد و می‌تواند با عروسک هوشمند صحبت کند.

### دستورات Git برای ارسال تغییرات
پس از اعمال این تغییرات، از این دستورات برای پوش کردن کدها استفاده کنید.

