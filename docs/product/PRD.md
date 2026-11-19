# SecureOps — Product Requirements Document

**Version:** 0.1.0
**Status:** Draft
**Last Updated:** 2026-11-19

---

## 1. Executive Summary

**SecureOps** is a unified Security Operations and Governance, Risk & Compliance (GRC) SaaS platform.

**Positioning:** *One platform to manage security, compliance, risk, and audit evidence.*

Organizations today manage security posture, compliance obligations, vulnerability remediation, and audit evidence across disconnected tools — spreadsheets, siloed scanners, manual evidence folders, and fragmented GRC platforms. SecureOps consolidates these into a single multi-tenant platform that connects cloud security findings to compliance controls, maps vulnerabilities to risk, automates evidence collection, and prepares organizations for audit with continuous visibility.

**Core value proposition:**

- Eliminate tool sprawl by unifying cloud security, vulnerability management, and GRC.
- Reduce compliance preparation from months to weeks with automated evidence and control mapping.
- Provide continuous security posture visibility across cloud environments.
- Enable MSPs to manage multiple customer tenants from a single platform.
- Deliver AI-assisted security operations without replacing human judgment on consequential decisions.

---

## 2. Target Market

### 2.1 Customer Segments

| Segment | Size | Primary Pain Point |
|---|---|---|
| SaaS Companies | 10–200 employees | SOC 2/ISO 27001 readiness with limited security staff |
| Technology Startups | 10–100 employees | First-time compliance, no dedicated GRC team |
| Managed Service Providers (MSPs) | 20–500 employees | Managing security/compliance across multiple customer tenants |
| Cloud Consultancies | 10–200 employees | Delivering security assessments and posture reports to clients |
| Mid-Market Businesses | 200–2,000 employees | Consolidating fragmented security and compliance tooling |
| Enterprise Organizations | 2,000+ employees | Unified risk visibility and audit automation at scale |

### 2.2 Initial Market Focus

- **Geographies:** United States, United Kingdom, United Arab Emirates.
- **Ideal Customer Profile:** SaaS companies and MSPs with 10–200 employees, pursuing or maintaining SOC 2 or ISO 27001 certification, running workloads on AWS and/or Azure.
- **Expansion path:** Mid-market → enterprise; additional geographies as demand warrants.

### 2.3 Competitive Landscape

SecureOps competes with:

- **Pure-play GRC** platforms (Vanta, Drata, Sprinto) — strong on compliance automation, weaker on cloud security depth and vulnerability management.
- **CSPM tools** (Wiz, Prisma Cloud, Prowler) — strong on cloud posture, no GRC or evidence management.
- **Vulnerability managers** (Qualys, Tenable, DefectDojo) — focused on vulnerabilities, no compliance mapping.
- **Enterprise GRC** (ServiceNow GRC, Archer) — comprehensive but expensive and complex for mid-market.

**Differentiation:** SecureOps bridges all four domains in a single, affordable platform purpose-built for SaaS companies and MSPs.

---

## 3. Product Modules

### Module A — Organization & Tenancy

Multi-tenant foundation supporting isolated customer environments and MSP management.

| Capability | Description |
|---|---|
| Organization creation | Self-service signup with organization provisioning |
| Tenant isolation | Complete data separation per organization; enforced at database and application layers |
| User management | Invite, activate, deactivate, remove users within an organization |
| Team management | Group users into teams for assignment and notification purposes |
| Invitations | Email-based invitation flow with expiring tokens |
| Role-based access control | Predefined and custom roles with granular permissions |
| Subscription management | Plan tiers, feature gates, usage limits |
| Organization settings | Branding, notification preferences, timezone, data retention policies |
| Audit history | Append-only log of all significant actions within the organization |

**Key constraints:**
- Every tenant-owned resource is scoped by `tenant_id` at the database level.
- Tenant identity is resolved from the authenticated session, never from client-supplied parameters.
- PostgreSQL Row-Level Security (RLS) is used as defense-in-depth.

### Module B — Compliance Management

Framework-aware compliance engine supporting multiple standards with version tracking.

**Initial frameworks:**

| Framework | Version | Status |
|---|---|---|
| SOC 2 | 2017 Trust Services Criteria | MVP |
| ISO 27001 | 2022 | MVP |
| NIST CSF | 2.0 | Post-MVP |
| CIS Controls | v8 | Post-MVP |
| GDPR | — | Post-MVP |
| ISO 27701 | 2019 | Planned |
| ISO 42001 | 2023 | Planned |
| HIPAA | — | Planned |
| PCI DSS | v4.0 | Planned |

