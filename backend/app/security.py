"""Password hashing and JWT token utilities."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Literal, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

settings = get_settings()

# bcrypt with a reasonable cost factor; passlib handles salt internally
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


# ─── Password hashing ────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# ─── JWT ─────────────────────────────────────────────────────────────────

TokenType = Literal["access", "refresh"]


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_minutes: int,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a signed JWT."""
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int, role: str) -> str:
    """Create a short-lived access token."""
    return _create_token(
        subject=str(user_id),
        token_type="access",
        expires_minutes=settings.access_token_expire_minutes,
        extra={"role": role},
    )


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived refresh token."""
    return _create_token(
        subject=str(user_id),
        token_type="refresh",
        expires_minutes=settings.refresh_token_expire_minutes,
    )


def decode_token(token: str, expected_type: TokenType) -> Dict[str, Any]:
    """Decode and validate a JWT. Raises JWTError on failure."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    if payload.get("type") != expected_type:
        raise JWTError(f"Invalid token type: expected {expected_type}")
    if "sub" not in payload:
        raise JWTError("Token missing subject")
    return payload
