# SecureOps — Database Design

## 1. Overview

SecureOps uses PostgreSQL 16 as its primary data store, accessed via SQLAlchemy 2.x async (asyncpg driver) with Alembic for schema migrations. The database serves a multi-tenant SaaS product covering GRC, cloud security, vulnerability management, and evidence collection.

**Key design constraints:**

- Every tenant-owned row is scoped by `tenant_id`.
- PostgreSQL Row-Level Security (RLS) provides defense-in-depth tenant isolation.
- All timestamps are stored in UTC.
- UUIDs are used as primary keys for all entities (prevents enumeration, simplifies distributed generation).
- Soft deletes via `deleted_at` on entities that require audit trails; hard deletes only where legally required (e.g., GDPR erasure).

---

## 2. Multi-Tenant Strategy

### Approach: Shared Database, Shared Schema

All tenants share a single PostgreSQL database and schema. Tenant isolation is enforced at three layers:

| Layer | Mechanism | Purpose |
|-------|-----------|---------|
| Application | SQLAlchemy query filters, middleware sets tenant context | Primary isolation |
| Database | RLS policies on all tenant-scoped tables | Defense in depth |
| Infrastructure | Connection pooling per-tenant limits | Resource fairness |

### Tenant Context Propagation

```sql
-- Set at the start of every transaction by the application
SET LOCAL app.current_tenant_id = '<tenant-uuid>';
```

The application middleware resolves the tenant from the authenticated user's membership and sets the session variable before any query executes. `SET LOCAL` scopes the variable to the current transaction, preventing leakage across pooled connections.

### RLS Activation

```sql
ALTER TABLE <table> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <table> FORCE ROW LEVEL SECURITY;
```

`FORCE ROW LEVEL SECURITY` ensures RLS applies even to table owners, preventing accidental bypasses during migrations or admin operations.

---

## 3. Core Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          IDENTITY & TENANCY                                 │
│                                                                             │
│  ┌──────────┐     ┌────────────┐     ┌──────────┐                          │
│  │  Tenant   │────<│ Membership │>────│   User   │                          │
│  └──────────┘     └────────────┘     └──────────┘                          │
│       │                 │                  │                                 │
│       │            ┌────┘                  │                                 │
│       │            ▼                       │                                 │
│       │       ┌──────────┐                 │                                 │
│       │       │   Role   │>────────────────┘                                │
│       │       └──────────┘                                                  │
│       │            │                                                        │
│       │            ▼                                                        │
│       │      ┌────────────┐                                                 │
│       │      │ Permission │                                                 │
│       │      └────────────┘                                                 │
└───────┼─────────────────────────────────────────────────────────────────────┘
        │
        │  (tenant_id FK on all tables below)
        │
┌───────┼─────────────────────────────────────────────────────────────────────┐
│       │              INTEGRATIONS & ASSETS                                  │
│       │                                                                     │
│       ├───>┌─────────────────────┐                                          │
│       │    │IntegrationConnection│                                          │
│       │    └─────────────────────┘                                          │
│       │              │                                                      │
│       │              ▼                                                      │
│       ├───>┌──────────────┐      ┌─────────┐                               │
│       │    │ CloudAccount │──────>│  Asset  │                               │
│       │    └──────────────┘      └─────────┘                               │
│       │                               │                                     │
│       │                               ▼                                     │
│       │    ┌───────────────┐    ┌─────────────┐    ┌───────────────┐       │
│       ├───>│ ScanExecution │───>│   Finding   │───>│ Vulnerability │       │
│       │    └───────────────┘    └─────────────┘    └───────────────┘       │
│       │                               │                                     │
│       │                               ▼                                     │
│       │                       ┌─────────────────┐                           │
│       ├──────────────────────>│RemediationTask  │                           │
│       │                       └─────────────────┘                           │
└───────┼─────────────────────────────────────────────────────────────────────┘
        │
┌───────┼─────────────────────────────────────────────────────────────────────┐
│       │              GRC & COMPLIANCE                                       │
│       │                                                                     │
│       │    ┌───────────┐    ┌──────────────────┐                           │
│       │    │ Framework │───>│ FrameworkVersion │                            │
│       │    └───────────┘    └──────────────────┘                           │
│       │                            │                                        │
│       │                            ▼                                        │
│       │                      ┌───────────┐    ┌────────────────┐           │
│       │                      │  Control  │<──>│ControlMapping  │           │
│       │                      └───────────┘    └────────────────┘           │
│       │                            │                                        │
│       │                            ▼                                        │
│       ├───>┌──────────┐    ┌─────────────┐                                 │
│       │    │   Risk   │    │  Evidence   │                                  │
│       │    └──────────┘    └─────────────┘                                 │
│       │                          │                                          │
│       │                          ▼                                          │
│       │                  ┌───────────────────────┐                          │
│       │                  │ EvidenceCollectionRun  │                          │
│       │                  └───────────────────────┘                          │
│       │                                                                     │
│       ├───>┌──────────┐     ┌──────────┐                                   │
│       │    │  Policy  │     │  Vendor  │                                    │
│       │    └──────────┘     └──────────┘                                   │
└───────┼─────────────────────────────────────────────────────────────────────┘
        │
┌───────┼─────────────────────────────────────────────────────────────────────┐
│       │              AUDIT & NOTIFICATIONS                                  │
│       │                                                                     │
│       ├───>┌────────────┐     ┌──────────────┐                             │
│            │ AuditEvent │     │ Notification │                              │
│            └────────────┘     └──────────────┘                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Relationship Summary

| From | To | Cardinality | Description |
|------|----|-------------|-------------|
| Tenant | Membership | 1:N | A tenant has many members |
| User | Membership | 1:N | A user can belong to many tenants |
| Membership | Role | N:1 | Each membership has one role |
| Role | Permission | N:N | Roles grant many permissions |
| Tenant | IntegrationConnection | 1:N | Tenant configures integration connectors |
| IntegrationConnection | CloudAccount | 1:N | Connector manages cloud accounts |
| CloudAccount | Asset | 1:N | Account contains discovered assets |
| ScanExecution | Finding | 1:N | Scan produces findings |
| Finding | Asset | N:1 | Finding relates to an asset |
| Finding | Vulnerability | N:1 | Finding may reference a CVE/vulnerability |
| Finding | RemediationTask | 1:1 | Finding may have a remediation task |
| Framework | FrameworkVersion | 1:N | Framework has versioned releases |
| FrameworkVersion | Control | 1:N | Version defines controls |
| Control | ControlMapping | 1:N | Control maps across frameworks (many-to-many via mapping) |
| Control | Evidence | N:N | Controls require evidence (via join table) |
| Evidence | EvidenceCollectionRun | N:1 | Evidence produced by collection run |
| Risk | Control | N:N | Risks relate to controls |
| Tenant | AuditEvent | 1:N | All events scoped to tenant |
| Tenant | Notification | 1:N | Notifications per tenant |

---

## 4. Table Definitions

### 4.1 Tenant

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| name | VARCHAR(255) | NOT NULL | Organization display name |
| slug | VARCHAR(100) | NOT NULL, UNIQUE | URL-safe identifier |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | active, suspended, deactivated |
| subscription_tier | VARCHAR(50) | NOT NULL, DEFAULT 'free' | free, starter, professional, enterprise |
| settings | JSONB | NOT NULL, DEFAULT '{}' | Tenant-level configuration |
| max_users | INTEGER | NOT NULL, DEFAULT 5 | Subscription limit |
| max_integrations | INTEGER | NOT NULL, DEFAULT 2 | Subscription limit |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |

**Indexes:**
- `idx_tenant_slug` UNIQUE on (slug) WHERE deleted_at IS NULL
- `idx_tenant_status` on (status)

---

### 4.2 User

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| email | VARCHAR(320) | NOT NULL, UNIQUE | RFC 5321 max length |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt hash |
| full_name | VARCHAR(255) | NOT NULL | |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | |
| is_superadmin | BOOLEAN | NOT NULL, DEFAULT false | Platform-level admin only |
| mfa_enabled | BOOLEAN | NOT NULL, DEFAULT false | |
| mfa_secret_enc | BYTEA | NULL | Encrypted TOTP secret |
| last_login_at | TIMESTAMPTZ | NULL | |
| failed_login_count | INTEGER | NOT NULL, DEFAULT 0 | Rate limiting |
| locked_until | TIMESTAMPTZ | NULL | Account lockout |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_user_email` UNIQUE on (email) — case-insensitive via `lower(email)`
- `idx_user_active` on (is_active) WHERE is_active = true

**Note:** User is NOT tenant-scoped. Users exist globally and access tenants via Membership.

---

### 4.3 Membership

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| user_id | UUID | NOT NULL, FK → User(id) | |
| role_id | UUID | NOT NULL, FK → Role(id) | |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | active, invited, suspended |
| invited_by | UUID | NULL, FK → User(id) | |
| invited_at | TIMESTAMPTZ | NULL | |
| accepted_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_membership_tenant_user` UNIQUE on (tenant_id, user_id)
- `idx_membership_user` on (user_id)
- `idx_membership_tenant_status` on (tenant_id, status)

---

### 4.4 Role

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NULL, FK → Tenant(id) | NULL = system-defined role |
| name | VARCHAR(100) | NOT NULL | e.g., admin, security_manager, engineer, auditor |
| description | TEXT | NULL | |
| is_system | BOOLEAN | NOT NULL, DEFAULT false | System roles are immutable |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_role_tenant_name` UNIQUE on (tenant_id, name)

---

### 4.5 Permission

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| resource | VARCHAR(100) | NOT NULL | e.g., compliance, risks, evidence, admin |
| action | VARCHAR(50) | NOT NULL | e.g., read, write, delete, manage |
| description | TEXT | NULL | |

**Indexes:**
- `idx_permission_resource_action` UNIQUE on (resource, action)

---

### 4.6 RolePermission (Join Table)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| role_id | UUID | PK, FK → Role(id) ON DELETE CASCADE | |
| permission_id | UUID | PK, FK → Permission(id) ON DELETE CASCADE | |

---

### 4.7 IntegrationConnection

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| name | VARCHAR(255) | NOT NULL | User-assigned connection name |
| integration_type | VARCHAR(50) | NOT NULL | prowler, trivy, defectdojo, cloudquery |
| provider | VARCHAR(50) | NOT NULL | aws, azure, gcp, kubernetes |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending, connected, error, disabled |
| credentials_enc | BYTEA | NOT NULL | Envelope-encrypted credential blob |
| credential_metadata | JSONB | NOT NULL, DEFAULT '{}' | Non-sensitive metadata (region, account alias) |
| last_validated_at | TIMESTAMPTZ | NULL | |
| last_error | TEXT | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| deleted_at | TIMESTAMPTZ | NULL | |

**Indexes:**
- `idx_integration_tenant_type` on (tenant_id, integration_type)
- `idx_integration_tenant_status` on (tenant_id, status) WHERE deleted_at IS NULL

---

### 4.8 CloudAccount

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| integration_id | UUID | NOT NULL, FK → IntegrationConnection(id) | |
| provider | VARCHAR(50) | NOT NULL | aws, azure, gcp |
| account_id | VARCHAR(255) | NOT NULL | AWS account ID, Azure subscription ID, etc. |
| display_name | VARCHAR(255) | NOT NULL | |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | active, disconnected, error |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | Provider-specific metadata |
| last_scanned_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_cloud_account_tenant` on (tenant_id)
- `idx_cloud_account_tenant_provider` on (tenant_id, provider)
- `idx_cloud_account_integration` on (integration_id)

---

### 4.9 Asset

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| cloud_account_id | UUID | NULL, FK → CloudAccount(id) | NULL for non-cloud assets |
| asset_type | VARCHAR(100) | NOT NULL | e.g., ec2_instance, azure_vm, s3_bucket, container_image |
| provider | VARCHAR(50) | NOT NULL | aws, azure, gcp, on_prem |
| resource_id | VARCHAR(500) | NOT NULL | ARN, Azure resource ID, etc. |
| name | VARCHAR(255) | NOT NULL | |
| region | VARCHAR(100) | NULL | |
| tags | JSONB | NOT NULL, DEFAULT '{}' | |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | |
| first_seen_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| last_seen_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | active, stale, deleted |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_asset_tenant_type` on (tenant_id, asset_type)
- `idx_asset_tenant_provider` on (tenant_id, provider)
- `idx_asset_resource_id` on (tenant_id, resource_id)
- `idx_asset_cloud_account` on (cloud_account_id)
- `idx_asset_tags` GIN on (tags)

---

### 4.10 Finding

The central normalized model. All security findings from all sources (Prowler, Trivy, manual) are stored here.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| scan_execution_id | UUID | NOT NULL, FK → ScanExecution(id) | |
| asset_id | UUID | NULL, FK → Asset(id) | |
| vulnerability_id | UUID | NULL, FK → Vulnerability(id) | |
| source | VARCHAR(50) | NOT NULL | prowler, trivy, defectdojo, manual |
| source_finding_id | VARCHAR(500) | NOT NULL | Original ID from source scanner |
| title | VARCHAR(500) | NOT NULL | |
| description | TEXT | NOT NULL | |
| severity | VARCHAR(20) | NOT NULL | critical, high, medium, low, info |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'open' | open, in_progress, resolved, accepted, false_positive |
| category | VARCHAR(100) | NOT NULL | e.g., iam, encryption, network, vulnerability |
| compliance_references | JSONB | NOT NULL, DEFAULT '[]' | e.g., [{"framework":"SOC2","control":"CC6.1"}] |
| remediation_guidance | TEXT | NULL | |
| raw_data | JSONB | NOT NULL, DEFAULT '{}' | Full original scanner output |
| risk_score | DECIMAL(5,2) | NULL | Computed risk score 0.00–100.00 |
| first_detected_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| last_detected_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| resolved_at | TIMESTAMPTZ | NULL | |
| resolved_by | UUID | NULL, FK → User(id) | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_finding_tenant_severity` on (tenant_id, severity)
- `idx_finding_tenant_status` on (tenant_id, status)
- `idx_finding_tenant_source` on (tenant_id, source)
- `idx_finding_tenant_category` on (tenant_id, category)
- `idx_finding_asset` on (asset_id)
- `idx_finding_scan_execution` on (scan_execution_id)
- `idx_finding_dedup` on (tenant_id, source, source_finding_id) — deduplication
- `idx_finding_compliance` GIN on (compliance_references)
- `idx_finding_open` on (tenant_id, severity, first_detected_at) WHERE status = 'open'

---

### 4.11 Vulnerability

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| cve_id | VARCHAR(30) | NULL, UNIQUE | CVE-YYYY-NNNNN |
| title | VARCHAR(500) | NOT NULL | |
| description | TEXT | NOT NULL | |
| severity | VARCHAR(20) | NOT NULL | critical, high, medium, low |
| cvss_v3_score | DECIMAL(3,1) | NULL | 0.0–10.0 |
| cvss_v3_vector | VARCHAR(200) | NULL | |
| cwe_ids | JSONB | NOT NULL, DEFAULT '[]' | e.g., ["CWE-79","CWE-89"] |
| affected_packages | JSONB | NOT NULL, DEFAULT '[]' | |
| references | JSONB | NOT NULL, DEFAULT '[]' | URLs |
| published_at | TIMESTAMPTZ | NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_vulnerability_cve` UNIQUE on (cve_id) WHERE cve_id IS NOT NULL
- `idx_vulnerability_severity` on (severity)

**Note:** Vulnerability is NOT tenant-scoped — it is a shared reference table of known CVEs.

---

### 4.12 Risk

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| title | VARCHAR(500) | NOT NULL | |
| description | TEXT | NOT NULL | |
| category | VARCHAR(100) | NOT NULL | e.g., operational, technical, compliance, strategic |
| likelihood | INTEGER | NOT NULL, CHECK (1–5) | 1=rare, 5=almost certain |
| impact | INTEGER | NOT NULL, CHECK (1–5) | 1=negligible, 5=catastrophic |
| inherent_score | DECIMAL(5,2) | NOT NULL | Computed: likelihood * impact * weight |
| residual_likelihood | INTEGER | NULL, CHECK (1–5) | After mitigations |
| residual_impact | INTEGER | NULL, CHECK (1–5) | After mitigations |
| residual_score | DECIMAL(5,2) | NULL | |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'identified' | identified, assessed, mitigating, accepted, closed |
| treatment | VARCHAR(30) | NOT NULL, DEFAULT 'mitigate' | mitigate, accept, transfer, avoid |
| owner_id | UUID | NOT NULL, FK → User(id) | |
| review_date | DATE | NOT NULL | Next review due |
| notes | TEXT | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_risk_tenant_status` on (tenant_id, status)
- `idx_risk_tenant_category` on (tenant_id, category)
- `idx_risk_owner` on (owner_id)
- `idx_risk_review_due` on (tenant_id, review_date) WHERE status NOT IN ('accepted', 'closed')

---

### 4.13 Framework

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| name | VARCHAR(255) | NOT NULL | e.g., SOC 2, ISO 27001 |
| code | VARCHAR(50) | NOT NULL, UNIQUE | e.g., soc2, iso27001 |
| description | TEXT | NOT NULL | |
| publisher | VARCHAR(255) | NOT NULL | e.g., AICPA, ISO/IEC |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_framework_code` UNIQUE on (code)

**Note:** Framework is a shared reference table, not tenant-scoped.

---

### 4.14 FrameworkVersion

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| framework_id | UUID | NOT NULL, FK → Framework(id) | |
| version | VARCHAR(50) | NOT NULL | e.g., Type II 2017, 2022 |
| effective_date | DATE | NULL | |
| is_current | BOOLEAN | NOT NULL, DEFAULT true | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_fwversion_framework` on (framework_id)
- `idx_fwversion_framework_version` UNIQUE on (framework_id, version)

---

### 4.15 Control

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| framework_version_id | UUID | NOT NULL, FK → FrameworkVersion(id) | |
| code | VARCHAR(50) | NOT NULL | e.g., CC6.1, A.5.1 |
| title | VARCHAR(500) | NOT NULL | |
| description | TEXT | NOT NULL | |
| category | VARCHAR(100) | NULL | Grouping within framework |
| parent_control_id | UUID | NULL, FK → Control(id) | Hierarchical controls |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_control_framework_version` on (framework_version_id)
- `idx_control_code` on (framework_version_id, code)
- `idx_control_parent` on (parent_control_id)

**Note:** Control is a shared reference table. Tenant-specific control status is in TenantControlStatus (below).

---

### 4.16 TenantControlStatus

Tracks each tenant's status against each control.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| control_id | UUID | NOT NULL, FK → Control(id) | |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'not_assessed' | not_assessed, not_applicable, partially_implemented, implemented, effective |
| owner_id | UUID | NULL, FK → User(id) | |
| notes | TEXT | NULL | |
| last_tested_at | TIMESTAMPTZ | NULL | |
| last_tested_by | UUID | NULL, FK → User(id) | |
| effectiveness | VARCHAR(20) | NULL | effective, partially_effective, ineffective |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_tcs_tenant_control` UNIQUE on (tenant_id, control_id)
- `idx_tcs_tenant_status` on (tenant_id, status)

---

### 4.17 ControlMapping

Many-to-many cross-framework control mapping.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| source_control_id | UUID | NOT NULL, FK → Control(id) | |
| target_control_id | UUID | NOT NULL, FK → Control(id) | |
| mapping_type | VARCHAR(30) | NOT NULL | equivalent, partial, related |
| notes | TEXT | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_controlmap_source` on (source_control_id)
- `idx_controlmap_target` on (target_control_id)
- `idx_controlmap_pair` UNIQUE on (source_control_id, target_control_id)

---

### 4.18 Evidence

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| collection_run_id | UUID | NULL, FK → EvidenceCollectionRun(id) | NULL for manual uploads |
| title | VARCHAR(500) | NOT NULL | |
| description | TEXT | NULL | |
| evidence_type | VARCHAR(50) | NOT NULL | document, screenshot, log, config, report, automated |
| source | VARCHAR(50) | NOT NULL | manual, prowler, trivy, system |
| file_path | VARCHAR(1000) | NULL | Object storage path |
| file_name | VARCHAR(255) | NULL | Original filename |
| file_size_bytes | BIGINT | NULL | |
| content_type | VARCHAR(100) | NULL | MIME type |
| sha256_hash | VARCHAR(64) | NULL | Integrity verification |
| storage_backend | VARCHAR(20) | NOT NULL, DEFAULT 'local' | local, azure_blob, s3 |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | active, expired, superseded, deleted |
| collected_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | When the evidence was captured |
| expires_at | TIMESTAMPTZ | NULL | Evidence expiry |
| approved_by | UUID | NULL, FK → User(id) | |
| approved_at | TIMESTAMPTZ | NULL | |
| uploaded_by | UUID | NOT NULL, FK → User(id) | |
| version | INTEGER | NOT NULL, DEFAULT 1 | Evidence versioning |
| previous_version_id | UUID | NULL, FK → Evidence(id) | Links to prior version |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_evidence_tenant` on (tenant_id)
- `idx_evidence_tenant_type` on (tenant_id, evidence_type)
- `idx_evidence_tenant_status` on (tenant_id, status)
- `idx_evidence_collection_run` on (collection_run_id)
- `idx_evidence_hash` on (tenant_id, sha256_hash)
- `idx_evidence_expiry` on (tenant_id, expires_at) WHERE status = 'active' AND expires_at IS NOT NULL

---

### 4.19 ControlEvidence (Join Table)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| tenant_control_status_id | UUID | PK, FK → TenantControlStatus(id) ON DELETE CASCADE | |
| evidence_id | UUID | PK, FK → Evidence(id) ON DELETE CASCADE | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

---

### 4.20 EvidenceCollectionRun

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| source | VARCHAR(50) | NOT NULL | prowler, trivy, manual_batch |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'running' | running, completed, failed |
| started_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| completed_at | TIMESTAMPTZ | NULL | |
| evidence_count | INTEGER | NOT NULL, DEFAULT 0 | |
| error_message | TEXT | NULL | |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_ecr_tenant` on (tenant_id)
- `idx_ecr_tenant_source` on (tenant_id, source)

---

### 4.21 RemediationTask

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| finding_id | UUID | NULL, FK → Finding(id) | |
| risk_id | UUID | NULL, FK → Risk(id) | |
| title | VARCHAR(500) | NOT NULL | |
| description | TEXT | NOT NULL | |
| priority | VARCHAR(20) | NOT NULL, DEFAULT 'medium' | critical, high, medium, low |
| status | VARCHAR(30) | NOT NULL, DEFAULT 'open' | open, in_progress, pending_verification, resolved, closed |
| assigned_to | UUID | NULL, FK → User(id) | |
| due_date | DATE | NULL | |
| sla_deadline | TIMESTAMPTZ | NULL | Computed from finding severity |
| sla_breached | BOOLEAN | NOT NULL, DEFAULT false | |
| resolution_notes | TEXT | NULL | |
| verified_by | UUID | NULL, FK → User(id) | |
| verified_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_remediation_tenant_status` on (tenant_id, status)
- `idx_remediation_tenant_priority` on (tenant_id, priority)
- `idx_remediation_assignee` on (assigned_to)
- `idx_remediation_finding` on (finding_id)
- `idx_remediation_sla` on (tenant_id, sla_deadline) WHERE sla_breached = false AND status NOT IN ('resolved', 'closed')

---

### 4.22 ScanExecution

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| integration_id | UUID | NOT NULL, FK → IntegrationConnection(id) | |
| scanner | VARCHAR(50) | NOT NULL | prowler, trivy |
| scan_type | VARCHAR(50) | NOT NULL | cloud_posture, vulnerability, iac, container |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'queued' | queued, running, completed, failed, cancelled |
| started_at | TIMESTAMPTZ | NULL | |
| completed_at | TIMESTAMPTZ | NULL | |
| finding_count | INTEGER | NOT NULL, DEFAULT 0 | |
| findings_by_severity | JSONB | NOT NULL, DEFAULT '{}' | {"critical":0,"high":0,...} |
| error_message | TEXT | NULL | |
| triggered_by | UUID | NULL, FK → User(id) | NULL = scheduled |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_scan_tenant` on (tenant_id)
- `idx_scan_tenant_scanner` on (tenant_id, scanner)
- `idx_scan_tenant_status` on (tenant_id, status)
- `idx_scan_integration` on (integration_id)

---

### 4.23 Policy

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| title | VARCHAR(500) | NOT NULL | |
| content | TEXT | NOT NULL | Markdown policy text |
| category | VARCHAR(100) | NOT NULL | e.g., access_control, data_protection, incident_response |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'draft' | draft, review, approved, retired |
| version | INTEGER | NOT NULL, DEFAULT 1 | |
| approved_by | UUID | NULL, FK → User(id) | |
| approved_at | TIMESTAMPTZ | NULL | |
| effective_date | DATE | NULL | |
| review_date | DATE | NULL | |
| owner_id | UUID | NOT NULL, FK → User(id) | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_policy_tenant` on (tenant_id)
- `idx_policy_tenant_category` on (tenant_id, category)
- `idx_policy_tenant_status` on (tenant_id, status)

---

### 4.24 Vendor

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| name | VARCHAR(255) | NOT NULL | |
| description | TEXT | NULL | |
| category | VARCHAR(100) | NOT NULL | e.g., infrastructure, saas, professional_services |
| risk_tier | VARCHAR(20) | NOT NULL, DEFAULT 'medium' | critical, high, medium, low |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | active, under_review, offboarding, offboarded |
| contact_name | VARCHAR(255) | NULL | |
| contact_email | VARCHAR(320) | NULL | |
| website | VARCHAR(500) | NULL | |
| contract_expiry | DATE | NULL | |
| last_assessment_at | TIMESTAMPTZ | NULL | |
| next_review_date | DATE | NULL | |
| notes | TEXT | NULL | |
| metadata | JSONB | NOT NULL, DEFAULT '{}' | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_vendor_tenant` on (tenant_id)
- `idx_vendor_tenant_risk` on (tenant_id, risk_tier)
- `idx_vendor_tenant_status` on (tenant_id, status)

---

### 4.25 AuditEvent

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| user_id | UUID | NULL, FK → User(id) | NULL for system events |
| event_type | VARCHAR(100) | NOT NULL | e.g., auth.login, auth.logout, auth.failed, evidence.upload, risk.updated |
| resource_type | VARCHAR(100) | NULL | e.g., finding, evidence, risk, user |
| resource_id | UUID | NULL | |
| action | VARCHAR(50) | NOT NULL | create, read, update, delete, login, logout, export |
| details | JSONB | NOT NULL, DEFAULT '{}' | Changed fields, context |
| ip_address | INET | NULL | |
| user_agent | VARCHAR(500) | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | Immutable — no updated_at |

**Indexes:**
- `idx_audit_tenant_created` on (tenant_id, created_at DESC)
- `idx_audit_tenant_event_type` on (tenant_id, event_type)
- `idx_audit_tenant_resource` on (tenant_id, resource_type, resource_id)
- `idx_audit_user` on (user_id)

**Critical constraints:**
- No UPDATE or DELETE trigger — audit events are append-only at the application level.
- The application database role used for normal operations should not have DELETE on this table; a separate migration role handles retention.

---

### 4.26 Notification

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, DEFAULT gen_random_uuid() | |
| tenant_id | UUID | NOT NULL, FK → Tenant(id) | |
| user_id | UUID | NOT NULL, FK → User(id) | |
| title | VARCHAR(255) | NOT NULL | |
| body | TEXT | NOT NULL | |
| notification_type | VARCHAR(50) | NOT NULL | finding, remediation, review_due, system |
| resource_type | VARCHAR(100) | NULL | |
| resource_id | UUID | NULL | |
| is_read | BOOLEAN | NOT NULL, DEFAULT false | |
| read_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

**Indexes:**
- `idx_notification_user_unread` on (user_id, created_at DESC) WHERE is_read = false
- `idx_notification_tenant_user` on (tenant_id, user_id)

---

### 4.27 RiskControl (Join Table)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| risk_id | UUID | PK, FK → Risk(id) ON DELETE CASCADE | |
| control_id | UUID | PK, FK → Control(id) ON DELETE CASCADE | |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() | |

---

## 5. Indexing Strategy

### Principles

1. **Tenant-first compound indexes.** Every query against a tenant-scoped table filters on `tenant_id`. The first column in every composite index on these tables is `tenant_id`.

2. **Partial indexes for active records.** Most queries target active records. Use `WHERE deleted_at IS NULL` or `WHERE status = 'active'` to shrink index size and speed up common queries.

3. **GIN indexes for JSONB search.** Columns like `tags`, `compliance_references`, and `metadata` that support containment queries use GIN indexes.

4. **Covering indexes** for dashboard count queries (e.g., findings by severity by tenant).

5. **No over-indexing.** Indexes are added based on known query patterns. New indexes require justification from a slow-query analysis, not speculation.

### Index Naming Convention

```
idx_{table}_{columns}          -- standard
idx_{table}_{columns}_partial  -- partial/conditional
idx_{table}_{column}_gin       -- GIN
```

---

## 6. Row-Level Security Policies

### Pattern: Tenant Isolation

Applied to every tenant-scoped table:

```sql
-- Example: findings table
ALTER TABLE finding ENABLE ROW LEVEL SECURITY;
ALTER TABLE finding FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_select ON finding
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_isolation_insert ON finding
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_isolation_update ON finding
    FOR UPDATE
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_isolation_delete ON finding
    FOR DELETE
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

### Pattern: Audit Event Immutability

```sql
ALTER TABLE audit_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_event FORCE ROW LEVEL SECURITY;

-- Normal app role can only SELECT and INSERT
CREATE POLICY audit_select ON audit_event
    FOR SELECT
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY audit_insert ON audit_event
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- No UPDATE or DELETE policies — queries from the app role are denied by default.
-- A separate retention_role with its own policy handles TTL-based cleanup.
```

### Pattern: Shared Reference Tables

Framework, FrameworkVersion, Control, ControlMapping, Permission, and Vulnerability are shared reference data. They do NOT have RLS enabled — all tenants can read them. Write access is restricted to the migration role via GRANT/REVOKE.

```sql
-- The app role has SELECT only on reference tables
GRANT SELECT ON framework, framework_version, control, control_mapping,
    permission, vulnerability TO secureops_app;
```

### Application-Layer Integration

```python
# Middleware sets tenant context before every DB operation
async def set_tenant_context(session: AsyncSession, tenant_id: UUID) -> None:
    await session.execute(
        text("SET LOCAL app.current_tenant_id = :tid"),
        {"tid": str(tenant_id)},
    )
```

---

## 7. Migration Strategy

### Tools

- **Alembic** for versioned schema migrations.
- Migrations stored in `backend/app/db/migrations/versions/`.

### Rules

1. **Online-safe only.** No `ALTER TABLE ... ADD COLUMN ... NOT NULL` without a default on large tables. Use the expand-contract pattern:
   - Add column as nullable.
   - Backfill in batches.
   - Add NOT NULL constraint.

2. **No table locks.** Avoid `LOCK TABLE`, `ALTER TABLE ... ADD CONSTRAINT ... VALIDATE` on large tables during peak hours. Use `CREATE INDEX CONCURRENTLY`.

3. **Backward-compatible.** Every migration must be compatible with the previous application version (rolling deploy). No column renames or drops in the same release as the code change that stops using them.

4. **Reversible.** Every migration has a downgrade path. If a migration is not safely reversible, document why.

5. **RLS policies in migrations.** When a new tenant-scoped table is created, the same migration must enable RLS and create the four tenant isolation policies.

6. **Tested in CI.** The CI pipeline runs `alembic upgrade head` against a clean database and verifies no errors.

### Migration File Naming

```
{revision_id}_{description}.py
```

Example: `001a2b3c4d5e_add_finding_table.py`

---

## 8. Data Integrity

### Foreign Key Constraints

All relationships use explicit foreign keys. `ON DELETE` behavior:

| Relationship | ON DELETE |
|-------------|-----------|
| Membership → Tenant | CASCADE |
| Membership → User | CASCADE |
| Finding → ScanExecution | RESTRICT (don't delete scans with findings) |
| Finding → Asset | SET NULL (asset can be removed, finding persists) |
| RemediationTask → Finding | SET NULL |
| Evidence → EvidenceCollectionRun | SET NULL |
| TenantControlStatus → Control | CASCADE |
| AuditEvent → Tenant | RESTRICT (never delete a tenant with audit history) |

### Check Constraints

```sql
ALTER TABLE risk ADD CONSTRAINT chk_risk_likelihood
    CHECK (likelihood BETWEEN 1 AND 5);

ALTER TABLE risk ADD CONSTRAINT chk_risk_impact
    CHECK (impact BETWEEN 1 AND 5);

ALTER TABLE finding ADD CONSTRAINT chk_finding_severity
    CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info'));

ALTER TABLE vulnerability ADD CONSTRAINT chk_vuln_cvss
    CHECK (cvss_v3_score IS NULL OR (cvss_v3_score >= 0.0 AND cvss_v3_score <= 10.0));

ALTER TABLE evidence ADD CONSTRAINT chk_evidence_hash_format
    CHECK (sha256_hash IS NULL OR length(sha256_hash) = 64);
```

### Audit Event Immutability

The `audit_event` table has no `updated_at` column. Application code never issues UPDATE or DELETE against it. The database role used by the application has INSERT and SELECT permissions only. A separate `secureops_retention` role, used by a scheduled maintenance job, can DELETE records older than the configured retention period.

### Evidence Hash Verification

Every evidence file has its SHA-256 hash stored at upload time. On download, the application verifies the stored hash against the file's current hash before serving it. Hash mismatches are logged as security events and block the download.

### Timestamps

All timestamps use `TIMESTAMPTZ` and are stored in UTC. The application never stores or compares timestamps without timezone information. Display-layer localization is handled in the frontend.

---

## 9. Database Roles

| Role | Purpose | Permissions |
|------|---------|------------|
| secureops_app | Application runtime | SELECT, INSERT, UPDATE on tenant tables; SELECT on reference tables; INSERT on audit_event; no DELETE on audit_event |
| secureops_migration | Alembic migrations | Full DDL, all tables |
| secureops_retention | Scheduled cleanup jobs | DELETE on audit_event, notification (WHERE age conditions) |
| secureops_readonly | Reporting, analytics | SELECT only on all tables |

### Connection Pooling

- Use `asyncpg` connection pool with `min_size=5`, `max_size=20` (tuned per environment).
- Every connection sets `app.current_tenant_id` via `SET LOCAL` at transaction start.
- Pool connections are reset on return (no stale tenant context).

---

## 10. Performance Considerations

### Query Patterns and Indexes

| Query Pattern | Index Used |
|--------------|------------|
| Dashboard: findings by severity for a tenant | `idx_finding_tenant_severity` |
| Open findings for a tenant | `idx_finding_open` (partial) |
| Finding deduplication on import | `idx_finding_dedup` |
| Evidence for a control | `ControlEvidence` join + `idx_evidence_tenant` |
| Audit trail for a resource | `idx_audit_tenant_resource` |
| Upcoming risk reviews | `idx_risk_review_due` (partial) |
| SLA-breached remediation tasks | `idx_remediation_sla` (partial) |
| Unread notifications | `idx_notification_user_unread` (partial) |

### Pagination

All list endpoints use keyset pagination (cursor-based) rather than OFFSET/LIMIT for consistent performance on large datasets. The cursor is typically `(created_at, id)`.

### Batch Operations

- Finding imports from scanners use `INSERT ... ON CONFLICT (tenant_id, source, source_finding_id) DO UPDATE` for upsert.
- Asset discovery uses batch upsert keyed on `(tenant_id, resource_id)`.
- Evidence collection runs insert in batches of 100.

### Partitioning (Future)

If `audit_event` or `finding` tables grow beyond ~100M rows, partition by `created_at` using declarative range partitioning. Not required for MVP but the schema is designed to support it (no cross-partition foreign keys to these tables).
