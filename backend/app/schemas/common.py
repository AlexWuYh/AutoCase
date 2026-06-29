"""Common Pydantic schemas shared across endpoints."""
from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=200)


class Message(BaseModel):
    """Generic message response."""

    message: str


class ErrorDetail(BaseModel):
    """Standard error payload."""

    detail: str
    code: str | None = None
