from datetime import datetime
from typing import Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.schemas.user import ProfileResponse


class ProfileRepository:
    """Repository for managing user profile data in MongoDB."""

    def __init__(self, client: AsyncIOMotorClient):
        self.client: AsyncIOMotorClient = client
        self.database: AsyncIOMotorDatabase = client[settings.db.MONGODB_DB_NAME]
        self.collection: AsyncIOMotorCollection = self.database["profiles"]

    async def create_profile(self, profile_id: str, user_id: str) -> ProfileResponse:
        """Create a new user profile."""
        try:
            profile_dict = {
                "id": profile_id,
                "user_id": user_id,
                "bio": None,
                "avatar_url": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            result = await self.collection.insert_one(profile_dict)

            if result.inserted_id:
                return await self.get_profile_by_user_id(user_id)
            else:
                raise DatabaseException("Failed to create profile")

        except Exception as e:
            raise DatabaseException(f"Failed to create profile: {str(e)}")

    async def get_profile_by_user_id(self, user_id: str) -> Optional[ProfileResponse]:
        """Get profile by user ID."""
        try:
            doc = await self.collection.find_one({"user_id": user_id})
            if doc:
                doc.pop("_id", None)
                return ProfileResponse(**doc)
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to get profile: {str(e)}")

    async def update_profile(
        self, user_id: str, bio: Optional[str] = None, avatar_url: Optional[str] = None
    ) -> Optional[ProfileResponse]:
        """Update user profile."""
        try:
            update_data = {}
            if bio is not None:
                update_data["bio"] = bio
            if avatar_url is not None:
                update_data["avatar_url"] = avatar_url

            if update_data:
                update_data["updated_at"] = datetime.utcnow()

                result = await self.collection.update_one(
                    {"user_id": user_id}, {"$set": update_data}
                )

                if result.modified_count > 0:
                    return await self.get_profile_by_user_id(user_id)

            return await self.get_profile_by_user_id(user_id)
        except Exception as e:
            raise DatabaseException(f"Failed to update profile: {str(e)}")

    async def delete_profile(self, user_id: str) -> bool:
        """Delete a user profile."""
        try:
            result = await self.collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            raise DatabaseException(f"Failed to delete profile: {str(e)}")
