# SecureOps — Threat Model

**Document version:** 0.1.0
**Last updated:** 2026-11-19
**Methodology:** STRIDE
**Scope:** Full application stack including multi-tenant SaaS, cloud integrations, and scanner engines.

---

## 1. System Overview

SecureOps is a multi-tenant B2B SaaS platform that manages security operations, compliance (SOC 2, ISO 27001), risk, and audit evidence for customer organizations. It connects to customer cloud accounts (AWS, Azure) using stored credentials, runs security scanners (Prowler, Trivy) as containerized workers, stores compliance evidence in object storage, and optionally calls external AI services for security analysis.

Each tenant is an organization with its own users, cloud accounts, findings, evidence, and compliance data. A single PostgreSQL database stores all tenants, isolated via row-level security and application-enforced tenant scoping. Background workers process security scans that require access to customer cloud credentials.

The core security contract: **no tenant can access, infer, or influence another tenant's data, credentials, or operations.**

---

## 2. Trust Boundaries

```
                         ┌──────────────────────────────────────────────────────┐
                         │                    INTERNET                          │
                         └──────────┬───────────────────────┬───────────────────┘
                                    │                       │
                                    ▼                       ▼
                         ┌──────────────────┐    ┌──────────────────┐
                         │  Browser / User   │    │  API Consumers   │
                         └────────┬─────────┘    └────────┬─────────┘
                    ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │─ ─ ─ ─ TB1: Internet → App
                                  │                       │
                                  ▼                       ▼
                         ┌──────────────────────────────────────────┐
                         │              NEXT.JS FRONTEND            │
                         │          (SSR + Static Assets)           │
                         └────────────────────┬─────────────────────┘
                    ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─ TB2: Frontend → API
                                               │
                                               ▼
                         ┌──────────────────────────────────────────┐
                         │          FASTAPI BACKEND (API)           │
                         │    Auth │ RBAC │ Tenant Middleware        │
                         └──┬──────┬──────┬──────┬──────┬───────────┘
                            │      │      │      │      │
              ─ ─ ─ ─ ─ ─ ─│─ ─ ─ │─ ─ ─ │─ ─ ─ │─ ─ ─ │─ ─ ─ ─ ─ TB3: API → Internal
                            │      │      │      │      │
                            ▼      ▼      │      ▼      ▼
                    ┌───────────┐ ┌────┐  │  ┌───────┐ ┌─────────────┐
                    │PostgreSQL │ │Redis│  │  │Object │ │External AI  │
                    │  (RLS)    │ │    │  │  │Storage│ │  Service    │
                    └───────────┘ └──┬─┘  │  └───────┘ └─────────────┘
                                     │    │       ▲           TB6: API → AI ─ ─ ─
              ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │─ ─ │─ ─ ─ ─ TB5: Workers → Storage
                                     │    │
                                     ▼    ▼
                         ┌──────────────────────────────────────────┐
                         │           CELERY WORKERS                 │
                         └──────┬───────────────────┬───────────────┘
              ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ │─ ─ ─ TB4: Workers → External
                                │                   │
                   ┌────────────▼──┐          ┌─────▼──────────────┐
                   │Scanner Containers│        │Customer Cloud APIs │
                   │(Prowler, Trivy) │        │  (AWS, Azure)      │
                   └──────────────────┘        └────────────────────┘

TB1: Internet → Application boundary
TB2: Frontend → API boundary
TB3: API → Internal services (DB, Redis, Object Storage)
TB4: Workers → External systems (customer clouds)
TB5: Workers → Evidence storage
TB6: API → External AI services
```

---

## 3. STRIDE Analysis by Trust Boundary

### TB1: Internet → Application

| Threat | Category | Description | Severity |
|--------|----------|-------------|----------|
| T1.1 | **Spoofing** | Attacker impersonates a legitimate user via stolen credentials or session tokens. Brute-force attacks against login. | Critical |
| T1.2 | **Spoofing** | Attacker bypasses authentication by exploiting SSO/OIDC misconfiguration or token validation flaws. | Critical |
| T1.3 | **Tampering** | Man-in-the-middle modifies API requests if TLS termination is misconfigured. | High |
| T1.4 | **Repudiation** | User performs destructive actions (e.g., deleting evidence) and denies it; no audit trail proves otherwise. | Medium |
| T1.5 | **Information Disclosure** | Error responses leak internal stack traces, database schema, or tenant identifiers to unauthenticated callers. | Medium |
| T1.6 | **Denial of Service** | Unauthenticated flood of requests to login, registration, or public endpoints exhausts API capacity. | High |
| T1.7 | **Elevation of Privilege** | Attacker exploits registration flow to create an admin account, or crafts a JWT with elevated claims. | Critical |

