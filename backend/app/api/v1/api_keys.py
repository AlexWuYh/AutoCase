"""API Key management endpoints (for logged-in users to manage their own keys)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ...database import get_db
from ...deps import get_current_user
from ...models.api_key import ApiKey
from ...models.user import User
from ...schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyOut
from ...schemas.common import Message
from ...security import generate_api_key

router = APIRouter()


@router.get("", response_model=list[ApiKeyOut], tags=["api-keys"])
def list_api_keys(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ApiKeyOut]:
    """List the current user's API keys (plaintext never returned)."""
    rows = db.execute(
        select(ApiKey).where(ApiKey.owner_id == current_user.id).order_by(ApiKey.id.desc())
    ).scalars().all()
    return [ApiKeyOut.model_validate(r) for r in rows]


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED, tags=["api-keys"])
def create_api_key(
    payload: ApiKeyCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiKeyCreated:
    """Create a new API key. The plaintext key is returned exactly once."""
    plaintext, key_hash, prefix = generate_api_key()
    row = ApiKey(
        name=payload.name,
        key_hash=key_hash,
        prefix=prefix,
        owner_id=current_user.id,
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ApiKeyCreated(
        id=row.id,
        name=row.name,
        prefix=row.prefix,
        is_active=row.is_active,
        created_at=row.created_at,
        last_used_at=row.last_used_at,
        key=plaintext,
    )


@router.delete("/{key_id}", response_model=Message, tags=["api-keys"])
def revoke_api_key(
    key_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Message:
    """Revoke (delete) one of the current user's API keys."""
    row = db.get(ApiKey, key_id)
    if row is None or row.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key 不存在")
    db.delete(row)
    db.commit()
    return Message(message="已吊销")
