"""Generated test case ORM model."""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class GeneratedCase(Base):
    __tablename__ = "generated_cases"
    __table_args__ = (
        Index("ix_cases_job_id", "job_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False
    )
    case_id: Mapped[str] = mapped_column(String(32), nullable=False)
    module: Mapped[str] = mapped_column(String(256), nullable=False)
    case_type: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    name: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    priority: Mapped[str] = mapped_column(String(8), nullable=False, default="2")
    preconditions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    steps: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    expected: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    keywords: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    stage: Mapped[str] = mapped_column(String(64), nullable=False, default="功能测试阶段")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
