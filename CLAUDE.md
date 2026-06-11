# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Kefcatic** is a no-code AI assistant automation platform where users create "cat assistants" (고양이 비서) that automate repetitive tasks by connecting to external services (YouTube, Gmail, Google Drive, Slack, Notion). The key UX metaphor is each assistant represented as a cat character with 9 status states.

Core principles:
- Users always know what the AI is about to do before it acts
- High-risk actions are never executed automatically
- All execution history is transparently logged
- Non-technical users must be able to create assistants without code

## Current Status

The project has not been implemented yet. Only planning documents exist: `plan.md` (detailed implementation plan with code skeletons, DB schema, Safety Rules, and phase checklists) and `frontend_plan.md` (frontend/design plan with design tokens, component library, screen layouts, and cat asset guidelines). The implementation plan (`plan.md`) takes precedence on technical decisions.

## Planned Tech Stack (from `frontend_plan.md`)

```
Backend:   FastAPI + Python 3.12
ORM:       SQLAlchemy 2.x (async) + Alembic migrations
Auth:      Google/GitHub OAuth2 + JWT sessions
Queue:     Celery + Redis (DB-scan Beat scheduler, NOT dynamic Redis schedule)
DB:        PostgreSQL 16 (primary), Redis (cache/broker)
Frontend:  React 19 + Vite + TailwindCSS
State:     Zustand (global) + TanStack Query (server state)
Forms:     react-hook-form
Desktop:   Separate project, Phase 5+
Infra:     Docker Compose (dev) → Railway/Render or VPS (prod)
```

## Planned Monorepo Structure

```
/
├── backend/
│   └── app/
│       ├── api/         # FastAPI routers
│       ├── core/        # config, security, database deps
│       ├── models/      # SQLAlchemy models
│       ├── schemas/     # Pydantic v2 schemas
│       ├── services/    # business logic (including action_engine.py, llm_service.py)
│       ├── tasks/       # Celery tasks (celery_app.py, assistant_tasks.py)
│       └── connectors/  # Connector SDK (base.py + per-service implementations)
├── frontend/src/
│   ├── components/
│   ├── pages/
│   ├── api/             # API client layer
│   └── stores/          # Zustand stores
└── docker-compose.yml
```

## Development Commands (once implemented)

```bash
# Start all services
docker compose up

# Apply DB migrations
docker compose exec backend alembic upgrade head

# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Run backend tests (uses testcontainers, not SQLite)
docker compose exec backend pytest

# Run a single test
docker compose exec backend pytest tests/path/to/test_file.py::test_name -v

# Run frontend dev server
docker compose exec frontend npm run dev

# Frontend tests
docker compose exec frontend npm run test
```

## Code Conventions

**Python (backend)**:
- Type hints required on all function signatures
- Use `async`/`await` consistently (SQLAlchemy async engine, httpx async)
- Pydantic v2: use `model_validate()` and `model_dump()`, not v1 methods
- Dependency injection via FastAPI `Depends()` pattern
- Exceptions: `HTTPException` + custom `AppException`

**TypeScript (frontend)**:
- TypeScript strict mode required
- Props types must be explicitly declared on all components

## Connector SDK Pattern

All connectors implement `BaseConnector` (see `frontend_plan.md` §1-1) with these abstract methods:
- `validate_credentials()`, `list_items()`, `read_item()`
- Optional: `create_item()`, `update_item()`, `delete_item()`, `search()`

Register connectors via `@register_connector` decorator into `CONNECTOR_REGISTRY`.

## Action Engine

Actions are defined as `ActionDefinition` objects in `ACTION_REGISTRY` with:
- `risk_level`: low / medium / high
- `default_approval_mode`: auto / draft_only / require_approval / always_manual / disabled

The approval mode gates every external API call — see Platform Safety Rules below.

## Celery Beat Scheduler

Use **DB-scan approach**, NOT dynamic Redis schedule injection:
- One fixed task `celerybeat_dispatch()` runs every 1 minute
- It queries `triggers` table for `is_active=true` rows where `next_run_at` has passed
- Fires `run_assistant_task.delay()` per matching trigger and updates `next_run_at`
- Rationale: DB is the single source of truth; no schedule loss on worker restart

## Platform Safety Rules (non-negotiable)

These rules take precedence over feature implementation speed:

| Rule | Requirement |
|------|-------------|
| SR-01 | Check `approval_mode` from `permission_policies` before every external API call. `disabled` → reject immediately. `draft_only` → save draft, no API call. `require_approval`/`always_manual` → create `approval_requests` and stop. Only `auto` proceeds. |
| SR-02 | Never attempt rollback if `action_logs.external_resource_id` is NULL. |
| SR-03 | Decrypt `connector_credentials` only through `ConnectorCredentialService.get_decrypted()`. Never access the raw JSONB in API routers or log decrypted tokens. |
| SR-04 | Only one `pending` approval_request per action_log at a time. Return existing ID instead of creating a duplicate. |
| SR-05 | Celery tasks must use `get_async_session()` context manager, never create DB sessions directly. Wrap in try/finally to ensure rollback on failure. |
| SR-06 | When installing marketplace templates, force the user to re-confirm each `action_type` approval_mode. Never inherit template author's `auto` setting as-is. |

## DB Schema Notes

- `oauth_accounts` = login credentials (who logged in via Google/GitHub)
- `connector_credentials` = service credentials (what external APIs the assistant can call) — these are separate concerns even if both use Google OAuth
- `action_logs.rollback_data` is only populated when `is_reversible=true`
- `marketplace_templates` and `template_reviews` tables are added in Phase 4 via separate Alembic migration — do NOT create them in Phase 0

## Testing Strategy

**Backend**:
- pytest + pytest-asyncio
- Use `testcontainers-python` (PostgreSQL 16 container) — **SQLite is forbidden** due to JSONB, UUID, TEXT[] types
- `conftest.py`: spin up container → run Alembic migrations → yield session → teardown
- Isolate tests via transaction rollback per test
- Mock external APIs with `httpx.MockTransport`
- Core coverage targets: `action_engine`, approval flow, connector base

**Frontend**:
- Vitest + React Testing Library
- Core coverage targets: approval inbox interactions, assistant creation wizard

## Design System (Kefcatic Design Brief)

Style: monochrome-first SaaS productivity tool. References: Notion, Linear, Raycast, Superhuman.

**Colors**:
- Background: `#FAFAFA` / Text: `#0A0A0A`
- Borders: `#E5E7EB`
- One accent color maximum (Gray-900 solid)
- Status badges: Active = solid neutral, Idle = gray muted, Error = icon + text only (no red backgrounds)

**Cat Room constraints**:
- Black-and-white line art or simple silhouettes — no game UI (no HP bars, sparkle effects, levels)
- 9 states: idle / watching / reading / sorting / drafting / waiting_approval / executing / done / error
- Every state must also show natural-language text (e.g., "댓글을 살펴보고 있어요." not "status: reading")
- Animations: subtle CSS transitions only, no complex animation libraries for state changes

**Typography**: Inter or Geist Sans; no overly cute fonts.

## Phase Dependencies

```
Phase 0 (Foundation) → Phase 1 (Core Engine) → Phase 2 (MVP Product)
→ Phase 3 (Platform) → Phase 4 (Marketplace) → Phase 5 (Production)
```

Parallel work allowed within Phase 3 (connector additions ↔ builder UI) and Phase 4 (backend ↔ frontend after API contract is set).
