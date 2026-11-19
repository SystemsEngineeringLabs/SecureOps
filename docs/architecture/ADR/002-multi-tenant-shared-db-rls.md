# ADR-002: Multi-Tenant Strategy — Shared Database with RLS

**Status:** Accepted
**Date:** 2024-11-19
**Decision Makers:** Engineering Team, Security Architect

## Context

SecureOps is a multi-tenant B2B SaaS. We need to decide between:

1. Database-per-tenant (strongest isolation, highest operational cost)
2. Schema-per-tenant (good isolation, complex migrations)
3. Shared database with tenant_id column + Row-Level Security (simplest operations, requires careful implementation)

## Decision

Use a **shared PostgreSQL database** with:
- `tenant_id` foreign key on all tenant-owned tables
- PostgreSQL Row-Level Security (RLS) policies as **defense in depth**
- Application-layer tenant scoping as the primary access control
- Tenant context set via `SET LOCAL` session variable within database transactions

## Consequences

**Positive:**
- Single database simplifies operations, backups, and migrations
- RLS provides a database-level safety net against application bugs
- Lower infrastructure cost at small-to-medium scale
- Standard Alembic migrations work for all tenants

**Negative:**
- "Noisy neighbor" risk — one tenant's heavy queries affect others
- Must rigorously enforce tenant_id on every query
- RLS adds slight query overhead
- Data residency requirements may eventually need per-region databases

**Mitigations:**
- Connection pooling with per-tenant query timeouts
- Automated cross-tenant access tests in CI
- Application-layer tenant filtering + RLS = two independent layers
- Regional deployment architecture planned for future phases
