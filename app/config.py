import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Конфигурация приложения из переменных окружения (со значениями по умолчанию)."""

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_path: str = "data/app.db"
    log_level: str = "INFO"


def load_settings() -> Settings:
    return Settings(
        app_host=os.getenv("APP_HOST", Settings.app_host),
        app_port=int(os.getenv("APP_PORT", Settings.app_port)),
        database_path=os.getenv("DATABASE_PATH", Settings.database_path),
        log_level=os.getenv("LOG_LEVEL", Settings.log_level),
    )
