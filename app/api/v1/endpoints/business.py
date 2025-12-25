from fastapi import APIRouter

from app.controllers.business_controller import BusinessController


class BusinessRouter:
    """Router for business management endpoints."""

    def __init__(self):
        self.controller = BusinessController()
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self) -> None:
        """Setup all business-related routes."""

        # Create business
        self.router.add_api_route(
            "",
            self.controller.create_business,
            methods=["POST"],
            summary="Create Business",
            description="Create a new business with SQL database connection",
        )

        # List businesses
        self.router.add_api_route(
            "",
            self.controller.list_businesses,
            methods=["GET"],
            summary="List Businesses",
            description="List all businesses for the authenticated user",
        )

        # Get business by ID
        self.router.add_api_route(
            "/{business_id}",
            self.controller.get_business,
            methods=["GET"],
            summary="Get Business",
            description="Get business details by ID",
        )

        # Update business
        self.router.add_api_route(
            "/{business_id}",
            self.controller.update_business,
            methods=["PUT"],
            summary="Update Business",
            description="Update business metadata (name, description, industry, primary_tables)",
        )

        # Delete business
        self.router.add_api_route(
            "/{business_id}",
            self.controller.delete_business,
            methods=["DELETE"],
            summary="Delete Business",
            description="Delete a business and its database connection",
        )

        # Test business connection
        self.router.add_api_route(
            "/{business_id}/test",
            self.controller.test_connection,
            methods=["POST"],
            summary="Test Connection",
            description="Test database connection for a business",
        )
