import uuid
from datetime import datetime
from typing import Optional

from app.core.exceptions import DatabaseException
from app.core.security.security import get_password_hash, verify_password
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    """Service for managing users and profiles."""

    def __init__(self, user_repository: UserRepository, profile_repository: ProfileRepository):
        self.user_repository = user_repository
        self.profile_repository = profile_repository

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user with profile."""
        try:
            # Check if user already exists
            existing_user = await self.user_repository.get_user_by_email(user_data.email)
            if existing_user:
                raise DatabaseException("User with this email already exists")

            # Validate and hash password
            if len(user_data.password.encode("utf-8")) > 72:
                # Log a warning but continue (password will be truncated safely)
                print(
                    f"Warning: Password for user {user_data.email} is longer than 72 bytes and will be truncated"
                )

            hashed_password = get_password_hash(user_data.password)

            # Create user
            user_id = str(uuid.uuid4())
            user = await self.user_repository.create_user(user_id, user_data, hashed_password)

            # Create profile
            profile_id = str(uuid.uuid4())
            await self.profile_repository.create_profile(profile_id, user_id)

            return user

        except Exception as e:
            raise DatabaseException(f"Failed to create user: {str(e)}")

    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        return await self.user_repository.get_user_by_id(user_id)

    async def authenticate_user(self, email: str, password: str) -> Optional[dict]:
        """Authenticate user with email and password."""
        try:
            user = await self.user_repository.get_user_by_email(email)
            if not user:
                return None

            if not verify_password(password, user["hashed_password"]):
                return None

            if not user.get("is_active", True):
                return None

            return user

        except Exception as e:
            raise DatabaseException(f"Failed to authenticate user: {str(e)}")

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[UserResponse]:
        """Update user information."""
        return await self.user_repository.update_user(user_id, user_data)

    async def update_token_creation_at(self, user_id: str, token_creation_at: datetime) -> None:
        """Update user's token creation timestamp."""
        await self.user_repository.update_token_creation_at(user_id, token_creation_at)

    async def get_by_token_creation_at(self, user_id: str, token_creation_at: float) -> bool:
        """Check if user's token creation time matches."""
        return await self.user_repository.get_by_token_creation_at(user_id, token_creation_at)

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user and their profile."""
        try:
            # Delete profile first
            await self.profile_repository.delete_profile(user_id)

            # Delete user
            return await self.user_repository.delete_user(user_id)

        except Exception as e:
            raise DatabaseException(f"Failed to delete user: {str(e)}")
