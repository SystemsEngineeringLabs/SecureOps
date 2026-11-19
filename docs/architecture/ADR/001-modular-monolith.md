# ADR-001: Modular Monolith Architecture

**Status:** Accepted
**Date:** 2024-11-19
**Decision Makers:** Engineering Team

## Context

SecureOps combines GRC compliance management, cloud security posture management, vulnerability management, and evidence collection into a single product. We need to decide between:

1. Microservices from the start
2. Modular monolith with clear domain boundaries
3. Traditional monolith without internal boundaries

## Decision

Adopt a **modular monolith** architecture with clearly defined bounded contexts (Organization, Compliance, Risk, Cloud Security, Vulnerability, Evidence, Remediation, AI). Each module has its own models, services, and API routes but shares a single database and deployment unit.

Background workers (Celery) run as separate processes for scan execution, evidence collection, and async jobs.

## Consequences

**Positive:**
- Simpler deployment and operations for an early-stage product
- Easier cross-module queries and transactions
- Lower infrastructure cost
- Faster development velocity
- Can extract services later if scale demands it

**Negative:**
- Must enforce domain boundaries through code conventions, not network boundaries
- Single deployment means all modules scale together
- Risk of coupling if boundaries aren't maintained

**Mitigations:**
- Each module has its own service layer — no direct cross-module DB access
- Inter-module communication via well-defined service interfaces
- Code review enforces boundary discipline
- Worker processes already run separately, easing future extraction
