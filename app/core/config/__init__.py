from pydantic_settings import BaseSettings

from .application import ApplicationSettings
from .database import DatabaseSettings
from .logging import LoggingSettings
from .security import SecuritySettings
from .ai import AISettings


class Settings(BaseSettings):
    app: ApplicationSettings = ApplicationSettings()
    db: DatabaseSettings = DatabaseSettings()
    ai: AISettings = AISettings()
    security: SecuritySettings = SecuritySettings()
    logging: LoggingSettings = LoggingSettings()

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "allow"


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
