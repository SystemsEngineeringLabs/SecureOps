# SecureOps — System Architecture

## 1. Architecture Overview

SecureOps is a **modular monolith** organized into bounded contexts. Each domain module has clear internal boundaries, communicates through defined internal interfaces, and can be extracted into a standalone service in the future without redesigning the system.

The system runs as two primary process types — an API server (FastAPI) and background workers (Celery) — backed by PostgreSQL, Redis, and pluggable object storage.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                          │
│                   Next.js 14 / React / TypeScript                  │
│         Server Components │ Client Components │ TanStack Query      │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ HTTPS / JSON
┌────────────────────────────────▼────────────────────────────────────┐
│                      API / APPLICATION LAYER                       │
│                    FastAPI  ·  Pydantic v2  ·  /api/v1/            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │  Auth /   │ │ Tenant   │ │   GRC    │ │ SecOps   │ │   AI    │ │
│  │  AuthZ    │ │ Mgmt     │ │ Domain   │ │ Domain   │ │ Service │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────┘ │
└──────┬─────────────┬─────────────┬─────────────┬────────────┬──────┘
       │             │             │             │            │
┌──────▼─────────────▼─────────────▼─────────────▼────────────▼──────┐
│                      DOMAIN SERVICE LAYER                          │
│  Services  ·  Repositories  ·  Domain Events  ·  Validators       │
└──────┬─────────────┬─────────────┬─────────────┬────────────┬──────┘
       │             │             │             │            │
┌──────▼─────────────▼─────────────▼─────────────▼────────────▼──────┐
│                      DATA / INTEGRATION LAYER                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────────┐   │
│  │ PostgreSQL │  │   Redis    │  │  Object Storage (Blob/S3)  │   │
│  │  + RLS     │  │ Queue/Cache│  │  Evidence Store             │   │
│  └────────────┘  └────────────┘  └────────────────────────────┘   │
└────────────────────────┬───────────────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────────────┐
│                 BACKGROUND / INTEGRATION LAYER                     │
│  Celery Workers  ·  Scanner Adapters  ·  Notification Dispatch     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Prowler  │  │  Trivy   │  │DefectDojo│  │  CloudQuery (opt)│  │
│  │ Adapter  │  │ Adapter  │  │ Adapter  │  │    Adapter       │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                              │
│  OpenTelemetry  ·  Prometheus  ·  Grafana  ·  Structured Logs      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 2. System Layers

### 2.1 Presentation Layer

| Concern | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript 5+ (strict) |
| Styling | Tailwind CSS + daisyUI |
| Forms | React Hook Form + Zod |
| Data fetching | TanStack Query → `/api/v1/` |
| Auth UI | Login, MFA, SSO redirect pages |

The frontend is a standalone deployment artifact. It communicates exclusively through the versioned REST API. No direct database access, no server-side secrets embedded in client bundles.

### 2.2 API / Application Layer

FastAPI application exposing `/api/v1/` endpoints. Responsibilities:

- Request validation (Pydantic v2 models).
- Authentication (JWT verification, session validation).
- Authorization (RBAC middleware + resource-level checks).
- Tenant context resolution (from authenticated identity, never from request body).
- Route delegation to domain services.
- Consistent error response envelope.
- OpenAPI spec generation at `/api/v1/openapi.json`.

### 2.3 Authentication & Authorization

```
Request → JWT/Session Middleware → Tenant Resolution → RBAC Check → Endpoint
                                       │
                               ┌───────▼────────┐
                               │ memberships     │
                               │ table lookup    │
                               │ (user → tenant) │
                               └─────────────────┘
```

- **Authentication**: JWT access tokens (short-lived, 30 min) + refresh tokens (7 days). Password hashing with bcrypt. MFA support (TOTP). SSO via OIDC/SAML in later phases.
- **Authorization**: RBAC with predefined roles (owner, admin, security_manager, engineer, auditor). Resource-level permissions checked in service layer. Default deny.
- **Session management**: Token revocation via Redis blocklist. Forced expiry on password change.

### 2.4 Tenant Management

Every tenant-owned row has a `tenant_id` column. Tenant context flows from the authentication layer into every database session:

1. JWT decoded → `user_id` extracted.
2. Active membership lookup → `tenant_id` resolved.
3. `tenant_id` set in SQLAlchemy session context.
4. PostgreSQL RLS policies enforce row filtering as defense in depth.

There is no API parameter for tenant selection — the system derives it from the authenticated user's membership.

### 2.5 GRC Domain

Covers: frameworks, controls, control mappings, compliance assessments, policies, and related evidence links. The framework registry supports versioned frameworks with many-to-many control mappings. Controls are not hardcoded to any single framework.

### 2.6 Security Operations Domain

Covers: cloud security findings, vulnerability findings, asset inventory, severity classification, risk scoring, remediation workflows. All scanner output is normalized into a unified `Finding` model before storage.

### 2.7 Integration / Connector Layer

Each external tool (Prowler, Trivy, DefectDojo) is wrapped by an **adapter** that:

- Manages container lifecycle (start, monitor, collect output).
- Parses tool-specific output into the normalized finding schema.
- Handles credential injection (from encrypted storage, short-lived where possible).
- Reports status back via Celery task state.

Adapters are independently replaceable. The core application never imports Prowler/Trivy internals.

### 2.8 Event / Job Processing (Celery)

```
┌──────────────┐     ┌─────────┐     ┌──────────────────────┐
│  API Server  │────▶│  Redis   │────▶│   Celery Workers     │
│  (enqueue)   │     │  Broker  │     │                      │
└──────────────┘     └─────────┘     │  cloud_scan_worker   │
                                      │  vuln_scan_worker    │
                                      │  evidence_worker     │
                                      │  notification_worker │
                                      │  report_worker       │
                                      └──────────────────────┘
```

Workers are separate OS processes. Long-running scans do not block the API. Workers share the same codebase but run with `celery -A app.workers.celery_app worker`.

### 2.9 Storage / Evidence Layer

| Store | Purpose | Tech |
|---|---|---|
| Operational data | Tenants, users, findings, controls, risks | PostgreSQL 16 |
| Evidence files | Uploaded docs, screenshots, scan reports | Azure Blob / S3 (via adapter) |
| Queues & cache | Job broker, session blocklist, temp cache | Redis 7 |

Evidence files are never served directly. The API generates short-lived signed download URLs after verifying tenant ownership.

### 2.10 AI Service Layer

Provides LLM-powered capabilities: finding explanation, risk summary, policy drafting, remediation suggestions. All AI output is marked as a suggestion requiring human review. Customer data is not sent to external AI without documented tenant authorization.

### 2.11 Observability / Audit Layer

- **Structured logs**: `structlog` emitting JSON, no PII/secrets.
- **Metrics**: Prometheus exposition at `/metrics` (API latency, error rates, queue depth, worker utilization).
- **Traces**: OpenTelemetry SDK with OTLP export to a collector.
- **Audit log**: Append-only `audit_events` table recording security-relevant actions (login, permission change, evidence access, control status change).

---

## 3. Bounded Contexts

