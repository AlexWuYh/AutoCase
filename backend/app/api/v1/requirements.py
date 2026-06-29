"""Requirement group + requirement endpoints."""
from __future__ import annotations

from typing import Annotated, List

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ...database import get_db
from ...deps import get_current_user
from ...models.requirement import Requirement
from ...models.requirement_group import RequirementGroup
from ...models.user import User, UserRole
from ...schemas.common import PageResponse
from ...schemas.requirement import (
    GroupCreate,
    GroupOut,
    GroupUpdate,
    ImportResult,
    RequirementBatchCreate,
    RequirementCreate,
    RequirementOut,
    RequirementUpdate,
)
from ...services.yaml_service import (
    parse_yaml_to_specs,
    render_group_to_yaml,
)

router = APIRouter()


# ─── Helpers ────────────────────────────────────────────────────────────

def _can_access_group(group: RequirementGroup, user: User) -> bool:
    return user.role == UserRole.ADMIN or group.owner_id == user.id


def _can_modify_group(group: RequirementGroup, user: User) -> bool:
    return _can_access_group(group, user)


def _get_group_or_404(
    db: Session, group_id: int, user: User, *, modify: bool = False
) -> RequirementGroup:
    group = db.get(RequirementGroup, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="需求集不存在")
    if modify and not _can_modify_group(group, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此需求集")
    if not _can_access_group(group, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此需求集")
    return group


def _to_group_out(group: RequirementGroup) -> GroupOut:
    return GroupOut(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        owner_username=group.owner.username if group.owner else None,
        requirement_count=len(group.requirements) if group.requirements is not None else 0,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


# ─── Group CRUD ─────────────────────────────────────────────────────────

@router.get("", response_model=PageResponse[GroupOut], tags=["requirement-groups"])
def list_groups(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: str | None = Query(None, description="按名称/描述搜索"),
    scope: str = Query(None, pattern="^(mine|all)$", description="mine=仅我创建的; all=全部 (admin 默认全部)"),
) -> PageResponse[GroupOut]:
    """List requirement groups. Admin sees all by default; non-admin only own."""
    if scope == "all" and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="仅管理员可查看全部需求集")

    # None (unspecified) → admin sees all, user sees own
    # "all" → admin sees all; "mine" → only own
    filter_to_owner = current_user.role != UserRole.ADMIN or scope == "mine"

    stmt = select(RequirementGroup)
    if filter_to_owner:
        stmt = stmt.where(RequirementGroup.owner_id == current_user.id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            RequirementGroup.name.ilike(like) | RequirementGroup.description.ilike(like)
        )
    stmt = stmt.order_by(RequirementGroup.id.desc())

    # Count before pagination
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    rows = (
        db.execute(
            stmt.options(selectinload(RequirementGroup.owner))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )

    # Requirement counts in a single query
    if rows:
        ids = [g.id for g in rows]
        counts = dict(
            db.execute(
                select(Requirement.group_id, func.count(Requirement.id))
                .where(Requirement.group_id.in_(ids))
                .group_by(Requirement.group_id)
            ).all()
        )
    else:
        counts = {}

    items: List[GroupOut] = []
    for g in rows:
        out = _to_group_out(g)
        out.requirement_count = counts.get(g.id, 0)
        items.append(out)

    return PageResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED, tags=["requirement-groups"])
def create_group(
    payload: GroupCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GroupOut:
    """Create a new requirement group. Caller becomes the owner."""
    group = RequirementGroup(
        name=payload.name,
        description=payload.description,
        owner_id=current_user.id,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return _to_group_out(group)


@router.get("/{group_id}", response_model=GroupOut, tags=["requirement-groups"])
def get_group(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GroupOut:
    group = _get_group_or_404(db, group_id, current_user)
    return _to_group_out(group)


@router.put("/{group_id}", response_model=GroupOut, tags=["requirement-groups"])
def update_group(
    group_id: int,
    payload: GroupUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GroupOut:
    group = _get_group_or_404(db, group_id, current_user, modify=True)
    if payload.name is not None:
        group.name = payload.name
    if payload.description is not None:
        group.description = payload.description
    db.commit()
    db.refresh(group)
    return _to_group_out(group)


@router.delete("/{group_id}", tags=["requirement-groups"])
def delete_group(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    group = _get_group_or_404(db, group_id, current_user, modify=True)
    db.delete(group)
    db.commit()
    return {"message": "已删除"}


# ─── Requirements within a group ────────────────────────────────────────

def _next_sort_order(db: Session, group_id: int) -> int:
    current_max = db.execute(
        select(func.coalesce(func.max(Requirement.sort_order), -1)).where(
            Requirement.group_id == group_id
        )
    ).scalar_one()
    return int(current_max) + 1


@router.get(
    "/{group_id}/requirements",
    response_model=PageResponse[RequirementOut],
    tags=["requirement-groups"],
)
def list_requirements(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: str | None = Query(None, description="按 module/feature/description 搜索"),
) -> PageResponse[RequirementOut]:
    group = _get_group_or_404(db, group_id, current_user)
    stmt = select(Requirement).where(Requirement.group_id == group.id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            Requirement.module.ilike(like)
            | Requirement.feature.ilike(like)
            | Requirement.description.ilike(like)
        )
    stmt = stmt.order_by(Requirement.sort_order, Requirement.id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return PageResponse(
        items=[RequirementOut.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{group_id}/requirements",
    response_model=List[RequirementOut],
    status_code=status.HTTP_201_CREATED,
    tags=["requirement-groups"],
)
def batch_create_requirements(
    group_id: int,
    payload: RequirementBatchCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> List[RequirementOut]:
    """Batch create requirements. mode=replace deletes all existing first."""
    group = _get_group_or_404(db, group_id, current_user, modify=True)

    if payload.mode == "replace":
        db.query(Requirement).filter(Requirement.group_id == group.id).delete()
        db.flush()
        base_order = 0
    else:
        base_order = _next_sort_order(db, group.id)

    new_rows: List[Requirement] = []
    for i, item in enumerate(payload.items):
        new_rows.append(
            Requirement(
                group_id=group.id,
                module=item.module,
                feature=item.feature,
                description=item.description,
                keywords=item.keywords,
                sort_order=base_order + i,
            )
        )
    db.add_all(new_rows)
    db.commit()
    for r in new_rows:
        db.refresh(r)
    return [RequirementOut.model_validate(r) for r in new_rows]


# ─── Single requirement operations ──────────────────────────────────────

@router.put(
    "/requirements/{req_id}",
    response_model=RequirementOut,
    tags=["requirement-groups"],
)
def update_requirement(
    req_id: int,
    payload: RequirementUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RequirementOut:
    req = db.get(Requirement, req_id)
    if req is None:
        raise HTTPException(status_code=404, detail="需求点不存在")
    _get_group_or_404(db, req.group_id, current_user, modify=True)
    if payload.module is not None:
        req.module = payload.module
    if payload.feature is not None:
        req.feature = payload.feature
    if payload.description is not None:
        req.description = payload.description
    if payload.keywords is not None:
        req.keywords = payload.keywords
    db.commit()
    db.refresh(req)
    return RequirementOut.model_validate(req)


@router.delete(
    "/requirements/{req_id}",
    tags=["requirement-groups"],
)
def delete_requirement(
    req_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    req = db.get(Requirement, req_id)
    if req is None:
        raise HTTPException(status_code=404, detail="需求点不存在")
    _get_group_or_404(db, req.group_id, current_user, modify=True)
    db.delete(req)
    db.commit()
    return {"message": "已删除"}


# ─── YAML import / export ───────────────────────────────────────────────

@router.post(
    "/{group_id}/import-yaml",
    response_model=ImportResult,
    tags=["requirement-groups"],
)
async def import_yaml(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile | None = None,
    text: Annotated[str | None, Form()] = None,
    mode: str = Query("append", pattern="^(append|replace)$"),
) -> ImportResult:
    """Import requirements from a YAML file or raw text body.

    Provide exactly one of `file` (multipart) or `text` (form field).
    """
    group = _get_group_or_404(db, group_id, current_user, modify=True)

    if file is not None and text is not None:
        raise HTTPException(status_code=400, detail="file 和 text 不可同时提供")
    if file is None and text is None:
        raise HTTPException(status_code=400, detail="必须提供 file 或 text")

    if file is not None:
        raw = (await file.read()).decode("utf-8", errors="replace")
    else:
        raw = text or ""

    try:
        specs = parse_yaml_to_specs(raw)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"YAML 解析失败: {e}")

    if mode == "replace":
        deleted = db.query(Requirement).filter(Requirement.group_id == group.id).delete()
        db.flush()
        base_order = 0
    else:
        base_order = _next_sort_order(db, group.id)

    new_rows: List[Requirement] = []
    for i, spec in enumerate(specs):
        new_rows.append(
            Requirement(
                group_id=group.id,
                module=spec.module,
                feature=spec.feature,
                description=spec.description,
                keywords=spec.keywords,
                sort_order=base_order + i,
            )
        )
    db.add_all(new_rows)
    db.commit()
    return ImportResult(imported=len(new_rows), skipped=0, total_in_file=len(specs))


@router.get(
    "/{group_id}/export-yaml",
    response_class=PlainTextResponse,
    tags=["requirement-groups"],
)
def export_yaml(
    group_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> str:
    """Export a group's requirements as YAML in CLI-compatible format."""
    group = _get_group_or_404(db, group_id, current_user)
    # Force-load requirements
    db.refresh(group, attribute_names=["requirements"])
    return render_group_to_yaml(group)
