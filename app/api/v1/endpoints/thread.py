from fastapi import APIRouter, Query

from app.controllers.thread_controller import ThreadController
from app.core.db import get_database
from app.repositories.thread_repository import ThreadRepository
from app.schemas import BaseResponse
from app.schemas.thread import ThreadUpdateRequest
from app.services.thread_service import ThreadService


class ThreadRouter:
    """Router for thread management endpoints."""

    def __init__(self):
        # Initialize dependencies
        db_client = get_database()
        thread_repository = ThreadRepository(db_client)
        thread_service = ThreadService(thread_repository)
        self.controller = ThreadController(thread_service)

        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self) -> None:
        """Setup all thread-related routes."""

        # Create thread
        self.router.add_api_route(
            "",
            self.controller.create_thread,
            methods=["POST"],
            response_model=BaseResponse,
            summary="Create Thread",
            description="Create a new thread with SQL database connection",
        )

        # List threads
        self.router.add_api_route(
            "",
            self.list_threads,
            methods=["GET"],
            response_model=BaseResponse,
            summary="List Threads",
            description="List all threads with pagination",
        )

        # Get thread by ID
        self.router.add_api_route(
            "/{thread_id}",
            self.get_thread,
            methods=["GET"],
            response_model=BaseResponse,
            summary="Get Thread",
            description="Get thread details by ID",
        )

        # Update thread
        self.router.add_api_route(
            "/{thread_id}",
            self.update_thread,
            methods=["PUT"],
            response_model=BaseResponse,
            summary="Update Thread",
            description="Update thread metadata (name, description)",
        )

        # Delete thread
        self.router.add_api_route(
            "/{thread_id}",
            self.delete_thread,
            methods=["DELETE"],
            response_model=BaseResponse,
            summary="Delete Thread",
            description="Delete a thread and its database connection",
        )

        # Test thread connection
        self.router.add_api_route(
            "/{thread_id}/test",
            self.test_connection,
            methods=["POST"],
            response_model=BaseResponse,
            summary="Test Connection",
            description="Test database connection for a thread",
        )

    async def list_threads(
        self,
        limit: int = Query(50, ge=1, le=100, description="Number of threads to return"),
        offset: int = Query(0, ge=0, description="Number of threads to skip"),
    ) -> BaseResponse:
        """List threads with pagination."""
        return await self.controller.list_threads(limit=limit, offset=offset)

    async def get_thread(self, thread_id: str) -> BaseResponse:
        """Get thread by ID."""
        return await self.controller.get_thread(thread_id)

    async def update_thread(self, thread_id: str, request: ThreadUpdateRequest) -> BaseResponse:
        """Update thread metadata."""
        return await self.controller.update_thread(thread_id, request)

    async def delete_thread(self, thread_id: str) -> BaseResponse:
        """Delete thread."""
        return await self.controller.delete_thread(thread_id)

    async def test_connection(self, thread_id: str) -> BaseResponse:
        """Test thread database connection."""
        return await self.controller.test_thread_connection(thread_id)