```
┌─────────────────────────────────────────────────────────────────┐
│                     SecureOps Application                       │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Organization │  │  Compliance  │  │   Risk Management    │  │
│  │  & Tenancy   │  │  Management  │  │                      │  │
│  │              │  │              │  │  risk_register        │  │
│  │  tenants     │  │  frameworks  │  │  risk_categories     │  │
│  │  users       │  │  controls    │  │  risk_treatments     │  │
│  │  memberships │  │  mappings    │  │  risk_reviews        │  │
│  │  roles       │  │  assessments │  │                      │  │
│  │  invitations │  │  policies    │  │                      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                      │              │
│         │     ┌───────────┴──────────────────────┘              │
│         │     │   (control↔risk mappings, evidence links)       │
│         │     │                                                 │
│  ┌──────▼─────▼──┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Evidence    │  │    Cloud     │  │   Vulnerability      │ │
│  │  Management   │  │   Security   │  │   Management         │ │
│  │               │  │              │  │                       │ │
│  │  evidence     │  │  cloud_accts │  │  vulnerabilities     │ │
│  │  collections  │  │  assets      │  │  scanner_results     │ │
│  │  approvals    │  │  findings    │  │  cve_tracking        │ │
│  │  integrity    │  │  snapshots   │  │  deduplication       │ │
│  └──────┬────────┘  └──────┬───────┘  └──────────┬────────────┘ │
│         │                  │                      │             │
│         └──────────────────┼──────────────────────┘             │
│                            │                                    │
│  ┌─────────────────────────▼─────────────────────────────────┐  │
│  │              Remediation Management                       │  │
│  │  tasks  ·  assignments  ·  deadlines  ·  verification     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              AI Security Assistant                        │  │
│  │  explanation  ·  summarization  ·  recommendation         │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Inter-context communication

Contexts communicate through **internal service interfaces**, not direct model imports:

| From | To | Mechanism |
|---|---|---|
| Cloud Security | Evidence | `evidence_service.create_from_scan(scan_id, artifacts)` |
| Cloud Security | Remediation | `remediation_service.create_task(finding_id, ...)` |
| Compliance | Evidence | `evidence_service.link_to_control(evidence_id, control_id)` |
| Vulnerability | Remediation | `remediation_service.create_task(vuln_id, ...)` |
| Remediation | Notification | Celery task: `send_notification.delay(...)` |
| AI Assistant | Any read model | Read-only service calls; never writes compliance status |

Cross-context writes go through the owning context's service. No context directly modifies another context's tables.

---

## 4. API Design

### Versioning

All endpoints are under `/api/v1/`. Version bumps create a new prefix (`/api/v2/`) with a deprecation period for the old version.

### URL structure

```
/api/v1/auth/login
/api/v1/auth/refresh
/api/v1/auth/mfa/verify

/api/v1/tenants/current
/api/v1/users/me
/api/v1/users/{user_id}
/api/v1/memberships/

/api/v1/frameworks/
/api/v1/frameworks/{framework_id}/controls
/api/v1/controls/{control_id}
/api/v1/controls/{control_id}/evidence

/api/v1/risks/
/api/v1/risks/{risk_id}

/api/v1/cloud-accounts/
/api/v1/cloud-accounts/{account_id}/scan
/api/v1/findings/
/api/v1/findings/{finding_id}

/api/v1/vulnerabilities/
/api/v1/evidence/
/api/v1/evidence/{evidence_id}/download

/api/v1/remediation-tasks/
/api/v1/audit-events/
```

### Error response envelope

```json
{
  "error": {
    "code": "TENANT_NOT_FOUND",
    "message": "The requested tenant does not exist.",
    "details": null
  }
}
```

All 4xx/5xx responses use this shape. Field-level validation errors include `details` as an array of `{ field, message }` objects.

### Pagination

Cursor-based pagination for large collections (findings, vulnerabilities, audit events):

```
GET /api/v1/findings?cursor=eyJpZCI6MTAwfQ&limit=50
```

Response includes `next_cursor` and `has_more`. Offset-based pagination available for smaller, frequently filtered collections (controls, risks) with `?page=2&page_size=25`.

### Rate limiting

Endpoint-level rate limits enforced via middleware:

| Category | Limit |
|---|---|
| Auth endpoints | 10 req/min per IP |
| Standard read | 300 req/min per user |
| Standard write | 60 req/min per user |
| Scan triggers | 5 req/min per tenant |
| Evidence upload | 20 req/min per tenant |

---

## 5. Multi-Tenant Architecture

### Strategy: shared database, row-level isolation

All tenants share one PostgreSQL database. Every tenant-owned table includes a non-nullable `tenant_id UUID` column with a foreign key to the `tenants` table.

### Tenant context flow

```
1. Request arrives with JWT
2. Auth middleware decodes JWT → extracts user_id
3. Tenant resolution middleware:
   a. Looks up active membership for user_id
   b. If user has multiple tenants, uses X-Tenant-Id header
      (validated against membership list — not trusted blindly)
   c. Sets tenant_id on request state
4. Database session sets:
   SET LOCAL app.current_tenant_id = '<tenant_id>';
