"""Generation job ORM model — tracks a batch test-case generation run."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    __table_args__ = (
        Index("ix_jobs_group_id", "group_id"),
        Index("ix_jobs_user_id", "user_id"),
        Index("ix_jobs_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("requirement_groups.id", ondelete="SET NULL"), nullable=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    llm_config_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("llm_configs.id", ondelete="SET NULL"), nullable=True
    )
    prompt_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("system_prompts.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending"
    )  # pending | running | success | failed | canceled
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    finished: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    group = relationship("RequirementGroup", lazy="joined")
    user = relationship("User", lazy="joined")
    llm_config = relationship("LLMConfig", lazy="joined")
    prompt = relationship("SystemPrompt", lazy="joined")
