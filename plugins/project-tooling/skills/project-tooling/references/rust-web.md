# Small Rust web service (SQLite, htmx)

Adds to the baseline in `SKILL.md` and to `rust-cli.md`: same layout (`<name>-core` +
`<name>`), toolchain, lints, `anyhow`, shadow-rs version, and CalVer-from-the-tag rules. Where
this file differs, it says so.

The goal is one small, static binary that carries everything it serves: templates, htmx, CSS.
No SPA framework, no JS build step, no files to ship next to the binary.

The default is SQLite on a local disk and nothing else. Two options are off unless the user
asks for them or the app clearly needs them (ask when unsure):

- **Object storage (S3)**: the app stores files or blobs (uploads, images, exports).
- **Litestream**: the database needs continuous off-machine backup.

## Choices

| Concern        | Choice                                                                 |
|----------------|------------------------------------------------------------------------|
| HTTP           | `axum` on `tokio`; `tower-http` for `TraceLayer`, compression, timeouts |
| Templates      | `askama` + `askama_web` (axum feature): compile-time checked, compiled into the binary |
| Static assets  | `static/` embedded with `rust-embed`; served under a versioned path (e.g. `/static/<version>/…`) with long `Cache-Control` |
| htmx           | a pinned `htmx.min.js` vendored into `static/`; note its version and source URL in a comment or `static/README` |
| SQLite         | `sqlx` with the `sqlite` feature (bundles libsqlite3) and `runtime-tokio`; WAL mode, `foreign_keys = on`, `busy_timeout` set on the pool's connect options |
| Queries        | start with `query_as()` (checked at runtime); adopt the `query!` macros only with `sqlx-cli` in mise and a committed `.sqlx/` (`cargo sqlx prepare --check` in `ci`) |
| Migrations     | `migrations/*.sql`, embedded with `sqlx::migrate!()`, run at startup   |
| TLS            | `rustls` everywhere, never OpenSSL (keeps the musl build static)       |
| Config         | env vars only, via clap's `env` feature (`#[arg(long, env = "<NAME>_DATABASE_URL")]`), so they also work as flags locally; replaces the TOML config of `rust-cli.md` |
| Logging        | `tracing` + `tracing-subscriber` (`env-filter`, optional JSON via an env var) |
| Endpoints      | `/healthz` runs `SELECT 1` and returns 200/503; `/version` returns the shadow-rs version |
| Shutdown       | `axum::serve(...).with_graceful_shutdown(...)` on SIGINT and SIGTERM   |
| Errors         | `anyhow` inside; one `AppError` implementing `IntoResponse` so handlers use `?` |
| Allocator      | `mimalloc` as the global allocator (musl's malloc is slow under load)  |
| Tests          | black-box `tests/http.rs`: start the app in-process on `127.0.0.1:0` with a `tempfile` SQLite DB, send real requests with `reqwest` (rustls) |
| Backup         | by default the host's job (snapshots of the data volume); see the Litestream option |

Release profile in the workspace `Cargo.toml`:

```toml
[profile.release]
lto = true
codegen-units = 1
strip = true
```

## justfile additions

Those from `rust-cli.md`, plus:

- `run *args` = `cargo run --quiet -- {{ args }}` with dev defaults (local SQLite file under
  `data/`), so `just run` serves the app with no setup.
- `docker` = build the release binary for the host's Linux arch and `docker build` the image.
- `data/` is gitignored.

## Release

Deviates from `rust-cli.md`:

- Linux only: `x86_64-unknown-linux-musl` and `aarch64-unknown-linux-musl`, fully static.
  No macOS or Windows release builds; developing on macOS with `cargo run` still works. Tests
  run on ubuntu.
- The binaries go on the GitHub release as usual (`<name>-linux-<arch>` archives).
- A multi-arch container image (`linux/amd64`, `linux/arm64`) is pushed to GHCR, tagged with
  the CalVer version and `latest`.

`Dockerfile` copies the prebuilt binaries; nothing compiles inside Docker:

- Base image `gcr.io/distroless/static`, pinned by digest; runs as the nonroot user.
- `COPY` the binary for `$TARGETARCH`; `ENTRYPOINT ["/<name>"]`.
- `HEALTHCHECK` can't use curl in distroless: give the binary a `healthcheck` subcommand that
  requests `/healthz` and exits 0/1.
- Database on a volume (`/data`).

## Option: object storage (S3)

Only when the app stores files or blobs. Files never go into SQLite.

| Concern        | Choice                                                                 |
|----------------|------------------------------------------------------------------------|
| Client         | `object_store` (`aws` feature) behind one `Arc<dyn ObjectStore>` built from config; works with any S3-compatible service |
| Dev            | `object_store`'s `LocalFileSystem` under `data/` by default, so `just run` still needs no setup |
| Tests          | `InMemory` store in the black-box tests                                |
| Real S3 locally| Garage, only to test against a real S3 API                             |

## Option: Litestream

Only when the database needs continuous off-machine backup. Replicates to an S3-compatible
bucket (the object-storage bucket under its own prefix if the app has one, otherwise a bucket
just for backups; the app itself needs no S3 client for this).

- `COPY` the Litestream binary (pinned release) and a `litestream.yml` into the image.
- `ENTRYPOINT ["/litestream", "replicate", "-exec", "/<name>"]`, so the app runs under
  Litestream.
- On start, restore first with `litestream restore -if-replica-exists -if-db-not-exists`
  (a small entrypoint in the app's own binary or a second Litestream invocation; there's no
  shell in distroless).
- Test a restore once before relying on it.

## Open

- Hosting (VPS with docker compose, Fly.io, home server): the image works on all of them; ask
  the user when a real project needs a deploy step, then record it here.

## Gotchas

- `rust-embed` reads files from disk in debug builds and embeds them in release builds; test
  the release build once before shipping.
- askama templates live in `templates/` next to the crate's `Cargo.toml`; changing a template
  triggers a rebuild, not a reload.
- Building musl from macOS needs a cross toolchain; build release binaries in CI (or with
  `cargo zigbuild`) instead of locally.
- `object_store`'s `LocalFileSystem` needs its root directory to exist; create it at startup.
