# SecureOps — Implementation Roadmap

> **Status**: Phase 0 (Discovery & Architecture) complete. Ready to begin Phase 1.
> **Last updated**: 2026-11-19

---

## 1. Phase Overview

| Phase | Name | Duration | Key Deliverable | Primary Agents |
|-------|------|----------|-----------------|----------------|
| 0 | Discovery & Architecture | 1 week | Approved engineering blueprint | 1 (Architect), 2 (Security) |
| 1 | Platform Foundation | 3–4 weeks | Secure multi-tenant SaaS skeleton | 2, 3, 4, 8 |
| 2 | GRC Engine | 3–4 weeks | Functional GRC product (MVP) | 3, 4, 7, 9 |
| 3 | Cloud Security | 3 weeks | Cloud security visibility | 3, 5, 7 |
| 4 | Vulnerability & Remediation | 2–3 weeks | Connected security operations | 3, 6, 7 |
| 5 | AI & Reporting | 2 weeks | AI-assisted security management | 3, 4, 7 |
| 6 | Commercial Readiness | 3–4 weeks | Commercial MVP candidate | All |

**Total estimated timeline**: 17–21 weeks to commercial MVP candidate.

**MVP = Phase 1 + Phase 2** — a working multi-tenant GRC platform with SOC 2 and ISO 27001 compliance management, risk register, and evidence management.

---

## 2. Phase 1 — Platform Foundation (Detailed)

### 1.1 Backend Core

**Owner**: Agent 3 (Backend Engineer)
**Effort**: 5–6 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/db/base.py` | SQLAlchemy async engine, session factory, base model with `id`, `tenant_id`, `created_at`, `updated_at` |
| `backend/app/db/session.py` | Async session dependency, tenant-context session variable setter |
| `backend/app/models/__init__.py` | Model registry |
| `backend/app/models/tenant.py` | `Tenant` model |
| `backend/app/models/user.py` | `User` model |
| `backend/app/models/membership.py` | `Membership` model (user ↔ tenant with role) |
| `backend/app/models/role.py` | `Role` and `Permission` models |
| `backend/app/models/audit.py` | `AuditEvent` model |
| `backend/alembic.ini` | Alembic configuration |
| `backend/alembic/env.py` | Async migration environment |
| `backend/alembic/versions/001_initial_schema.py` | Initial migration: tenants, users, memberships, roles, permissions, audit_events + RLS policies |
| `backend/app/api/__init__.py` | API router aggregation |
| `backend/app/api/v1/__init__.py` | v1 router |
| `backend/app/api/deps.py` | Common dependencies (get_db, get_current_user, get_current_tenant) |

**Acceptance criteria**:
- `alembic upgrade head` creates all tables with correct constraints and indexes on a clean PostgreSQL 16 instance.
- RLS policies are created and enabled for all tenant-scoped tables.
- All models have `tenant_id` FK (except `Tenant` itself and global lookup tables).
- `(tenant_id, id)` compound indexes exist on all tenant-scoped tables.
- Health endpoint returns `{"status": "healthy"}` and readiness endpoint verifies DB + Redis connectivity.

---

### 1.2 Authentication System

**Owner**: Agent 2 (Security Architect) + Agent 3 (Backend Engineer)
**Effort**: 5–6 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/core/security.py` | Password hashing (bcrypt), JWT creation/verification, token schemas |
| `backend/app/schemas/auth.py` | `LoginRequest`, `RegisterRequest`, `TokenResponse`, `PasswordResetRequest` |
| `backend/app/services/auth_service.py` | Registration, login, logout, token refresh, password reset logic |
| `backend/app/api/v1/endpoints/auth.py` | `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/refresh`, `/auth/password-reset`, `/auth/password-reset/confirm` |
| `backend/app/core/rate_limit.py` | Redis-based rate limiter middleware |
| `backend/tests/unit/test_security.py` | Password hashing, JWT encode/decode |
| `backend/tests/integration/test_auth.py` | Full auth flow tests against DB |

**Acceptance criteria**:
- User can register, login, receive JWT access + refresh tokens, refresh expired access tokens, and logout (token revoked).
- Passwords are bcrypt-hashed; plaintext never stored or logged.
- Login endpoint is rate-limited (5 failures per minute per IP).
- Password reset generates a time-limited token sent via configurable transport (email stub for Phase 1).
- JWT tokens include `user_id`, `tenant_id`, `role`, `exp`; verified on every protected endpoint.
- All auth tests pass in CI.

---

### 1.3 RBAC & Authorization

