from pydantic import BaseModel, Field


class ExtractedQuery(BaseModel):
    off_topic: bool = Field(
        ...,
        description="True if the user messages are greetings or unrelated to SQL/data queries, otherwise False.",
    )
    off_topic_reply: str = Field(
        ...,
        description="If off_topic is True, provide a polite reply (e.g., greeting reply or note that this bot is focused on SQL/data queries). Empty string if off_topic is False.",
    )
    extracted_query: str = Field(
        ...,
        description="The extracted query from the user's messages in its original form, possibly reflecting or building upon previous human messages. Empty string if off_topic is True.",
    )
