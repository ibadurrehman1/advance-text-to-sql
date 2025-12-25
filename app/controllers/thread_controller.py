from http import HTTPStatus
from typing import Any, Dict

from fastapi import Depends, Query

from app.core.db import get_database
from app.core.security.dependencies import protected_auth
from app.repositories.business_repository import BusinessRepository
from app.repositories.thread_repository import ThreadRepository
from app.schemas import BaseResponse
from app.schemas.thread import ThreadCreateRequest, ThreadUpdateRequest
from app.services.business_service import BusinessService
from app.services.thread_service import ThreadService


class ThreadController:
    """Controller for thread management endpoints."""

    def __init__(self):
        # Initialize dependencies
        db_client = get_database()
        thread_repository = ThreadRepository(db_client)
        business_repository = BusinessRepository(db_client)
        business_service = BusinessService(business_repository)
        self.thread_service = ThreadService(thread_repository, business_service)

    async def create_thread(
        self, request: ThreadCreateRequest, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Create a new thread with business database connection."""
        try:
            user_id = user.get("id") or user.get("user_id")
            thread = await self.thread_service.create_thread(request, created_by=user_id)

            return BaseResponse(
                message="Thread created successfully", status_code=HTTPStatus.CREATED, data=thread
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to create thread: {str(e)}",
                status_code=HTTPStatus.BAD_REQUEST,
                data=None,
            )

    async def get_thread(
        self, thread_id: str, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Get thread by ID."""
        try:
            user_id = user.get("id") or user.get("user_id")
            # Check ownership first
            has_access = await self.thread_service.thread_repository.check_thread_ownership(
                thread_id, user_id
            )
            if not has_access:
                return BaseResponse(
                    message="Access denied: You don't have permission to access this thread",
                    status_code=HTTPStatus.FORBIDDEN,
                    data=None,
                )

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

    async def list_threads(
        self,
        limit: int = Query(50, ge=1, le=100, description="Number of threads to return"),
        offset: int = Query(0, ge=0, description="Number of threads to skip"),
        user: Dict[str, Any] = Depends(protected_auth),
    ) -> BaseResponse:
        """List all threads for the authenticated user with pagination."""
        try:
            user_id = user.get("id") or user.get("user_id")
            result = await self.thread_service.list_threads(user_id, limit=limit, offset=offset)

            return BaseResponse(
                message="Threads retrieved successfully", status_code=HTTPStatus.OK, data=result
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to list threads: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def update_thread(
        self,
        thread_id: str,
        request: ThreadUpdateRequest,
        user: Dict[str, Any] = Depends(protected_auth),
    ) -> BaseResponse:
        """Update thread metadata."""
        try:
            user_id = user.get("id") or user.get("user_id")
            # Check ownership first
            has_access = await self.thread_service.thread_repository.check_thread_ownership(
                thread_id, user_id
            )
            if not has_access:
                return BaseResponse(
                    message="Access denied: You don't have permission to modify this thread",
                    status_code=HTTPStatus.FORBIDDEN,
                    data=None,
                )

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

    async def delete_thread(
        self, thread_id: str, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Delete a thread."""
        try:
            user_id = user.get("id") or user.get("user_id")
            deleted = await self.thread_service.delete_thread(thread_id, user_id)

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

    async def test_thread_connection(
        self, thread_id: str, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Test database connection for a thread."""
        try:
            user_id = user.get("id") or user.get("user_id")
            result = await self.thread_service.test_thread_connection(thread_id, user_id)

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
