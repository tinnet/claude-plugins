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
| SQLite         | `sqlx` with `default-features = false` and `runtime-tokio`, `sqlite` (bundles libsqlite3), `migrate`, `macros`; WAL mode, `foreign_keys = on`, `busy_timeout` set on the pool's connect options |
| Queries        | start with `query_as()` (checked at runtime); adopt the `query!` macros only with `sqlx-cli` in mise and a committed `.sqlx/` (`cargo sqlx prepare --check` in `ci`) |
| Migrations     | `migrations/*.sql`, embedded with `sqlx::migrate!()`, run at startup   |
| TLS            | `rustls` everywhere, never OpenSSL (keeps the musl build static)       |
| HTTP client    | `reqwest` with `default-features = false` and `rustls`, `json` (plus `form` if needed) |
| Config         | env vars via clap's `env` feature (`#[arg(long, env = "<NAME>_DATABASE_URL")]`), so they also work as flags; replaces the TOML config of `rust-cli.md`. Locally, `dotenvy::dotenv()` loads the gitignored `.env` before clap parses (a missing file is fine); containers use real env vars |
| Logging        | `tracing` + `tracing-subscriber` (`env-filter`, optional JSON via an env var) |
| Endpoints      | `/healthz` runs `SELECT 1` and returns 200/503; `/version` returns the shadow-rs version |
| Shutdown       | `axum::serve(...).with_graceful_shutdown(...)` on SIGINT and SIGTERM   |
| Errors         | `anyhow` inside; one `AppError` implementing `IntoResponse` so handlers use `?` |
| Allocator      | `mimalloc` as the global allocator (musl's malloc is slow under load)  |
| Background work| one tokio task looping "process due items, then wait on a `tokio::sync::Notify` or a tick"; handlers `notify_one()` after enqueuing; whether an item is due is a pure function in core, unit-tested |
| Upstream data  | store the raw upstream JSON per endpoint and parse on read: new fields need no refetch, and a failed fetch keeps the last good data |
| Tests          | black-box `tests/http.rs`: start the app in-process on `127.0.0.1:0` with a `tempfile` SQLite DB, send real requests with `reqwest` (rustls) |
| Fake upstream  | an in-process axum server on `127.0.0.1:0` serving fixture JSON; the client's base URLs are hidden clap args/env vars (`hide = true`) that only tests set; count requests with an `AtomicUsize` to assert (no) refetches |
| Backup         | by default the host's job (snapshots of the data volume); see the Litestream option |

Release profile in the workspace `Cargo.toml`:

```toml
[profile.release]
lto = true
codegen-units = 1
strip = true
```

## Pages and htmx

- Every action is a plain form POST answered with a 303 redirect, so it works without JS. The
  same form carries `hx-post`/`hx-target`; the handler checks the `HX-Request` header and
  returns just the re-rendered fragment.
- The fragment is an `{% include %}`d partial template, shared by the full page and the htmx
  response.
- htmx swaps only 2xx responses by default: validation errors go back as a 200 fragment
  (keeping the typed input) to htmx, and as a 422 full page otherwise.
- Poll (`hx-trigger="every 3s"`) only while background work is pending; the rendered fragment
  drops the trigger when it's done.

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
- Build natively, no cross/zigbuild in CI: `ubuntu-24.04` (x86_64) and `ubuntu-24.04-arm`
  (aarch64), `musl-tools` apt-installed, the musl targets listed in mise
  (`rust = { version = …, profile = "default", targets = "x86_64-unknown-linux-musl,aarch64-unknown-linux-musl" }`).
- CI builds the same binaries on PRs and smoke-tests them: `ldd` says "not a dynamic
  executable", then start `serve` with a temp DB and poll the `healthcheck` subcommand.
- The binaries go on the GitHub release as usual (`<name>-linux-<arch>` archives).
- A multi-arch container image (`linux/amd64`, `linux/arm64`) is pushed to GHCR, tagged with
  the CalVer version and `latest`. The image job downloads the per-arch binaries into
  `dist/linux-<amd64|arm64>/` and builds with buildx, no QEMU (the Dockerfile only copies).

`Dockerfile` copies the prebuilt binaries; nothing compiles inside Docker:

- Base image `gcr.io/distroless/static:nonroot`, pinned by digest; `USER nonroot`. Getting
  the digest without crane/skopeo:

  ```sh
  TOKEN=$(curl -s "https://gcr.io/v2/token?scope=repository:distroless/static:pull" | jq -r .token)
  curl -sI -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.oci.image.index.v1+json" \
    https://gcr.io/v2/distroless/static/manifests/nonroot | grep -i docker-content-digest
  ```

- `ARG TARGETARCH`, `COPY` `dist/linux-${TARGETARCH}/<name>`; `ENTRYPOINT ["/<name>"]`.
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
- askama: inside Rust expressions in a template (e.g. `format!(…)` arguments) bare names are
  not the template struct's fields; a same-named fn in the module gets picked, or "cannot find
  value". Expose a method instead (`{% let base = roster.base() %}`).
- askama escapes `<`/`>` as `&#60;`/`&#62;`; HTTP tests asserting escaped text expect the
  numeric entities.
- Building musl from macOS needs a cross toolchain: release binaries come from CI; the local
  `docker` recipe uses `cargo zigbuild`.
- `object_store`'s `LocalFileSystem` needs its root directory to exist; create it at startup.
