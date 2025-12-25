from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic_settings import BaseSettings


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    JSON = "json"
    TEXT = "text"


class LoggingSettings(BaseSettings):
    # General Settings
    LEVEL: LogLevel = LogLevel.INFO
    FORMAT: LogFormat = LogFormat.JSON

    # File Logging
    TO_FILE: bool = True
    FILE_PATH: str = "logs/app.log"
    FILE_MAX_SIZE: int = 10485760
    FILE_BACKUP_COUNT: int = 5
    FILE_ENCODING: str = "utf-8"

    # Console Logging
    TO_CONSOLE: bool = False
    CONSOLE_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Sentry Integration
    SENTRY_ENABLED: bool = False
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # LangSmith
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: Optional[str] = None
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: Optional[str] = None

    def get_logging_config(self) -> Dict[str, Any]:
        # check if logs folder exists and create it if not
        if self.TO_FILE:
            log_file_path = Path(self.FILE_PATH)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "fmt": "%(asctime)s %(name)s %(levelname)s %(message)s",
                },
                "standard": {"format": self.CONSOLE_FORMAT},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": ("json" if self.FORMAT == LogFormat.JSON else "standard"),
                    "level": self.LEVEL.value,
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": self.FILE_PATH,
                    "maxBytes": self.FILE_MAX_SIZE,
                    "backupCount": self.FILE_BACKUP_COUNT,
                    "formatter": ("json" if self.FORMAT == LogFormat.JSON else "standard"),
                    "encoding": self.FILE_ENCODING,
                },
            },
            "root": {
                "level": self.LEVEL.value,
                "handlers": ["file"] if self.TO_FILE else [],
            },
        }

    class Config:
        env_prefix = "LOG_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields to ignore env vars with other prefixes
