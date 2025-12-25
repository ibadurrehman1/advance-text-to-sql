from http import HTTPStatus
from typing import Any, Dict

from fastapi import Depends

from app.core.db import get_database
from app.core.security.dependencies import protected_auth
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas import BaseResponse
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


class UserController:
    """Controller for user management endpoints."""

    def __init__(self):
        # Initialize dependencies
        db_client = get_database()
        user_repository = UserRepository(db_client)
        profile_repository = ProfileRepository(db_client)
        self.user_service = UserService(user_repository, profile_repository)

    async def create_user(self, request: UserCreate) -> BaseResponse:
        """Create a new user account."""
        try:
            user = await self.user_service.create_user(request)

            return BaseResponse(
                message="User created successfully", status_code=HTTPStatus.CREATED, data=user
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to create user: {str(e)}",
                status_code=HTTPStatus.BAD_REQUEST,
                data=None,
            )

    async def get_user(
        self, user_id: str, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Get user by ID (users can only access their own data)."""
        try:
            requesting_user_id = user.get("id") or user.get("user_id")
            # Users can only access their own data
            if user_id != requesting_user_id:
                return BaseResponse(
                    message="Access denied: You can only access your own user data",
                    status_code=HTTPStatus.FORBIDDEN,
                    data=None,
                )

            user = await self.user_service.get_user(user_id)

            if not user:
                return BaseResponse(
                    message="User not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="User retrieved successfully", status_code=HTTPStatus.OK, data=user
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to get user: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def get_current_user(
        self, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Get current authenticated user's data."""
        try:
            user_id = user.get("id") or user.get("user_id")
            user_data = await self.user_service.get_user(user_id)

            if not user_data:
                return BaseResponse(
                    message="User not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="Current user retrieved successfully",
                status_code=HTTPStatus.OK,
                data=user_data,
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to get current user: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def update_current_user(
        self, request: UserUpdate, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Update current authenticated user's information."""
        try:
            user_id = user.get("id") or user.get("user_id")
            updated_user = await self.user_service.update_user(user_id, request)

            return BaseResponse(
                message="User updated successfully", status_code=HTTPStatus.OK, data=updated_user
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to update current user: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def delete_current_user(
        self, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Delete current authenticated user's account."""
        try:
            user_id = user.get("id") or user.get("user_id")
            deleted = await self.user_service.delete_user(user_id)

            if not deleted:
                return BaseResponse(
                    message="User not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="User account deleted successfully", status_code=HTTPStatus.OK, data=None
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to delete current user: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def update_user(
        self, user_id: str, request: UserUpdate, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Update user information (users can only update their own data)."""
        try:
            requesting_user_id = user.get("id") or user.get("user_id")
            # Users can only update their own data
            if user_id != requesting_user_id:
                return BaseResponse(
                    message="Access denied: You can only update your own user data",
                    status_code=HTTPStatus.FORBIDDEN,
                    data=None,
                )

            user = await self.user_service.update_user(user_id, request)

            if not user:
                return BaseResponse(
                    message="User not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="User updated successfully", status_code=HTTPStatus.OK, data=user
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to update user: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def delete_user(
        self, user_id: str, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Delete user account (users can only delete their own account)."""
        try:
            requesting_user_id = user.get("id") or user.get("user_id")
            # Users can only delete their own account
            if user_id != requesting_user_id:
                return BaseResponse(
                    message="Access denied: You can only delete your own account",
                    status_code=HTTPStatus.FORBIDDEN,
                    data=None,
                )

            deleted = await self.user_service.delete_user(user_id)

            if not deleted:
                return BaseResponse(
                    message="User not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="User deleted successfully",
                status_code=HTTPStatus.OK,
                data={"user_id": user_id, "deleted": True},
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to delete user: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )
