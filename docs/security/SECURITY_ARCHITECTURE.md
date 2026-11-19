# SecureOps — Security Architecture

## Document Control

| Field | Value |
|-------|-------|
| Status | Draft |
| Version | 0.1.0 |
| Last Updated | 2026-11-19 |
| Classification | Internal |

---

## 1. Authentication

SecureOps uses JWT-based authentication with short-lived access tokens and longer-lived refresh tokens. No custom cryptographic primitives are used — all crypto operations rely on `python-jose` (JOSE/JWK standards) and the `bcrypt` library (cost 12, 72-byte input limit enforced; see ADR-004).

### Token Architecture

| Token | Lifetime | Storage | Purpose |
|-------|----------|---------|---------|
| Access token | 30 minutes | Memory / Authorization header | API request authentication |
| Refresh token | 7 days | HttpOnly secure cookie | Silent access token renewal |
| MFA challenge token | 5 minutes | Server-side session | Intermediate auth during MFA verification |
| Password reset token | 1 hour | Database (hashed) | One-time password reset |

### Token Flow

```
Client → POST /api/v1/auth/login { email, password }
Server → Validate credentials
       → If MFA enabled: return { mfa_challenge_token, mfa_required: true }
         Client → POST /api/v1/auth/mfa/verify { challenge_token, totp_code }
       → Issue access_token (body) + refresh_token (HttpOnly cookie)
       → Record audit event: AUTH_LOGIN_SUCCESS
```

### Access Token Claims

```python
{
    "sub": "<user_uuid>",           # user identifier
    "tid": "<tenant_uuid>",         # resolved tenant — authoritative for all downstream access
    "role": "security_manager",     # user's role within this tenant
    "iat": 1732000000,
    "exp": 1732001800,
    "jti": "<unique_token_id>"      # for revocation tracking
}
```

The `tid` claim is set at login based on the user's active membership. It is the **sole source of tenant identity** for every downstream operation. No API endpoint accepts a tenant identifier from query parameters, path variables, or request bodies for access-control purposes.

### Session Management

- **Revocation**: A `revoked_tokens` table tracks invalidated JTIs. Middleware checks this on every request. Token revocation propagates within one access-token lifetime (30 min max). For immediate revocation, a Redis-backed blocklist provides sub-second propagation.
- **Concurrent sessions**: Users may hold multiple active refresh tokens (e.g., browser + mobile). Each refresh token is tracked independently and revocable.
- **Session expiration**: Refresh tokens have absolute expiry. No indefinite "remember me." Idle timeout enforced via sliding window — if no refresh occurs within 24 hours, the refresh token is invalidated.
- **Logout**: `POST /api/v1/auth/logout` revokes the current refresh token and adds the access token JTI to the blocklist.

### Rate Limiting

| Endpoint | Limit | Window | Lockout |
|----------|-------|--------|---------|
| `/auth/login` | 5 attempts | 15 minutes | 30-minute lockout after 10 failed attempts per account |
| `/auth/mfa/verify` | 5 attempts | 5 minutes | Challenge token invalidated after 5 failures |
| `/auth/password/reset` | 3 requests | 1 hour | Per email address, not per IP |
| `/auth/register` | 10 requests | 1 hour | Per IP |

Rate limiting is implemented via Redis sliding window counters keyed by `(endpoint, identifier)`.

### Password Policy

- Minimum 12 characters
- Checked against HaveIBeenPwned k-anonymity API (SHA-1 prefix, no full hash sent)
- Bcrypt with cost factor 12
- Password history: last 5 hashes stored to prevent reuse

### MFA

- TOTP-based (RFC 6238) via `pyotp`
- Recovery codes: 10 single-use codes generated at MFA enrollment, stored as bcrypt hashes
- MFA enforcement: configurable per organization (optional, required for admins, required for all)

### SSO (Planned — Phase 2+)

- OIDC and SAML 2.0 via `authlib`
- SSO users skip local password authentication
- JIT provisioning: user accounts created on first SSO login, assigned a default role
- SSO-enforced organizations disable password login for non-admin users

### Account Recovery

- Password reset via time-limited token sent to registered email
- Reset tokens are stored hashed (SHA-256), single-use, expire in 1 hour
- Successful reset invalidates all existing sessions
- Recovery codes for MFA bypass (single-use, logged)

---

## 2. Authorization (RBAC)

