# Small Rust web service (SQLite, S3, htmx)

Adds to the baseline in `SKILL.md`.

> **Stub.** Only the bullets below are decided. Everything marked TODO is open; ask the user
> instead of picking, and update this file with the answer.

## Decided

- Rust, same toolchain/lint/version rules as `rust-cli.md` (clippy `-D warnings`, CalVer from
  the tag, `dev` locally).
- Storage: SQLite for data, S3-compatible object storage for files/blobs.
- UI: server-rendered HTML + htmx. No SPA framework, no JS build step.
- Black-box tests use real HTTP requests against the running app (baseline item 4).

## TODO

- HTTP framework (axum?)
- Templates (askama / maud / minijinja?)
- SQLite access (sqlx / rusqlite) and migrations; backup/replication (Litestream?)
- S3 client (aws-sdk-s3 / object_store / rust-s3) and the local dev stand-in (MinIO? Garage?)
- How htmx is shipped (vendored file embedded in the binary?)
- Config (env vars only?), logging/tracing, `/healthz` and `/version` endpoints
- Deployment target and release artifact (container image? static binary + systemd? Fly?),
  and how the baseline's release workflow changes for it
- CI matrix: drop windows (server-only)?
