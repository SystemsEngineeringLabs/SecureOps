# SecureOps — CLAUDE.md

## Project Overview
SecureOps is a unified Security Operations, GRC (Governance, Risk & Compliance) SaaS platform.

## Tech Stack
- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 16, Redis, Celery
- **Frontend**: Next.js 14+, React 18+, TypeScript 5+, Tailwind CSS, daisyUI
- **Infrastructure**: Docker, Terraform, GitHub Actions, Prometheus, Grafana, OpenTelemetry
- **Security Engines**: Prowler (cloud security), Trivy (vulnerability scanning)

## Commands
- **Backend**: `cd backend && uvicorn app.main:app --reload`
- **Frontend**: `cd frontend && npm run dev`
- **Tests (backend)**: `cd backend && pytest`
- **Tests (frontend)**: `cd frontend && npm test`
- **Lint (backend)**: `cd backend && ruff check . && mypy .`
- **Lint (frontend)**: `cd frontend && npm run lint`
- **Docker**: `docker compose up -d`
- **Migrations**: `cd backend && alembic upgrade head`

## Architecture Principles
- Modular monolith with bounded contexts
- Multi-tenant with PostgreSQL RLS as defense in depth
- All tenant-owned data scoped by tenant_id
- Strict domain boundaries between modules
- Background workers for heavy operations (scans, evidence collection)
- Normalized internal finding model for all scanner integrations

## Security Rules
- Never commit secrets or credentials
- Never trust tenant IDs from frontend — resolve via auth context
- Default-deny authorization
- Parameterized queries only (via SQLAlchemy ORM)
- Validate all external input at API boundary
- Encrypt evidence at rest and in transit
- Read-only cloud permissions for scanning
- Append-only audit logging for security events

## Code Conventions
- Backend: snake_case, type hints on all public functions, Pydantic for validation
- Frontend: camelCase for variables, PascalCase for components, strict TypeScript
- Tests: pytest (backend), vitest (frontend), test files mirror source structure
- API: versioned under /api/v1/, OpenAPI documented
- Commits: conventional commits (feat:, fix:, docs:, chore:, security:)