SecureOps uses role-based access control with resource-level authorization checks. The system defaults to **deny** — every endpoint requires explicit permission.

### Role Hierarchy

| Role | Scope | Description |
|------|-------|-------------|
| `super_admin` | Platform | Platform operator. Manages all tenants. Not a customer-facing role. |
| `org_admin` | Tenant | Full control within one organization. Manages users, integrations, settings. |
| `security_manager` | Tenant | Manages compliance, risks, findings, evidence, remediation. Cannot manage users or billing. |
| `engineer` | Tenant | Views and responds to assigned findings and remediation tasks. Limited create/edit scope. |
| `auditor` | Tenant | Read-only access to compliance, evidence, and audit trails. Cannot modify data. |

### Permission Matrix

| Resource | Action | `super_admin` | `org_admin` | `security_manager` | `engineer` | `auditor` |
|----------|--------|:---:|:---:|:---:|:---:|:---:|
| **Users** | List / View | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Users** | Create / Invite | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Users** | Update role | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Users** | Delete / Deactivate | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Integrations** | List / View | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Integrations** | Create / Update | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Integrations** | Delete | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Cloud Accounts** | List / View | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Cloud Accounts** | Create / Update | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Cloud Accounts** | Trigger scan | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Findings** | List / View | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Findings** | Update status | ✅ | ✅ | ✅ | ✅* | ❌ |
| **Findings** | Delete / Suppress | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Risks** | List / View | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Risks** | Create / Update | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Controls** | List / View | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Controls** | Update status / owner | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Evidence** | List / View | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Evidence** | Upload | ✅ | ✅ | ✅ | ✅ | ❌ |
| **Evidence** | Approve / Reject | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Evidence** | Download | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Evidence** | Delete | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Remediation** | List / View | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Remediation** | Create / Assign | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Remediation** | Update progress | ✅ | ✅ | ✅ | ✅* | ❌ |
| **Remediation** | Verify / Close | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Policies** | List / View | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Policies** | Create / Update | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Vendors** | List / View | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Vendors** | Create / Update | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Audit Log** | View | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Organization Settings** | View | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Organization Settings** | Update | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Billing** | Manage | ✅ | ✅ | ❌ | ❌ | ❌ |

*`engineer` can only update findings/remediation tasks **assigned to them**.

### Implementation Pattern

Authorization is enforced via FastAPI dependency injection:

```python
from fastapi import Depends, HTTPException, status
from app.core.auth import get_current_user
from app.models.user import User


class RequirePermission:
    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_permission(self.resource, self.action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user


# Usage in endpoint
@router.get("/risks")
async def list_risks(
    user: User = Depends(RequirePermission("risks", "read")),
    db: AsyncSession = Depends(get_tenant_db),
):
    ...
```

### Resource-Level Authorization

Beyond role checks, resource-level authorization verifies ownership:

- An `engineer` can update a finding **only if** `finding.assigned_to == current_user.id`
- Evidence downloads verify `evidence.tenant_id == current_user.tenant_id` at the storage layer
- Integration credential access checks both role and ownership

### Authorization Testing

Every protected endpoint has a corresponding test matrix that verifies:

1. Correct role can access the resource → 200
2. Insufficient role gets 403
3. Cross-tenant access gets 404 (not 403, to prevent tenant enumeration)
4. Unauthenticated access gets 401

---

## 3. Multi-Tenant Isolation

Multi-tenant isolation is the most critical security boundary in SecureOps. A failure here exposes one customer's security posture, credentials, and compliance evidence to another.

### Defense-in-Depth Layers

```
┌──────────────────────────────────────────────┐
│  Layer 1: JWT tenant claim (tid)             │  ← Tenant identity resolved at auth
├──────────────────────────────────────────────┤
│  Layer 2: Service-layer tenant scoping       │  ← Every query includes tenant_id filter
├──────────────────────────────────────────────┤
│  Layer 3: PostgreSQL Row-Level Security      │  ← Database enforces tenant boundaries
├──────────────────────────────────────────────┤
│  Layer 4: Storage-layer tenant isolation     │  ← Evidence stored under tenant prefix
└──────────────────────────────────────────────┘
```

### Layer 1: Tenant Identity from JWT

The tenant ID is **never** accepted from the client. It is resolved from the authenticated user's JWT `tid` claim and injected into the request context:

