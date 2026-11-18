---
name: project-tooling
description: My preferred tooling and must-haves for software projects - mise for tools, just for tasks, lefthook git hooks, betterleaks secret scanning, Conventional Commits with signed commits, CalVer releases with git-cliff changelogs, pinned GitHub Actions - plus per-stack choices for Rust CLIs/daemons, Java native (GraalVM) CLIs, and small Rust web services (SQLite, htmx; optional S3 and Litestream). Use when scaffolding a new repo, adding CI/hooks/release automation, reviewing a repo's setup, or when asked to "set this up the way I like it".
---

# Project tooling preferences

These are preferences and requirements, not a template. **Pin exact versions, but never copy
them from this skill or from memory**: look up the current release when creating or touching
config (`mise latest <tool>`, the package registry, `gh release view -R <owner>/<repo>`). Use a
tool's own scaffolder where one exists.

`assets/` holds files to copy and adapt: `justfile` (skeleton), `lefthook.yml`,
`lefthook/` (hook scripts, copy to `.lefthook/`), `cliff.toml`. Replace the `<PLACEHOLDERS>`.

## Pick the stack, then read its file

| Project kind                                     | Read                      |
|--------------------------------------------------|---------------------------|
| Rust command-line tool or daemon                 | `references/rust-cli.md`  |
| Java command-line tool, compiled to native       | `references/java-cli.md`  |
| Small Rust web service (SQLite, htmx)            | `references/rust-web.md`  |
| Anything else                                    | Apply the baseline and ask about stack choices |

The baseline applies to every stack. A stack file adds to it; where it deviates, it says so.

## Baseline

### Tools and tasks: mise for *what*, just for *how*

- `mise.toml` `[tools]` pins every tool at an exact version: toolchain, build tool, just,
  lefthook, betterleaks, git-cliff, and merman (`github:Latias94/merman`) only if the repo has
  Mermaid diagrams. A short comment explains any non-obvious pin. No build-tool wrappers
  (e.g. no `gradlew`); mise provides the tool.
- The `justfile` holds every task. **Don't use mise tasks.** Reasons: just is widely known and
  works without mise, has arguments/defaults (`release version=…`, `run *args`) and OS
  attributes (`[unix]`) built in, and recipes are plain shell rather than shell in TOML strings.
- `just` with no arguments lists recipes. Every recipe has a comment line (it becomes the
  `--list` description). Set `windows-shell` if the project builds on Windows.
- Standard recipes (see `assets/justfile`):

  | Recipe       | Does                                                                  |
  |--------------|-----------------------------------------------------------------------|
  | `setup`      | `mise install` + `lefthook install`                                   |
  | `test *args` | tests                                                                 |
  | `run *args`  | run the app from source                                               |
  | `fmt`        | format code **and** `just --fmt`                                      |
  | `fmt-check`  | fail if anything is unformatted (code + `just --fmt --check`)         |
  | `ci`         | exactly what CI runs (`fmt-check test`, plus stack lint)              |
  | `changelog`  | preview the next release notes                                        |
  | `release`    | see Releases                                                          |

  Plus stack-specific recipes (build, native, install, ...). Static analysis runs inside
  compile where the stack allows it; otherwise add a `lint` recipe and put it in `ci`.

### Git hooks: lefthook

`lefthook.yml` (see `assets/`), installed by `just setup`:

- **pre-commit**: betterleaks on staged changes, and `just fmt` on matching globs with
  `stage_fixed: true`.
- **commit-msg**: `.lefthook/commit-msg/conventional.sh` rejects non-Conventional-Commit
  subjects (lets through merges, reverts, `fixup!`/`squash!`/`amend!`).
- **pre-push**: `.lefthook/pre-push/signed.sh` (`use_stdin: true`) rejects unsigned commits
  among those being pushed. It must be a script, not `run`: lefthook skips `run` jobs in
  pre-push when `git diff HEAD @{push}` is empty.

### Secrets and personal data: before anything leaves the machine

- betterleaks in the pre-commit hook, on staged changes. That's the required layer; no CI
  scan job (by the time CI runs, a pushed secret is already out).
- Plus whatever protection the git host offers for free/on the current plan, turned on and
  checked. On GitHub: secret scanning and push protection (`gh api repos/<owner>/<repo>
  -q .security_and_analysis`); on by default for public repos, paid for private ones.
- If build output trips rules, add a `.betterleaks.toml` that extends the defaults and
  allowlists the output dir.
- Local secrets (API credentials) go in a gitignored `.env`: put `.env`, `.env.*` and
  `!.env.example` in `.gitignore` before anything else is created, commit a `.env.example`
  listing every variable without values, and `set dotenv-load` in the justfile so recipes see
  it. Deployed containers get real env vars.
- Public repos: no real identifiers of real people (player or character names, guild names,
  account ids, emails) in fixtures, tests, docs, logs or commit messages; betterleaks won't
  catch them. Fixtures use made-up data shaped like real responses. Say so in the project's
  `AGENTS.md`.

### Commits

- Conventional Commits: `feat`, `fix`, `perf`, `refactor`, `test`, `docs`, `build`, `ci`,
  `chore`, `style`, `revert`; optional scope; lower-case imperative description, no period;
  body says why, wrapped at 72. `!` marks a breaking change to the CLI/config/API.
