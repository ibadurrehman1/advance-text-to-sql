from pydantic import BaseModel, EmailStr, Field, validator


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password", max_length=128)

    @validator("password")
    def validate_password(cls, value):
        """Validate password length."""
        if len(value) > 128:
            raise ValueError("Password cannot be longer than 128 characters")
        return value


class LoginResponse(BaseModel):
    """Response schema for successful login."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: dict = Field(description="User information")


class TokenResponse(BaseModel):
    """Response schema for token operations."""

    access_token: str = Field(description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