**Capabilities:**

- **Framework registry** — versioned framework definitions; frameworks can be updated without breaking historical assessments.
- **Control library** — organization-specific controls derived from framework requirements.
- **Framework-to-control mappings** — many-to-many relationships. A single control can satisfy requirements across multiple frameworks. Mappings are not hardcoded into application logic.
- **Control ownership** — every control has an assigned owner and optional delegates.
- **Control testing** — define test procedures, record test results, schedule recurring tests.
- **Control status & effectiveness** — track implementation status (Not Implemented → Partially → Fully Implemented) and operational effectiveness.
- **Evidence requirements** — each control defines required evidence types, collection frequency, and freshness thresholds.
- **Gap assessments** — identify controls that are not implemented, lack evidence, or have expired evidence.
- **Compliance reports** — generate per-framework readiness reports showing control coverage, gaps, and evidence status.

**Constraints:**
- Framework content must respect applicable licensing and copyright. Use licensed materials, permitted identifiers, or customer-supplied content as appropriate.
- Internal readiness scores do not represent formal certification or independent audit assurance. The UI must make this distinction clear.

### Module C — Risk Management

Structured risk register with scoring, ownership, treatment tracking, and review history.

| Capability | Description |
|---|---|
| Risk register | Central repository of identified risks with unique identifiers |
| Risk categories | Configurable taxonomy (operational, technical, compliance, strategic, third-party) |
| Likelihood & impact | Configurable scales (e.g., 1–5) with qualitative descriptors |
| Risk scoring | Inherent risk = likelihood × impact; residual risk after treatment |
| Risk ownership | Every risk has a responsible owner; ownership is audited |
| Risk treatment | Accept, mitigate, transfer, avoid — with documented rationale |
| Mitigation tracking | Link mitigations to remediation tasks; track completion |
| Residual risk | Recalculate after treatment; track delta from inherent |
| Review history | Timestamped review log; configurable review cadence with reminders |

**Constraints:**
- Risks without an assigned owner cannot be marked as "accepted."
- Risk review history is append-only.

### Module D — Cloud Security

Cloud security posture management with multi-provider support.

**Initial providers:**

| Provider | Scope | Priority |
|---|---|---|
| AWS | IAM, S3, EC2, RDS, VPC, Lambda, CloudTrail, KMS, etc. | MVP |
| Microsoft Azure | AAD, Storage, VMs, SQL, NSGs, Key Vault, etc. | MVP |
| Google Cloud | — | Post-MVP |
| Kubernetes | — | Post-MVP |
| Microsoft 365 | — | Planned |
| GitHub | — | Planned |

**Capabilities:**

- **Cloud account connections** — secure credential storage for read-only scanning; support for cross-account roles (AWS) and service principals (Azure).
- **Asset discovery** — inventory of cloud resources with metadata, tags, and relationships.
- **Configuration assessments** — rule-based checks against security best practices and compliance benchmarks via Prowler integration.
- **Security findings** — normalized findings with severity (Critical/High/Medium/Low/Info), affected resource, remediation guidance.
- **Risk mapping** — link cloud findings to risk register entries and compliance controls.
- **Historical snapshots** — point-in-time posture records for trend analysis and audit.
- **Remediation recommendations** — actionable guidance per finding; link to remediation tasks.
- **Reassessment** — re-scan to verify remediation; track finding lifecycle (Open → In Progress → Resolved → Verified).

**Constraints:**
- Read-only cloud permissions only. No automated infrastructure remediation in v1.
- Scanner containers are isolated with CPU/memory limits and restricted network egress.
- Cloud credentials never appear in scanner output or application logs.

### Module E — Vulnerability Management

Centralized vulnerability tracking with scanner integration and deduplication.

| Capability | Description |
|---|---|
| Scanner integration | Import findings from Trivy (containers, filesystems, IaC, dependencies, secrets) |
| Vulnerability imports | Ingest from multiple scanners; normalize to internal schema |
| CVE tracking | Link vulnerabilities to CVE identifiers; track CVSS scores and EPSS data |
| Severity & prioritization | Combine CVSS, exploitability, asset criticality, and business context |
| Asset relationships | Map vulnerabilities to specific assets, services, and owners |
| Finding deduplication | Merge duplicate findings across scanners and scan runs |
| Remediation ownership | Assign vulnerability remediation to specific users/teams |
| SLA tracking | Define resolution SLAs by severity; alert on approaching/breached deadlines |
| Resolution verification | Re-scan to confirm fix; track false-positive dispositions |
| Historical records | Full lifecycle history per vulnerability |

