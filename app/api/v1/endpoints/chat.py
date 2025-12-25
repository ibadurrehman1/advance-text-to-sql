from fastapi import APIRouter

from app.controllers import ChatController
from app.schemas import BaseResponse
from app.services import ChatService


class ChatRouter:
    def __init__(self, chat_service: ChatService):
        self.controller = ChatController(chat_service)
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self) -> None:
        self.router.add_api_route(
            "",
            self.controller.chat_with_agent,
            methods=["POST"],
            response_model=BaseResponse,
        )
