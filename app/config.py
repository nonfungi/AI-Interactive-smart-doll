from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database configuration
    database_url: str

    # JWT authentication settings
    jwt_secret_key: str
    jwt_algorithm: str

    # API Keys for external services
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str | None = None
    google_api_key: str
    huggingface_api_key: str | None = None # Optional, depending on future use

    # Master token for doll hardware authentication
    doll_master_auth_token: str

    # --- NEW: Google Cloud Service Account Credentials ---
    # This will hold the content of the service account JSON file.
    google_credentials_json: str | None = None

    # Server configuration
    api_port: int = 8001

    class Config:
        env_file = ".env"

settings = Settings()
