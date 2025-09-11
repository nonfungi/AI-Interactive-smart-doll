# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # با این پیکربندی، lowercase و uppercase هر دو پذیرفته می‌شن
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

    # Database configuration
    database_url: str = Field(..., alias="DATABASE_URL")

    # JWT authentication settings
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"

    # API Keys for external services
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str | None = None
    google_api_key: str
    huggingface_api_key: str | None = None

    # Master token for doll hardware authentication
    doll_master_auth_token: str

    # Google Cloud Service Account JSON (as string)
    google_credentials_json: str | None = None

    # Optional TTS tuning
    gcp_tts_voice: str | None = None
    gcp_tts_rate: float | None = None
    gcp_tts_pitch: float | None = None

    # Server
    api_port: int = 8001

settings = Settings()