5. RLS policies filter all SELECT/INSERT/UPDATE/DELETE
```

### PostgreSQL RLS policy (defense in depth)

```sql
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON findings
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_insert ON findings
  FOR INSERT
  WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

RLS is **defense in depth**, not the sole protection. Application-level tenant scoping (via SQLAlchemy query filters) is the primary mechanism. RLS catches bugs where application code forgets to scope.

### Background job tenant isolation

Every Celery task receives `tenant_id` as an explicit parameter. The worker sets `app.current_tenant_id` in its database session before any query. Tasks never infer tenant context from global state.

### Cross-tenant access tests

Automated tests attempt to read, update, and delete resources belonging to Tenant B using Tenant A's credentials. These tests must pass in CI for any PR that touches data-access code.

---

## 6. Background Processing

### Celery configuration

| Setting | Value | Rationale |
|---|---|---|
| Broker | Redis (db 1) | Low latency, simple ops |
| Result backend | Redis (db 2) | Task result retrieval |
| Serializer | JSON | No pickle — prevents deserialization attacks |
| Task acks late | True | Redelivery on worker crash |
| Worker prefetch | 1 | Fair distribution for mixed task durations |
| Max retries | 3 (configurable per task) | Bounded retry budget |

### Task categories

| Queue | Tasks | Concurrency |
|---|---|---|
| `default` | Notifications, report generation | 4 |
| `scans` | Prowler runs, Trivy scans | 2 (resource-heavy) |
| `evidence` | Evidence collection, integrity checks | 2 |
| `imports` | DefectDojo sync, vulnerability imports | 2 |

### Retry and failure strategy

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    retry_backoff=True,       # exponential: 60s, 120s, 240s
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
)
def run_cloud_scan(self, tenant_id: str, account_id: str, scan_config: dict):
    ...
```

- **Idempotency**: Each task carries a `scan_execution_id`. Re-running the same execution ID is a no-op if results already exist.
- **Dead-letter queue**: After max retries, the task is routed to a `dead_letter` queue. A monitoring alert fires. Manual inspection required.
- **Graceful shutdown**: Workers handle SIGTERM by finishing the current task (up to a configurable timeout) before exiting.

---

## 7. Integration Architecture

### Adapter pattern

```
┌──────────────┐
│   Core App   │
│              │    ┌─────────────────────────┐
│  ScanService │───▶│  ScannerAdapter (ABC)   │
│              │    │                         │
└──────────────┘    │  + configure(creds)     │
                    │  + execute(config) → id │
                    │  + poll_status(id)      │
                    │  + collect_results(id)  │
                    │  + normalize(raw) → []  │
                    └────────┬────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼──┐  ┌───────▼───┐  ┌───────▼──────┐
     │  Prowler  │  │   Trivy   │  │  DefectDojo  │
     │  Adapter  │  │  Adapter  │  │   Adapter    │
     └───────────┘  └───────────┘  └──────────────┘
```

### Prowler integration

- Execution: Docker container with read-only cloud credentials mounted as environment variables.
- Output: JSON findings parsed by `ProwlerAdapter.normalize()` into `NormalizedFinding` objects.
- Resource limits: CPU (2 cores), memory (2 GB), 30-minute execution timeout.
- Network: Outbound only to the target cloud provider APIs. No inbound ports.

### Trivy integration

- Execution: Docker container scanning images, filesystems, or IaC configs.
- Output: JSON vulnerability report normalized into `NormalizedVulnerability` objects with CVE references.
- Resource limits: CPU (1 core), memory (1 GB), 15-minute timeout.

### DefectDojo integration (optional)

- Communication: REST API calls to a separately deployed DefectDojo instance.
- Purpose: Advanced vulnerability deduplication and lifecycle management.
- Normalized findings are pushed to DefectDojo and status synced back.

### Normalized Finding model

All scanner outputs are converted into this internal representation:

```
NormalizedFinding:
  id: UUID
  tenant_id: UUID
  source: enum (prowler | trivy | defectdojo | manual)
  source_id: str          # original ID from scanner
  category: enum (cloud_config | vulnerability | iac | secret | custom)
  severity: enum (critical | high | medium | low | info)
  title: str
  description: str
  resource_type: str
  resource_id: str
  recommendation: str
  raw_output: jsonb       # preserved for audit
  first_seen: datetime
  last_seen: datetime
  status: enum (open | acknowledged | remediated | false_positive | accepted)
  scan_execution_id: UUID
