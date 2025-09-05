# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import datetime

class Settings(BaseSettings):
    # All variables should be lowercase here
    api_port: int = 8001
    doll_master_auth_token: str
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    huggingface_api_key: str # --- ADD THIS LINE ---

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    @property
    def current_time(self) -> str:
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

settings = Settings()
