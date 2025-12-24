from datetime import timedelta
from typing import Optional

from pydantic_settings import BaseSettings


class SecuritySettings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    VERIFICATION_TOKEN_EXPIRE_MINUTES: int = 10
    RESET_PASSWORD_OTP_EXPIRE_MINUTES: int = 1
    COOKIE_SECURE: bool = False

    # Password Settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 50
    PASSWORD_REGEX: str = r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"

    # Authentication Settings
    AUTH_HEADER_NAME: str = "Authorization"
    AUTH_TOKEN_PREFIX: str = "Bearer"
    AUTH_COOKIE_NAME: str = "access_token"
    AUTH_COOKIE_DOMAIN: Optional[str] = None
    AUTH_COOKIE_SECURE: bool = True
    AUTH_COOKIE_SAMESITE: str = "lax"

    # API Key Settings
    API_KEY_HEADER_NAME: str = "X-API-Key"
    API_KEY_ENABLED: bool = True

    @property
    def access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

    @property
    def refresh_token_expires(self) -> timedelta:
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

    @property
    def verification_token_expires(self) -> timedelta:
        return timedelta(minutes=self.VERIFICATION_TOKEN_EXPIRE_MINUTES)

    class Config:
        env_prefix = "SECURITY_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields to ignore env vars with other prefixes
