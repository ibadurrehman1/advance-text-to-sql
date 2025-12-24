from typing import Any, Dict

from fastapi import Cookie, Depends, Request, Response, Security
from fastapi.security import HTTPBearer

from app.core.db import mongodb
from app.core.exceptions import (
    AuthenticationException,
    NotFoundException,
    UnauthorizedException,
)
from app.core.security.security import verify_token
from app.repositories import ProfileRepository, UserRepository
from app.services import UserService

security = HTTPBearer()


async def get_user_service() -> UserService:
    user_repository = UserRepository(mongodb.client)
    profile_repository = ProfileRepository(mongodb.client)
    user_service = UserService(user_repository, profile_repository)
    return user_service


async def protected_auth(
    request: Request,
    user_service: UserService = Depends(get_user_service),
    authorization: HTTPBearer = Security(security),
) -> Dict[str, Any]:
    if not authorization:
        raise AuthenticationException()

    access_token = authorization.credentials

    access_token_payload = verify_token(access_token, "access")
    if access_token_payload is None:
        raise AuthenticationException(message="Invalid token payload")
    user = await user_service.get_user(user_id=access_token_payload["sub"])
    if user is None:
        raise NotFoundException(message="User not found")

    user_check = await user_service.get_by_token_creation_at(
        user_id=access_token_payload["sub"],
        token_creation_at=access_token_payload["iat"],
    )
    if not user_check:
        raise UnauthorizedException(
            message="Invalid token, please use the refresh token to refresh the access token"
        )

    request.state.user = user
    return user.model_dump()


async def refresh_auth(
    response: Response,
    user_service: UserService = Depends(get_user_service),
    refresh_token: str = Cookie(None),
) -> Dict[str, Any]:
    if not refresh_token:
        raise AuthenticationException(message="No refresh token in cookie")
    refresh_token_payload = verify_token(refresh_token, "refresh")
    if refresh_token_payload is None:
        response.delete_cookie("refresh_token")
        raise AuthenticationException(message="Invalid token payload")
    user = await user_service.get_user(user_id=refresh_token_payload["sub"])
    if user is None:
        response.delete_cookie("refresh_token")
        raise AuthenticationException(message="Invalid token")
    return refresh_token_payload
