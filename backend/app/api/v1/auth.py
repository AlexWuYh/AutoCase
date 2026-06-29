"""Authentication endpoints: login, refresh, me, change-password."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from ...config import get_settings
from ...database import get_db
from ...deps import get_current_user
from ...models.user import User
from ...schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from ...schemas.user import UserChangePassword, UserOut
from ...security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from ...security import hash_password

router = APIRouter()
settings = get_settings()


def _build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/login", response_model=TokenResponse, tags=["auth"])
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    """Authenticate with username + password, return access + refresh tokens."""
    user = db.query(User).filter(User.username == payload.username).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        # Constant message to avoid leaking which field is wrong
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    user.last_login_at = datetime.utcnow()
    db.commit()
    return _build_token_response(user)


@router.post("/refresh", response_model=TokenResponse, tags=["auth"])
def refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        decoded = decode_token(payload.refresh_token, expected_type="refresh")
        user_id = int(decoded["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer valid",
        )
    return _build_token_response(user)


@router.get("/me", response_model=UserOut, tags=["auth"])
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Return the currently authenticated user's profile."""
    return current_user


@router.post("/change-password", tags=["auth"])
def change_password(
    payload: UserChangePassword,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Change the current user's own password (requires old password)."""
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated"}
