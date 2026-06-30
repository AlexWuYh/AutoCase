"""LLM config + prompt schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


# ─── LLM Config ─────────────────────────────────────────────────────────

class LLMConfigBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    provider: str = "openai"
    enabled: bool = True
    api_key_env: Optional[str] = None
    allow_empty_key: bool = False
    base_url: Optional[str] = None
    api_mode: str = "chat_completions"
    model: str = "gpt-4o-mini"
    temperature: float = Field(ge=0.0, le=2.0, default=0.2)
    max_tokens: int = Field(ge=1, le=16384, default=2000)
    top_p: float = Field(ge=0.0, le=1.0, default=1.0)
    frequency_penalty: float = Field(ge=-2.0, le=2.0, default=0.0)
    presence_penalty: float = Field(ge=-2.0, le=2.0, default=0.0)
    retry_count: int = Field(ge=0, le=10, default=2)
    debug_log: bool = False
    extra_body: Optional[Dict[str, Any]] = Field(
        default=None,
        description='透传给 API 的额外参数，如推理模型禁用思维链: {"chat_template_kwargs": {"enable_thinking": false}}',
    )
    is_default: bool = False


class LLMConfigCreate(LLMConfigBase):
    pass


class LLMConfigUpdate(BaseModel):
    """All fields optional for PATCH-style updates."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    provider: Optional[str] = None
    enabled: Optional[bool] = None
    api_key_env: Optional[str] = None
    allow_empty_key: Optional[bool] = None
    base_url: Optional[str] = None
    api_mode: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=16384)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0)
    retry_count: Optional[int] = Field(default=None, ge=0, le=10)
    debug_log: Optional[bool] = None
    extra_body: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None


class LLMConfigOut(LLMConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class LLMConfigTestPayload(BaseModel):
    """Payload for testing LLM connectivity."""
    message: str = Field(default="Hello, respond with OK.", max_length=200)


class LLMConfigTestResult(BaseModel):
    success: bool
    elapsed_ms: float
    message: str


# ─── System Prompt ──────────────────────────────────────────────────────

class SystemPromptBase(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    content: str = Field(default="", max_length=20000)
    description: Optional[str] = Field(default=None, max_length=512)
    is_default: bool = False


class SystemPromptCreate(SystemPromptBase):
    pass


class SystemPromptUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    content: Optional[str] = Field(default=None, max_length=20000)
    description: Optional[str] = Field(default=None, max_length=512)
    is_default: Optional[bool] = None


class SystemPromptOut(SystemPromptBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