### TB2: Frontend → API

| Threat | Category | Description | Severity |
|--------|----------|-------------|----------|
| T2.1 | **Spoofing** | CSRF attack causes authenticated user's browser to issue state-changing API calls. | High |
| T2.2 | **Tampering** | Attacker modifies frontend-supplied tenant_id or object IDs in API requests (IDOR). | Critical |
| T2.3 | **Tampering** | XSS in dashboard renders attacker-controlled content that steals session tokens or exfiltrates page data. | High |
| T2.4 | **Information Disclosure** | Frontend bundle exposes API keys, internal endpoints, or tenant enumeration data. | Medium |
| T2.5 | **Elevation of Privilege** | User manipulates frontend role/permission values sent to the backend; backend trusts them. | Critical |

### TB3: API → Internal Services (DB, Redis, Object Storage)

| Threat | Category | Description | Severity |
|--------|----------|-------------|----------|
| T3.1 | **Spoofing** | Compromised API server connects to database without mutual authentication; attacker substitutes a rogue DB. | Medium |
| T3.2 | **Tampering** | SQL injection through unsanitized input modifies or exfiltrates data across tenants. | Critical |
| T3.3 | **Tampering** | Attacker with Redis access poisons Celery task queue, injecting malicious job payloads. | High |
| T3.4 | **Information Disclosure** | Cross-tenant data leakage through missing or misconfigured RLS policies — the highest-impact risk in this system. | Critical |
| T3.5 | **Information Disclosure** | Cached data in Redis is accessible without tenant scoping; tenant A reads tenant B's cached dashboard. | High |
| T3.6 | **Information Disclosure** | Object storage evidence URLs are predictable or lack tenant authorization checks. | Critical |
| T3.7 | **Denial of Service** | Unbounded queries (e.g., fetching all findings without pagination) exhaust database connections. | Medium |

### TB4: Workers → Customer Cloud Accounts

| Threat | Category | Description | Severity |
|--------|----------|-------------|----------|
| T4.1 | **Spoofing** | Attacker retrieves stored cloud credentials from the database or worker memory and impersonates the customer. | Critical |
| T4.2 | **Tampering** | Malicious worker modifies scan parameters to expand scope beyond read-only, or targets wrong cloud account. | High |
| T4.3 | **Tampering** | Scanner output is manipulated between the container and the ingest pipeline, hiding real findings or injecting false ones. | High |
| T4.4 | **Repudiation** | No record of which scan touched which cloud resources and when; disputed scan activity cannot be verified. | Medium |
| T4.5 | **Information Disclosure** | Cloud credentials appear in scanner logs, worker stdout, or error messages. | Critical |
| T4.6 | **Information Disclosure** | Scanner results from tenant A's cloud are written to tenant B's finding store due to tenant context leak in async workers. | Critical |
| T4.7 | **Denial of Service** | Runaway scanner consumes all worker CPU/memory, blocking scans for other tenants. | High |
| T4.8 | **Elevation of Privilege** | Scanner container escapes isolation, accesses host filesystem, other containers, or the Docker socket. | Critical |

### TB5: Workers → Evidence Storage

| Threat | Category | Description | Severity |
|--------|----------|-------------|----------|
| T5.1 | **Tampering** | Evidence files are modified after collection; audit integrity is lost. | High |
| T5.2 | **Tampering** | Worker overwrites historical evidence with new collection, destroying audit trail. | High |
| T5.3 | **Information Disclosure** | Evidence download link for tenant A's document is accessible to tenant B user. | Critical |
| T5.4 | **Denial of Service** | Unrestricted upload size floods object storage, exhausting quota or budget. | Medium |

### TB6: API → External AI Services

| Threat | Category | Description | Severity |
|--------|----------|-------------|----------|
| T6.1 | **Information Disclosure** | Customer evidence content, finding details, or infrastructure specifics are sent to a third-party AI without customer consent. | Critical |
| T6.2 | **Tampering** | AI response is injected with prompt-injection payload that alters compliance assessment or marks a control as compliant. | High |
| T6.3 | **Spoofing** | AI service API key is leaked; attacker uses it to make calls on our behalf or to extract conversation history. | Medium |
| T6.4 | **Repudiation** | AI-generated compliance recommendation is acted upon without tracking who requested it and what data was sent. | Medium |

---

## 4. High-Risk Attack Surfaces

### 4.1 Multi-Tenant Boundary (CRITICAL)

**Why #1:** A single cross-tenant data leak destroys customer trust, triggers breach notification obligations, and is likely fatal to the business.