**Optional integration:** DefectDojo for advanced aggregation across multiple scanner types.

### Module F — Evidence Management

Secure evidence lifecycle management for audit readiness.

| Capability | Description |
|---|---|
| Manual upload | Drag-and-drop upload with metadata (description, control mapping, period) |
| Automated collection | Scheduled evidence collection from integrations (cloud configs, scan results, access reviews) |
| Evidence source | Track origin (manual, automated, integration name) |
| Collection timestamps | UTC timestamp for collection and processing |
| Evidence versioning | New uploads create new versions; previous versions are preserved |
| Evidence expiry | Configurable freshness windows; alerts when evidence ages out |
| Evidence approval | Workflow for reviewer approval before evidence is marked valid |
| Integrity hashes | SHA-256 hash computed at upload; verified on retrieval |
| Evidence retention | Configurable retention periods; automated cleanup with audit trail |
| Control mappings | Link evidence to one or more controls across frameworks |
| Audit export | Package evidence for external auditors with index and integrity manifest |

**Constraints:**
- Historical evidence is never silently overwritten. Overwrite attempts create a new version.
- Evidence is encrypted at rest and in transit.
- File type validation and size limits enforced server-side (default 50 MB).
- Executable files are rejected.
- Tenant ownership is verified before every download.
- All access is logged.

### Module G — Remediation Management

Task-based remediation workflow connecting findings to resolution.

| Capability | Description |
|---|---|
| Task creation | Create from cloud findings, vulnerabilities, risk mitigations, or compliance gaps |
| Owner assignment | Assign to users or teams; support reassignment with history |
| Deadlines | Due dates with SLA awareness; escalation on breach |
| Progress tracking | Status workflow: Open → In Progress → Pending Verification → Resolved |
| Comments | Threaded comments with mentions and attachments |
| Verification | Require evidence or re-scan before marking resolved |
| History | Full audit trail of status changes, assignments, and comments |
| Notifications | Email/in-app notifications for assignments, deadlines, and status changes |

### Module H — AI Security Assistant

AI-powered assistance for security and compliance workflows.

| Capability | Description |
|---|---|
| Finding explanations | Plain-language explanation of security findings and their business impact |
| Risk summaries | Aggregate risk posture summaries for management reporting |
| Policy drafting | Generate policy document drafts based on framework requirements |
| Evidence descriptions | Suggest descriptions and metadata for uploaded evidence |
| Remediation recommendations | Context-aware fix guidance for specific findings |
| Compliance gap summaries | Natural-language gap analysis for framework readiness |
| Executive reporting | Generate board-ready security posture summaries |

**Constraints:**
- AI output is clearly labeled as AI-generated suggestions requiring human review.
- AI cannot independently mark a control as compliant or declare an organization certified.
- Customer evidence, credentials, and sensitive infrastructure data are never sent to external AI services without the customer's documented authorization and appropriate data-protection safeguards.
- AI features are gated behind explicit opt-in per organization.

---

## 4. User Roles

| Role | Description | Key Permissions |
|---|---|---|
| **Organization Administrator** | Full control over organization settings, users, billing, and integrations | All permissions; user/role management; billing; integration setup |
| **Security Manager** | Manages compliance programs, risk register, and security operations | Manage frameworks, controls, risks, evidence, remediation; view all findings; generate reports |
| **Engineer** | Resolves assigned findings and remediation tasks | View assigned findings/tasks; update remediation status; upload evidence; view relevant dashboards |
| **Auditor (Read-Only)** | Reviews compliance posture and evidence without modification | Read-only access to controls, evidence, findings, risks, and reports; export evidence packages |
| **MSP Administrator** | Manages multiple customer organizations from a parent tenant | All Organization Administrator permissions across managed tenants; cross-tenant dashboards and reporting |

**Authorization principles:**
- Default-deny: users have no access unless explicitly granted via role.
- Navigation items hidden for unauthorized roles, but authorization is enforced server-side — UI hiding is not a security control.
- Role changes are audit-logged.

