# ADR-004: Password Hashing via `bcrypt` Directly (Replacing passlib)

**Status:** Accepted
**Date:** 2026-11-19
**Decision Makers:** Engineering Team

## Context

Password hashing used `passlib[bcrypt]` 1.7.4. passlib has had no release since 2020.
On a fresh install, pip resolves `bcrypt` 5.x. During initialization, passlib's
bcrypt backend runs a self-test that hashes a password longer than 72 bytes, and
bcrypt 5.x raises `ValueError` on that input. As a result, **every call to
`hash_password` and `verify_password` failed**, so registration and login were broken
on any fresh install.

Separately, the registration schema allowed passwords of up to 128 *characters*,
but bcrypt only uses the first 72 *bytes*. Under older bcrypt versions, two
different long passwords with the same 72-byte prefix would both verify.

## Decision

- Call the maintained `bcrypt` library directly (`hashpw` / `checkpw`, cost 12).
  This is a thin wrapper around a vetted primitive, not custom cryptography.
- Enforce a **72-byte (UTF-8) maximum** in the registration schema and in
  `hash_password`. Never silently truncate.
- `verify_password` returns `False` for over-length input and for malformed or
  placeholder hashes (for example, a pending invitation), instead of raising.

## Consequences

- Existing `$2b$` hashes remain valid. No migration is needed.
- Passphrases longer than 72 bytes are rejected with a clear validation error.
- Algorithm agility (for example, a later move to Argon2id) now has to be built
  explicitly. If we migrate, evaluate `pwdlib` with argon2 and rehash on login.

## Alternatives Considered

- **Pin `bcrypt<4.1`.** Rejected: it keeps an unmaintained dependency and pins
  a security library to an old version.
- **Pre-hash with SHA-256 to lift the 72-byte limit.** Rejected for now: it
  adds a non-standard construction and needs care to avoid NUL-byte issues.
