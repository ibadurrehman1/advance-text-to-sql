from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ThreadCreateRequest(BaseModel):
    """Request schema for creating a new thread with SQL database connection."""

    sql_uri: str = Field(
        description="SQL database connection URI",
        example="postgresql://user:password@localhost:5432/dbname",
    )
    schema: Optional[str] = Field(
        default=None, description="Database schema name (optional)", example="public"
    )
    include_tables: Optional[str] = Field(
        default=None,
        description="Comma-separated list of tables to include (optional)",
        example="users,orders,products",
    )
    exclude_tables: Optional[str] = Field(
        default=None,
        description="Comma-separated list of tables to exclude (optional)",
        example="migrations,logs",
    )
    name: Optional[str] = Field(
        default=None, description="Optional name for the thread", example="Sales Database Analysis"
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
    sql_uri: str = Field(description="Database connection URI (masked for security)")
    schema: Optional[str] = Field(description="Database schema")
    include_tables: Optional[str] = Field(description="Included tables")
    exclude_tables: Optional[str] = Field(description="Excluded tables")
    tables_count: int = Field(description="Number of available tables")
    columns_count: int = Field(description="Number of available columns")
    created_at: datetime = Field(description="Thread creation timestamp")
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
