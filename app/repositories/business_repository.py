from datetime import datetime
from typing import List, Optional

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.schemas.business import (
    BusinessCreateRequest,
    BusinessResponse,
    BusinessUpdateRequest,
)
from app.utilities.encryption import encryption_service


class BusinessRepository:
    """Repository for managing business data in MongoDB."""

    def __init__(self, client: AsyncIOMotorClient):
        self.client: AsyncIOMotorClient = client
        self.database: AsyncIOMotorDatabase = client[settings.db.MONGODB_DB_NAME]
        self.collection: AsyncIOMotorCollection = self.database["businesses"]

    async def create_business(
        self,
        business_id: str,
        request: BusinessCreateRequest,
        created_by: str,
        tables_count: int = 0,
        columns_count: int = 0,
        status: str = "active",
    ) -> BusinessResponse:
        """Create a new business with database connection info."""
        try:
            # Encrypt the SQL URI for security
            encrypted_uri = encryption_service.encrypt(request.sql_uri)
            # Mask the SQL URI for responses (hide password)
            masked_uri = self._mask_sql_uri(request.sql_uri)

            business_dict = {
                "business_id": business_id,
                "name": request.name,
                "description": request.description,
                "industry": request.industry,
                "sql_uri": encrypted_uri,  # Store encrypted URI
                "masked_sql_uri": masked_uri,  # Store masked version for responses
                "schema": request.schema,
                "include_tables": request.include_tables,
                "exclude_tables": request.exclude_tables,
                "primary_tables": request.primary_tables,
                "tables_count": tables_count,
                "columns_count": columns_count,
                "created_by": created_by,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": status,
            }

            result = await self.collection.insert_one(business_dict)

            if result.inserted_id:
                return await self.get_business_by_id(business_id)
            else:
                raise DatabaseException("Failed to create business")

        except Exception as e:
            raise DatabaseException(f"Failed to create business: {str(e)}")

    async def get_business_by_id(self, business_id: str) -> Optional[BusinessResponse]:
        """Get business by ID."""
        try:
            doc = await self.collection.find_one({"business_id": business_id})
            if doc:
                # Use masked URI for response
                doc["sql_uri"] = doc.get("masked_sql_uri", doc["sql_uri"])
                doc.pop("_id", None)
                doc.pop("masked_sql_uri", None)
                return BusinessResponse(**doc)
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to get business: {str(e)}")

    async def get_business_sql_config(self, business_id: str) -> Optional[dict]:
        """Get the actual SQL configuration for database connection (internal use only)."""
        try:
            doc = await self.collection.find_one(
                {"business_id": business_id},
                {
                    "sql_uri": 1,
                    "schema": 1,
                    "include_tables": 1,
                    "exclude_tables": 1,
                    "primary_tables": 1,
                    "name": 1,
                    "description": 1,
                    "industry": 1,
                },
            )
            if doc:
                # Decrypt the SQL URI for internal use
                decrypted_uri = encryption_service.decrypt(doc["sql_uri"])

                return {
                    "sql_uri": decrypted_uri,
                    "schema": doc.get("schema"),
                    "include_tables": doc.get("include_tables"),
                    "exclude_tables": doc.get("exclude_tables"),
                    "primary_tables": doc.get("primary_tables"),
                    "name": doc["name"],
                    "description": doc["description"],
                    "industry": doc["industry"],
                }
            return None
        except Exception as e:
            raise DatabaseException(f"Failed to get business SQL config: {str(e)}")

    async def list_businesses_by_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[BusinessResponse]:
        """List all businesses created by a specific user with pagination."""
        try:
            cursor = (
                self.collection.find({"created_by": user_id})
                .sort("created_at", -1)
                .skip(offset)
                .limit(limit)
            )
            businesses = []
            async for doc in cursor:
                # Use masked URI for response
                doc["sql_uri"] = doc.get("masked_sql_uri", doc["sql_uri"])
                doc.pop("_id", None)
                doc.pop("masked_sql_uri", None)
                businesses.append(BusinessResponse(**doc))
            return businesses
        except Exception as e:
            raise DatabaseException(f"Failed to list businesses: {str(e)}")

    async def update_business(
        self, business_id: str, request: BusinessUpdateRequest
    ) -> Optional[BusinessResponse]:
        """Update business metadata."""
        try:
            update_data = {}
            if request.name is not None:
                update_data["name"] = request.name
            if request.description is not None:
                update_data["description"] = request.description
            if request.industry is not None:
                update_data["industry"] = request.industry
            if request.primary_tables is not None:
                update_data["primary_tables"] = request.primary_tables

            if update_data:
                update_data["updated_at"] = datetime.utcnow()

                result = await self.collection.update_one(
                    {"business_id": business_id}, {"$set": update_data}
                )

                if result.modified_count > 0:
                    return await self.get_business_by_id(business_id)

            return await self.get_business_by_id(business_id)
        except Exception as e:
            raise DatabaseException(f"Failed to update business: {str(e)}")

    async def update_business_stats(
        self, business_id: str, tables_count: int, columns_count: int
    ) -> None:
        """Update business statistics (table and column counts)."""
        try:
            await self.collection.update_one(
                {"business_id": business_id},
                {
                    "$set": {
                        "tables_count": tables_count,
                        "columns_count": columns_count,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
        except Exception as e:
            raise DatabaseException(f"Failed to update business stats: {str(e)}")

    async def update_business_status(self, business_id: str, status: str) -> None:
        """Update business status."""
        try:
            await self.collection.update_one(
                {"business_id": business_id},
                {"$set": {"status": status, "updated_at": datetime.utcnow()}},
            )
        except Exception as e:
            raise DatabaseException(f"Failed to update business status: {str(e)}")

    async def delete_business(self, business_id: str) -> bool:
        """Delete a business."""
        try:
            result = await self.collection.delete_one({"business_id": business_id})
            return result.deleted_count > 0
        except Exception as e:
            raise DatabaseException(f"Failed to delete business: {str(e)}")

    async def count_businesses_by_user(self, user_id: str) -> int:
        """Count total number of businesses for a user."""
        try:
            return await self.collection.count_documents({"created_by": user_id})
        except Exception as e:
            raise DatabaseException(f"Failed to count businesses: {str(e)}")

    async def check_business_ownership(self, business_id: str, user_id: str) -> bool:
        """Check if a user owns a specific business."""
        try:
            doc = await self.collection.find_one(
                {"business_id": business_id, "created_by": user_id}
            )
            return doc is not None
        except Exception as e:
            raise DatabaseException(f"Failed to check business ownership: {str(e)}")

    def _mask_sql_uri(self, sql_uri: str) -> str:
        """Mask sensitive information in SQL URI for security."""
        try:
            if not sql_uri or "://" not in sql_uri:
                return "***masked***"

            parts = sql_uri.split("://")
            if len(parts) != 2:
                return "***masked***"

            protocol = parts[0]
            rest = parts[1]

            # Case 1: URI with authentication (user:pass@host or user@host)
            if "@" in rest:
                auth_part, host_part = rest.split("@", 1)
                if ":" in auth_part:
                    username, _ = auth_part.split(":", 1)
                    return f"{protocol}://{username}:***@{host_part}"
                else:
                    return f"{protocol}://***@{host_part}"

            # Case 2: URI without explicit authentication (like trusted connection, sqlite, etc.)
            # Mask the server/database details for security
            if protocol.lower() in ["sqlite"]:
                # For SQLite, just show the protocol
                return f"{protocol}://***"
            elif "/" in rest:
                # For server-based DBs without auth, mask server but show database name pattern
                if "?" in rest:
                    # Has query parameters (like SQL Server with trusted_connection)
                    db_part = rest.split("?")[0]
                    return f"{protocol}://***/{db_part.split('/')[-1]}?***"
                else:
                    # Simple server/database format
                    return f"{protocol}://***/{rest.split('/')[-1]}"
            else:
                # Fallback for any other format
                return f"{protocol}://***"

        except Exception:
            return "***masked***"  # Fallback masking
