from datetime import datetime
from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserRepository:
    """Repository for managing user data in MongoDB."""

    def __init__(self, client: AsyncIOMotorClient):
        self.client: AsyncIOMotorClient = client
        self.database: AsyncIOMotorDatabase = client[settings.db.MONGODB_DB_NAME]
        self.collection: AsyncIOMotorCollection = self.database["users"]

    async def create_user(
        self, user_id: str, user_data: UserCreate, hashed_password: str
    ) -> UserResponse:
        """Create a new user."""
        try:
            user_dict = {
                "id": user_id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "hashed_password": hashed_password,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "token_creation_at": datetime.utcnow(),
            }

            result = await self.collection.insert_one(user_dict)

            if result.inserted_id:
                return await self.get_user_by_id(user_id)
            else:
                raise DatabaseException("Failed to create user")

        except Exception as e:
            raise DatabaseException(f"Failed to create user: {str(e)}")

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """Get user by ID."""
        try:
            doc = await self.collection.find_one({"id": user_id})
            if doc:
                doc.pop("_id", None)
                doc.pop("hashed_password", None)  # Don't return password
                return UserResponse(**doc)
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to get user: {str(e)}")

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email (including password for authentication)."""
        try:
            doc = await self.collection.find_one({"email": email})
            if doc:
                doc.pop("_id", None)
                return doc
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to get user by email: {str(e)}")

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[UserResponse]:
        """Update user information."""
        try:
            update_data = {}
            if user_data.full_name is not None:
                update_data["full_name"] = user_data.full_name
            if user_data.is_active is not None:
                update_data["is_active"] = user_data.is_active

            if update_data:
                update_data["updated_at"] = datetime.utcnow()

                result = await self.collection.update_one({"id": user_id}, {"$set": update_data})

                if result.modified_count > 0:
                    return await self.get_user_by_id(user_id)

            return await self.get_user_by_id(user_id)
        except Exception as e:
            raise DatabaseException(f"Failed to update user: {str(e)}")

    async def update_token_creation_at(self, user_id: str, token_creation_at: datetime) -> None:
        """Update user's token creation timestamp."""
        try:
            await self.collection.update_one(
                {"id": user_id},
                {"$set": {"token_creation_at": token_creation_at, "updated_at": datetime.utcnow()}},
            )
        except Exception as e:
            raise DatabaseException(f"Failed to update token creation time: {str(e)}")

    async def get_by_token_creation_at(self, user_id: str, token_creation_at: float) -> bool:
        """Check if user's token creation time matches."""
        try:
            # Convert Unix timestamp to datetime for comparison
            # The JWT iat field is in Unix timestamp format (seconds since epoch)
            target_datetime = datetime.fromtimestamp(token_creation_at)

            # Find user and check if token creation time matches (with small tolerance for precision)
            doc = await self.collection.find_one({"id": user_id})
            if not doc:
                return False

            stored_datetime = doc.get("token_creation_at")
            if not stored_datetime:
                return False

            # Compare with a small tolerance (1 second) to account for precision differences
            time_diff = abs((stored_datetime - target_datetime).total_seconds())
            return time_diff <= 1.0

        except Exception as e:
            raise DatabaseException(f"Failed to check token creation time: {str(e)}")

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        try:
            result = await self.collection.delete_one({"id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            raise DatabaseException(f"Failed to delete user: {str(e)}")
