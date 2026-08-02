import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file if available
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Config(BaseSettings):
    """
    Application configuration settings loaded from environment variables or .env file.
    """
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    CHANNEL: str = os.getenv("CHANNEL", "")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "jobs.db")
    FETCH_INTERVAL_MINUTES: int = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOCATION_FILTER: str = os.getenv("LOCATION_FILTER", "GLOBAL,MENA,EGYPT")

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def clean_channel(self) -> str:
        """
        Normalize channel handle from URL or raw handle string.
        e.g., 'https://t.me/dailymobiledevjobs' -> '@dailymobiledevjobs'
        'dailymobiledevjobs' -> '@dailymobiledevjobs'
        '@dailymobiledevjobs' -> '@dailymobiledevjobs'
        """
        ch = self.CHANNEL.strip()
        if not ch:
            return ""
        if ch.startswith("https://t.me/"):
            ch = ch.replace("https://t.me/", "")
        if ch.startswith("http://t.me/"):
            ch = ch.replace("http://t.me/", "")
        if ch.startswith("t.me/"):
            ch = ch.replace("t.me/", "")
        ch = ch.rstrip("/")
        if not ch.startswith("@") and not ch.startswith("-100"):
            ch = f"@{ch}"
        return ch


settings = Config()