```

---

## 8. Storage Architecture

### PostgreSQL 16

- **Connection pooling**: Application uses SQLAlchemy async with `asyncpg`. Connection pool size: 20 per API process, 5 per worker.
- **Indexing strategy**: Composite indexes on `(tenant_id, <frequently filtered column>)` for all tenant-scoped tables. GIN indexes on JSONB columns where queried.
- **Partitioning**: `audit_events` table partitioned by month (range partitioning on `created_at`) to manage growth.
- **Migrations**: Alembic with `--autogenerate` for schema changes. All migrations reviewed before merge. Backward-compatible migrations only — no column drops without a deprecation migration first.

### Object storage (evidence)

```python
class EvidenceStorageBackend(ABC):
    @abstractmethod
    async def upload(self, tenant_id: str, key: str, data: BinaryIO, metadata: dict) -> str: ...

    @abstractmethod
    async def download_url(self, tenant_id: str, key: str, expires_in: int = 300) -> str: ...

    @abstractmethod
    async def delete(self, tenant_id: str, key: str) -> None: ...

class AzureBlobBackend(EvidenceStorageBackend): ...
class S3Backend(EvidenceStorageBackend): ...
class LocalFileBackend(EvidenceStorageBackend): ...  # dev only
```

Evidence is stored under `{tenant_id}/{evidence_id}/{filename}`. Tenant ID is part of the storage key — no cross-tenant access at the storage layer.

### Redis

| Database | Purpose |
|---|---|
| db 0 | Application cache (session blocklist, rate limit counters) |
| db 1 | Celery broker |
| db 2 | Celery result backend |

All Redis keys are prefixed with `secureops:{tenant_id}:` where tenant-scoped. TTLs enforced on all cache entries.

---

## 9. Deployment Architecture

### Local development

```
docker compose up -d    # PostgreSQL, Redis
cd backend && uvicorn app.main:app --reload
cd frontend && npm run dev
```

Optional: `docker compose --profile full up` to also run backend, worker, and frontend in containers.

### Staging / Production

```
┌──────────────────────────────────────────────────┐
│                 Load Balancer / CDN              │
│              (Azure Front Door / CloudFront)      │
└────────┬──────────────────────────┬───────────────┘
         │                          │
┌────────▼────────┐     ┌──────────▼──────────┐
│  Frontend       │     │   API Server(s)      │
│  (Static/SSR)   │     │   FastAPI (2+ inst)  │
│  Next.js on     │     │   Behind app gateway │
│  Azure Static   │     │                      │
│  Web Apps       │     │   /health → 200      │
└─────────────────┘     │   /ready  → 200      │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
           ┌───────▼───┐  ┌──────▼──────┐ ┌─────▼──────┐
           │ PostgreSQL │  │    Redis    │ │   Workers  │
           │ (managed)  │  │  (managed)  │ │ (2+ inst)  │
           └────────────┘  └─────────────┘ └────────────┘