```python
from contextvars import ContextVar

_tenant_id: ContextVar[str] = ContextVar("tenant_id")


async def get_current_tenant(
    token_data: TokenData = Depends(decode_access_token),
) -> str:
    tenant_id = token_data.tid
    _tenant_id.set(tenant_id)
    return tenant_id
```

### Layer 2: Service-Layer Tenant Scoping

Every database session is scoped to the current tenant. The `TenantScopedSession` applies a default filter:

```python
from sqlalchemy import event
from sqlalchemy.orm import Session


def set_tenant_context(session: Session, tenant_id: str) -> None:
    """Set RLS context variable for this transaction."""
    session.execute(
        text("SET LOCAL app.current_tenant_id = :tid"),
        {"tid": tenant_id},
    )


async def get_tenant_db(
    tenant_id: str = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> AsyncSession:
    await session.execute(
        text("SET LOCAL app.current_tenant_id = :tid"),
        {"tid": tenant_id},
    )
    return session
```

All service methods add explicit `tenant_id` filters as the primary safety mechanism:

```python
async def get_risks(db: AsyncSession, tenant_id: str) -> list[Risk]:
    result = await db.execute(
        select(Risk).where(Risk.tenant_id == tenant_id)
    )
    return list(result.scalars().all())
```

### Layer 3: PostgreSQL Row-Level Security

RLS policies act as defense in depth. Even if a service-layer bug omits the tenant filter, the database rejects cross-tenant access:

```sql
-- Enable RLS on tenant-owned tables
ALTER TABLE risks ENABLE ROW LEVEL SECURITY;
ALTER TABLE risks FORCE ROW LEVEL SECURITY;

-- Policy: rows visible only when app.current_tenant_id matches
CREATE POLICY tenant_isolation ON risks
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- The application connects as a non-superuser role (secureops_app)
-- Superusers bypass RLS, so the app role must NOT be a superuser
```

RLS is enabled on **every tenant-owned table**: `risks`, `findings`, `evidence`, `controls`, `assets`, `cloud_accounts`, `integration_connections`, `audit_events`, `remediation_tasks`, `policies`, `vendors`, `vulnerabilities`, `scan_executions`.

### Layer 4: Storage-Layer Tenant Isolation

Evidence files are stored under tenant-prefixed paths:

```
evidence-store/
  {tenant_uuid}/
    {year}/
      {evidence_uuid}/{filename}
```

The storage adapter verifies tenant ownership before generating download URLs:

```python
async def get_evidence_download_url(
    evidence_id: str,
    tenant_id: str,
    db: AsyncSession,
) -> str:
    evidence = await db.get(Evidence, evidence_id)
    if evidence is None or evidence.tenant_id != tenant_id:
        raise NotFoundException("Evidence not found")
    return storage.generate_signed_url(
        path=f"{tenant_id}/{evidence.storage_path}",
        expires_in=300,  # 5-minute signed URL
    )
```

### Tenant-Aware Background Jobs

Celery tasks carry tenant context in task headers, not arguments (to prevent accidental logging of tenant IDs in task result stores):

```python
@celery_app.task(bind=True)
def run_cloud_scan(self, cloud_account_id: str) -> dict:
    tenant_id = self.request.get("tenant_id")
    if not tenant_id:
        raise SecurityError("Task missing tenant context")
    with tenant_scoped_session(tenant_id) as db:
        # All DB operations within this block are tenant-scoped
        ...
```

Task dispatch sets the tenant context:

```python
run_cloud_scan.apply_async(
    args=[cloud_account_id],
    headers={"tenant_id": str(current_tenant_id)},
)
```

### Automated Cross-Tenant Access Tests

The test suite includes dedicated cross-tenant tests:

```python
@pytest.mark.security
async def test_tenant_a_cannot_access_tenant_b_risks(
    tenant_a_client: AsyncClient,
    tenant_b_risk: Risk,
):
    """Attempt to read Tenant B's risk using Tenant A's credentials."""
    response = await tenant_a_client.get(f"/api/v1/risks/{tenant_b_risk.id}")
    assert response.status_code == 404  # Not 403 — prevent enumeration


@pytest.mark.security
async def test_tenant_a_cannot_update_tenant_b_finding(
    tenant_a_client: AsyncClient,
    tenant_b_finding: Finding,
):
    """Attempt to update Tenant B's finding using Tenant A's credentials."""
    response = await tenant_a_client.patch(
        f"/api/v1/findings/{tenant_b_finding.id}",
        json={"status": "resolved"},
    )
    assert response.status_code == 404
```

