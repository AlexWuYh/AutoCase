"""LLM configuration ORM model — mirrors config/llm.yaml fields."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="openai")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    api_key_env: Mapped[str | None] = mapped_column(String(128), nullable=True)
    allow_empty_key: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    api_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="chat_completions")
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="gpt-4o-mini")
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=2000)
    top_p: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    frequency_penalty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    presence_penalty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    debug_log: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
