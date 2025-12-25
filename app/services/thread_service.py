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
from app.services.business_service import BusinessService


class ThreadService:
    """Service for managing threads with business database connections."""

    def __init__(self, thread_repository: ThreadRepository, business_service: BusinessService):
        self.thread_repository = thread_repository
        self.business_service = business_service

    async def create_thread(self, request: ThreadCreateRequest, created_by: str) -> ThreadResponse:
        """
        Create a new thread with business database connection.

        Args:
            request: Thread creation request with business ID
            created_by: User ID who is creating the thread

        Returns:
            ThreadResponse with thread details

        Raises:
            DatabaseException: If business not found or thread creation fails
        """
        thread_id = str(uuid.uuid4())

        try:
            # Check if business exists and user has access
            has_access = await self.business_service.check_business_access(
                request.business_id, created_by
            )
            if not has_access:
                raise DatabaseException(
                    "Access denied: You don't have permission to use this business"
                )

            # Get business info
            business = await self.business_service.get_business(request.business_id)
            if not business:
                raise DatabaseException("Business not found")

            # Get table and column counts from business
            tables_count = business.tables_count
            columns_count = business.columns_count

            # Create thread in database
            thread = await self.thread_repository.create_thread(
                thread_id=thread_id,
                request=request,
                created_by=created_by,
                business_name=business.name,
                tables_count=tables_count,
                columns_count=columns_count,
                status="active",
            )

            return thread

        except Exception as e:
            # Update thread status to error if it was created
            with suppress(Exception):
                await self.thread_repository.update_thread_status(thread_id, "error")

            raise DatabaseException(f"Failed to create thread: {str(e)}")

    async def get_thread(self, thread_id: str) -> Optional[ThreadResponse]:
        """Get thread by ID."""
        return await self.thread_repository.get_thread_by_id(thread_id)

    async def list_threads(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> ThreadListResponse:
        """List all threads for a user with pagination."""
        threads = await self.thread_repository.list_threads_by_user(
            user_id, limit=limit, offset=offset
        )
        total = await self.thread_repository.count_threads_by_user(user_id)

        return ThreadListResponse(threads=threads, total=total)

    async def update_thread(
        self, thread_id: str, request: ThreadUpdateRequest
    ) -> Optional[ThreadResponse]:
        """Update thread metadata."""
        return await self.thread_repository.update_thread(thread_id, request)

    async def delete_thread(self, thread_id: str, user_id: str) -> bool:
        """Delete a thread (with ownership check)."""
        # Check ownership
        has_access = await self.thread_repository.check_thread_ownership(thread_id, user_id)
        if not has_access:
            raise DatabaseException(
                "Access denied: You don't have permission to delete this thread"
            )

        # Delete from database
        return await self.thread_repository.delete_thread(thread_id)

    async def test_thread_connection(self, thread_id: str, user_id: str) -> ThreadConnectionTest:
        """Test the database connection for a thread."""
        try:
            # Check ownership
            has_access = await self.thread_repository.check_thread_ownership(thread_id, user_id)
            if not has_access:
                return ThreadConnectionTest(
                    thread_id=thread_id,
                    connection_status="error",
                    tables_found=0,
                    columns_found=0,
                    error_message="Access denied: You don't have permission to test this thread",
                    sample_tables=[],
                )

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

            # Test business connection
            business_test = await self.business_service.test_business_connection(thread.business_id)

            return ThreadConnectionTest(
                thread_id=thread_id,
                connection_status=business_test.connection_status,
                tables_found=business_test.tables_found,
                columns_found=business_test.columns_found,
                error_message=business_test.error_message,
                sample_tables=business_test.sample_tables,
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

    async def get_thread_tables(self, thread_id: str) -> List[str]:
        """Get all tables for a thread."""
        # Get business ID from thread
        business_id = await self.thread_repository.get_thread_business_id(thread_id)
        if not business_id:
            raise DatabaseException("Thread business ID not found")

        # Get tables from business service
        return await self.business_service.get_business_tables(business_id)

    async def get_thread_columns(
        self, thread_id: str, include_tables: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get columns for a thread, optionally filtered by specific tables."""
        # Get business ID from thread
        business_id = await self.thread_repository.get_thread_business_id(thread_id)
        if not business_id:
            raise DatabaseException("Thread business ID not found")

        # Get columns from business service
        return await self.business_service.get_business_columns(business_id, include_tables)
