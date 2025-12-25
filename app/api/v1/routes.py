from fastapi import APIRouter

from app.api.v1.endpoints.auth import AuthRouter
from app.api.v1.endpoints.business import BusinessRouter
from app.api.v1.endpoints.chat import ChatRouter
from app.api.v1.endpoints.thread import ThreadRouter
from app.api.v1.endpoints.user import UserRouter
from app.core.db import mongodb
from app.repositories.message_repository import MessageRepository
from app.services import AgentService, ChatService


def create_api_router() -> APIRouter:
    api_router = APIRouter()
    mongodb_client = mongodb.client

    message_repository = MessageRepository(mongodb_client)
    agent_service = AgentService()
    chat_service = ChatService(agent_service, message_repository)

    # Chat endpoints
    chat_router = ChatRouter(chat_service)
    api_router.include_router(chat_router.router, prefix="/chat", tags=["chat"])

    # Thread endpoints
    thread_router = ThreadRouter()
    api_router.include_router(thread_router.router, prefix="/threads", tags=["threads"])

    # Business endpoints
    business_router = BusinessRouter()
    api_router.include_router(business_router.router, prefix="/businesses", tags=["businesses"])

    # User endpoints
    user_router = UserRouter()
    api_router.include_router(user_router.router, prefix="/users", tags=["users"])

    # Auth endpoints
    auth_router = AuthRouter()
    api_router.include_router(auth_router.router, prefix="/auth", tags=["authentication"])

    return api_router