---

## 5. Non-Functional Requirements

### 5.1 Performance Targets

These are engineering targets to be validated through representative load testing.

| Metric | Target | Conditions |
|---|---|---|
| API read (p95) | < 300 ms | Under agreed baseline load |
| API write (p95) | < 500 ms | Under agreed baseline load |
| Dashboard initial load | < 2 seconds | Under agreed baseline load |
| Worker memory | No uncontrolled growth | Sustained operation over 24 hours |
| Job reliability | No lost jobs during expected worker restarts | Graceful shutdown with in-flight completion |
| External integration retry | Exponential backoff with jitter | Circuit breaker after configurable failure threshold |

### 5.2 Scalability

- Support 100+ organizations with 50+ users each in a single deployment.
- Pagination for all list endpoints; no unbounded queries.
- Background processing for all heavy operations (scans, imports, report generation).
- Connection pooling for database and Redis.
- Horizontally scalable workers.
- Resource limits on scanner containers.

### 5.3 Reliability

- Health and readiness endpoints for all services.
- Graceful shutdown for workers with in-flight job completion.
- Dead-letter queues for permanently failed jobs.
- Idempotent job execution.
- Database migration safety (no destructive migrations without explicit review).
- Backup and restoration procedures with tested recovery.

### 5.4 Security

Security is a product feature, not an afterthought. See the Security Architecture document for full requirements. Summary:

- Multi-tenant isolation at database, application, and storage layers.
- Secure authentication with MFA and SSO support.
- Default-deny RBAC with resource-level authorization.
- Encryption at rest and in transit for all sensitive data.
- Append-only audit logging for security-relevant events.
- Dependency scanning, SAST, secret scanning, and container scanning in CI.
- No production containers running as root.

### 5.5 Observability

- Structured JSON logging via structlog.
- OpenTelemetry instrumentation for distributed tracing.
- Prometheus metrics with Grafana dashboards.
- Alerting on error rate spikes, queue depth growth, scanner failures, and authentication anomalies.

---

## 6. MVP Scope

The Minimum Viable Product consists of **Phase 1** (Platform Foundation) and **Phase 2** (GRC Engine).

### Phase 1 — Platform Foundation

| Component | Scope |
|---|---|
| Authentication | Email/password with bcrypt; JWT access/refresh tokens; session expiry and revocation |
| Multi-tenancy | Organization creation; tenant-scoped database access; RLS policies |
| RBAC | Organization Administrator, Security Manager, Engineer, Auditor roles with permissions |
| User management | Invite, activate, deactivate users; team creation |
| API foundation | FastAPI with versioned endpoints (`/api/v1/`); OpenAPI documentation |
| Frontend shell | Next.js app with authenticated layout, navigation, and role-aware routing |
| Audit logging | Append-only event log for auth, permission, and data-change events |
| Infrastructure | Docker Compose dev environment; CI pipeline with lint, test, security scan |
| Database | PostgreSQL with Alembic migrations; core tenant/user/role schema |

### Phase 2 — GRC Engine

| Component | Scope |
|---|---|
| Framework registry | SOC 2 and ISO 27001:2022 with versioned definitions |
| Control library | Organization-specific controls with framework mappings |
| Control management | Ownership, status tracking, test scheduling, effectiveness rating |
| Risk register | Risk creation, scoring, ownership, treatment, review history |
| Evidence management | Upload, versioning, integrity hashing, expiry, control mapping, audit export |
| Compliance dashboard | Per-framework readiness view with control coverage and gap indicators |
| Remediation tasks | Create from gaps; assign, track, verify |

**What is NOT in MVP:**
- Cloud security scanning (Phase 3)
- Vulnerability management (Phase 4)
- AI assistant (Phase 5)
- Billing/subscription management (Phase 6)
- MSP multi-customer management (Phase 6)
- SSO/SAML (Phase 6)
- Google Cloud, Kubernetes, M365 connectors

---

## 7. Success Metrics

### Product Metrics

| Metric | Target (6 months post-launch) | Measurement |
|---|---|---|
| Organizations onboarded | 20+ | Active organizations with at least one completed compliance assessment |
| Monthly active users | 100+ | Users logging in and performing actions within a 30-day window |
| Framework assessments started | 50+ | SOC 2 or ISO 27001 assessments with at least 25% control coverage |
| Evidence items collected | 500+ | Total evidence items across all organizations |
| Remediation tasks resolved | 200+ | Tasks moved to Resolved status with verification |

