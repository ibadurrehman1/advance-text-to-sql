from http import HTTPStatus

from app.schemas import BaseResponse, ChatRequest
from app.services import ChatService


class ChatController:
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    async def chat_with_agent(self, request: ChatRequest) -> BaseResponse:
        result = await self.chat_service.chat_with_agent(request)

        return BaseResponse(
            message="Chat with agent successfully",
            status_code=HTTPStatus.OK,
            data=result,
        )
