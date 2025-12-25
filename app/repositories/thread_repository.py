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
        tables_count: int = 0,
        columns_count: int = 0,
        status: str = "active",
    ) -> ThreadResponse:
        """Create a new thread with database connection info."""
        try:
            # Mask the SQL URI for security (hide password)
            masked_uri = self._mask_sql_uri(request.sql_uri)

            thread_dict = {
                "thread_id": thread_id,
                "name": request.name,
                "description": request.description,
                "sql_uri": request.sql_uri,  # Store full URI (encrypted in production)
                "masked_sql_uri": masked_uri,  # Store masked version for responses
                "schema": request.schema,
                "include_tables": request.include_tables,
                "exclude_tables": request.exclude_tables,
                "tables_count": tables_count,
                "columns_count": columns_count,
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
                # Use masked URI for response
                doc["sql_uri"] = doc.get("masked_sql_uri", doc["sql_uri"])
                doc.pop("_id", None)
                doc.pop("masked_sql_uri", None)
                return ThreadResponse(**doc)
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to get thread: {str(e)}")

    async def get_thread_sql_uri(self, thread_id: str) -> Optional[str]:
        """Get the actual SQL URI for database connection (internal use only)."""
        try:
            doc = await self.collection.find_one(
                {"thread_id": thread_id},
                {"sql_uri": 1, "schema": 1, "include_tables": 1, "exclude_tables": 1},
            )
            if doc:
                return {
                    "sql_uri": doc["sql_uri"],
                    "schema": doc.get("schema"),
                    "include_tables": doc.get("include_tables"),
                    "exclude_tables": doc.get("exclude_tables"),
                }
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to get thread SQL URI: {str(e)}")

    async def list_threads(self, limit: int = 50, offset: int = 0) -> List[ThreadResponse]:
        """List all threads with pagination."""
        try:
            cursor = self.collection.find().sort("created_at", -1).skip(offset).limit(limit)
            threads = []
            async for doc in cursor:
                # Use masked URI for response
                doc["sql_uri"] = doc.get("masked_sql_uri", doc["sql_uri"])
                doc.pop("_id", None)
                doc.pop("masked_sql_uri", None)
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

    async def count_threads(self) -> int:
        """Count total number of threads."""
        try:
            return await self.collection.count_documents({})
        except Exception as e:
            raise DatabaseException(f"Failed to count threads: {str(e)}")

    def _mask_sql_uri(self, sql_uri: str) -> str:
        """Mask sensitive information in SQL URI for security."""
        try:
            # Simple masking - replace password with ***
            if "://" in sql_uri and "@" in sql_uri:
                parts = sql_uri.split("://")
                if len(parts) == 2:
                    protocol = parts[0]
                    rest = parts[1]

                    if "@" in rest:
                        auth_part, host_part = rest.split("@", 1)
                        if ":" in auth_part:
                            username, _ = auth_part.split(":", 1)
                            return f"{protocol}://{username}:***@{host_part}"
                        else:
                            return f"{protocol}://***@{host_part}"

            return sql_uri  # Return as-is if can't parse
        except Exception:
            return "***masked***"  # Fallback masking
