from typing import List

from pydantic import BaseModel, Field


class ShortlistTablesResponse(BaseModel):
    """Response schema for shortlisted tables."""

    tables: List[str] = Field(description="List of table names that are relevant to the query")

    class Config:
        json_schema_extra = {"example": {"tables": ["users", "orders", "products"]}}
