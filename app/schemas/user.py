from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr = Field(description="User email address")
    password: str = Field(description="User password", min_length=8, max_length=128)
    full_name: str = Field(description="User full name")

    @validator("password")
    def validate_password(cls, value):
        """Validate password requirements."""
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(value) > 128:
            raise ValueError("Password cannot be longer than 128 characters")
        if len(value.encode("utf-8")) > 72:
            # Warn user about truncation but allow it
            pass  # We'll handle truncation in the security layer
        return value


class UserResponse(BaseModel):
    """Schema for user response."""

    user_id: str = Field(description="User ID", alias="id")
    email: EmailStr = Field(description="User email address")
    full_name: str = Field(description="User full name")
    is_active: bool = Field(description="Whether user is active")
    created_at: datetime = Field(description="User creation timestamp")
    updated_at: datetime = Field(description="User last update timestamp")


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    full_name: Optional[str] = Field(default=None, description="User full name")
    is_active: Optional[bool] = Field(default=None, description="Whether user is active")


class ProfileResponse(BaseModel):
    """Schema for user profile response."""

    profile_id: str = Field(description="Profile ID", alias="id")
    user_id: str = Field(description="User ID")
    bio: Optional[str] = Field(description="User bio")
    avatar_url: Optional[str] = Field(description="User avatar URL")
    created_at: datetime = Field(description="Profile creation timestamp")
    updated_at: datetime = Field(description="Profile last update timestamp")
