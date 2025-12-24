from typing import Any, Dict, Optional

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    MONGODB_MIN_POOL_SIZE: int = 10
    MONGODB_MAX_POOL_SIZE: int = 100
    MONGODB_TIMEOUT_MS: int = 5000
    MONGODB_RETRY_WRITES: bool = True
    MONGODB_TLS: bool = False
    MONGODB_TLS_CERT_PATH: Optional[str] = None

    @property
    def mongodb_connection_params(self) -> Dict[str, Any]:
        return {
            "minPoolSize": self.MONGODB_MIN_POOL_SIZE,
            "maxPoolSize": self.MONGODB_MAX_POOL_SIZE,
            "timeoutMS": self.MONGODB_TIMEOUT_MS,
            "retryWrites": self.MONGODB_RETRY_WRITES,
            "tls": self.MONGODB_TLS,
        }

    class Config:
        env_prefix = "DB_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields to ignore env vars with other prefixes
