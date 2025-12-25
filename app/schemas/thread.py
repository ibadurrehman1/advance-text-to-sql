from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ThreadCreateRequest(BaseModel):
    """Request schema for creating a new thread with business database connection."""

    business_id: str = Field(
        description="Business ID to connect to", example="550e8400-e29b-41d4-a716-446655440000"
    )
    name: Optional[str] = Field(
        default=None, description="Optional name for the thread", example="Sales Analysis Thread"
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional description for the thread",
        example="Thread for analyzing sales data and customer information",
    )


class ThreadResponse(BaseModel):
    """Response schema for thread operations."""

    thread_id: str = Field(description="Unique thread identifier")
    name: Optional[str] = Field(description="Thread name")
    description: Optional[str] = Field(description="Thread description")
    business_id: str = Field(description="Business ID this thread is connected to")
    business_name: str = Field(description="Business name for reference")
    tables_count: int = Field(description="Number of available tables")
    columns_count: int = Field(description="Number of available columns")
    created_by: str = Field(description="User ID who created the thread")
    created_at: datetime = Field(description="Thread creation timestamp")
    updated_at: datetime = Field(description="Thread last update timestamp")
    status: str = Field(description="Thread status (active, error, etc.)")


class ThreadListResponse(BaseModel):
    """Response schema for listing threads."""

    threads: list[ThreadResponse] = Field(description="List of threads")
    total: int = Field(description="Total number of threads")


class ThreadUpdateRequest(BaseModel):
    """Request schema for updating thread metadata."""

    name: Optional[str] = Field(default=None, description="Thread name")
    description: Optional[str] = Field(default=None, description="Thread description")


class ThreadConnectionTest(BaseModel):
    """Response schema for testing thread database connection."""

    thread_id: str = Field(description="Thread identifier")
    connection_status: str = Field(description="Connection status (success, error)")
    tables_found: int = Field(description="Number of tables found")
    columns_found: int = Field(description="Number of columns found")
    error_message: Optional[str] = Field(
        default=None, description="Error message if connection failed"
    )
    sample_tables: list[str] = Field(description="Sample table names (first 5)")
