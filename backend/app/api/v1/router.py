"""Aggregated v1 API router."""
from fastapi import APIRouter

from .auth import router as auth_router
from .requirements import router as requirements_router
from .users import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(
    requirements_router, prefix="/requirement-groups", tags=["requirement-groups"]
)
