"""Aggregated v1 API router."""
from fastapi import APIRouter

from .api_keys import router as api_keys_router
from .auth import router as auth_router
from .jobs import router as jobs_router
from .llm_configs import router as llm_configs_router
from .open_api import router as open_api_router
from .prompts import router as prompts_router
from .requirements import router as requirements_router
from .system import router as system_router
from .users import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(
    requirements_router, prefix="/requirement-groups", tags=["requirement-groups"]
)
router.include_router(llm_configs_router, prefix="/llm-configs", tags=["llm-configs"])
router.include_router(prompts_router, prefix="/system-prompts", tags=["system-prompts"])
router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
router.include_router(system_router, prefix="/system", tags=["system"])
router.include_router(api_keys_router, prefix="/api-keys", tags=["api-keys"])
router.include_router(open_api_router, prefix="/open", tags=["open-api"])
