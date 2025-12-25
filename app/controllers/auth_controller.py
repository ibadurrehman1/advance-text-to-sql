from datetime import datetime
from http import HTTPStatus
from typing import Any, Dict

from fastapi import Depends

from app.core.db import get_database
from app.core.security.dependencies import protected_auth
from app.core.security.security import create_access_token
from app.repositories.profile_repository import ProfileRepository
from app.repositories.user_repository import UserRepository
from app.schemas import BaseResponse
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.user_service import UserService

# Constants
TOKEN_TYPE = "bearer"  # nosec B105 - This is a standard OAuth2 token type, not a password


class AuthController:
    """Controller for authentication endpoints."""

    def __init__(self):
        # Initialize dependencies
        db_client = get_database()
        user_repository = UserRepository(db_client)
        profile_repository = ProfileRepository(db_client)
        self.user_service = UserService(user_repository, profile_repository)

    async def login(self, request: LoginRequest) -> BaseResponse:
        """Authenticate user and return access token."""
        try:
            # Authenticate user
            user_data = await self.user_service.authenticate_user(request.email, request.password)

            if not user_data:
                return BaseResponse(
                    message="Invalid email or password",
                    status_code=HTTPStatus.UNAUTHORIZED,
                    data=None,
                )

            # Create access token first to get the actual timestamp used
            token_data = {
                "sub": user_data["id"],
                "email": user_data["email"],
                "user_id": user_data["id"],
                "id": user_data["id"],
            }

            # create_access_token returns (token, timestamp)
            access_token, token_creation_at = create_access_token(data=token_data)

            # Update token creation timestamp with the actual timestamp used in JWT
            await self.user_service.update_token_creation_at(user_data["id"], token_creation_at)

            # Prepare user data for response (exclude sensitive info)
            user_response = {
                "id": user_data["id"],
                "email": user_data["email"],
                "full_name": user_data["full_name"],
                "is_active": user_data["is_active"],
                "created_at": user_data["created_at"],
                "updated_at": user_data["updated_at"],
            }

            login_response = LoginResponse(
                access_token=access_token, token_type=TOKEN_TYPE, user=user_response
            )

            return BaseResponse(
                message="Login successful", status_code=HTTPStatus.OK, data=login_response
            )

        except Exception as e:
            return BaseResponse(
                message=f"Login failed: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def logout(self, user: Dict[str, Any] = Depends(protected_auth)) -> BaseResponse:
        """Logout user by invalidating token creation timestamp."""
        try:
            user_id = user.get("id") or user.get("user_id")
            # Update token creation timestamp to invalidate current tokens
            await self.user_service.update_token_creation_at(user_id, datetime.utcnow())

            return BaseResponse(
                message="Logout successful", status_code=HTTPStatus.OK, data={"logged_out": True}
            )

        except Exception as e:
            return BaseResponse(
                message=f"Logout failed: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )
