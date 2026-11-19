# SecureOps Execution Tracker

Update this file after every meaningful milestone. Claims here must be backed by
command output from a real run.

## Status Summary

| Phase | Status | Notes |
|---|---|---|
| 0: Discovery and architecture | Done | Blueprint, ADR-001 to ADR-003, threat model |
| 1: Platform foundation | Done | Auth, tenancy, RBAC, audit |
| 2: GRC engine | Done, with gaps (see below) | Frontend uses mock data, and only local evidence storage exists |
| CI stabilization | Done locally (2026-11-19) | Waiting for a green GitHub Actions run |
| 3: Cloud security | Pending | Next phase |
| 4 to 6 | Pending | |

## Latest Verification (2026-11-19, local, Python 3.12, Node 20+)

| Check | Result |
|---|---|
| `ruff check .` / `ruff format --check .` | Pass |
| `mypy app/` (strict) | Pass, 71 files |
| `pytest -m "not performance"` | **457 passed**, 60% line coverage (fresh venv from declared deps only) |
| `bandit -r app/` | 2 reviewed, intentional placeholders (`nosec` annotated) |
| `npm ci` (fresh copy) | Pass (lockfile regenerated) |
| `next lint` / `tsc --noEmit` / `vitest --run` | Pass / Pass / 4 passed |

## CI Root Causes Fixed (2026-11-19)

1. The build backend `setuptools.backends._legacy` doesn't exist. Switched to `setuptools.build_meta`.
2. Setuptools auto-discovered both `app/` and `alembic/` as packages. Now only `app*` is packaged.
3. `email-validator` was missing, so every `EmailStr` schema crashed on import. Added `pydantic[email]`.
4. Ruff and mypy had never run, so 1,114 and 50 issues had built up. They are fixed, and test-only ignores are scoped narrowly.
5. The frontend had no ESLint config, an inconsistent `package-lock.json`, no jest-dom setup, and no tests.
6. CI's `cd frontend && npm ci || npm install` ran `npm install` in the repo root whenever `npm ci` failed. It is now `npm ci` only.
7. Gitleaks requires a paid licence for organization repositories, so it was removed. **Secret scanning is now a gap** (see Pending).

## Security Findings

| ID | Severity | Finding | Status |
|---|---|---|---|
| SF-001 | Critical | Path traversal in the local evidence store. A crafted filename could write files outside the tenant directory, including into another tenant's area. | Fixed. Filenames are sanitized and every read/write/delete is checked for containment. Tests in `tests/security/test_storage_path_traversal.py` |
| SF-002 | High | The `SECRET_KEY` default (`CHANGE-ME-IN-PRODUCTION`) was accepted in any environment, so JWTs were forgeable if the env var was unset. | Fixed, and fails closed. `ENVIRONMENT` defaults to `production`, and outside dev/test the app refuses to start with a missing, short or known-placeholder key. docker-compose, CI and the tests opt into development/test explicitly. |
| SF-003 | High | Auth was broken on fresh installs (passlib with bcrypt 5), and long passwords were silently truncated at 72 bytes. | Fixed. See ADR-004. |
| SF-004 | Medium | Token refresh trusted the tenant and role in the old token, so removed or demoted members could keep refreshing. API authorization already re-checked the database, which limited the impact. | Fixed. Refresh now re-checks live membership. |
| SF-005 | Medium | `?sort_by=` on risks was passed to `getattr(Risk, ...)` unchecked, so arbitrary attribute names caused 500s. | Fixed. Sort fields are allowlisted. |
| SF-006 | Low | List filters were typed as `str`, so invalid enum values caused 500s instead of 422s. | Fixed. Filters are typed as enums. |
| SF-007 | Low | The download `Content-Disposition` header was built from the raw filename, which allowed header breakage and caused a 500 for non-Latin names. | Fixed. Filenames are sanitized and bidi overrides stripped, and the header uses an RFC 5987 `filename*`. |
| SF-008 | Low | A rules-of-hooks violation on the framework detail page (conditional `useState`). | Fixed. |

## Technical Debt and Gaps

- Coverage is 60%. Raise it as the API and integration tests land.
- From review (out of scope here): no `Tenant.is_active` check on login or refresh, no refresh-token rotation or revocation, and login timing reveals which emails exist.

- **Secret scanning is not in CI** after the Gitleaks removal. Replace it with the free `gitleaks` CLI or `trufflehog` (no licence needed).
- **The S3 and Azure Blob evidence adapters don't exist.** Only `LocalStorage` is implemented, although earlier summaries claimed otherwise.
- **Frontend pages use mock data.** Example: `getFramework()` in the framework detail page. They aren't wired to the API yet.
- **There are no API-level or integration tests.** `tests/integration` and `tests/e2e` are empty, and none of the tests exercise PostgreSQL or RLS.
- `RiskService.create_risk` ignores `created_by`, so the risk creator isn't persisted.
- Ruff UP042 (`str, Enum` to `StrEnum`) is deferred because it changes `str()` output.
- Prowler and Trivy images are configured as `:latest`. Pin them to digests before Phase 3.
- Docs required by the master prompt are still missing: devops/*, most of operations/*, product user stories and acceptance criteria, and most compliance docs.

## Blockers

- None for Phase 3 local development. Real cloud connectors will need test credentials (AWS/Azure read-only), which we'll mock until they're provided.
