from datetime import datetime
from typing import List, Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.schemas.thread import ThreadCreateRequest, ThreadResponse, ThreadUpdateRequest


class ThreadRepository:
    """Repository for managing thread data in MongoDB."""

    def __init__(self, client: AsyncIOMotorClient):
        self.client: AsyncIOMotorClient = client
        self.database: AsyncIOMotorDatabase = client[settings.db.MONGODB_DB_NAME]
        self.collection: AsyncIOMotorCollection = self.database["threads"]

    async def create_thread(
        self,
        thread_id: str,
        request: ThreadCreateRequest,
        created_by: str,
        business_name: str,
        tables_count: int = 0,
        columns_count: int = 0,
        status: str = "active",
    ) -> ThreadResponse:
        """Create a new thread with business connection info."""
        try:
            thread_dict = {
                "thread_id": thread_id,
                "name": request.name,
                "description": request.description,
                "business_id": request.business_id,
                "business_name": business_name,
                "tables_count": tables_count,
                "columns_count": columns_count,
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": status,
            }

            result = await self.collection.insert_one(thread_dict)

            if result.inserted_id:
                return await self.get_thread_by_id(thread_id)
            else:
                raise DatabaseException("Failed to create thread")

        except Exception as e:
            raise DatabaseException(f"Failed to create thread: {str(e)}")

    async def get_thread_by_id(self, thread_id: str) -> Optional[ThreadResponse]:
        """Get thread by ID."""
        try:
            doc = await self.collection.find_one({"thread_id": thread_id})
            if doc:
                doc.pop("_id", None)
                return ThreadResponse(**doc)
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to get thread: {str(e)}")

    async def get_thread_business_id(self, thread_id: str) -> Optional[str]:
        """Get the business ID for a thread (internal use only)."""
        try:
            doc = await self.collection.find_one(
                {"thread_id": thread_id},
                {"business_id": 1},
            )
            if doc:
                return doc["business_id"]
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to get thread business ID: {str(e)}")

    async def list_threads_by_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[ThreadResponse]:
        """List all threads for a user with pagination."""
        try:
            cursor = (
                self.collection.find({"created_by": user_id})
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )
            threads = []
            async for doc in cursor:
                doc.pop("_id", None)
                threads.append(ThreadResponse(**doc))
            return threads
        except Exception as e:
            raise DatabaseException(f"Failed to list threads: {str(e)}")

    async def update_thread(
        self, thread_id: str, request: ThreadUpdateRequest
    ) -> Optional[ThreadResponse]:
        """Update thread metadata."""
        try:
            update_data = {}
            if request.name is not None:
                update_data["name"] = request.name
            if request.description is not None:
                update_data["description"] = request.description

            if update_data:
                update_data["updated_at"] = datetime.utcnow()

                result = await self.collection.update_one(
                    {"thread_id": thread_id}, {"$set": update_data}
                )

                if result.modified_count > 0:
                    return await self.get_thread_by_id(thread_id)

            return await self.get_thread_by_id(thread_id)
        except Exception as e:
            raise DatabaseException(f"Failed to update thread: {str(e)}")

    async def update_thread_stats(
        self, thread_id: str, tables_count: int, columns_count: int
    ) -> None:
        """Update thread statistics (table and column counts)."""
        try:
            await self.collection.update_one(
                {"thread_id": thread_id},
                {
                    "$set": {
                        "tables_count": tables_count,
                        "columns_count": columns_count,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
        except Exception as e:
            raise DatabaseException(f"Failed to update thread stats: {str(e)}")

    async def update_thread_status(self, thread_id: str, status: str) -> None:
        """Update thread status."""
        try:
            await self.collection.update_one(
                {"thread_id": thread_id},
                {"$set": {"status": status, "updated_at": datetime.utcnow()}},
            )
        except Exception as e:
            raise DatabaseException(f"Failed to update thread status: {str(e)}")

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread."""
        try:
            result = await self.collection.delete_one({"thread_id": thread_id})
            return result.deleted_count > 0
        except Exception as e:
            raise DatabaseException(f"Failed to delete thread: {str(e)}")

    async def count_threads_by_user(self, user_id: str) -> int:
        """Count total number of threads for a user."""
        try:
            return await self.collection.count_documents({"created_by": user_id})
        except Exception as e:
            raise DatabaseException(f"Failed to count threads: {str(e)}")

    async def check_thread_ownership(self, thread_id: str, user_id: str) -> bool:
        """Check if a user owns a specific thread."""
        try:
            doc = await self.collection.find_one({"thread_id": thread_id, "created_by": user_id})
            return doc is not None
        except Exception as e:
            raise DatabaseException(f"Failed to check thread ownership: {str(e)}")
