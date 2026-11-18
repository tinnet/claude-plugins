# Rust CLI or daemon

Adds to the baseline in `SKILL.md`.

## Layout

A Cargo workspace (`resolver = "3"`) under `crates/`:

- `<name>-core`: pure logic (config parsing, models, algorithms). No I/O, no hardware, no
  network, so it's trivially unit-testable.
- `<name>`: the binary plus a `lib.rs` with the I/O modules; `main.rs` only parses arguments
  and dispatches.

Shared metadata in `[workspace.package]` (`version`, `edition`, `rust-version`, `license`,
`repository`) and each crate inherits it with `.workspace = true`. Single-crate is fine for
something tiny; split when there's logic worth testing without I/O.

## Choices

| Concern        | Choice                                                                 |
|----------------|------------------------------------------------------------------------|
| Toolchain      | stable Rust pinned exactly in mise (`profile = "default"`), newest edition, `rust-version` = that toolchain |
| Lints          | `[workspace.lints.rust] unsafe_code = "forbid"`; `[workspace.lints.clippy] pedantic = { level = "warn", priority = -1 }`; every crate `[lints] workspace = true`; clippy runs with `-D warnings` |
| Lint config    | `clippy.toml` `doc-valid-idents` for product names pedantic `doc_markdown` would flag |
| Docs           | public functions returning `Result` have an `# Errors` section         |
| Arg parsing    | `clap` derive; subcommands enum; global flags for config path; hidden global flags for roots that only tests override |
| Errors         | `anyhow` in the binary                                                 |
| Config         | TOML via `serde` + `toml`; an `examples/<name>.toml` that tests use     |
| Version        | `shadow-rs` in the binary's `build.rs`, `#[command(version = build::CLAP_LONG_VERSION)]`; make the short version the tag's version (`build::TAG` without `v`, `dev` when empty). Runtime dep with `default-features = false` (no git2/libgit2, keeps static builds simple), build-dep with `features = ["build"]` |
| Tests          | unit tests next to the code; black-box `tests/cli.rs` with `assert_cmd` + `predicates` + `tempfile`, running the binary against a fake tree in a temp dir; `proptest` for property tests |
| Parser sanity  | unit test `Cli::command().debug_assert()`                              |
| Unix APIs      | `rustix` and `signal-hook` over raw `libc`                              |

## justfile additions

- `test` = `cargo test --workspace`
- `lint` = `cargo clippy --workspace --all-targets -- -D warnings`, and add it to `ci`
- `fmt` = `cargo fmt --all` + `just --fmt`; `fmt-check` = `cargo fmt --all --check` + `just --fmt --check`
- `build` = `cargo build --workspace --release`
- `run *args` = `cargo run --quiet -- {{ args }}`
- Recipes for the app's everyday read-only commands against the example config (e.g. `status`,
  `check`) are welcome.
- Daemons: `install` = release build, `sudo install -Dm755` the binary, `-Dm644` the systemd
  unit from `dist/`, install the example config only if none exists, `systemctl daemon-reload`.

## Release

Distributed CLIs follow the baseline flow (`just release`, `release.yml` per target, archives
named `<name>-<os>-<arch>`). Targets: linux x86_64 + aarch64, macOS aarch64, windows x86_64,
minus what the tool can't support (a Linux-only daemon builds Linux only).

Don't use cargo-dist: it parses tags as SemVer and requires them to match `Cargo.toml`'s
`version`; CalVer tags break that (`v2026.01.05` has leading zeros, `.N` isn't SemVer). Leave
`Cargo.toml` `version` at `0.1.0`; the binary's version comes from the tag.

## Gotchas

- shadow-rs needs the tags in CI: `fetch-depth: 0`.
- Feature names move between a crate's majors; check them for the version you pin
  (`curl -s https://crates.io/api/v1/crates/<crate>/<version> | jq .version.features`)
  rather than from memory. Prefer `default-features = false` plus the features you use.
- betterleaks can flag build-script logs under `target/`: allowlist `(^|/)target/` in
  `.betterleaks.toml`.
- Windows binaries are `<name>.exe`; package them with `Compress-Archive`.