These tests are run in CI on every PR. The security test suite creates two fully provisioned tenants and systematically attempts cross-tenant access on every CRUD endpoint.

---

## 4. Secrets Management

SecureOps handles sensitive credentials for cloud scanning (AWS keys, Azure service principals, GCP service accounts). These require rigorous protection.

### Credential Storage Architecture

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  User provides   │────▶│  Envelope encryption │────▶│  PostgreSQL      │
│  cloud creds     │     │  (app-level DEK +    │     │  encrypted_blob  │
│  via HTTPS       │     │   platform KEK)      │     │  column          │
└─────────────────┘     └──────────────────────┘     └──────────────────┘
```

### Envelope Encryption

1. **Data Encryption Key (DEK)**: A unique AES-256-GCM key generated per credential. Encrypts the credential payload.
2. **Key Encryption Key (KEK)**: A platform-wide master key (stored in a managed key vault — Azure Key Vault or AWS KMS in production). Encrypts the DEK.
3. **Storage**: The database stores `{encrypted_dek, encrypted_payload, nonce, key_version}`. The plaintext DEK never touches disk.

```python
class CredentialEncryption:
    def encrypt(self, plaintext: bytes, tenant_id: str) -> EncryptedCredential:
        dek = os.urandom(32)  # 256-bit DEK
        nonce = os.urandom(12)
        cipher = AESGCM(dek)
        # AAD includes tenant_id to bind ciphertext to tenant
        aad = tenant_id.encode()
        encrypted_payload = cipher.encrypt(nonce, plaintext, aad)
        encrypted_dek = self.kek_provider.encrypt(dek)
        return EncryptedCredential(
            encrypted_dek=encrypted_dek,
            encrypted_payload=encrypted_payload,
            nonce=nonce,
            key_version=self.kek_provider.current_version,
        )
```

The tenant ID is bound as Additional Authenticated Data (AAD), so a credential ciphertext cannot be moved between tenants without detection.

### Credential Lifecycle

| Operation | Handling |
|-----------|----------|
| Create | Encrypted immediately, plaintext never stored |
| Read (for scanning) | Decrypted in-memory, passed to scanner, zeroed after use |
| Rotate | New credential encrypted, old marked for deletion after grace period |
| Delete | Ciphertext deleted, audit event recorded |
| Display | Only metadata shown (provider, account alias, last used). Never the secret. |

### What Is Never Logged

- Access tokens, refresh tokens, JWTs
- Cloud provider credentials (access keys, client secrets, service account keys)
- Password hashes
- MFA secrets or recovery codes
- Evidence file contents
- Encrypted credential payloads

Structured logging uses a `SecureFormatter` that redacts fields matching configurable patterns (`*_secret`, `*_key`, `*_token`, `*_password`, `authorization`).

---

## 5. Evidence Security

Evidence files are compliance artifacts — audit logs, screenshots, policy documents, scan reports. They require integrity protection and access control.

### Upload Security

| Control | Implementation |
|---------|----------------|
| **File type allowlist** | `.pdf`, `.png`, `.jpg`, `.jpeg`, `.csv`, `.xlsx`, `.docx`, `.txt`, `.json`, `.xml`, `.zip` |
| **Content validation** | `python-magic` verifies MIME type matches extension; rejects mismatches |
| **Size limit** | 50 MB per file (configurable per tenant) |
| **Executable rejection** | Files with executable signatures (PE, ELF, Mach-O, script shebangs) are rejected regardless of extension |
| **Filename sanitization** | Strip path traversal characters, limit length, generate UUID-based storage name |
| **Malware scanning** | ClamAV scan before storage (when available); quarantine on detection |

### Storage Security

- **At rest**: AES-256 encryption via storage provider (Azure SSE / S3 SSE-S3)
- **In transit**: TLS 1.2+ for all storage API calls
- **Path isolation**: `{tenant_uuid}/{year}/{evidence_uuid}/{safe_filename}`
- **Integrity**: SHA-256 hash computed at upload, stored in DB, verified on download

### Access Control

```python
async def download_evidence(
    evidence_id: UUID,
    tenant_id: str = Depends(get_current_tenant),
    user: User = Depends(RequirePermission("evidence", "read")),
    db: AsyncSession = Depends(get_tenant_db),
) -> RedirectResponse:
    evidence = await evidence_service.get_by_id(db, evidence_id, tenant_id)
    if evidence is None:
        raise HTTPException(status_code=404)

    # Generate short-lived signed URL (5 minutes)
    url = storage.generate_signed_url(
        path=evidence.storage_path,
        expires_in=300,
        tenant_id=tenant_id,
    )

    # Audit log
    await audit_service.log(
        event_type="EVIDENCE_DOWNLOADED",
        tenant_id=tenant_id,
        user_id=user.id,
        resource_type="evidence",
        resource_id=str(evidence_id),
    )

    return RedirectResponse(url=url, status_code=307)
