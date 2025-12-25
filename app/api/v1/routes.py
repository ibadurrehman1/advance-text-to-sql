from fastapi import APIRouter

from app.api.v1.endpoints.chat import ChatRouter
from app.core.db import mongodb
from app.repositories.message_repository import MessageRepository
from app.services import AgentService, ChatService


def create_api_router() -> APIRouter:
    api_router = APIRouter()
    mongodb_client = mongodb.client

    message_repository = MessageRepository(mongodb_client)
    agent_service = AgentService()
    chat_service = ChatService(agent_service, message_repository)

    chat_router = ChatRouter(chat_service)
    api_router.include_router(chat_router.router, prefix="/chat", tags=["chat"])
    return api_router