Attack vectors:
- Missing `WHERE tenant_id = :current_tenant` in any query.
- RLS policy not set on a new table.
- Background worker processes a job with stale or wrong tenant context.
- Redis cache key not namespaced by tenant.
- Object storage path traversal returns another tenant's evidence.
- API endpoint accepts tenant_id from request body instead of deriving from auth context.
- Database migration adds a table without RLS policy.
- Bulk operations (CSV export, report generation) aggregate across tenants.

### 4.2 Cloud Credential Storage and Usage

Customer cloud credentials (AWS access keys, Azure service principal secrets) are the most sensitive data in the system after customer evidence. Compromise grants an attacker read access (and potentially write access, if misconfigured) to the customer's entire cloud environment.

Attack vectors:
- Credentials stored in plaintext in the database.
- Credentials logged during scanner execution.
- Credentials accessible to any authenticated user via API (not just org admins).
- Credentials persisted in worker memory after scan completes.
- Credentials included in error payloads or crash dumps.
- Database backup contains unencrypted credentials.

### 4.3 Evidence Storage Integrity

Evidence files are the audit artifacts customers rely on. Unauthorized modification or access undermines the entire product's value proposition.

Attack vectors:
- Direct object storage access bypassing application authorization.
- Evidence URL enumeration or prediction.
- Missing integrity hash validation on retrieval.
- Silent overwrite of historical evidence versions.
- File upload containing executable content that triggers code execution during processing.

### 4.4 Scanner Container Isolation

Prowler and Trivy run as containers on the worker host. A container escape gives the attacker access to other tenants' scan processes, credentials in memory, and the host Docker socket.

Attack vectors:
- Container runs as root.
- Container has access to Docker socket (used for sibling containers).
- Container has unrestricted network egress.
- Container resource limits not set, enabling resource exhaustion.
- Scanner binary replaced with malicious version (supply chain).

### 4.5 AI Service Data Leakage

External AI calls carry customer-specific context. Without controls, every AI request potentially exfiltrates customer data to a third party.

Attack vectors:
- Evidence content included in AI prompt without redaction.
- Infrastructure details (IP addresses, hostnames, account IDs) sent to AI.
- AI responses cached without tenant isolation.
- No customer consent mechanism gates AI data processing.
- Prompt injection in finding descriptions causes AI to return misleading analysis.

### 4.6 Webhook and Integration Endpoints

Inbound webhooks (from Jira, Slack, CI/CD systems) accept data from external sources and must not be spoofable.

Attack vectors:
- Missing webhook signature verification.
- SSRF via user-configured callback URLs.
- Webhook payload contains malicious content processed unsafely.
- Webhook endpoint accessible without authentication.

---

## 5. Mitigation Strategy

### M1: Multi-Tenant Isolation

| Control | Implementation |
|---------|----------------|
| PostgreSQL Row-Level Security | Enable RLS on every tenant-owned table. Policy: `USING (tenant_id = current_setting('app.current_tenant_id')::uuid)`. |
| Tenant context middleware | FastAPI middleware sets `app.current_tenant_id` in the database session from the authenticated user's membership. Never from a request parameter. |
| Default-deny RLS | All new tables require `ALTER TABLE ... ENABLE ROW LEVEL SECURITY; ALTER TABLE ... FORCE ROW LEVEL SECURITY;` in the migration. A CI check verifies this. |
| Tenant-scoped cache keys | All Redis keys prefixed with `tenant:{tenant_id}:`. A wrapper enforces this. |
| Object storage path convention | Evidence stored at `/{tenant_id}/{evidence_id}/{version}/{filename}`. Authorization checked before signed-URL generation. |
| Cross-tenant integration tests | Test suite attempts to read/write tenant B resources using tenant A's authenticated session. Asserts 403 on every endpoint. |
| Migration lint | CI step scans every Alembic migration for new tables and asserts presence of RLS policy statements. |

### M2: Cloud Credential Protection

| Control | Implementation |
|---------|----------------|
| Envelope encryption | Credentials encrypted with a per-tenant data encryption key (DEK); DEKs encrypted with a master key (KEK) stored in a secrets manager (Azure Key Vault / AWS KMS). |
| Never log credentials | Structlog processor strips fields matching `*credential*`, `*secret*`, `*password*`, `*token*`, `*key*` patterns. |
| Credential access RBAC | Only org admin role can create/view/rotate integration credentials. API enforces this. |
| Short-lived credentials preferred | Documentation and UI recommend AWS IAM roles with external ID + STS assume-role, and Azure managed identity or short-lived service principal tokens. |
| Worker memory cleanup | After scan completes, credential references are explicitly cleared from worker task scope. |
| Audit credential access | Every credential read (for scan execution) is recorded in the audit log with user/worker identity, timestamp, and target account. |

