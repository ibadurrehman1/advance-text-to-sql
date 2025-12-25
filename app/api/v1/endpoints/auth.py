from fastapi import APIRouter

from app.controllers.auth_controller import AuthController


class AuthRouter:
    """Router for authentication endpoints."""

    def __init__(self):
        self.controller = AuthController()
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self) -> None:
        """Setup all authentication-related routes."""

        # Login
        self.router.add_api_route(
            "/login",
            self.controller.login,
            methods=["POST"],
            summary="User Login",
            description="Authenticate user and return access token",
        )

        # Logout
        self.router.add_api_route(
            "/logout",
            self.controller.logout,
            methods=["POST"],
            summary="User Logout",
            description="Logout user and invalidate current token",
        )
