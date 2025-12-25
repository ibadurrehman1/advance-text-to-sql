from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    PRIMARY_MODEL_NAME: str
    PRIMARY_MODEL_TEMPERATURE: float
    SECONDARY_MODEL_NAME: str
    SECONDARY_MODEL_TEMPERATURE: float

    class Config:
        env_prefix = "AI_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields to ignore env vars with other prefixes
