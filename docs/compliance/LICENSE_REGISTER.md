# License Register — Software Bill of Materials (SBOM)

> SecureOps — Living document. Update whenever dependencies change.
>
> Last reviewed: 2024-11-19

## Compatibility Legend

| Symbol | Meaning |
|---|---|
| OK | Compatible with proprietary SaaS distribution |
| REVIEW | Requires per-component or legal review before use |
| BLOCKED | Incompatible with proprietary SaaS without separate license |

---

## Backend Dependencies (Python)

| Package | License | Compatibility | Obligations | Notes |
|---|---|---|---|---|
| fastapi | MIT | OK | Include license notice | Web framework |
| uvicorn | BSD-3-Clause | OK | Include license notice | ASGI server |
| sqlalchemy | MIT | OK | Include license notice | ORM / database toolkit |
| alembic | MIT | OK | Include license notice | Database migrations |
| asyncpg | Apache 2.0 | OK | Include license + NOTICE | PostgreSQL async driver |
| pydantic | MIT | OK | Include license notice | Data validation |
| pydantic-settings | MIT | OK | Include license notice | Settings management |
| python-jose | MIT | OK | Include license notice | JWT handling |
| bcrypt | Apache 2.0 | OK | Include license + NOTICE | Password hashing (replaced passlib, ADR-004) |
| email-validator | Unlicense | OK | None required | Email validation (pydantic[email]) |
| python-multipart | Apache 2.0 | OK | Include license + NOTICE | Form data parsing |
| redis (redis-py) | MIT | OK | Include license notice | Redis client |
| celery | BSD-3-Clause | OK | Include license notice | Task queue |
| httpx | BSD-3-Clause | OK | Include license notice | HTTP client |
| boto3 | Apache 2.0 | OK | Include license + NOTICE | AWS SDK |
| azure-storage-blob | MIT | OK | Include license notice | Azure Blob SDK |
| opentelemetry-api | Apache 2.0 | OK | Include license + NOTICE | Telemetry API |
| opentelemetry-sdk | Apache 2.0 | OK | Include license + NOTICE | Telemetry SDK |
| opentelemetry-instrumentation-fastapi | Apache 2.0 | OK | Include license + NOTICE | FastAPI instrumentation |
| structlog | Apache 2.0 / MIT | OK | Include license notice | Structured logging |

### Backend Dev Dependencies

| Package | License | Compatibility | Notes |
|---|---|---|---|
| pytest | MIT | OK | Test framework (dev only) |
| pytest-asyncio | MIT | OK | Async test support |
| pytest-cov | MIT | OK | Coverage reporting |
| factory-boy | MIT | OK | Test fixtures |
| ruff | MIT | OK | Linter / formatter |
| mypy | MIT | OK | Type checker |
| bandit | Apache 2.0 | OK | Security linter |
| safety | MIT | OK | Dependency vulnerability check |

---

## Frontend Dependencies (Node.js)

| Package | License | Compatibility | Obligations | Notes |
|---|---|---|---|---|
| next | MIT | OK | Include license notice | React framework |
| react | MIT | OK | Include license notice | UI library |
| react-dom | MIT | OK | Include license notice | React DOM renderer |
| react-hook-form | MIT | OK | Include license notice | Form state |
| zod | MIT | OK | Include license notice | Schema validation |
| @hookform/resolvers | MIT | OK | Include license notice | Form + Zod bridge |
| @tanstack/react-query | MIT | OK | Include license notice | Server state management |
| clsx | MIT | OK | Include license notice | Class name utility |
| tailwind-merge | MIT | OK | Include license notice | Tailwind class merge |
| lucide-react | ISC | OK | Include license notice | Icon library |

### Frontend Dev Dependencies

| Package | License | Compatibility | Notes |
|---|---|---|---|
| typescript | Apache 2.0 | OK | Language (dev only) |
| @types/react | MIT | OK | Type definitions |
| @types/react-dom | MIT | OK | Type definitions |
| @types/node | MIT | OK | Type definitions |
| tailwindcss | MIT | OK | CSS framework |
| daisyui | MIT | OK | Tailwind component lib |
| postcss | MIT | OK | CSS processing |
| autoprefixer | MIT | OK | CSS vendor prefixes |
| eslint | MIT | OK | Linter |
| eslint-config-next | MIT | OK | ESLint config for Next.js |
| vitest | MIT | OK | Test framework |
| @testing-library/react | MIT | OK | React test utilities |
| @testing-library/jest-dom | MIT | OK | DOM matchers |
| @vitejs/plugin-react | MIT | OK | Vite React support |

---

## Infrastructure Dependencies

| Component | License | Compatibility | Notes |
|---|---|---|---|
| PostgreSQL 16 | PostgreSQL License (permissive) | OK | Primary database |
| Redis 7 | BSD-3-Clause (Redis Source Available License for 7.4+) | REVIEW | Verify exact version; RSAL applies to Redis >= 7.4. Use 7.2.x if RSAL is a concern. |
| Docker | Apache 2.0 (Engine) | OK | Container runtime |
| Docker Compose | Apache 2.0 | OK | Development orchestration |
| Node.js 20 LTS | MIT | OK | Frontend runtime |
| Python 3.12 | PSF License | OK | Backend runtime |

---

## Open-Source Security Engines

| Engine | License | Compatibility | Integration Phase | Obligations / Risks |
|---|---|---|---|---|
| **Prowler** | Apache 2.0 | OK | Phase 3 | Include license + NOTICE. Containerized execution only; no code copied into our codebase. |
| **Trivy** | Apache 2.0 | OK | Phase 4 | Include license + NOTICE. Containerized execution only. |
| **DefectDojo** | BSD-3-Clause | OK | Phase 4 (optional) | Include license notice. API integration only; deployed as separate service. |
| **CloudQuery** (core) | Apache 2.0 | OK | Phase 3 (optional) | Core is fine. **Each plugin has its own license — audit individually before use.** |
| **CloudQuery plugins** | Various | REVIEW | Phase 3 (optional) | AWS plugin: Apache 2.0. Azure plugin: Apache 2.0. Others: verify per-plugin. Some may be proprietary or restrictive. |
| **CISO Assistant** | **AGPL-3.0** | **BLOCKED** | Never (without commercial license) | AGPL requires derivative works and network-interacting software to be released under AGPL. **Incompatible with proprietary SaaS.** Do not incorporate code, schemas, or framework data. A commercial license may be negotiable — requires legal review. |

---

## Compliance Framework Content

| Content | Status | Notes |
|---|---|---|
| SOC 2 Trust Services Criteria | Use permitted identifiers | TSC names/numbers are factual references. Do not reproduce AICPA copyrighted assessment text without license. |
| ISO 27001:2022 controls | Licensed standard | Control titles (Annex A) are widely referenced. Full standard text requires purchase from ISO/national body. Do not embed standard text. |
| NIST CSF 2.0 | Public domain (US Gov) | Freely usable. Attribute to NIST. |
| CIS Controls | CC BY-NC-SA 4.0 | Non-commercial use only in the free version. Commercial use requires CIS SecureSuite membership. |

---

## Actions Required

| Action | Priority | Owner | Status |
|---|---|---|---|
| Verify Redis version and license (RSAL vs BSD) | High | DevOps | Pending |
| Audit CloudQuery plugin licenses before integration | High | Security Architect | Pending — Phase 3 |
| Obtain legal opinion on CISO Assistant AGPL implications | Medium | Legal / Product | Pending |
| Verify CIS Controls license for commercial use | Medium | Product | Pending |
| Set up automated license scanning in CI (e.g., FOSSA, licensee) | Medium | DevOps | Pending |
| Create NOTICE file aggregating all Apache 2.0 NOTICE requirements | Low | Backend Engineer | Pending |
| Review transitive dependency licenses | Medium | Security | Pending |

---

## Maintenance

This register must be updated when:

- A direct dependency is added, removed, or upgraded.
- An open-source engine is added or replaced.
- A new compliance framework is added to the product.
- A license audit reveals new obligations.
- Transitive dependency scanning surfaces a concern.

Automated license scanning in CI (see Actions Required) should flag new dependencies for review.
