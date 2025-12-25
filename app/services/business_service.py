import uuid
from contextlib import suppress
from typing import List, Optional

from app.core.exceptions import DatabaseException
from app.repositories.business_repository import BusinessRepository
from app.schemas.business import (
    BusinessConnectionTest,
    BusinessContext,
    BusinessCreateRequest,
    BusinessListResponse,
    BusinessResponse,
    BusinessUpdateRequest,
)
from app.utilities.database_connector import DatabaseConnector


class BusinessService:
    """Service for managing businesses with SQL database connections."""

    def __init__(self, business_repository: BusinessRepository):
        self.business_repository = business_repository
        self._business_connectors: dict[str, DatabaseConnector] = {}

    async def create_business(
        self, request: BusinessCreateRequest, created_by: str
    ) -> BusinessResponse:
        """
        Create a new business with SQL database connection.

        Args:
            request: Business creation request with SQL URI and configuration
            created_by: User ID who is creating the business

        Returns:
            BusinessResponse with business details

        Raises:
            DatabaseException: If database connection fails or business creation fails
        """
        business_id = str(uuid.uuid4())

        try:
            # Validate SQL URI format first
            if not self._validate_sql_uri(request.sql_uri):
                raise DatabaseException("Invalid SQL URI format")

            # Test the database connection
            connector = DatabaseConnector(request.sql_uri)

            # Apply table filters
            include_tables = self._parse_table_list(request.include_tables)
            exclude_tables = self._parse_table_list(request.exclude_tables)

            # Get table and column counts
            tables = connector.get_all_tables(
                include_tables=include_tables, exclude_tables=exclude_tables, schema=request.schema
            )

            columns_info = connector.get_all_columns(
                include_tables=include_tables, exclude_tables=exclude_tables, schema=request.schema
            )

            tables_count = len(tables)
            columns_count = sum(len(cols) for cols in columns_info.values())

            # Store the connector for this business
            self._business_connectors[business_id] = connector

            # Create business in database
            business = await self.business_repository.create_business(
                business_id=business_id,
                request=request,
                created_by=created_by,
                tables_count=tables_count,
                columns_count=columns_count,
                status="active",
            )

            return business

        except Exception as e:
            # Clean up connector if it was created
            if business_id in self._business_connectors:
                self._business_connectors[business_id].close()
                del self._business_connectors[business_id]

            # Update business status to error if it was created
            with suppress(Exception):
                await self.business_repository.update_business_status(business_id, "error")

            raise DatabaseException(f"Failed to create business: {str(e)}")

    async def get_business(self, business_id: str) -> Optional[BusinessResponse]:
        """Get business by ID."""
        return await self.business_repository.get_business_by_id(business_id)

    async def list_businesses(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> BusinessListResponse:
        """List all businesses for a user with pagination."""
        businesses = await self.business_repository.list_businesses_by_user(
            user_id, limit=limit, offset=offset
        )
        total = await self.business_repository.count_businesses_by_user(user_id)

        return BusinessListResponse(businesses=businesses, total=total)

    async def update_business(
        self, business_id: str, request: BusinessUpdateRequest
    ) -> Optional[BusinessResponse]:
        """Update business metadata."""
        return await self.business_repository.update_business(business_id, request)

    async def delete_business(self, business_id: str) -> bool:
        """Delete a business and clean up its database connection."""
        # Close database connection if exists
        if business_id in self._business_connectors:
            self._business_connectors[business_id].close()
            del self._business_connectors[business_id]

        # Delete from database
        return await self.business_repository.delete_business(business_id)

    async def test_business_connection(self, business_id: str) -> BusinessConnectionTest:
        """Test the database connection for a business."""
        try:
            # Get business info
            business = await self.get_business(business_id)
            if not business:
                return BusinessConnectionTest(
                    business_id=business_id,
                    connection_status="error",
                    tables_found=0,
                    columns_found=0,
                    error_message="Business not found",
                    sample_tables=[],
                )

            # Get database connector
            connector = await self.get_business_connector(business_id)
            if not connector:
                return BusinessConnectionTest(
                    business_id=business_id,
                    connection_status="error",
                    tables_found=0,
                    columns_found=0,
                    error_message="Database connector not available",
                    sample_tables=[],
                )

            # Test connection by getting tables
            tables = connector.get_all_tables()
            columns_info = connector.get_all_columns()
            columns_count = sum(len(cols) for cols in columns_info.values())

            return BusinessConnectionTest(
                business_id=business_id,
                connection_status="success",
                tables_found=len(tables),
                columns_found=columns_count,
                sample_tables=tables[:5],  # First 5 tables
            )

        except Exception as e:
            return BusinessConnectionTest(
                business_id=business_id,
                connection_status="error",
                tables_found=0,
                columns_found=0,
                error_message=str(e),
                sample_tables=[],
            )

    async def check_business_access(self, business_id: str, user_id: str) -> bool:
        """Check if a user has access to a business."""
        return await self.business_repository.check_business_ownership(business_id, user_id)

    async def get_business_connector(self, business_id: str) -> Optional[DatabaseConnector]:
        """
        Get database connector for a business.
        Creates a new connector if one doesn't exist.
        """
        # Return existing connector if available
        if business_id in self._business_connectors:
            return self._business_connectors[business_id]

        # Get business configuration from database
        business_config = await self.business_repository.get_business_sql_config(business_id)
        if not business_config:
            return None

        try:
            # Create new connector
            connector = DatabaseConnector(business_config["sql_uri"])

            # Store for future use
            self._business_connectors[business_id] = connector

            return connector

        except Exception as e:
            # Update business status to error
            await self.business_repository.update_business_status(business_id, "error")
            raise DatabaseException(f"Failed to create database connector: {str(e)}")

    async def get_business_tables(self, business_id: str) -> List[str]:
        """Get all tables for a business."""
        connector = await self.get_business_connector(business_id)
        if not connector:
            raise DatabaseException("Business connector not available")

        # Get business configuration for filters
        business_config = await self.business_repository.get_business_sql_config(business_id)
        if not business_config:
            raise DatabaseException("Business configuration not found")

        include_tables = self._parse_table_list(business_config.get("include_tables"))
        exclude_tables = self._parse_table_list(business_config.get("exclude_tables"))

        return connector.get_all_tables(
            include_tables=include_tables,
            exclude_tables=exclude_tables,
            schema=business_config.get("schema"),
        )

    async def get_business_columns(
        self, business_id: str, include_tables: Optional[List[str]] = None
    ) -> dict:
        """Get columns for a business, optionally filtered by specific tables."""
        connector = await self.get_business_connector(business_id)
        if not connector:
            raise DatabaseException("Business connector not available")

        # Get business configuration for filters
        business_config = await self.business_repository.get_business_sql_config(business_id)
        if not business_config:
            raise DatabaseException("Business configuration not found")

        # Use provided tables or fall back to business configuration
        if include_tables:
            filter_include_tables = include_tables
            filter_exclude_tables = None
        else:
            filter_include_tables = self._parse_table_list(business_config.get("include_tables"))
            filter_exclude_tables = self._parse_table_list(business_config.get("exclude_tables"))

        return connector.get_all_columns(
            include_tables=filter_include_tables,
            exclude_tables=filter_exclude_tables,
            schema=business_config.get("schema"),
        )

    async def get_business_context(self, business_id: str) -> Optional[BusinessContext]:
        """Get business context information for agent prompts."""
        business_config = await self.business_repository.get_business_sql_config(business_id)
        if not business_config:
            return None

        return BusinessContext(
            business_name=business_config["name"],
            business_description=business_config["description"],
            business_industry=business_config["industry"],
            primary_tables=business_config.get("primary_tables"),
        )

    def _parse_table_list(self, table_string: Optional[str]) -> Optional[List[str]]:
        """Parse comma-separated table string into list."""
        if not table_string:
            return None
        return [table.strip() for table in table_string.split(",") if table.strip()]

    def _validate_sql_uri(self, sql_uri: str) -> bool:
        """Validate SQL URI format and supported database types."""
        if not sql_uri:
            return False

        # Check for supported database schemes (including SQLAlchemy dialects)
        supported_schemes = [
            "postgresql://",
            "postgres://",
            "postgresql+",  # PostgreSQL with dialects (e.g., postgresql+psycopg2://)
            "postgres+",  # PostgreSQL with dialects
            "mysql://",
            "mysql+",  # MySQL with dialects (e.g., mysql+pymysql://)
            "sqlite:///",
            "sqlite+",  # SQLite with dialects
            "mssql://",
            "mssql+",  # SQL Server with dialects (e.g., mssql+pyodbc://)
            "oracle://",
            "oracle+",  # Oracle with dialects
        ]

        # Check if URI starts with a supported scheme
        uri_lower = sql_uri.lower()
        if not any(uri_lower.startswith(scheme) for scheme in supported_schemes):
            return False

        # Basic URI structure validation
        if "://" not in sql_uri:
            return False

        # For non-sqlite databases, ensure there's a host part
        if not uri_lower.startswith("sqlite:"):
            parts = sql_uri.split("://", 1)
            if len(parts) != 2 or not parts[1]:
                return False

            # Check for basic host/database structure
            host_part = parts[1]

            # Handle different URI formats
            if "@" in host_part:
                # Format: user:pass@host:port/db or host/db?params
                auth_part, host_db_part = host_part.split("@", 1)
                if not host_db_part:  # auth_part can be empty for trusted connections
                    return False
            else:
                # Format: host:port/db or host/db?params (no auth)
                host_db_part = host_part

            # Allow URIs with query parameters (e.g., ?driver=...)
            if "?" in host_db_part:
                host_db_part = host_db_part.split("?")[0]

            # Must have at least a host or database part
            if not host_db_part or host_db_part == "/":
                return False

        return True

    def cleanup_connections(self):
        """Clean up all database connections (call on shutdown)."""
        for connector in self._business_connectors.values():
            with suppress(Exception):
                connector.close()
        self._business_connectors.clear()
