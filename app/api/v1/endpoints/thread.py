from fastapi import APIRouter

from app.controllers.thread_controller import ThreadController


class ThreadRouter:
    """Router for thread management endpoints."""

    def __init__(self):
        self.controller = ThreadController()
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self) -> None:
        """Setup all thread-related routes."""

        # Create thread
        self.router.add_api_route(
            "",
            self.controller.create_thread,
            methods=["POST"],
            summary="Create Thread",
            description="Create a new thread with business database connection",
        )

        # List threads
        self.router.add_api_route(
            "",
            self.controller.list_threads,
            methods=["GET"],
            summary="List Threads",
            description="List all threads with pagination",
        )

        # Get thread by ID
        self.router.add_api_route(
            "/{thread_id}",
            self.controller.get_thread,
            methods=["GET"],
            summary="Get Thread",
            description="Get thread details by ID",
        )

        # Update thread
        self.router.add_api_route(
            "/{thread_id}",
            self.controller.update_thread,
            methods=["PUT"],
            summary="Update Thread",
            description="Update thread metadata (name, description)",
        )

        # Delete thread
        self.router.add_api_route(
            "/{thread_id}",
            self.controller.delete_thread,
            methods=["DELETE"],
            summary="Delete Thread",
            description="Delete a thread and its database connection",
        )

        # Test thread connection
        self.router.add_api_route(
            "/{thread_id}/test",
            self.controller.test_connection,
            methods=["POST"],
            summary="Test Connection",
            description="Test database connection for a thread",
        )
