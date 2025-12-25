from fastapi import APIRouter

from app.controllers.user_controller import UserController


class UserRouter:
    """Router for user management endpoints."""

    def __init__(self):
        self.controller = UserController()
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self) -> None:
        """Setup all user-related routes."""

        # Create user (public endpoint for registration)
        self.router.add_api_route(
            "/register",
            self.controller.create_user,
            methods=["POST"],
            summary="Register User",
            description="Create a new user account",
        )

        # Get current user (authenticated)
        self.router.add_api_route(
            "/me",
            self.controller.get_current_user,
            methods=["GET"],
            summary="Get Current User",
            description="Get current authenticated user's information",
        )

        # Update current user (authenticated)
        self.router.add_api_route(
            "/me",
            self.controller.update_current_user,
            methods=["PUT"],
            summary="Update Current User",
            description="Update current authenticated user's information",
        )

        # Delete current user (authenticated)
        self.router.add_api_route(
            "/me",
            self.controller.delete_current_user,
            methods=["DELETE"],
            summary="Delete Current User",
            description="Delete current authenticated user's account",
        )

        # Get user by ID (authenticated, self-only)
        self.router.add_api_route(
            "/{user_id}",
            self.controller.get_user,
            methods=["GET"],
            summary="Get User",
            description="Get user by ID (users can only access their own data)",
        )

        # Update user by ID (authenticated, self-only)
        self.router.add_api_route(
            "/{user_id}",
            self.controller.update_user,
            methods=["PUT"],
            summary="Update User",
            description="Update user by ID (users can only update their own data)",
        )

        # Delete user by ID (authenticated, self-only)
        self.router.add_api_route(
            "/{user_id}",
            self.controller.delete_user,
            methods=["DELETE"],
            summary="Delete User",
            description="Delete user by ID (users can only delete their own account)",
        )
