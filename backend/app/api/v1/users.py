"""User management endpoints (admin only)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...database import get_db
from ...deps import require_admin
from ...models.user import User, UserRole
from ...schemas.common import PageResponse
from ...schemas.user import (
    UserCreate,
    UserOut,
    UserPasswordReset,
    UserUpdate,
)
from ...security import hash_password

router = APIRouter()


@router.get("", response_model=PageResponse[UserOut], tags=["users"])
def list_users(
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, description="Search by username or email"),
) -> PageResponse[UserOut]:
    """List all users (admin only)."""
    stmt = select(User)
    if search:
        like = f"%{search}%"
        stmt = stmt.where((User.username.ilike(like)) | (User.email.ilike(like)))
    stmt = stmt.order_by(User.id.desc())
    total = len(db.execute(stmt).all())
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return PageResponse[UserOut](
        items=[UserOut.model_validate(u) for u in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(
    payload: UserCreate,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UserOut:
    """Create a new user (admin only)."""
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )
    db.refresh(user)
    return UserOut.model_validate(user)


@router.get("/{user_id}", response_model=UserOut, tags=["users"])
def get_user(
    user_id: int,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UserOut:
    """Get a single user by ID (admin only)."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut.model_validate(user)


@router.put("/{user_id}", response_model=UserOut, tags=["users"])
def update_user(
    user_id: int,
    payload: UserUpdate,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> UserOut:
    """Update a user (admin only). Prevents demoting the last active admin."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Guard: cannot demote/disable the last admin
    is_demoting = payload.role is not None and payload.role != UserRole.ADMIN
    is_disabling = payload.is_active is False
    if (is_demoting or is_disabling) and user.role == UserRole.ADMIN:
        active_admin_count = db.query(User).filter(
            User.role == UserRole.ADMIN, User.is_active.is_(True)
        ).count()
        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote or disable the last active admin",
            )

    if payload.email is not None:
        user.email = payload.email
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)


@router.delete("/{user_id}", tags=["users"])
def delete_user(
    user_id: int,
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Delete a user (admin only). Refuses to delete the last active admin."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    if user.role == UserRole.ADMIN:
        active_admin_count = db.query(User).filter(
            User.role == UserRole.ADMIN, User.is_active.is_(True)
        ).count()
        if active_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last active admin",
            )
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@router.post("/{user_id}/reset-password", tags=["users"])
def reset_password(
    user_id: int,
    payload: UserPasswordReset,
    _admin: Annotated[User, Depends(require_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Reset a user's password (admin only). No old password required."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password reset"}
