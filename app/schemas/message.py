from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    thread_id: str
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageResponse(BaseModel):
    id_: str = Field(alias="id")
    thread_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
