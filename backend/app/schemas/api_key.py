"""API Key schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class ApiKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None


class ApiKeyCreated(ApiKeyOut):
    """Returned only once at creation — includes the plaintext key."""

    key: str
