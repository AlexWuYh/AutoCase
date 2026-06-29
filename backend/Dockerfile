# AutoCase Web Platform - Backend Dockerfile
# Build context is the project root (so we can install the CLI core as a package).

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps (curl for healthcheck, build-essential for any wheel needs)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install the CLI core package first (so its deps are cached in a separate layer)
COPY pyproject.toml /tmp/cli_pyproject.toml
COPY src /tmp/cli_src
RUN pip install /tmp/cli_src/ \
    && rm -rf /tmp/cli_src /tmp/cli_pyproject.toml

# Install backend dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copy backend code
COPY backend/ /app/

# Ensure data and uploads directories exist
RUN mkdir -p /app/data /app/uploads

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/health || exit 1

# Entrypoint runs migrations (once we add Alembic) and starts uvicorn.
# For Phase 1 we just start uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