- `feat`/`fix`/`perf`/`docs` subjects become the changelog, so write them for users.
- Every commit is signed. One logical change per commit; tests in the same commit as the change.

### Tests

- Every user-facing behavior has a test that drives the real entry point the way a user does
  (the CLI binary or its `main`, real HTTP for services).
- Code that touches the outside world (filesystem roots, sysfs, APIs) takes that dependency as
  a parameter so tests use a fake (temp dir tree, in-process fake server). For CLIs, a hidden
  global flag that only tests set is fine.
- Tests that need the network are tagged, excluded from `just test`, and have their own recipe.
  Real identifiers they need come from env vars (`<NAME>_TEST_<THING>`, via `.env`), never
  from the code.
- Property-based tests where there is real input space (parsing, ordering, round-trips, path
  handling). When a generator can produce input the validator rightly rejects, skip it in that
  property (`let Ok(x) = parse(&s) else { return Ok(()) };`) instead of narrowing the
  generator until it tests nothing. Anything that normalises user input gets an idempotence
  property (`normalise(display(x)) == x`); it finds real bugs.

### External APIs

When the app talks to an undocumented or thinly documented API:

- Write `docs/<api>.md` before the client: each fact with its source (official doc, community
  post, our own request and its date), a table of what we verified with our client, and what
  the app uses. New facts go there, with their source.
- A read-only `<name> api <path>` debug subcommand (plus `just api <path>`) that prints any
  response using the app's credentials, for exploring and re-verifying.
- Tests run against an in-process fake serving fixture JSON; only the network tests hit the
  real API.

### CI (GitHub Actions)

On push to `main` and on PRs; `permissions: contents: read`; `persist-credentials: false` on
every checkout:

- `test`: ubuntu, `jdx/mise-action`, runs `just ci`.
- build matrix for distributed binaries (ubuntu, macos, windows; only the platforms the
  project supports): build the release artifact and smoke-test it.
- `actions-lock`: every `uses:` is pinned in `.github/workflows/actions.lock` via
  `gh actions-lock` (extension `github/gh-actions-lock`); CI runs `gh actions-lock --verify`.
  Commit the lockfile with every workflow change. Use full `vX.Y.Z` tags in `uses:`.
  `gh actions-lock` warns about a pin newer than Dependabot's cooldown: pin the newest release
  older than it (`gh release list -R <owner>/<repo> --json tagName,publishedAt`). Install the
  extension pinned (`gh extension install github/gh-actions-lock --pin <ver>`), the same
  version locally and in CI.
- Install tools with `mise-action`, not language setup actions (stack files list exceptions).
- Dependabot weekly for `github-actions` and the language ecosystem, grouped, with a 7-day
  `cooldown` (a new release settles, or gets pulled, before we take it).

### Versions and releases

- CalVer `vYYYY.MM.DD`, `vYYYY.MM.DD.N` for another release the same day. Local/untagged
  builds report `dev`. The release build gets its version from the tag; nothing is hand-edited.
- `just release [version]` (default today's date) refuses unless on a clean `main` matching
  `origin/main`; writes `CHANGELOG.md` with git-cliff, commits `chore(release): <version>`,
  pushes, creates a **signed** tag, pushes the tag. No other way of tagging; never move or
  delete a published tag.
- `release.yml` on `v20*` tags, `permissions: {}` at the top with per-job grants: build per
  platform with the tag's version, **check `--version` prints the tag's version**, package
  archives named `<name>-<os>-<arch>` (`.tar.gz`, `.zip` on Windows) so
  `mise use -g github:<owner>/<repo>` installs them, publish with
  `gh release create --verify-tag`, a `SHA256SUMS` file, git-cliff notes for that release
  (`git cliff --current --strip all`), and `actions/attest` build provenance for public repos.
- Tools only installed locally (e.g. a daemon with a systemd unit) may skip `release.yml` and
  ship an `install` recipe instead; tags and changelog still apply.

### Docs

- `AGENTS.md` is the agent guide: setup and commands, code rules, commit rules, releases.
  `CLAUDE.md` contains only `@AGENTS.md`. It says "run `just ci` before declaring work done".
- `README.md` is for users. Contributor material goes in `docs/` (`development.md` for build,
  tests, hooks, CI and releases; `design.md` for internals).
- Diagrams are Mermaid in Markdown, checked in `lint`/`ci`. `merman-cli lint` takes one file
  and exits 1 on errors, so loop:
  `for f in docs/*.md; do merman-cli lint "$f" >/dev/null || exit 1; done`.
- MIT license. `.gitignore`: `.env`, build output, editor dirs, tool reports, local run
  artifacts.

## Strong preferences

- Newest stable toolchain / LTS the stack supports; say why in a comment when it isn't simply
  the newest.
- Static analysis as strict as the stack allows, findings fail the build. Don't suppress a
  check without a comment saying why.
- CLIs: help text per subcommand says what it does and whether it changes anything
  (read-only, needs root). No subcommand prints help.
- Small functions with one purpose; comments and doc comments say why, not what.
- Comments in config say why (why a pin, why a script instead of `run`).

## Reviewing an existing repo against this

Report gaps as a checklist against the baseline and the stack file, then propose changes.
Don't silently rewrite working config that differs only in taste; list it and ask.