### Engineering Metrics

| Metric | Target | Measurement |
|---|---|---|
| Test coverage (backend) | > 80% line coverage | pytest-cov |
| Test coverage (frontend) | > 70% line coverage | vitest coverage |
| CI pass rate | > 95% | GitHub Actions success rate on main |
| Critical vulnerability SLA | < 48 hours to patch | Time from CVE disclosure to deployed fix |
| Incident response | < 4 hours to acknowledge | Time from alert to first human response |

### Business Metrics

| Metric | Target | Measurement |
|---|---|---|
| Time to first value | < 1 hour | Time from signup to first framework assessment started |
| Customer retention | > 90% monthly | Organizations active month-over-month |
| NPS | > 40 | Quarterly in-app survey |
| Support ticket volume | < 5 per org per month | Help desk tracking |

---

## 8. Constraints & Assumptions

### Constraints

1. **No custom cryptography.** All authentication, encryption, and hashing uses established libraries (bcrypt, python-jose, standard TLS).
2. **No auto-remediation in v1.** Cloud scanning is read-only. Automated infrastructure changes require explicit future authorization.
3. **Framework licensing.** SOC 2 Trust Services Criteria and ISO 27001 control text may have licensing restrictions. Use permitted identifiers or customer-supplied content.
4. **AGPL caution.** CISO Assistant Community is AGPL-licensed. No incorporation into our proprietary SaaS without legal review and compliance with AGPL obligations.
5. **No real customer data in development.** All test environments use synthetic fixtures.
6. **No production deployment without explicit authorization.** Infrastructure plans are reviewed but not applied without approval.
7. **Regional data residency is architecturally supported but not implemented in MVP.** Single-region deployment initially.
8. **AI features require customer opt-in.** No customer data sent to external AI services without documented authorization.

### Assumptions

1. Target customers have existing AWS and/or Azure workloads.
2. Customers have personnel who can serve as control owners (security manager or engineering lead).
3. Customers are pursuing or maintaining SOC 2 Type II or ISO 27001 certification.
4. PostgreSQL 16+ is available in the target deployment environment.
5. Docker and container orchestration are available for scanner execution.
6. Customers accept a web-based SaaS model (no on-premises requirement for MVP).
7. English is the primary interface language for MVP; localization readiness is built in but translations are deferred.
8. External auditors will use the Auditor role and evidence export, not direct database access.

---

## Appendix A — Module Dependency Map

```
┌─────────────────────────────────────────────────────────┐
│                  Module A: Organization & Tenancy        │
│              (Foundation — all modules depend on this)   │
└──────────┬──────────┬──────────┬──────────┬─────────────┘
           │          │          │          │
    ┌──────▼──┐  ┌────▼────┐  ┌─▼────┐  ┌─▼──────────┐
    │Module B │  │Module C │  │Mod D │  │  Module E   │
    │Compliance│  │  Risk   │  │Cloud │  │Vulnerability│
    └────┬─────┘  └───┬─────┘  └──┬───┘  └──────┬──────┘
         │            │           │              │
         ├────────────┼───────────┼──────────────┤
         │            │           │              │
    ┌────▼────────────▼───────────▼──────────────▼──┐
    │           Module F: Evidence Management        │
    └────────────────────┬──────────────────────────┘
                         │
    ┌────────────────────▼──────────────────────────┐
    │          Module G: Remediation Management      │
    └────────────────────┬──────────────────────────┘
                         │
    ┌────────────────────▼──────────────────────────┐
    │           Module H: AI Security Assistant      │
    └───────────────────────────────────────────────┘
```

## Appendix B — Glossary

| Term | Definition |
|---|---|
| Tenant | An isolated organization within the platform |
| Control | A security measure mapped to one or more framework requirements |
| Finding | A security issue discovered by a scanner or assessment |
| Evidence | An artifact demonstrating control implementation or effectiveness |
| Framework | A compliance standard (e.g., SOC 2, ISO 27001) with versioned requirements |
| RLS | PostgreSQL Row-Level Security — database-enforced tenant isolation |
| CSPM | Cloud Security Posture Management |
| GRC | Governance, Risk, and Compliance |
| MSP | Managed Service Provider |
| RBAC | Role-Based Access Control |