### M3: Evidence Integrity

| Control | Implementation |
|---------|----------------|
| SHA-256 integrity hash | Computed at upload, stored in database. Verified on every download. |
| Versioned storage | Evidence is append-only. New collection creates a new version; old versions are never overwritten. |
| Signed download URLs | Short-lived (15 min), per-request signed URLs. No direct public access to storage. |
| File type validation | Allowlist of MIME types (PDF, PNG, JPG, CSV, JSON, TXT). Content-type sniffing validates actual content matches declared type. |
| Upload size limit | 50 MB default, configurable per tenant. |
| Antivirus scan | Uploaded files scanned via ClamAV or equivalent before persisting to evidence store. |
| Tenant ownership check | Download handler verifies `evidence.tenant_id == requesting_user.tenant_id` before generating signed URL. |

### M4: Scanner Container Isolation

| Control | Implementation |
|---------|----------------|
| Non-root containers | Scanner Dockerfiles use `USER 1000`. |
| No Docker socket mount | Workers launch scanner containers via Docker SDK using a restricted Docker API endpoint, not by mounting `/var/run/docker.sock`. |
| Resource limits | `--memory=2g --cpus=1.0 --pids-limit=256` on every scanner container. |
| Network restriction | Scanner containers run in a network with egress limited to cloud provider API endpoints. |
| Read-only filesystem | Scanner containers mount `/tmp` as tmpfs; root filesystem is read-only. |
| Image pinning | Scanner images pinned to specific digests in configuration; changes require a reviewed PR. |
| Execution timeout | Scans killed after configurable timeout (default: 30 minutes). |

### M5: AI Service Safeguards

| Control | Implementation |
|---------|----------------|
| Customer consent | AI features disabled per-tenant by default. Org admin must explicitly enable and accept data-processing terms. |
| Data minimization | AI prompts include only the minimum context: finding title, severity, control ID. Never raw evidence, credentials, or full infrastructure inventories. |
| PII/infrastructure redaction | Preprocessor strips IP addresses, hostnames, account IDs, email addresses before sending to AI. |
| Response validation | AI responses are treated as untrusted input. Never used to automatically change control status, approve evidence, or modify risk scores. |
| Audit logging | Every AI request/response pair logged with tenant, user, timestamp, and a hash of the prompt content. |
| Prompt injection defense | AI system prompts include explicit instructions to ignore embedded instructions in user-supplied data. Responses are validated against expected schema. |

### M6: Webhook Security

| Control | Implementation |
|---------|----------------|
| HMAC signature verification | All inbound webhooks verify the signature using a shared secret per integration. |
| URL allowlisting | Outbound webhook/callback URLs validated against an allowlist of permitted domains. No private IP ranges (SSRF prevention). |
| Input validation | Webhook payloads parsed through Pydantic schemas; unexpected fields are dropped. |
| Rate limiting | Per-integration rate limits on webhook endpoints. |

---

## 6. Risk Matrix

Likelihood: **1** (Rare) → **5** (Almost Certain)
Impact: **1** (Negligible) → **5** (Catastrophic)

| ID | Threat | Likelihood | Impact | Risk Score | Priority |
|----|--------|-----------|--------|------------|----------|
| T3.4 | Cross-tenant data leak via missing RLS | 3 | 5 | **15** | P0 |
| T4.1 | Cloud credential theft from database | 2 | 5 | **10** | P0 |
| T4.6 | Cross-tenant finding contamination in workers | 3 | 5 | **15** | P0 |
| T5.3 | Cross-tenant evidence access | 3 | 5 | **15** | P0 |
| T6.1 | Customer data sent to AI without consent | 2 | 5 | **10** | P0 |
| T3.2 | SQL injection | 2 | 5 | **10** | P1 |
| T4.8 | Scanner container escape | 1 | 5 | **5** | P1 |
| T1.1 | Credential stuffing / brute force | 4 | 3 | **12** | P1 |
| T2.2 | IDOR via manipulated object IDs | 3 | 4 | **12** | P1 |
| T4.5 | Credentials leaked in scanner logs | 3 | 4 | **12** | P1 |
| T2.3 | Stored XSS in dashboard | 2 | 4 | **8** | P1 |
| T5.1 | Evidence tampering post-collection | 2 | 4 | **8** | P2 |
| T1.6 | API DDoS / resource exhaustion | 3 | 3 | **9** | P2 |
| T4.7 | Scanner resource exhaustion (noisy neighbor) | 3 | 3 | **9** | P2 |
| T6.2 | Prompt injection via finding descriptions | 3 | 3 | **9** | P2 |

