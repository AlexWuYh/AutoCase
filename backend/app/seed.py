"""First-run seeding: initial admin, LLM config, system prompt."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models.llm_config import LLMConfig
from .models.prompt import SystemPrompt
from .models.user import User, UserRole
from .security import hash_password

logger = logging.getLogger("autocase.seed")

settings = get_settings()


def seed_initial_admin(db: Session) -> Optional[User]:
    existing = db.execute(select(User).limit(1)).scalar_one_or_none()
    if existing is not None:
        logger.debug("Users already exist, skipping initial admin seed")
        return None

    admin = User(
        username=settings.initial_admin_username,
        email=settings.initial_admin_email,
        password_hash=hash_password(settings.initial_admin_password),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    logger.warning(
        "Initial admin user '%s' created.", admin.username,
    )
    return admin


def seed_default_llm_config(db: Session) -> Optional[LLMConfig]:
    from yaml import safe_load
    cfg_path = Path("config/llm.yaml")
    if not cfg_path.exists():
        return None

    existing = db.execute(select(LLMConfig).limit(1)).scalar_one_or_none()
    if existing is not None:
        return None

    try:
        raw = safe_load(cfg_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None

    cfg = LLMConfig(
        name="默认配置 (from config/llm.yaml)",
        is_default=True,
        provider=raw.get("provider", "openai"),
        enabled=bool(raw.get("enabled", True)),
        api_key_env=raw.get("api_key_env") or None,
        allow_empty_key=bool(raw.get("allow_empty_key", False)),
        base_url=raw.get("base_url") or None,
        api_mode=raw.get("api_mode", "chat_completions"),
        model=raw.get("model", "gpt-4o-mini"),
        temperature=float(raw.get("temperature", 0.2)),
        max_tokens=int(raw.get("max_tokens", 2000)),
        top_p=float(raw.get("top_p", 1.0)),
        frequency_penalty=float(raw.get("frequency_penalty", 0.0)),
        presence_penalty=float(raw.get("presence_penalty", 0.0)),
        retry_count=int(raw.get("retry_count", 2)),
        debug_log=bool(raw.get("debug_log", False)),
    )
    db.add(cfg)
    db.commit()
    logger.info("Seeded default LLM config from config/llm.yaml")
    return cfg


def seed_default_prompt(db: Session) -> Optional[SystemPrompt]:
    prompt_path = Path("config/system_prompt.txt")
    if not prompt_path.exists():
        return None

    existing = db.execute(select(SystemPrompt).limit(1)).scalar_one_or_none()
    if existing is not None:
        return None

    content = prompt_path.read_text(encoding="utf-8")
    if not content.strip():
        return None

    p = SystemPrompt(
        name="默认 Prompt (from config/system_prompt.txt)",
        content=content,
        description="AutoCase 测试用例生成器默认提示词，来源: config/system_prompt.txt",
        is_default=True,
    )
    db.add(p)
    db.commit()
    logger.info("Seeded default system prompt from config/system_prompt.txt")
    return p


def run_all_seeds(db: Session) -> None:
    seed_initial_admin(db)
    seed_default_llm_config(db)
    seed_default_prompt(db)