```

### Retention and Deletion

- Evidence has a configurable retention period per organization (default: 7 years for compliance)
- Expired evidence is soft-deleted first (30-day grace period), then permanently purged
- Deletion is audited and irreversible after purge
- Historical evidence is never silently overwritten — new uploads create new versions

---

## 6. Cloud Scanning Security

SecureOps orchestrates Prowler and Trivy as containerized scanner engines. Scanner execution is security-sensitive because it requires cloud credentials and processes untrusted output.

### Container Isolation

```yaml
# Scanner container constraints (Docker)
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp:size=512M
mem_limit: 2g
cpus: 1.0
pids_limit: 256
network_mode: none  # No network for Trivy filesystem scans
# For Prowler (needs API access): restricted egress via network policy
```

### Credential Handling for Scans

1. Credentials decrypted in the worker process (memory-only)
2. Passed to scanner container via environment variables (not mounted files when possible)
3. Container environment cleared after scan completes
4. If temporary files are necessary (e.g., GCP service account JSON), they are written to a tmpfs mount and the container is destroyed after scan

### Scanner Output Validation

Scanner output (JSON/CSV) is parsed with strict schema validation before ingestion:

- Field types are validated against expected schemas
- String fields are length-limited
- No HTML/script content is rendered from scanner output
- Output size is capped (100 MB max per scan)
- Malformed output triggers an alert and the scan is marked as failed

### Credential Redaction

A post-processing step scans output for credential-like patterns before storage:

```python
REDACTION_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",           # AWS access key
    r"(?i)password\s*[:=]\s*\S+",   # password assignments
    r"-----BEGIN .* PRIVATE KEY-----",  # PEM keys
    r"eyJ[A-Za-z0-9_-]+\.eyJ",     # JWT tokens
]
```

### Scan Permissions

| Provider | Role Type | Permissions |
|----------|-----------|-------------|
| AWS | IAM Role (cross-account assume) | `SecurityAudit` + `ViewOnlyAccess` managed policies |
| Azure | Service Principal | `Reader` + `Security Reader` RBAC roles |
| GCP (planned) | Service Account | `roles/viewer` + `roles/iam.securityReviewer` |

Read-only. No write/modify/delete permissions. Documented in onboarding as a hard requirement.

---

## 7. API Security

### Security Headers

Applied via FastAPI middleware on all responses:

```python
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",  # Disabled in favor of CSP
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
```

### CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Explicit allowlist, never "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Input Validation

All request bodies are validated by Pydantic models with strict type checking:

```python
class CreateRiskRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    title: str = Field(min_length=1, max_length=500)
    description: str = Field(max_length=5000)
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    category: RiskCategory
    owner_id: UUID
```

### SSRF Prevention

Outbound HTTP requests (webhooks, integrations) are restricted:

```python
ALLOWED_OUTBOUND_HOSTS = {
    "management.azure.com",
    "sts.windows.net",
    "*.amazonaws.com",
    "oauth2.googleapis.com",
}

async def safe_outbound_request(url: str) -> httpx.Response:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("https",):
        raise SecurityError("Only HTTPS outbound requests allowed")
    if not any(fnmatch(parsed.hostname, pattern) for pattern in ALLOWED_OUTBOUND_HOSTS):
        raise SecurityError(f"Outbound host not in allowlist: {parsed.hostname}")
    # Resolve DNS and reject private IPs
    ip = socket.getaddrinfo(parsed.hostname, None)[0][4][0]
    if ipaddress.ip_address(ip).is_private:
        raise SecurityError("Outbound request to private IP blocked")
    return await httpx.AsyncClient().get(url)
```

### CSRF Protection

- API endpoints use `Authorization: Bearer` header tokens (not cookies for auth), making CSRF less applicable for API calls
- The frontend uses `SameSite=Strict` cookies for the refresh token
- State-changing operations via cookie-authenticated routes (if any) require a CSRF token validated server-side

### Rate Limiting (Global)

| Tier | Limit | Scope |
|------|-------|-------|
| Authenticated API | 1000 req/min | Per user |
| Unauthenticated | 60 req/min | Per IP |
| File upload | 20 req/min | Per user |
| Scan trigger | 10 req/hour | Per tenant |

Implemented via Redis sliding window. 429 responses include `Retry-After` header.

### Webhook Security

Inbound webhooks (e.g., from DefectDojo) are verified via HMAC signature:

```python
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## 8. Audit Logging

### Event Types

| Category | Events |
|----------|--------|
| **Authentication** | `AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILURE`, `AUTH_LOGOUT`, `AUTH_MFA_ENABLED`, `AUTH_MFA_DISABLED`, `AUTH_PASSWORD_CHANGED`, `AUTH_PASSWORD_RESET`, `AUTH_SESSION_REVOKED` |
| **Authorization** | `AUTHZ_PERMISSION_GRANTED`, `AUTHZ_PERMISSION_DENIED`, `AUTHZ_ROLE_CHANGED` |
| **Users** | `USER_CREATED`, `USER_INVITED`, `USER_DEACTIVATED`, `USER_DELETED` |
| **Integrations** | `INTEGRATION_CREATED`, `INTEGRATION_UPDATED`, `INTEGRATION_DELETED`, `INTEGRATION_CREDENTIAL_ROTATED` |
| **Evidence** | `EVIDENCE_UPLOADED`, `EVIDENCE_DOWNLOADED`, `EVIDENCE_APPROVED`, `EVIDENCE_REJECTED`, `EVIDENCE_DELETED` |
| **Findings** | `FINDING_CREATED`, `FINDING_STATUS_CHANGED`, `FINDING_ASSIGNED`, `FINDING_SUPPRESSED` |
| **Risks** | `RISK_CREATED`, `RISK_UPDATED`, `RISK_TREATMENT_CHANGED`, `RISK_REVIEW_COMPLETED` |
| **Controls** | `CONTROL_STATUS_CHANGED`, `CONTROL_OWNER_CHANGED`, `CONTROL_EVIDENCE_LINKED` |
| **Remediation** | `REMEDIATION_CREATED`, `REMEDIATION_ASSIGNED`, `REMEDIATION_COMPLETED`, `REMEDIATION_VERIFIED` |
| **Scanning** | `SCAN_STARTED`, `SCAN_COMPLETED`, `SCAN_FAILED` |
| **Admin** | `ORG_SETTINGS_CHANGED`, `BILLING_PLAN_CHANGED`, `DATA_EXPORT_REQUESTED`, `DATA_DELETION_REQUESTED` |

### Audit Event Schema

```python
class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    actor_ip: Mapped[str | None] = mapped_column(String(45))
    resource_type: Mapped[str | None] = mapped_column(String(50))
    resource_id: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
```

### Integrity Protection

- Audit events are **append-only** in the application layer — no UPDATE or DELETE operations exposed via any API or service method
- The `audit_events` table has a database-level trigger that rejects UPDATE and DELETE:

```sql
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit events cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_immutability
    BEFORE UPDATE OR DELETE ON audit_events
    FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();
```

- For exported audit data: SHA-256 hash chain where each event's hash includes the previous event's hash, providing tamper evidence (not tamper-proof — true immutability requires external verification)
- Audit retention: minimum 1 year, configurable up to 7 years per tenant

### Structured Logging

Application logs (separate from audit events) use `structlog` with JSON output:

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "cloud_scan_completed",
    tenant_id=tenant_id,
    scan_id=scan_id,
    findings_count=42,
    duration_seconds=128.5,
)
```

Sensitive fields are automatically redacted by the logging pipeline.

---

## 9. Data Classification

| Classification | Examples | Controls |
|---------------|----------|----------|
| **Critical** | Cloud provider credentials, encryption keys, JWT signing keys, MFA secrets | Encrypted at rest + in transit, envelope encryption, never logged, never in API responses, access audited, key rotation supported |
| **Confidential** | Evidence files, compliance reports, security findings with detail, user PII (email, name), audit logs | Encrypted at rest + in transit, tenant-isolated, access-controlled, download audited, retention-managed |
| **Sensitive** | Risk assessments, control statuses, vulnerability summaries, asset inventories | Tenant-isolated, role-based access, no public exposure |
| **Internal** | Application configs (non-secret), metrics, performance data, anonymized usage statistics | Not publicly accessible, standard access controls |
| **Public** | Marketing content, documentation, public API schema | No special controls |

### PII Handling

- User PII (name, email) stored in the `users` table, tenant-scoped
- PII is not included in application logs (structlog redaction)
- PII export available for GDPR data subject requests
- PII deletion supported (user account deletion cascades to anonymize audit references)

---

## 10. Compliance Mapping

### SOC 2 Trust Services Criteria

| TSC | Criterion | SecureOps Control |
|-----|-----------|-------------------|
| CC6.1 | Logical access security | RBAC, JWT auth, MFA, session management (§1, §2) |
| CC6.2 | Credentials and authentication | Bcrypt passwords, token expiry, MFA, SSO (§1) |
| CC6.3 | Authorization and access control | Permission matrix, resource-level auth, default-deny (§2) |
| CC6.6 | System boundaries | Tenant isolation, RLS, storage isolation (§3) |
| CC6.7 | Restrict information transmission | TLS 1.2+, encrypted storage, signed URLs (§5) |
| CC6.8 | Prevent unauthorized software | Container image pinning, no exec uploads, scanner isolation (§5, §6) |
| CC7.1 | Detect and address threats | Audit logging, rate limiting, anomaly detection (§7, §8) |
| CC7.2 | Monitor system components | Structured logging, OpenTelemetry, health checks |
| CC7.3 | Evaluate security events | Audit trail, event categorization (§8) |
| CC8.1 | Change management | CI/CD pipeline, code review, infrastructure as code |
| CC9.1 | Risk identification | Threat model, risk register, vulnerability management |

### ISO 27001:2022 Annex A Mapping

| Control | Description | SecureOps Implementation |
|---------|-------------|--------------------------|
| A.5.15 | Access control | RBAC with default-deny, permission matrix (§2) |
| A.5.17 | Authentication information | Bcrypt, credential rotation, MFA (§1) |
| A.5.23 | Information security for cloud services | Read-only scanning, container isolation (§6) |
| A.5.33 | Protection of records | Append-only audit, evidence integrity hashes (§5, §8) |
| A.8.2 | Privileged access rights | Role hierarchy, admin restrictions (§2) |
| A.8.3 | Information access restriction | Tenant isolation, RLS (§3) |
| A.8.5 | Secure authentication | JWT, MFA, rate limiting (§1) |
| A.8.9 | Configuration management | Infrastructure as code, security headers (§7) |
| A.8.10 | Information deletion | Evidence retention/purge, data deletion support (§5) |
| A.8.12 | Data leakage prevention | Credential redaction, SSRF prevention, secret scanning (§4, §7) |
| A.8.24 | Use of cryptography | AES-256-GCM, envelope encryption, TLS (§4, §5) |
| A.8.25 | Secure development lifecycle | TDD, SAST, dependency scanning, security tests (CI pipeline) |
| A.8.26 | Application security requirements | Input validation, parameterized queries, Pydantic (§7) |
| A.8.28 | Secure coding | Ruff, Bandit, Semgrep, code review (CI pipeline) |

---

## Appendix A: Security Configuration Checklist

For each deployment environment:

- [ ] JWT secret key is unique, random, and stored in key vault
- [ ] Database role is non-superuser (RLS enforcement)
- [ ] RLS policies enabled on all tenant-owned tables
- [ ] TLS certificates valid and auto-renewed
- [ ] CORS origins set to exact production domain
- [ ] Rate limiting enabled
- [ ] Security headers middleware active
- [ ] Audit logging operational
- [ ] Evidence encryption at rest verified
- [ ] Scanner containers run as non-root with resource limits
- [ ] No secrets in environment variables for CI/CD (use vault)
- [ ] Gitleaks and Trivy scans passing in CI
- [ ] Cross-tenant security tests passing

## Appendix B: Incident Response Triggers

The following events should trigger security investigation:

- Multiple failed login attempts from a single account (>10 in 15 minutes)
- Cross-tenant access attempt detected (should be impossible — indicates a bug)
- Scanner container resource limit exceeded
- Evidence integrity hash mismatch on download
- Audit event modification attempt (trigger fires)
- Credential decryption failure (possible key rotation issue or tampering)
- Webhook signature verification failure (>5 in 1 hour)
