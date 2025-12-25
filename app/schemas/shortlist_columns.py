from typing import List

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    """Schema for a single column reference."""

    table: str = Field(description="Table name")
    column: str = Field(description="Column name")

    class Config:
        json_schema_extra = {"example": {"table": "users", "column": "user_id"}}


class ShortlistColumnsResponse(BaseModel):
    """Response schema for shortlisted columns."""

    columns: List[ColumnInfo] = Field(description="List of columns that are relevant to the query")

    class Config:
        json_schema_extra = {
            "example": {
                "columns": [
                    {"table": "users", "column": "user_id"},
                    {"table": "users", "column": "name"},
                    {"table": "orders", "column": "order_id"},
                ]
            }
        }
