"""First-run seeding: create initial admin user from env settings."""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .models.user import User, UserRole
from .security import hash_password

logger = logging.getLogger("autocase.seed")

settings = get_settings()


def seed_initial_admin(db: Session) -> Optional[User]:
    """Create the initial admin if no users exist.

    Returns the created user, or None if a user already exists.
    """
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
        "Initial admin user '%s' created. CHANGE THE DEFAULT PASSWORD IMMEDIATELY.",
        admin.username,
    )
    return admin


def run_all_seeds(db: Session) -> None:
    """Run all seed routines. Idempotent — safe to call on every startup."""
    seed_initial_admin(db)
