"""FastAPI dependencies (auth, db, role checks)."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from .database import get_db
from .models.api_key import ApiKey
from .models.user import User, UserRole
from .security import decode_token, hash_api_key

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the current authenticated user from the JWT access token.

    Raises 401 if the token is missing or invalid, 401 if the user no longer exists
    or has been deactivated.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc
    try:
        payload = decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise credentials_exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_exc
    return user


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency that enforces admin role."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privilege required",
        )
    return current_user


def get_api_key_user(
    db: Annotated[Session, Depends(get_db)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> User:
    """Resolve the owning user from an X-API-Key header (Open API auth).

    Raises 401 if the key is missing, unknown, revoked, or the owner is
    inactive. Updates last_used_at on success.
    """
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "X-API-Key"},
    )
    if not x_api_key:
        raise exc
    key_hash = hash_api_key(x_api_key.strip())
    api_key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
    if api_key is None or not api_key.is_active:
        raise exc
    user = db.get(User, api_key.owner_id)
    if user is None or not user.is_active:
        raise exc
    api_key.last_used_at = datetime.utcnow()
    db.commit()
    return user
