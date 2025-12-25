from http import HTTPStatus
from typing import Any, Dict

from fastapi import Depends, Query

from app.core.db import get_database
from app.core.security.dependencies import protected_auth
from app.repositories.business_repository import BusinessRepository
from app.schemas import BaseResponse
from app.schemas.business import BusinessCreateRequest, BusinessUpdateRequest
from app.services.business_service import BusinessService


class BusinessController:
    """Controller for business management endpoints."""

    def __init__(self):
        # Initialize dependencies
        db_client = get_database()
        business_repository = BusinessRepository(db_client)
        self.business_service = BusinessService(business_repository)

    async def create_business(
        self, request: BusinessCreateRequest, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Create a new business with SQL database connection."""
        try:
            user_id = user.get("id") or user.get("user_id")
            business = await self.business_service.create_business(request, created_by=user_id)

            return BaseResponse(
                message="Business created successfully",
                status_code=HTTPStatus.CREATED,
                data=business,
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to create business: {str(e)}",
                status_code=HTTPStatus.BAD_REQUEST,
                data=None,
            )

    async def get_business(
        self, business_id: str, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Get business by ID."""
        try:
            user_id = user.get("id") or user.get("user_id")
            # Check if user has access to this business
            has_access = await self.business_service.check_business_access(business_id, user_id)
            if not has_access:
                return BaseResponse(
                    message="Access denied: You don't have permission to access this business",
                    status_code=HTTPStatus.FORBIDDEN,
                    data=None,
                )

            business = await self.business_service.get_business(business_id)

            if not business:
                return BaseResponse(
                    message="Business not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="Business retrieved successfully", status_code=HTTPStatus.OK, data=business
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to get business: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def list_businesses(
        self,
        limit: int = Query(50, ge=1, le=100, description="Number of businesses to return"),
        offset: int = Query(0, ge=0, description="Number of businesses to skip"),
        user: Dict[str, Any] = Depends(protected_auth),
    ) -> BaseResponse:
        """List all businesses for the authenticated user."""
        try:
            user_id = user.get("id") or user.get("user_id")
            result = await self.business_service.list_businesses(
                user_id, limit=limit, offset=offset
            )

            return BaseResponse(
                message="Businesses retrieved successfully", status_code=HTTPStatus.OK, data=result
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to list businesses: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def update_business(
        self,
        business_id: str,
        request: BusinessUpdateRequest,
        user: Dict[str, Any] = Depends(protected_auth),
    ) -> BaseResponse:
        """Update business metadata."""
        try:
            user_id = user.get("id") or user.get("user_id")
            # Check if user has access to this business
            has_access = await self.business_service.check_business_access(business_id, user_id)
            if not has_access:
                return BaseResponse(
                    message="Access denied: You don't have permission to modify this business",
                    status_code=HTTPStatus.FORBIDDEN,
                    data=None,
                )

            business = await self.business_service.update_business(business_id, request)

            if not business:
                return BaseResponse(
                    message="Business not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="Business updated successfully", status_code=HTTPStatus.OK, data=business
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to update business: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def delete_business(
        self, business_id: str, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Delete a business."""
        try:
            user_id = user.get("id") or user.get("user_id")
            # Check if user has access to this business
            has_access = await self.business_service.check_business_access(business_id, user_id)
            if not has_access:
                return BaseResponse(
                    message="Access denied: You don't have permission to delete this business",
                    status_code=HTTPStatus.FORBIDDEN,
                    data=None,
                )

            deleted = await self.business_service.delete_business(business_id)

            if not deleted:
                return BaseResponse(
                    message="Business not found", status_code=HTTPStatus.NOT_FOUND, data=None
                )

            return BaseResponse(
                message="Business deleted successfully",
                status_code=HTTPStatus.OK,
                data={"business_id": business_id, "deleted": True},
            )
        except Exception as e:
            return BaseResponse(
                message=f"Failed to delete business: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                data=None,
            )

    async def test_business_connection(
        self, business_id: str, user: Dict[str, Any] = Depends(protected_auth)
    ) -> BaseResponse:
        """Test database connection for a business."""
        try:
            user_id = user.get("id") or user.get("user_id")
            # Check if user has access to this business
            has_access = await self.business_service.check_business_access(business_id, user_id)
            if not has_access:
                return BaseResponse(
                    message="Access denied: You don't have permission to test this business connection",
                    status_code=HTTPStatus.FORBIDDEN,
                    data=None,
                )

            result = await self.business_service.test_business_connection(business_id)

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
