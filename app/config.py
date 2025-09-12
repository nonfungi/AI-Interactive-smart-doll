# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# This is the definitive Pydantic settings model.
# It defines all the required environment variables for the application.
class Settings(BaseSettings):
    # This configuration tells Pydantic to read from a .env file (for local dev)
    # and to ignore case sensitivity, which is crucial for Hugging Face secrets.
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

    # --- Variables will be loaded from environment secrets ---
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    
    # API Keys for external services
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    google_api_key: str
    elevenlabs_api_key: str
    
    # Master token for simple hardware authentication
    doll_master_auth_token: str

# --- The Correct Way to Handle Settings in FastAPI ---
# We use a function with a cache (@lru_cache). This ensures that the Settings
# object is created only ONCE, the very first time it's needed, and after
# the application has started and loaded all environment variables.
@lru_cache
def get_settings() -> Settings:
    """
    Returns the application settings.
    Uses a cache to ensure the settings are loaded only once.
    """
    print("Loading application settings...")
    settings = Settings()
    print("Application settings loaded successfully.")
    return settings

