from enum import Enum
from typing import List

from pydantic_settings import BaseSettings


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class ApplicationSettings(BaseSettings):
    # Basic Application Settings
    PROJECT_NAME: str = "Advance Text to SQL"
    VERSION: str = "0.0.1"
    DESCRIPTION: str = "Advance Text to SQL"
    API_V1_STR: str = "/api/v1"

    # Environment Settings
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEBUG: bool = False

    # Server Settings
    HOST: str
    PORT: int
    WORKERS_COUNT: int = 4
    RELOAD: bool = True

    # CORS Settings (TODO: add only allowed ones)
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    ALLOWED_HOSTS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_WINDOW_SIZE: int = 60
    RATE_LIMIT_BURST: int = 100
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_EXCLUDED_PATHS: List[str] = ["/health", "/metrics"]

    # Documentation Settings
    DOCS_URL: str = "/api/docs"
    REDOC_URL: str = "/api/redoc"
    OPENAPI_URL: str = "/api/openapi.json"

    # Middleware Settings
    MIDDLEWARE_GZIP_MINIMUM_SIZE: int = 1000

    class Config:
        env_prefix = "APP_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields to ignore env vars with other prefixes
