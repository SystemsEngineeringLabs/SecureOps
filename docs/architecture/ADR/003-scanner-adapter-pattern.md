# ADR-003: Scanner Integration via Adapter Pattern

**Status:** Accepted
**Date:** 2024-11-19
**Decision Makers:** Engineering Team

## Context

SecureOps integrates multiple security scanning engines (Prowler for cloud security, Trivy for vulnerabilities). Each has different output formats, execution models, and configuration. We need a strategy that:

- Normalizes all findings into a single internal model
- Makes individual scanners replaceable
- Supports adding new scanners without redesigning the core

## Decision

Implement a **scanner adapter pattern**:

1. Define a common `ScannerAdapter` interface (configure, execute, parse results, normalize findings)
2. Each scanner (Prowler, Trivy, etc.) gets its own adapter implementation
3. Scanners run as **containerized processes** — invoked via Docker API with resource limits
4. All scanner output is parsed and normalized into our internal `Finding` model
5. Adapters live in `backend/app/integrations/<scanner_name>/`

## Consequences

**Positive:**
- Adding a new scanner = implementing one adapter, no core changes
- Scanner upgrades are isolated to their adapter
- Containerized execution provides resource isolation and security boundaries
- Internal Finding model is scanner-agnostic

**Negative:**
- Normalization may lose scanner-specific detail (mitigated by storing raw output)
- Container orchestration adds complexity vs. direct library calls
- Each adapter needs its own test suite

**Mitigations:**
- Store raw scanner output alongside normalized findings for auditability
- Resource limits (CPU, memory, timeout) on all scanner containers
- Adapter interface contract enforced by abstract base class and integration tests