**P0** = Must be mitigated before first customer onboarding.
**P1** = Must be mitigated before public availability.
**P2** = Must be mitigated before scaling beyond pilot customers.

---

## 7. Security Testing Requirements

### 7.1 Automated Cross-Tenant Isolation Tests (P0)

Every API endpoint must have a test that:
1. Creates resources as Tenant A.
2. Authenticates as Tenant B.
3. Attempts to read, update, and delete Tenant A's resources.
4. Asserts 403 Forbidden or 404 Not Found on every attempt.

Implementation: `tests/security/test_tenant_isolation.py` with parametrized fixtures covering all resource types.

### 7.2 Database RLS Verification (P0)

A CI check must:
1. Parse every Alembic migration that creates a table with a `tenant_id` column.
2. Assert that the same migration includes `ENABLE ROW LEVEL SECURITY` and a policy creation.
3. Fail the build if any table is missing RLS.

Implementation: `scripts/check_rls_coverage.py` run in CI.

### 7.3 Credential Exposure Scanning (P0)

- Gitleaks runs on every PR to detect committed secrets.
- A unit test asserts that the structlog credential-stripping processor removes sensitive fields from sample log entries containing `password`, `secret_key`, `access_token`, and `connection_string` fields.
- Integration test verifies that a scan execution's log output (captured stdout) contains no credential material when a mock credential is provided.

### 7.4 IDOR Tests (P1)

For every endpoint accepting a resource ID:
1. Create a resource as User A.
2. Attempt to access it as User B (same tenant, insufficient role) → assert 403.
3. Attempt to access it as User C (different tenant) → assert 403/404.

Implementation: `tests/security/test_idor.py`.

### 7.5 Input Validation Tests (P1)

Parametrized tests submitting:
- SQL injection payloads in string fields.
- XSS payloads (`<script>`, event handlers, encoded variants) in text inputs.
- Path traversal (`../../../etc/passwd`) in file-related fields.
- Oversized payloads exceeding documented limits.

All must be rejected at the Pydantic validation layer or return a 422 without executing the payload.

Implementation: `tests/security/test_input_validation.py`.

### 7.6 Evidence Security Tests (P1)

- Upload a file as Tenant A. Attempt to download via direct URL manipulation as Tenant B. Assert failure.
- Upload a file exceeding size limit. Assert rejection.
- Upload an executable file (.exe, .sh, .bat). Assert rejection.
- Retrieve evidence and verify SHA-256 hash matches stored value.
- Attempt to overwrite an existing evidence version via API. Assert failure (append-only).

Implementation: `tests/security/test_evidence_security.py`.

### 7.7 Scanner Isolation Tests (P1)

- Verify scanner containers start with non-root user.
- Verify resource limits are applied (inspect container config).
- Verify scanner container cannot reach internal services (DB, Redis) on the network.
- Verify scan timeout enforcement by mocking a long-running scan.

Implementation: `tests/security/test_scanner_isolation.py` (integration tests requiring Docker).

### 7.8 Authentication and Session Tests (P1)

- Brute-force lockout: 10 failed logins trigger account lockout or escalating delays.
- Expired token rejection: API rejects access tokens past expiry.
- Revoked session rejection: After logout, the session token is rejected.
- MFA bypass: Authenticated session without MFA completion cannot access MFA-required endpoints.

Implementation: `tests/security/test_authentication.py`.

### 7.9 AI Data Leakage Tests (P2)

- Mock AI service call and assert that the outgoing request body does not contain IP addresses, hostnames, account IDs, or email addresses (regex scan of the prompt).
- Assert that AI features return 403 for tenants that have not enabled AI processing.
- Submit a finding description containing prompt-injection text; assert that the AI response handling does not alter any database records.

Implementation: `tests/security/test_ai_security.py`.

### 7.10 Performance/DoS Resilience (P2)

- Submit 1000 concurrent requests to the findings list endpoint; assert no 500 errors and p99 < 2s.
- Queue 100 scan jobs simultaneously; assert worker pool does not crash and jobs are processed (with backpressure).
- Submit an API request with a 100 MB body; assert rejection before full body is read.

Implementation: `tests/performance/test_resilience.py` (marked as `performance` to exclude from standard CI runs).

---

## Appendix: Review Schedule

This threat model must be reviewed and updated:
- When a new integration or trust boundary is added.
- When a new data store is introduced.
- When the tenant isolation mechanism is modified.
- Quarterly as a standing security review item.
- After any security incident.

Each review must be recorded in this document's version history with the reviewer, scope, and any changes made.
