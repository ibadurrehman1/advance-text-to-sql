from http import HTTPStatus

from app.schemas import BaseResponse
from app.schemas.thread import ThreadCreateRequest, ThreadUpdateRequest
from app.services.thread_service import ThreadService


class ThreadController:
    """Controller for thread management endpoints."""

    def __init__(self, thread_service: ThreadService):
        self.thread_service = thread_service

    async def create_thread(self, request: ThreadCreateRequest) -> BaseResponse:
        """Create a new thread with SQL database connection."""
        try:
            thread = await self.thread_service.create_thread(request)

            return BaseResponse(
                message="Thread created successfully", status_code=HTTPStatus.CREATED, data=thread
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to create thread: {str(e)}",
                status_code=HTTPStatus.BAD_REQUEST,
                data=None,
            )

    async def get_thread(self, thread_id: str) -> BaseResponse:
        """Get thread by ID."""
        try:
            thread = await self.thread_service.get_thread(thread_id)

            if not thread:
                return BaseResponse(
                    message="Thread not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="Thread retrieved successfully", status_code=HTTPStatus.OK, data=thread
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to get thread: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def list_threads(self, limit: int = 50, offset: int = 0) -> BaseResponse:
        """List all threads with pagination."""
        try:
            result = await self.thread_service.list_threads(limit=limit, offset=offset)

            return BaseResponse(
                message="Threads retrieved successfully", status_code=HTTPStatus.OK, data=result
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to list threads: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def update_thread(self, thread_id: str, request: ThreadUpdateRequest) -> BaseResponse:
        """Update thread metadata."""
        try:
            thread = await self.thread_service.update_thread(thread_id, request)

            if not thread:
                return BaseResponse(
                    message="Thread not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="Thread updated successfully", status_code=HTTPStatus.OK, data=thread
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to update thread: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def delete_thread(self, thread_id: str) -> BaseResponse:
        """Delete a thread."""
        try:
            deleted = await self.thread_service.delete_thread(thread_id)

            if not deleted:
                return BaseResponse(
                    message="Thread not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="Thread deleted successfully",
                status_code=HTTPStatus.OK,
                data={"thread_id": thread_id, "deleted": True},
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to delete thread: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def test_thread_connection(self, thread_id: str) -> BaseResponse:
        """Test database connection for a thread."""
        try:
            result = await self.thread_service.test_thread_connection(thread_id)

            status_code = (
                HTTPStatus.OK if result.connection_status == "success" else HTTPStatus.BAD_REQUEST
            )
            message = "Connection test completed"

            return BaseResponse(message=message, status_code=status_code, data=result)
        except Exception as e:
            return BaseResponse(
                message=f"Failed to test connection: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )
