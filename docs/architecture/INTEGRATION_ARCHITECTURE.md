# Integration Architecture

> SecureOps — Open-Source Engine Integration Strategy

## Overview

SecureOps integrates mature open-source security engines while keeping a proprietary commercial core. Every engine is accessed through an **adapter interface** so that any engine can be replaced without redesigning the application.

No engine runs inside the main API process. All scanning and heavy analysis is delegated to **background workers** that execute engines in isolated containers.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      SecureOps Core (API + Workers)             │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  GRC Engine   │  │  Findings DB │  │  Evidence Store        │  │
│  │  (Proprietary)│  │  (Normalized)│  │  (Blob / S3)          │  │
│  └──────────────┘  └──────┬───────┘  └───────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────┴────────────────────────────────┐    │
│  │              Scanner Adapter Layer                       │    │
│  │                                                          │    │
│  │  ┌─────────────────┐  ┌─────────────────┐               │    │
│  │  │ CloudScanner     │  │ VulnScanner      │              │    │
│  │  │ Protocol         │  │ Protocol         │              │    │
│  │  │                  │  │                  │              │    │
│  │  │ + execute(cfg)   │  │ + execute(cfg)   │              │    │
│  │  │ + parse(output)  │  │ + parse(output)  │              │    │
│  │  │ + normalize()    │  │ + normalize()    │              │    │
│  │  │ + health()       │  │ + health()       │              │    │
│  │  └────────┬────────┘  └────────┬────────┘               │    │
│  └───────────┼─────────────────────┼────────────────────────┘    │
│              │                     │                             │
└──────────────┼─────────────────────┼─────────────────────────────┘
               │                     │
    ┌──────────┴──────────┐    ┌─────┴──────────────┐
    │ Container Isolation │    │ Container Isolation │
    │                     │    │                     │
    │  ┌───────────────┐  │    │  ┌───────────────┐  │
    │  │   Prowler     │  │    │  │    Trivy       │  │
    │  │  (Cloud Sec)  │  │    │  │  (Vuln Scan)   │  │
    │  └───────────────┘  │    │  └───────────────┘  │
    │                     │    │                     │
    │  ┌───────────────┐  │    │  ┌───────────────┐  │
    │  │  CloudQuery   │  │    │  │  DefectDojo    │  │
    │  │  (Inventory)  │  │    │  │  (Aggregation) │  │
    │  │  [Phase 3+]   │  │    │  │  [Phase 4+]    │  │
    │  └───────────────┘  │    │  └───────────────┘  │
    └─────────────────────┘    └─────────────────────┘

              ▲                         ▲
              │                         │
    Tenant credentials           Scan targets
    (short-lived, scoped)        (repos, images, IaC)
```

---

## Adapter Pattern

Every scanner integration implements a common protocol. The application code never calls Prowler or Trivy directly — it calls the adapter.

```python
# backend/app/integrations/base.py  (conceptual)

class ScanRequest:
    tenant_id: str
    connection_id: str
    scan_type: str
    parameters: dict

class NormalizedFinding:
    source_engine: str
    source_id: str
    title: str
    description: str
    severity: Severity       # CRITICAL | HIGH | MEDIUM | LOW | INFO
    resource_type: str
    resource_id: str
    remediation: str | None
    raw_data: dict

class ScannerAdapter(Protocol):
    engine_name: str

    async def validate_connection(self, config: dict) -> bool: ...
    async def execute_scan(self, request: ScanRequest) -> ScanExecution: ...
    def parse_results(self, raw_output: bytes) -> list[NormalizedFinding]: ...
    async def health_check(self) -> bool: ...
```

Benefits:

- **Replaceability** — swap Prowler for ScoutSuite or custom checks without changing the domain layer.
- **Testability** — mock adapters for unit tests; no real containers needed.
- **Isolation** — each adapter owns its output parsing and normalization logic.
- **Consistency** — all findings land in one normalized schema regardless of source.

---

## Engine Evaluations

### 1. Prowler — Cloud Security Assessments

| Attribute | Detail |
|---|---|
| **Repository** | prowler-cloud/prowler |
| **License** | Apache 2.0 |
| **Purpose** | Security posture checks for AWS, Azure, GCP, Kubernetes |
| **Version strategy** | Pin to release tags (e.g., `prowler:4.x`) |

**Integration method**: Containerized CLI execution.

- Celery worker spawns a Docker container running `prowler` with tenant-specific credentials.
- Output format: `--output-formats json-ocsf` for structured findings.
- Worker reads the JSON output from a mounted volume or stdout, then passes it to the Prowler adapter for normalization.

**Containerization strategy**:

- Use the official `prowler/prowler` image pinned to a reviewed digest.
- Each execution runs in a fresh, short-lived container.
- Mount a temporary directory for output; delete after ingestion.
- No persistent state inside the container.

**Multi-tenant compatibility**:

- Each scan receives only the target tenant's cloud credentials via environment variables or mounted credential files.
- Credentials are fetched from encrypted storage at execution time, never baked into images.
- Container network is restricted to outbound cloud API calls only (no lateral access).

**Resource requirements**:

- CPU: 1–2 vCPU per scan (AWS full scan can take 15–45 min).
- Memory: 512 MB–2 GB depending on account size.
- Enforce `--cpus` and `--memory` Docker limits per container.
- Limit concurrent scans per worker node.

**Replacement strategy**:

- Implement `ProwlerAdapter(ScannerAdapter)`.
- To replace, implement a new adapter (e.g., `ScoutSuiteAdapter`) with the same protocol.
- Swap via configuration without domain code changes.

**Risks**:

| Risk | Severity | Mitigation |
|---|---|---|
| Long-running scans block workers | Medium | Dedicated scan worker pool, timeouts, scan cancellation |
| Credential leakage in container output | High | Scrub stdout/stderr, validate output before storage |
| Prowler breaking changes on upgrade | Medium | Pin versions, test upgrades in staging first |
| Resource exhaustion from large accounts | Medium | Per-container limits, scan scope configuration |

---

### 2. Trivy — Vulnerability and Configuration Scanning

| Attribute | Detail |
|---|---|
| **Repository** | aquasecurity/trivy |
| **License** | Apache 2.0 |
| **Purpose** | Container images, filesystems, dependencies, IaC, secrets |
| **Version strategy** | Pin to release tags (e.g., `aquasec/trivy:0.57`) |

**Integration method**: Containerized CLI execution.

- Worker spawns a Trivy container with the scan target (image reference, filesystem path, or git repo).
- Output: `--format json` for structured results.
- Adapter parses Trivy's JSON schema and normalizes vulnerabilities with CVE references.

**Containerization strategy**:

- Official `aquasec/trivy` image pinned to reviewed digest.
- DB cache volume shared across executions to avoid re-downloading the vulnerability database on every scan.
- Fresh container per scan; shared read-only DB cache mount.

**Multi-tenant compatibility**:

- Scan targets are tenant-scoped (their container images, their repos).
- No cross-tenant target access — the worker only receives the target identifier for the requesting tenant.
- Container registry credentials (if needed) are tenant-specific and injected at runtime.

**Resource requirements**:

- CPU: 0.5–1 vCPU per scan (typically completes in 1–5 min).
- Memory: 256 MB–1 GB.
- DB cache: ~500 MB disk, updated periodically.
- Much lighter than Prowler; can run more concurrent instances.

**Replacement strategy**:

- Implement `TrivyAdapter(ScannerAdapter)`.
- Alternative: Grype, Snyk CLI, or custom scanner behind the same interface.

**Risks**:

| Risk | Severity | Mitigation |
|---|---|---|
| Stale vulnerability DB | Medium | Scheduled DB updates, track DB freshness metadata |
| False positives in dependency scans | Low | Severity filtering, user-configurable thresholds |
| Large images cause timeouts | Medium | Scan timeouts, image size limits |
| Network needed for DB updates | Low | Pre-populate DB in CI, offline DB option |

---

### 3. DefectDojo — Vulnerability Aggregation

| Attribute | Detail |
|---|---|
| **Repository** | DefectDojo/django-DefectDojo |
| **License** | BSD-3-Clause |
| **Purpose** | Vulnerability aggregation, deduplication, remediation tracking |
| **Phase** | Phase 4 — optional integration, not MVP |

**Integration method**: REST API.

- If deployed, SecureOps pushes scan results to DefectDojo via its API for advanced deduplication.
- SecureOps pulls back deduplicated findings and enrichment data.
- SecureOps's own findings DB remains the source of truth; DefectDojo is an enrichment layer.

**Containerization strategy**:

- DefectDojo ships its own Docker Compose stack (Django + PostgreSQL + Celery + RabbitMQ).
- Deploy as a sidecar service or external deployment.
- SecureOps communicates only via DefectDojo's authenticated REST API.

**Multi-tenant compatibility**:

- DefectDojo supports "products" and "product types" which can map to tenants.
- However, DefectDojo is not designed as a multi-tenant SaaS — tenant isolation within DefectDojo is application-level, not row-level security.
- **Decision**: If used, deploy one DefectDojo instance per tenant group, or use it only for single-tenant deployments. Evaluate carefully before enabling in multi-tenant mode.

**Resource requirements**:

- Significant: its own PostgreSQL, Redis/RabbitMQ, Django workers.
- Adds operational complexity.
- Justify only when advanced dedup and vulnerability workflow management is needed beyond our built-in capabilities.

**Replacement strategy**:

- Implement `DefectDojoAdapter(ScannerAdapter)` or a dedicated `VulnAggregatorAdapter`.
- Our own dedup engine is the default; DefectDojo is opt-in.

**Risks**:

| Risk | Severity | Mitigation |
|---|---|---|
| Operational overhead of running DefectDojo | Medium | Make it optional, document resource requirements |
| Tenant isolation gaps | High | Evaluate per-tenant isolation before enabling |
| API breaking changes | Medium | Pin DefectDojo version, integration tests |
| Data sync consistency | Medium | Idempotent sync jobs, conflict resolution logic |

---

### 4. CloudQuery — Cloud Asset Inventory

| Attribute | Detail |
|---|---|
| **Repository** | cloudquery/cloudquery |
| **License** | Apache 2.0 (core); **plugins have individual licenses** |
| **Purpose** | Cloud resource inventory and configuration data |
| **Phase** | Phase 3+ — optional, evaluate after Prowler integration |

**Integration method**: CLI execution with PostgreSQL destination.

- CloudQuery syncs cloud resources into a PostgreSQL database.
- SecureOps reads the inventory tables for asset context and enrichment.
- Alternative: use Prowler's built-in asset discovery for the MVP.

**Containerization strategy**:

- Official CloudQuery Docker image.
- Runs as a scheduled sync job (e.g., every 6–24 hours).
- Writes to a dedicated schema in the SecureOps database or a separate inventory database.

**Multi-tenant compatibility**:

- Each sync runs with a single tenant's cloud credentials.
- Output tables must be tagged with `tenant_id` for isolation.
- CloudQuery itself has no multi-tenant concept; isolation is enforced by our orchestration layer.

**Resource requirements**:

- Varies by cloud account size and plugins.
- CPU: 1–2 vCPU during sync.
- Memory: 512 MB–2 GB.
- Disk: depends on number of resources synced.

**Replacement strategy**:

- Implement `CloudQueryAdapter` behind an `InventorySource` protocol.
- Alternative: Steampipe, custom AWS/Azure SDK collectors.

**Risks**:

| Risk | Severity | Mitigation |
|---|---|---|
| **Plugin licenses vary** — some may not be Apache 2.0 | High | Audit each plugin's license before use |
| Schema changes between versions | Medium | Pin versions, migration tests |
| Large sync durations for big accounts | Medium | Incremental sync, resource type filtering |
| Credential handling across plugins | Medium | Same credential isolation as Prowler |

---

### 5. CISO Assistant — GRC Workflows

| Attribute | Detail |
|---|---|
| **Repository** | intuitem/ciso-assistant-community |
| **License** | **AGPL-3.0** |
| **Purpose** | GRC workflows, framework management, risk assessments |
| **Decision** | **DO NOT INTEGRATE** |

**Why not**:

- AGPL-3.0 requires that any software interacting with CISO Assistant over a network must also be released under AGPL-3.0 or a compatible license.
- Incorporating AGPL code into a proprietary SaaS product creates license obligations that are incompatible with our commercial model.
- Even API-level integration may trigger AGPL obligations depending on coupling.

**What we take from it**:

- Study its data model for inspiration on framework versioning, control mappings, and risk register design.
- Do not copy code, schema definitions, or framework content.
- Build our own GRC engine from scratch.

**Commercial option**:

- CISO Assistant offers a commercial license (ciso-assistant.com). If future business requirements justify it, negotiate a commercial license that permits proprietary use. This requires legal review.

---

## Integration Lifecycle

Every integration follows this lifecycle:

```
1. EVALUATE     — License, API stability, multi-tenant fit, resources
2. PROTOTYPE    — Adapter + container execution in dev environment
3. TEST         — Unit tests (mocked), integration tests (real container)
4. HARDEN       — Credential isolation, resource limits, output validation
5. DEPLOY       — Staged rollout, monitoring, alerting
6. MAINTAIN     — Version pinning, upgrade testing, deprecation watching
```

---

## Credential Flow for Scanning

```
┌──────────┐    ┌──────────────┐    ┌────────────────┐    ┌───────────┐
│  Tenant   │───▶│  SecureOps   │───▶│  Celery Worker  │───▶│  Scanner  │
│  Portal   │    │  API         │    │                 │    │ Container │
└──────────┘    └──────────────┘    └────────────────┘    └───────────┘
                       │                     │
                       │  1. Validate         │  3. Fetch encrypted
                       │     request          │     credentials from
                       │                      │     secret store
                       │  2. Enqueue          │
                       │     scan job         │  4. Inject as env vars
                       │     (no creds        │     into container
                       │      in queue)       │
                       │                      │  5. Scrub creds from
                       ▼                      │     output before
                 ┌──────────┐                 │     storage
                 │  Redis   │                 │
                 │  Queue   │                 ▼
                 │ (job ID  │           6. Parse + normalize
                 │  only)   │              findings
                 └──────────┘
```

Credentials never appear in the job queue payload. Workers fetch them at execution time from encrypted storage.

---

## Phased Integration Timeline

| Phase | Engine | Status | Priority |
|---|---|---|---|
| Phase 1 | — (Foundation) | Adapter interfaces defined | — |
| Phase 3 | Prowler | Primary cloud security engine | P0 |
| Phase 3 | CloudQuery | Evaluate for asset inventory | P2 |
| Phase 4 | Trivy | Primary vulnerability scanner | P0 |
| Phase 4 | DefectDojo | Evaluate for advanced dedup | P2 |
| Never | CISO Assistant | AGPL — build our own GRC | Excluded |

---

## Decision Records

| Decision | Rationale | Date |
|---|---|---|
| Use adapter pattern for all integrations | Engines must be replaceable without domain changes | 2024-11-19 |
| Containerized execution for all scanners | Isolation, resource limits, credential safety | 2024-11-19 |
| Credentials never in queue payloads | Defense in depth — queue compromise does not leak creds | 2024-11-19 |
| Exclude CISO Assistant (AGPL) | License incompatible with proprietary SaaS | 2024-11-19 |
| Build own GRC engine | Full control over compliance logic, no license risk | 2024-11-19 |
| CloudQuery plugins need per-plugin license audit | Core is Apache 2.0 but plugins vary | 2024-11-19 |
