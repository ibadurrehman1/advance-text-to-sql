import uuid
from typing import Dict

from app.repositories.message_repository import MessageRepository
from app.schemas import ChatRequest, MessageCreate
from app.services import AgentService


class ChatService:
    def __init__(self, agent_service: AgentService, message_repository: MessageRepository):
        self.agent_service = agent_service
        self.message_repository = message_repository

    async def chat_with_agent(self, request: ChatRequest) -> Dict:
        # Generate or use provided thread_id
        thread_id = request.thread_id or str(uuid.uuid4())

        # Save user message
        user_message = MessageCreate(
            thread_id=thread_id,
            role="user",
            content=request.message,
        )
        await self.message_repository.add_message(user_message)

        # Retrieve all messages for the thread
        messages = await self.message_repository.get_messages_by_thread(thread_id)

        # Convert messages to the format expected by agent_service
        messages_list = []
        for message in messages:
            messages_list.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        # Get AI response from agent service
        ai_response = await self.agent_service.chat_with_agent(messages_list)

        # Save AI message
        ai_message = MessageCreate(
            thread_id=thread_id,
            role="assistant",
            content=ai_response["messages"][-1].content,
        )
        await self.message_repository.add_message(ai_message)

        return {
            "response": ai_response,
            "thread_id": thread_id,
        }
