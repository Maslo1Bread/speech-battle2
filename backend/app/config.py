from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"

load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str = "change-me-to-a-long-random-string-please"
    database_url: str = f"sqlite:///{(ROOT_DIR / 'speech_battle.db').as_posix()}"
    access_token_expire_minutes: int = 60 * 24 * 7
    groq_api_key: str = ""
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_email: str = "admin@speech-battle.local"
    turn_seconds: int = 120
    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
