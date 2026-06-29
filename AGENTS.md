# AGENTS

This document defines repository-specific guidance for AI agents working on this project.

## Project Overview
AutoCase is a CLI tool **and** a Web platform (Docker-deployed) that uses an LLM to generate standardized test cases. The CLI reads YAML and outputs Excel/CSV/JSON. The Web platform (under `feat/web-platform` branch) adds account management, requirement CRUD, async generation, and config management.

## Branches
- `main`: stable CLI tool only
- `feat/web-platform`: Web platform development (phases 1-6)
- `codex/dev`: legacy branch

## Key Commands
### CLI
- Install (editable): `pip3 install -e .`
- Run (default): `autocase -f input.example.yaml`
- JSON only: `autocase -f input.example.yaml --json-only`
- Help: `autocase -h`

### Web platform
- Setup: `cp .env.example .env` (then edit `SECRET_KEY` and `INITIAL_ADMIN_PASSWORD`)
- Start: `docker compose up -d --build`
- Logs: `docker compose logs -f backend` / `docker compose logs -f worker`
- Stop: `docker compose down`
- Backend dev: `cd backend && uvicorn app.main:app --reload`
- Frontend dev: `cd frontend && npm run dev`

## Inputs / Outputs (CLI)
- Default input directory: `inputs/`
- Default output directory: `outputs/`
- If `-o` is omitted, output is `{input}_{timestamp}_testcases.xlsx` in `outputs/`.

## Configuration Files
- LLM config: `config/llm.yaml` (local only; use `config/llm.example.yaml` as template)
- System prompt: `config/system_prompt.txt`
- **Web platform**: LLM config and prompts are managed in the Web UI and stored in SQLite; `config/llm.yaml` is only used to seed the default config on first run.

## Output Contract
The LLM must return a JSON array of objects with these fields:
- `type`
- `name`
- `priority`
- `pre`
- `steps`
- `expected`
- `stage`

The tool adds IDs, module, and keywords automatically.

## Coding Conventions
- Prefer explicit error messages and non-zero exit codes.
- Keep CLI behavior stable; `autocase` with no args prints banner + help.
- Use ASCII-only edits unless the file already contains non-ASCII.
- **Web backend MUST reuse CLI core modules** (`from autocase.parser import ...`); do not duplicate LLM call / YAML parsing / case assembly logic.
- **Web frontend**: Vue 3 `<script setup lang="ts">`, Pinia for state, Axios via `src/utils/request.ts` only.

## Testing Notes
- CLI: no automated tests currently. Manual checks:
  - `autocase -f inputs/input.example.yaml` (requires API key)
  - `autocase -f inputs/input.example.yaml --json-only`
- Web: pytest under `backend/tests/`. Mock LLM for unit tests; require Docker for e2e.

## Review Checklist
### CLI
- CLI flags work as documented.
- Output Excel formatting remains intact.
- CSV output works and columns are ordered correctly.
- LLM config and prompt are loaded correctly.
- Default input/output directory logic still works.

### Web platform
- API endpoints return correct status codes and JSON shape.
- JWT auth enforced on protected routes; role checks for admin endpoints.
- SQL injection / XSS guarded via Pydantic validation and SQLAlchemy ORM.
- Docker build succeeds and all 4 services (redis, backend, worker, frontend) start healthy.
- Web frontend builds without TypeScript errors.
- No regression in `src/autocase/` (CLI still works on `main`).
