import uuid
from contextlib import suppress
from typing import Any, Dict, List, Optional

from app.core.exceptions import DatabaseException
from app.repositories.thread_repository import ThreadRepository
from app.schemas.thread import (
    ThreadConnectionTest,
    ThreadCreateRequest,
    ThreadListResponse,
    ThreadResponse,
    ThreadUpdateRequest,
)
from app.utilities.database_connector import DatabaseConnector


class ThreadService:
    """Service for managing threads with SQL database connections."""

    def __init__(self, thread_repository: ThreadRepository):
        self.thread_repository = thread_repository
        self._thread_connectors: Dict[str, DatabaseConnector] = {}

    async def create_thread(self, request: ThreadCreateRequest) -> ThreadResponse:
        """
        Create a new thread with SQL database connection.

        Args:
            request: Thread creation request with SQL URI and configuration

        Returns:
            ThreadResponse with thread details

        Raises:
            DatabaseException: If database connection fails or thread creation fails
        """
        thread_id = str(uuid.uuid4())

        try:
            # Test the database connection first
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

            # Store the connector for this thread
            self._thread_connectors[thread_id] = connector

            # Create thread in database
            thread = await self.thread_repository.create_thread(
                thread_id=thread_id,
                request=request,
                tables_count=tables_count,
                columns_count=columns_count,
                status="active",
            )

            return thread

        except Exception as e:
            # Clean up connector if it was created
            if thread_id in self._thread_connectors:
                self._thread_connectors[thread_id].close()
                del self._thread_connectors[thread_id]

            # Update thread status to error if it was created
            with suppress(Exception):
                await self.thread_repository.update_thread_status(thread_id, "error")

            raise DatabaseException(f"Failed to create thread: {str(e)}")

    async def get_thread(self, thread_id: str) -> Optional[ThreadResponse]:
        """Get thread by ID."""
        return await self.thread_repository.get_thread_by_id(thread_id)

    async def list_threads(self, limit: int = 50, offset: int = 0) -> ThreadListResponse:
        """List all threads with pagination."""
        threads = await self.thread_repository.list_threads(limit=limit, offset=offset)
        total = await self.thread_repository.count_threads()

        return ThreadListResponse(threads=threads, total=total)

    async def update_thread(
        self, thread_id: str, request: ThreadUpdateRequest
    ) -> Optional[ThreadResponse]:
        """Update thread metadata."""
        return await self.thread_repository.update_thread(thread_id, request)

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread and clean up its database connection."""
        # Close database connection if exists
        if thread_id in self._thread_connectors:
            self._thread_connectors[thread_id].close()
            del self._thread_connectors[thread_id]

        # Delete from database
        return await self.thread_repository.delete_thread(thread_id)

    async def test_thread_connection(self, thread_id: str) -> ThreadConnectionTest:
        """Test the database connection for a thread."""
        try:
            # Get thread info
            thread = await self.get_thread(thread_id)
            if not thread:
                return ThreadConnectionTest(
                    thread_id=thread_id,
                    connection_status="error",
                    tables_found=0,
                    columns_found=0,
                    error_message="Thread not found",
                    sample_tables=[],
                )

            # Get database connector
            connector = await self.get_thread_connector(thread_id)
            if not connector:
                return ThreadConnectionTest(
                    thread_id=thread_id,
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

            return ThreadConnectionTest(
                thread_id=thread_id,
                connection_status="success",
                tables_found=len(tables),
                columns_found=columns_count,
                sample_tables=tables[:5],  # First 5 tables
            )

        except Exception as e:
            return ThreadConnectionTest(
                thread_id=thread_id,
                connection_status="error",
                tables_found=0,
                columns_found=0,
                error_message=str(e),
                sample_tables=[],
            )

    async def get_thread_connector(self, thread_id: str) -> Optional[DatabaseConnector]:
        """
        Get database connector for a thread.
        Creates a new connector if one doesn't exist.
        """
        # Return existing connector if available
        if thread_id in self._thread_connectors:
            return self._thread_connectors[thread_id]

        # Get thread configuration from database
        thread_config = await self.thread_repository.get_thread_sql_uri(thread_id)
        if not thread_config:
            return None

        try:
            # Create new connector
            connector = DatabaseConnector(thread_config["sql_uri"])

            # Store for future use
            self._thread_connectors[thread_id] = connector

            return connector

        except Exception as e:
            # Update thread status to error
            await self.thread_repository.update_thread_status(thread_id, "error")
            raise DatabaseException(f"Failed to create database connector: {str(e)}")

    async def get_thread_tables(self, thread_id: str) -> List[str]:
        """Get all tables for a thread."""
        connector = await self.get_thread_connector(thread_id)
        if not connector:
            raise DatabaseException("Thread connector not available")

        # Get thread configuration for filters
        thread_config = await self.thread_repository.get_thread_sql_uri(thread_id)
        if not thread_config:
            raise DatabaseException("Thread configuration not found")

        include_tables = self._parse_table_list(thread_config.get("include_tables"))
        exclude_tables = self._parse_table_list(thread_config.get("exclude_tables"))

        return connector.get_all_tables(
            include_tables=include_tables,
            exclude_tables=exclude_tables,
            schema=thread_config.get("schema"),
        )

    async def get_thread_columns(
        self, thread_id: str, include_tables: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get columns for a thread, optionally filtered by specific tables."""
        connector = await self.get_thread_connector(thread_id)
        if not connector:
            raise DatabaseException("Thread connector not available")

        # Get thread configuration for filters
        thread_config = await self.thread_repository.get_thread_sql_uri(thread_id)
        if not thread_config:
            raise DatabaseException("Thread configuration not found")

        # Use provided tables or fall back to thread configuration
        if include_tables:
            filter_include_tables = include_tables
            filter_exclude_tables = None
        else:
            filter_include_tables = self._parse_table_list(thread_config.get("include_tables"))
            filter_exclude_tables = self._parse_table_list(thread_config.get("exclude_tables"))

        return connector.get_all_columns(
            include_tables=filter_include_tables,
            exclude_tables=filter_exclude_tables,
            schema=thread_config.get("schema"),
        )

    def _parse_table_list(self, table_string: Optional[str]) -> Optional[List[str]]:
        """Parse comma-separated table string into list."""
        if not table_string:
            return None
        return [table.strip() for table in table_string.split(",") if table.strip()]

    def cleanup_connections(self):
        """Clean up all database connections (call on shutdown)."""
        for connector in self._thread_connectors.values():
            with suppress(Exception):
                connector.close()
        self._thread_connectors.clear()
