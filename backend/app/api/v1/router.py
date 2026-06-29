"""Aggregated v1 API router. Sub-routes are added in later phases."""
from fastapi import APIRouter

router = APIRouter()

# Each feature module will be included here as it lands:
# from .auth import router as auth_router
# from .users import router as users_router
# from .requirements import router as requirements_router
# from .jobs import router as jobs_router
# from .llm_configs import router as llm_configs_router
# from .prompts import router as prompts_router
# from .system import router as system_router
#
# router.include_router(auth_router, prefix="/auth", tags=["auth"])
# router.include_router(users_router, prefix="/users", tags=["users"])
# ...