**Owner**: Agent 2 (Security Architect) + Agent 3 (Backend Engineer)
**Effort**: 3–4 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/core/authorization.py` | Permission checker, `require_permission` dependency, `require_role` dependency |
| `backend/app/schemas/role.py` | Role/permission schemas |
| `backend/app/services/role_service.py` | Role CRUD, permission assignment |
| `backend/app/api/v1/endpoints/roles.py` | Role management endpoints (admin only) |
| `backend/tests/unit/test_authorization.py` | Permission matrix tests |
| `backend/tests/security/test_rbac.py` | Privilege escalation attempt tests |

**Default roles** (seeded in migration):

| Role | Permissions |
|------|------------|
| `org_admin` | All permissions within tenant |
| `security_manager` | Manage compliance, risks, evidence, integrations, remediation; read users |
| `engineer` | View compliance, manage remediation assigned to self, upload evidence |
| `auditor` | Read-only access to compliance, evidence, risks, audit logs |

**Acceptance criteria**:
- Every API endpoint beyond `/health`, `/auth/*` requires authentication and authorization.
- `require_permission("compliance:write")` decorator denies requests lacking the permission with 403.
- Default-deny: unlisted permissions are denied.
- Privilege escalation tests verify that `engineer` cannot access `org_admin` endpoints.
- Role assignments are scoped per-tenant (same user can have different roles in different tenants).

---

### 1.4 Multi-Tenant Architecture

**Owner**: Agent 2 (Security Architect) + Agent 3 (Backend Engineer)
**Effort**: 4–5 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/core/tenant.py` | Tenant context manager, middleware to extract tenant from JWT and set DB session variable |
| `backend/app/services/tenant_service.py` | Tenant CRUD, invitation management |
| `backend/app/schemas/tenant.py` | Tenant schemas |
| `backend/app/api/v1/endpoints/tenants.py` | Tenant management endpoints |
| `backend/tests/security/test_tenant_isolation.py` | **Critical**: cross-tenant access tests |

**Acceptance criteria**:
- Creating a user with a new organization creates a `Tenant` and `Membership` with `org_admin` role.
- Tenant ID is resolved exclusively from the authenticated JWT, never from request body or query parameters.
- PostgreSQL RLS policies prevent queries from returning rows belonging to other tenants, even if application code has a bug.
- `test_tenant_isolation.py` creates Tenant A and Tenant B, then systematically attempts to read/write/delete Tenant B's resources using Tenant A's credentials — all attempts must return 403 or empty results.
- Celery tasks carry `tenant_id` in task kwargs; worker sets DB session tenant context before executing.

---

### 1.5 Audit Logging

**Owner**: Agent 3 (Backend Engineer)
**Effort**: 2 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/services/audit_service.py` | `record_event(tenant_id, user_id, action, resource_type, resource_id, details, ip_address)` |
| `backend/app/core/logging.py` | structlog configuration, JSON formatter, sensitive-field redaction |
| `backend/app/api/v1/endpoints/audit.py` | Audit log query endpoint (admin/auditor only), paginated, filterable |
| `backend/tests/unit/test_audit.py` | Event recording and query tests |

**Logged events**: `user.login`, `user.login_failed`, `user.logout`, `user.created`, `user.invited`, `role.changed`, `tenant.created`, `tenant.settings_changed`, `integration.created`, `integration.deleted`, `evidence.uploaded`, `evidence.accessed`, `evidence.deleted`, `risk.created`, `risk.updated`, `control.status_changed`, `remediation.completed`, `admin.action`.

**Acceptance criteria**:
- Every auth and authorization event is automatically recorded without requiring explicit calls from endpoint code (middleware/hook-based).
- Audit records are append-only; no UPDATE or DELETE operations are permitted on the `audit_events` table (enforced by DB trigger or application constraint).
- Structured JSON logs include `tenant_id`, `user_id`, `action`, `timestamp`, `ip_address` but never include passwords, tokens, or credentials.
- Audit query endpoint supports filtering by `action`, `user_id`, `resource_type`, `date_range` with cursor-based pagination.

---

### 1.6 Frontend Foundation

**Owner**: Agent 4 (Frontend Engineer)
**Effort**: 6–7 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `frontend/src/lib/api.ts` | API client with auth header injection, token refresh interceptor |
| `frontend/src/lib/auth.ts` | Auth context provider, `useAuth` hook, token storage (httpOnly cookie or secure memory) |
| `frontend/src/types/api.ts` | Shared API response types |
| `frontend/src/components/layout/Sidebar.tsx` | Main navigation sidebar (13 nav items per spec) |
| `frontend/src/components/layout/Header.tsx` | Top bar with user menu, tenant switcher, notifications |
| `frontend/src/components/layout/AppLayout.tsx` | Authenticated layout wrapper |
| `frontend/src/app/(auth)/login/page.tsx` | Login page |
| `frontend/src/app/(auth)/register/page.tsx` | Registration page |
| `frontend/src/app/(auth)/forgot-password/page.tsx` | Password reset page |
| `frontend/src/app/(dashboard)/layout.tsx` | Dashboard layout using AppLayout |
| `frontend/src/app/(dashboard)/page.tsx` | Overview/dashboard page (placeholder) |
| `frontend/src/components/ui/Button.tsx` | Base button component |
| `frontend/src/components/ui/Input.tsx` | Form input component |
| `frontend/src/components/ui/Card.tsx` | Card component |
| `frontend/src/components/ui/Table.tsx` | Data table with pagination, sorting |
| `frontend/src/components/ui/Badge.tsx` | Status/severity badge |
| `frontend/src/components/ui/Modal.tsx` | Modal dialog |
| `frontend/src/components/ui/Toast.tsx` | Toast notification |
| `frontend/src/components/common/SeverityBadge.tsx` | Critical/High/Medium/Low/Info badge |
| `frontend/src/components/common/EmptyState.tsx` | Empty state placeholder |
| `frontend/src/components/common/LoadingState.tsx` | Loading skeleton |
| `frontend/src/components/common/ErrorState.tsx` | Error display |

**Acceptance criteria**:
- Login, register, and forgot-password pages render, validate inputs (Zod + React Hook Form), and communicate with the backend API.
- Authenticated routes redirect to `/login` if no valid token is present.
- Sidebar navigation shows all 13 primary nav items; items are grouped logically.
- All UI components follow the daisyUI `secureops` theme; dark mode toggles correctly.
- Responsive: sidebar collapses on mobile; pages are usable at 375px width.
- Loading, error, and empty states exist for every data-fetching page.

---

### 1.7 Docker & CI

**Owner**: Agent 8 (DevOps & Platform Engineer)
**Effort**: 2–3 days

**Files to create/update**:

| Path | Purpose |
|------|---------|
| `docker-compose.yml` | Updated with working health checks, volume mounts, env vars |
| `backend/Dockerfile` | Production-grade: multi-stage, non-root, minimal image |
| `frontend/Dockerfile` | Production-grade: multi-stage standalone build |
| `scripts/init-db.sh` | Database initialization + RLS setup script |
| `scripts/seed-dev.sh` | Development seed data (test tenant, admin user) |
| `.github/workflows/ci.yml` | Updated: backend lint → backend test → frontend lint → frontend test → security scan |
| `docs/devops/LOCAL_SETUP.md` | Developer onboarding: prerequisites, clone, docker compose up, seed, access |

**Acceptance criteria**:
- `docker compose up -d` starts all services (db, redis, backend, worker, frontend) and they pass health checks within 60 seconds.
- `scripts/seed-dev.sh` creates a test tenant and admin user for local development.
- CI pipeline passes on a clean checkout: ruff, mypy, pytest, eslint, tsc, vitest, trivy fs scan, gitleaks.
- Backend and frontend containers run as non-root.
- `docs/devops/LOCAL_SETUP.md` is sufficient for a new developer to go from clone to running application.

---

### Phase 1 — Total Estimated Effort

| Work Item | Effort (days) |
|-----------|---------------|
| 1.1 Backend Core | 5–6 |
| 1.2 Authentication | 5–6 |
| 1.3 RBAC & Authorization | 3–4 |
| 1.4 Multi-Tenant Architecture | 4–5 |
| 1.5 Audit Logging | 2 |
| 1.6 Frontend Foundation | 6–7 |
| 1.7 Docker & CI | 2–3 |
| **Total (sequential)** | **27–33 days** |
| **Total (parallel, 3 agents)** | **~12–15 days** |

---

## 3. Phase 2 — GRC Engine (Detailed)

### 2.1 Framework Registry & Control Library

**Owner**: Agent 3 (Backend Engineer)
**Effort**: 4–5 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/models/framework.py` | `Framework`, `FrameworkVersion`, `Control`, `ControlMapping` models |
| `backend/app/schemas/framework.py` | Framework/control schemas |
| `backend/app/services/framework_service.py` | Framework CRUD, control library, mapping management |
| `backend/app/api/v1/endpoints/frameworks.py` | Framework and control endpoints |
| `backend/alembic/versions/002_framework_tables.py` | Migration for framework tables |
| `backend/tests/unit/test_framework_service.py` | Framework logic tests |
| `backend/tests/integration/test_framework_api.py` | API integration tests |

**Acceptance criteria**:
- Framework registry supports versioned frameworks (e.g., ISO 27001:2022 vs. ISO 27001:2013).
- Controls belong to a framework version; a single control can map to controls in other frameworks (many-to-many via `ControlMapping`).
- Controls are not hardcoded; they are data-driven and loadable from seed files.
- Framework/control endpoints are tenant-scoped for custom controls; global frameworks are read-only to tenants.
- Pagination and filtering work on the control library (100+ controls per framework).

---

### 2.2 SOC 2 Framework Data

**Owner**: Agent 1 (Product Architect) + Agent 3
**Effort**: 2–3 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/data/frameworks/soc2_2017.json` | SOC 2 Trust Services Criteria seed data |
| `backend/app/services/seed/soc2_seeder.py` | SOC 2 framework seeder |
| `backend/tests/unit/test_soc2_seed.py` | Validate seed data structure and completeness |

**Acceptance criteria**:
- SOC 2 Trust Services Criteria (CC1–CC9, availability, processing integrity, confidentiality, privacy) are seeded with category, ID, title, and description.
- Controls use permitted identifiers and general descriptions (no verbatim copyrighted criteria text without appropriate rights).
- Seeder is idempotent — running twice does not duplicate data.
- Each criterion has defined evidence requirements.

---

### 2.3 ISO 27001:2022 Framework Data

**Owner**: Agent 1 (Product Architect) + Agent 3
**Effort**: 2–3 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/data/frameworks/iso27001_2022.json` | ISO 27001:2022 Annex A controls seed data |
| `backend/app/services/seed/iso27001_seeder.py` | ISO 27001 seeder |
| `backend/tests/unit/test_iso27001_seed.py` | Validate seed data |

**Acceptance criteria**:
- ISO 27001:2022 Annex A controls (93 controls across 4 themes) are seeded with clause, ID, title, and description.
- Cross-framework mappings to SOC 2 criteria are defined where applicable.
- Same licensing caution as SOC 2: use permitted identifiers and general descriptions.
- Seeder is idempotent.

---

### 2.4 Control Status Tracking & Gap Assessment

**Owner**: Agent 3 (Backend Engineer)
**Effort**: 3–4 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/models/control_status.py` | `TenantControlStatus` model (tenant-specific control implementation state) |
| `backend/app/schemas/control_status.py` | Control status schemas |
| `backend/app/services/control_status_service.py` | Status tracking, gap calculation, compliance scoring |
| `backend/app/api/v1/endpoints/control_status.py` | Control status CRUD, gap assessment endpoint |
| `backend/tests/unit/test_gap_assessment.py` | Gap calculation logic |
| `backend/tests/integration/test_control_status_api.py` | API tests |

**Acceptance criteria**:
- Each tenant can track implementation status per control: `not_started`, `in_progress`, `implemented`, `not_applicable`, with `effectiveness` rating.
- Controls have an assigned owner (user within tenant).
- Gap assessment endpoint returns: total controls, implemented, in-progress, gaps, compliance percentage — per framework.
- Compliance score is clearly labeled as internal readiness; never presented as formal certification.
- Status changes generate audit events.

---

### 2.5 Risk Register

**Owner**: Agent 3 (Backend Engineer)
**Effort**: 3–4 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/models/risk.py` | `Risk` model with scoring fields |
| `backend/app/schemas/risk.py` | Risk schemas |
| `backend/app/services/risk_service.py` | Risk CRUD, scoring, treatment tracking |
| `backend/app/api/v1/endpoints/risks.py` | Risk register endpoints |
| `backend/app/models/risk_control.py` | `RiskControl` join table linking risks to controls |
| `backend/tests/unit/test_risk_scoring.py` | Scoring logic tests |
| `backend/tests/integration/test_risk_api.py` | API tests |
| `frontend/src/app/(dashboard)/risks/page.tsx` | Risk register page |
| `frontend/src/app/(dashboard)/risks/[id]/page.tsx` | Risk detail page |
| `frontend/src/components/risks/RiskMatrix.tsx` | Likelihood × Impact heat map |
| `frontend/src/components/risks/RiskForm.tsx` | Risk create/edit form |

**Acceptance criteria**:
- Risks have: title, description, category, likelihood (1–5), impact (1–5), inherent score (L×I), treatment (accept/mitigate/transfer/avoid), residual likelihood, residual impact, residual score, owner, review date.
- Every risk has an assigned owner and a review schedule.
- Risks can be linked to controls (many-to-many) and to remediation tasks.
- Risk changes (score updates, treatment changes, owner changes) generate audit events with before/after values.
- Frontend displays a filterable risk register table and a visual risk matrix (heat map).

---

### 2.6 Evidence Management

**Owner**: Agent 3 (Backend Engineer) + Agent 4 (Frontend Engineer)
**Effort**: 4–5 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/models/evidence.py` | `Evidence`, `EvidenceCollectionRun` models |
| `backend/app/models/control_evidence.py` | `ControlEvidence` join table |
| `backend/app/schemas/evidence.py` | Evidence schemas |
| `backend/app/services/evidence_service.py` | Upload, download (signed URL), versioning, approval, integrity verification |
| `backend/app/services/storage/base.py` | `StorageBackend` abstract interface |
| `backend/app/services/storage/local.py` | Local filesystem backend (dev) |
| `backend/app/services/storage/azure_blob.py` | Azure Blob Storage backend |
| `backend/app/services/storage/s3.py` | S3-compatible backend |
| `backend/app/api/v1/endpoints/evidence.py` | Evidence CRUD, upload, download endpoints |
| `backend/tests/unit/test_evidence_service.py` | Evidence logic tests |
| `backend/tests/security/test_evidence_access.py` | Cross-tenant evidence access tests |
| `frontend/src/app/(dashboard)/evidence/page.tsx` | Evidence list page |
| `frontend/src/app/(dashboard)/evidence/[id]/page.tsx` | Evidence detail page |
| `frontend/src/components/evidence/EvidenceUpload.tsx` | Upload component with drag-and-drop |
| `frontend/src/components/evidence/EvidenceTimeline.tsx` | Version history timeline |

**Acceptance criteria**:
- Evidence upload validates file type (allowlist), size (configurable, default 50 MB), and computes SHA-256 integrity hash.
- Evidence is stored via the storage adapter interface; local, Azure Blob, and S3 backends are implemented.
- Evidence is linked to controls (many-to-many via `ControlEvidence`) with a `collected_at` timestamp.
- Evidence supports versioning: uploading a new version preserves the previous version. Historical evidence is never silently overwritten.
- Download generates a short-lived signed URL (or direct stream for local); tenant ownership is verified before download. Access is audit-logged.
- Evidence has approval states: `pending`, `approved`, `rejected`, with approver and timestamp.
- Cross-tenant evidence access test: Tenant A cannot download or list Tenant B's evidence.

---

### 2.7 Compliance Dashboard

**Owner**: Agent 4 (Frontend Engineer)
**Effort**: 4–5 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `frontend/src/app/(dashboard)/compliance/page.tsx` | Compliance overview — framework cards with readiness scores |
| `frontend/src/app/(dashboard)/compliance/[frameworkId]/page.tsx` | Framework detail — controls list with status |
| `frontend/src/app/(dashboard)/compliance/[frameworkId]/controls/[controlId]/page.tsx` | Control detail — status, evidence, risks, owner |
| `frontend/src/components/compliance/FrameworkCard.tsx` | Framework summary card with progress ring |
| `frontend/src/components/compliance/ControlTable.tsx` | Control list with status filters |
| `frontend/src/components/compliance/GapSummary.tsx` | Gap assessment visualization |
| `frontend/src/components/dashboard/ComplianceOverview.tsx` | Dashboard widget |
| `frontend/src/components/dashboard/RiskOverview.tsx` | Dashboard widget |
| `frontend/src/components/dashboard/EvidenceOverview.tsx` | Dashboard widget |
| `backend/app/api/v1/endpoints/dashboard.py` | Aggregated dashboard stats endpoint |

**Acceptance criteria**:
- Compliance dashboard shows each framework with a readiness progress ring and control status breakdown (implemented / in-progress / gaps / N/A).
- Framework detail page lists all controls with filterable status columns, assigned owner, linked evidence count, and linked risks.
- Control detail page shows full status, evidence timeline, linked risks, and edit capability for authorized roles.
- Main dashboard (`/`) shows summary widgets: compliance overview, risk heat map, recent evidence, and recent audit events.
- Dashboard data endpoint loads in under 2 seconds with 200 controls and 50 risks (per performance targets).

---

### 2.8 Policy Management (Basic)

**Owner**: Agent 3 (Backend Engineer) + Agent 4 (Frontend Engineer)
**Effort**: 2–3 days

**Files to create**:

| Path | Purpose |
|------|---------|
| `backend/app/models/policy.py` | `Policy` model with versioning |
| `backend/app/schemas/policy.py` | Policy schemas |
| `backend/app/services/policy_service.py` | Policy CRUD, versioning, approval |
| `backend/app/api/v1/endpoints/policies.py` | Policy endpoints |
| `frontend/src/app/(dashboard)/policies/page.tsx` | Policy list page |
| `frontend/src/app/(dashboard)/policies/[id]/page.tsx` | Policy detail/editor |

**Acceptance criteria**:
- Policies have: title, body (rich text/markdown), category, status (`draft`, `published`, `archived`), version number, owner, approval state.
- Publishing a new version preserves the previous version.
- Policies can be linked to controls.
- Only `security_manager` and `org_admin` can create/edit policies; all roles can view published policies.

---

### Phase 2 — Total Estimated Effort

| Work Item | Effort (days) |
|-----------|---------------|
| 2.1 Framework Registry & Control Library | 4–5 |
| 2.2 SOC 2 Framework Data | 2–3 |
| 2.3 ISO 27001:2022 Framework Data | 2–3 |
| 2.4 Control Status & Gap Assessment | 3–4 |
| 2.5 Risk Register | 3–4 |
| 2.6 Evidence Management | 4–5 |
| 2.7 Compliance Dashboard | 4–5 |
| 2.8 Policy Management | 2–3 |
| **Total (sequential)** | **24–32 days** |
| **Total (parallel, 3 agents)** | **~10–14 days** |

---

## 4. Phases 3–6 (High-Level)

### Phase 3 — Cloud Security (3 weeks)

**Key work items**:
1. Prowler integration adapter — containerized execution, JSON output parsing, finding normalization.
2. Azure cloud connector — tenant-provided credentials (encrypted), read-only RBAC role, account validation.
3. AWS cloud connector — IAM role assumption, cross-account access, credential rotation.
4. Normalized finding model — all scanner output mapped to internal `Finding` with severity, resource, remediation.
5. Asset inventory — cloud resources discovered during scans, stored with metadata.
6. Cloud security dashboard — findings by severity, resource, provider; historical trend.

**Technical risks**:
- Prowler execution can take 30+ minutes for large AWS accounts — need timeouts, progress tracking, and cancellation.
- Credential storage for customer cloud accounts is the highest-sensitivity data in the system.
- Scanner container isolation — prevent escape or cross-tenant data access.

**Dependencies**: Phase 1 (tenant architecture, auth, workers), Phase 2 (control mappings for linking findings to controls).

---

### Phase 4 — Vulnerability & Remediation (2–3 weeks)

**Key work items**:
1. Trivy integration adapter — container/filesystem/dependency scanning.
2. Vulnerability normalization — CVE tracking, severity (CVSS), affected assets, deduplication.
3. DefectDojo evaluation — optional REST API integration for advanced dedup and aggregation.
4. Remediation workflows — create tasks from findings/vulnerabilities, assign owners, set SLAs, track progress, verify resolution.
5. Remediation dashboard — open tasks, overdue SLAs, resolution rates.
6. Finding-to-control linking — security findings provide evidence for control effectiveness.

**Technical risks**:
- Vulnerability deduplication across multiple scanners is non-trivial; need robust matching logic.
- SLA tracking requires reliable background scheduling.

**Dependencies**: Phase 1 (foundation), Phase 3 (finding model and scanner adapter pattern).

---

### Phase 5 — AI & Reporting (2 weeks)

**Key work items**:
1. AI service adapter — abstract interface supporting multiple LLM providers (Claude API preferred).
2. Finding explanation — AI-generated plain-language explanations for security findings.
3. Risk summaries — AI-generated executive summaries for the risk register.
4. Compliance report generation — PDF/HTML reports for auditors with framework status, evidence, gaps.
5. Executive dashboard — high-level KPIs for leadership (compliance %, open risks, SLA compliance, trend).
6. Policy draft assistance — AI suggests policy content based on framework requirements.

**Technical risks**:
- AI responses must be flagged as suggestions, never as authoritative compliance determinations.
- Must not send customer evidence or credentials to external AI without tenant authorization.
- Report generation for large tenants (1000+ findings) needs background processing.

**Dependencies**: Phase 2 (GRC data to report on), Phase 3/4 (findings and vulnerabilities to explain).

---

### Phase 6 — Commercial Readiness (3–4 weeks)

**Key work items**:
1. Subscription management — plans, limits, billing integration (Stripe).
2. MSP multi-tenant management — MSP admins managing multiple customer tenants.
3. Vendor risk management — vendor register, assessments, questionnaires.
4. Comprehensive security testing — pen test prep, OWASP ASVS validation, cross-tenant audit.
5. Performance testing — load test with concurrent tenants, large datasets, concurrent scans.
6. Documentation completion — all docs from Section 17 of the master prompt.
7. Deployment automation — Terraform for staging/production, monitoring dashboards, runbooks.
8. Data export/portability — tenant data export for GDPR and customer requirements.

**Technical risks**:
- Billing integration touches payment data — PCI considerations.
- MSP architecture adds a third dimension to access control (MSP → Customer Tenant → User).
- Performance under realistic load has not been validated until this phase.

**Dependencies**: All prior phases.

---

## 5. Agent Assignment Matrix

| Agent | Role | Phase 1 Items | Phase 2 Items |
|-------|------|---------------|---------------|
| **1** | Product Architect | Architecture review | 2.2, 2.3 (framework data), 2.7 (dashboard specs) |
| **2** | Security Architect | 1.2, 1.3, 1.4 (security design) | Security review of all Phase 2 |
| **3** | Backend Engineer | 1.1, 1.2, 1.3, 1.4, 1.5 | 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.8 |
| **4** | Frontend Engineer | 1.6 | 2.5 (UI), 2.6 (UI), 2.7, 2.8 (UI) |
| **5** | Cloud Security Engineer | — | — (starts Phase 3) |
| **6** | Vulnerability Engineer | — | — (starts Phase 4) |
| **7** | QA & Reliability | Test review for 1.2, 1.4 | Tests for 2.4, 2.5, 2.6 |
| **8** | DevOps & Platform | 1.7 | CI updates, monitoring |
| **9** | Independent Code Reviewer | Phase 1 final review | Phase 2 final review |

**Parallelization plan for Phase 1**:
- **Stream A** (Agent 3): Backend Core → Authentication → RBAC → Multi-Tenant → Audit Logging (sequential — each builds on prior)
- **Stream B** (Agent 4): Frontend Foundation (independent of backend implementation order; uses API stubs/mocks)
- **Stream C** (Agent 8): Docker & CI (independent; enables integration testing)

Streams B and C run in parallel with Stream A from day 1.

---

## 6. Technical Risk Register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|------|-----------|--------|------------|-------|
| R1 | Cross-tenant data leakage | Low | Critical | PostgreSQL RLS + service-layer checks + automated cross-tenant tests in CI | Agent 2 |
| R2 | Cloud credential exposure | Low | Critical | Envelope encryption, short-lived tokens, credential redaction in logs, no credentials in scanner output | Agent 2 |
| R3 | Scanner resource exhaustion | Medium | High | Container resource limits (CPU/memory), execution timeouts, queue concurrency limits, per-tenant rate limiting | Agent 5 |
| R4 | Cloud provider API rate limits during scans | Medium | Medium | Exponential backoff, scan scheduling, provider-specific rate limit awareness | Agent 5 |
| R5 | Framework/control data licensing issues | Medium | High | Use permitted identifiers only, general descriptions, legal review for standards text, customer-supplied content model | Agent 1 |
| R6 | Evidence storage scaling | Low | Medium | Object storage backends (Azure Blob/S3), streaming uploads, configurable retention/deletion policies | Agent 3 |
| R7 | Celery worker reliability under load | Medium | Medium | Idempotent tasks, dead-letter queues, worker monitoring, graceful shutdown, retry with exponential backoff + jitter | Agent 8 |
| R8 | JWT/session security vulnerabilities | Low | High | Follow OWASP session management guidelines, short-lived access tokens, secure refresh token rotation, rate limiting | Agent 2 |
| R9 | Database migration failures on production | Low | High | Online-safe migrations only, no table locks, backward-compatible changes, migration testing in CI, rollback plans | Agent 3 |
| R10 | AI service sends sensitive data externally | Medium | High | Tenant-level AI opt-in, data classification check before AI calls, no evidence/credentials sent by default, audit logging of AI requests | Agent 2 |

---

## 7. Definition of Done

### Feature Done

A feature is complete when ALL of the following are true:

- [ ] Backend implementation passes all unit and integration tests.
- [ ] Frontend implementation renders correctly and handles loading/error/empty states.
- [ ] Database migration runs cleanly on an empty DB and on the current schema.
- [ ] Input validation is implemented (Pydantic for API, Zod for frontend forms).
- [ ] Authentication is required (no anonymous access to business endpoints).
- [ ] Authorization is enforced (permission checked, default-deny).
- [ ] Tenant isolation is verified (data is scoped, RLS active).
- [ ] Error handling returns consistent error responses.
- [ ] Security-relevant actions are audit-logged.
- [ ] Tests exist and pass: unit + integration + at least one security test.
- [ ] API endpoint is documented in OpenAPI.
- [ ] Code review completed by Agent 9.

### Phase Done

A phase is complete when:

- [ ] All features in the phase meet the Feature Done criteria.
- [ ] All tests pass in CI (lint + type check + unit + integration + security).
- [ ] Docker Compose environment works end-to-end for the phase's functionality.
- [ ] No critical or high security findings remain unresolved.
- [ ] Documentation is updated for new features.
- [ ] Cross-tenant isolation tests pass for all new tenant-scoped resources.
- [ ] Independent code review (Agent 9) has approved the phase.

### Release Candidate Done

Per Section 19 of the master prompt:

1. [ ] Successful automated test suite.
2. [ ] Successful build (Docker images).
3. [ ] Successful database migration test (empty DB and upgrade path).
4. [ ] No unresolved critical security findings.
5. [ ] No leaked secrets (Gitleaks clean).
6. [ ] Reviewed dependency and licensing status (LICENSE_REGISTER.md current).
7. [ ] Verified tenant isolation (cross-tenant test suite passes).
8. [ ] Verified backup restoration (DB dump and restore tested).
9. [ ] Verified background job reliability (worker restart test).
10. [ ] Documented deployment procedure.
11. [ ] Documented known limitations.
12. [ ] Security review sign-off (Agent 2 + Agent 9).

---

## 8. MVP Boundary

### In the MVP (Phase 1 + Phase 2)

| Category | Included |
|----------|----------|
| **Tenancy** | Multi-tenant with RLS, organization creation, user management, invitations, RBAC (4 roles) |
| **Auth** | JWT login/register, password reset, rate limiting, session management |
| **Compliance** | SOC 2 + ISO 27001:2022 frameworks, control library, control status tracking, gap assessment, compliance dashboard |
| **Risk** | Risk register, likelihood/impact scoring, treatment tracking, risk-control linking, risk matrix visualization |
| **Evidence** | Manual upload, file validation, integrity hashing, versioning, approval workflow, control linking, storage adapters |
| **Policy** | Basic policy CRUD, versioning, approval states |
| **Audit** | Append-only audit logging, audit log viewer |
| **UI** | Auth pages, compliance dashboard, risk register, evidence management, policy list, responsive, dark mode |
| **Infrastructure** | Docker Compose dev environment, CI pipeline (lint + test + security scan) |

### NOT in the MVP

| Category | Excluded (deferred to later phase) |
|----------|-------------------------------------|
| **Cloud Security** | Prowler integration, cloud account connections, asset discovery, cloud findings (Phase 3) |
| **Vulnerability Management** | Trivy integration, CVE tracking, vulnerability scanning (Phase 4) |
| **Remediation** | Automated remediation workflows, SLA tracking (Phase 4) |
| **AI** | AI assistant, finding explanations, policy drafting, report generation (Phase 5) |
| **SSO/MFA** | SAML/OIDC SSO, MFA enforcement (Phase 1 structure, Phase 2–3 implementation) |
| **MSP** | Multi-customer MSP management (Phase 6) |
| **Billing** | Subscription management, Stripe integration, plan limits (Phase 6) |
| **Vendor Risk** | Vendor register, assessments, questionnaires (Phase 6) |
| **Advanced Reporting** | PDF/HTML compliance reports, executive dashboards (Phase 5) |
| **Terraform** | Production infrastructure-as-code (Phase 6) |
| **Monitoring** | Grafana/Prometheus dashboards, alerting (Phase 6) |
| **Additional Frameworks** | NIST CSF, CIS Controls, GDPR, HIPAA, PCI DSS (post-MVP) |
| **Additional Cloud Providers** | GCP, Kubernetes, M365, GitHub, Cloudflare (post-Phase 3) |
| **Email Notifications** | Email delivery integration (Phase 3+) |
| **Data Export** | Tenant data export, GDPR portability (Phase 6) |
| **Auto-Remediation** | Automatic cloud infrastructure remediation (not in any current phase — future consideration) |

### Scope Creep Warning

If a feature request does not appear in the MVP "Included" table above, it must be explicitly approved and scheduled into a future phase before implementation begins. Phase 1 and Phase 2 work items are fixed unless a blocking issue is discovered during implementation.