```

Infrastructure defined in Terraform:

- `infrastructure/terraform/modules/` — reusable: database, redis, compute, storage, networking.
- `infrastructure/terraform/environments/{dev,staging,prod}/` — environment-specific variable files.

### Resource limits for scanners

Scanner containers launched by workers have hard limits:

| Scanner | CPU | Memory | Timeout | Network |
|---|---|---|---|---|
| Prowler | 2 cores | 2 GB | 30 min | Outbound to cloud APIs only |
| Trivy | 1 core | 1 GB | 15 min | Outbound to vuln DBs only |

Workers enforce these limits via Docker SDK `container.run(mem_limit=..., cpu_quota=..., network_mode=...)`.

---

## 10. Key Architecture Decisions

### ADR-001: Modular Monolith over Microservices

**Context**: The team is small and the product is in its first release. Microservices add operational overhead (service mesh, distributed tracing complexity, deployment coordination) without proportional benefit at this stage.

**Decision**: Ship as a modular monolith with strict domain boundaries. Each bounded context has its own `models/`, `schemas/`, `services/`, `api/` subdirectories. Cross-context communication uses internal service interfaces only.

**Consequences**: Simpler deployment and debugging. Context extraction into a service is possible later by replacing internal calls with HTTP/gRPC. Risk: developers must enforce boundaries by convention (enforced via code review and import linting).

---

### ADR-002: Shared Database with RLS for Multi-Tenancy

**Context**: Database-per-tenant is operationally expensive at scale. Schema-per-tenant complicates migrations. Shared tables with application-level filtering are the norm but rely on correct code in every query.

**Decision**: Shared database with `tenant_id` on every tenant-owned table. PostgreSQL Row-Level Security as defense in depth. Application-level filtering is the primary mechanism; RLS catches missed filters.

**Consequences**: Simple schema management, single migration path. RLS adds ~2% query overhead (measured on PostgreSQL 16 with 1M rows). Tenant context must be set in every database session — a missed `SET LOCAL` silently returns zero rows (safe by default via RLS `USING` clause).

---

### ADR-003: Containerized Scanner Execution

**Context**: Prowler and Trivy are CLI tools. Running them as library imports couples our application to their dependencies, Python/Go versions, and upgrade cycles.

**Decision**: Execute scanners as Docker containers managed by the Celery worker via the Docker SDK. Pass credentials as environment variables (never as CLI arguments). Collect output from container stdout/files.

**Consequences**: Clean isolation. Scanner upgrades are image tag changes. Resource limits enforced by Docker. Adds a Docker socket dependency on worker hosts. Workers must not run in environments where Docker-in-Docker is prohibited without an alternative (e.g., Kubernetes Jobs).

---

### ADR-004: Cursor-Based Pagination for Large Collections

**Context**: Findings and audit events can grow to millions of rows. Offset-based pagination degrades at high offsets (`OFFSET 1000000` scans and discards rows).

**Decision**: Cursor-based pagination (keyset pagination) using the primary key for findings, vulnerabilities, and audit events. Offset-based pagination retained for smaller, bounded collections (controls, risks, frameworks).

**Consequences**: Consistent query performance regardless of page depth. Clients cannot jump to arbitrary page numbers — navigation is forward/backward only. Acceptable trade-off for data tables that are typically filtered and sorted.

---

### ADR-005: JWT + Redis Blocklist for Authentication

**Context**: Stateless JWTs cannot be revoked without additional infrastructure. Pure session tokens require a database lookup on every request.

**Decision**: Short-lived JWT access tokens (30 min) + longer-lived refresh tokens (7 days). Token revocation via Redis blocklist (key = token JTI, TTL = remaining token lifetime). Refresh tokens stored hashed in PostgreSQL.

**Consequences**: Most requests are verified without a database hit. Revocation is near-instant (Redis lookup). Blocklist size is bounded by TTL expiry. Refresh token rotation on each use detects token theft.

---

### ADR-006: Evidence Storage via Pluggable Backend

**Context**: Customers may deploy on Azure, AWS, or on-premises. Hardcoding one cloud provider's object storage creates vendor lock-in.

**Decision**: Abstract evidence storage behind `EvidenceStorageBackend` interface. Ship with `AzureBlobBackend`, `S3Backend`, and `LocalFileBackend` (dev). Backend selected by configuration.

**Consequences**: Cloud-portable evidence layer. Each backend must implement upload, signed-URL download, and delete. Consistency semantics vary by provider (eventual vs. strong) — the application treats uploads as durable only after the backend confirms success.

---

### ADR-007: Append-Only Audit Events with Monthly Partitioning

**Context**: Audit events accumulate indefinitely. They must be queryable for compliance reviews but should not degrade operational query performance.

**Decision**: `audit_events` table uses PostgreSQL range partitioning on `created_at` with monthly partitions. Application writes are INSERT-only (no UPDATE or DELETE on audit events). Partition pruning keeps recent queries fast. Old partitions can be archived to cold storage.

**Consequences**: Predictable query performance. Partition maintenance requires a scheduled job to create future partitions. Export/archive procedures needed for long-term retention beyond the database.
