from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BusinessCreateRequest(BaseModel):
    """Request schema for creating a new business."""

    name: str = Field(description="Business name", example="My E-commerce Store")
    description: str = Field(
        description="Business description",
        example="Online retail business specializing in electronics",
    )
    industry: str = Field(description="Business industry", example="E-commerce")
    sql_uri: str = Field(
        description="SQL database connection URI",
        example="postgresql://user:password@localhost:5432/ecommerce",
    )
    schema: Optional[str] = Field(
        default=None, description="Database schema name (optional)", example="public"
    )
    include_tables: Optional[str] = Field(
        default=None,
        description="Comma-separated list of tables to include (optional)",
        example="users,orders,products,customers",
    )
    exclude_tables: Optional[str] = Field(
        default=None,
        description="Comma-separated list of tables to exclude (optional)",
        example="migrations,logs,temp_tables",
    )
    primary_tables: Optional[str] = Field(
        default=None,
        description="Comma-separated list of primary business tables for context",
        example="orders,products,customers",
    )


class BusinessUpdateRequest(BaseModel):
    """Request schema for updating business metadata."""

    name: Optional[str] = Field(default=None, description="Business name")
    description: Optional[str] = Field(default=None, description="Business description")
    industry: Optional[str] = Field(default=None, description="Business industry")
    primary_tables: Optional[str] = Field(default=None, description="Primary business tables")


class BusinessResponse(BaseModel):
    """Response schema for business operations."""

    business_id: str = Field(description="Unique business identifier")
    name: str = Field(description="Business name")
    description: str = Field(description="Business description")
    industry: str = Field(description="Business industry")
    sql_uri: str = Field(description="Database connection URI (masked for security)")
    schema: Optional[str] = Field(description="Database schema")
    include_tables: Optional[str] = Field(description="Included tables")
    exclude_tables: Optional[str] = Field(description="Excluded tables")
    primary_tables: Optional[str] = Field(description="Primary business tables")
    tables_count: int = Field(description="Number of available tables")
    columns_count: int = Field(description="Number of available columns")
    created_by: str = Field(description="User ID who created the business")
    created_at: datetime = Field(description="Business creation timestamp")
    updated_at: datetime = Field(description="Business last update timestamp")
    status: str = Field(description="Business status (active, error, etc.)")


class BusinessListResponse(BaseModel):
    """Response schema for listing businesses."""

    businesses: list[BusinessResponse] = Field(description="List of businesses")
    total: int = Field(description="Total number of businesses")


class BusinessConnectionTest(BaseModel):
    """Response schema for testing business database connection."""

    business_id: str = Field(description="Business identifier")
    connection_status: str = Field(description="Connection status (success, error)")
    tables_found: int = Field(description="Number of tables found")
    columns_found: int = Field(description="Number of columns found")
    error_message: Optional[str] = Field(
        default=None, description="Error message if connection failed"
    )
    sample_tables: list[str] = Field(description="Sample table names (first 5)")


class BusinessContext(BaseModel):
    """Business context information for agent prompts."""

    business_name: str = Field(description="Business name")
    business_description: str = Field(description="Business description")
    business_industry: str = Field(description="Business industry")
    primary_tables: Optional[str] = Field(description="Primary business tables")
