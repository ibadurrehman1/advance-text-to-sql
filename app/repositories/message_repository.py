from typing import List

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)

from app.core.config import settings
from app.core.exceptions import DatabaseException
from app.schemas.message import MessageCreate, MessageResponse


class MessageRepository:
    def __init__(self, client: AsyncIOMotorClient):
        self.client: AsyncIOMotorClient = client
        self.database: AsyncIOMotorDatabase = client[settings.db.MONGODB_DB_NAME]
        self.collection: AsyncIOMotorCollection = self.database["messages"]

    async def add_message(self, message: MessageCreate) -> MessageResponse:
        try:
            message_dict = message.model_dump(exclude={"id"}, mode="json")
            result = await self.collection.insert_one(message_dict)

            # Fetch the inserted document to get the _id
            inserted_doc = await self.collection.find_one({"_id": result.inserted_id})
            if inserted_doc:
                inserted_doc["id"] = str(inserted_doc.pop("_id"))
                return MessageResponse(**inserted_doc)
            else:
                raise DatabaseException("Failed to retrieve inserted message")
        except Exception as e:
            raise DatabaseException(f"Failed to add message: {str(e)}")

    async def get_messages_by_thread(self, thread_id: str) -> List[MessageResponse]:
        try:
            cursor = self.collection.find({"thread_id": thread_id}).sort("created_at", 1)
            messages = []
            async for doc in cursor:
                doc["id"] = str(doc.pop("_id"))
                messages.append(MessageResponse(**doc))
            return messages
        except Exception as e:
            raise DatabaseException(f"Failed to get messages: {str(e)}")
