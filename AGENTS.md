# AGENTS.md

A Claude Code plugin marketplace (`.claude-plugin/marketplace.json`) with plugins under
`plugins/`. The README explains the layout and how to add a plugin.

- Tools are pinned in `mise.toml`; tasks live in the `justfile`. `just setup` installs tools
  and git hooks. Run `just ci` (secret scan, justfile format, `claude plugin validate`)
  before declaring work done.
- Bump a plugin's `version` in its `plugin.json` whenever its content changes; installs only
  update when it does.
- Conventional Commits (`feat`, `fix`, `docs`, `chore`, ...; scope = plugin name), enforced by
  the commit-msg hook. Every commit is signed; the pre-push hook rejects unsigned ones.
- This repo is public: never commit credentials, private paths or personal data. The
  pre-commit hook runs betterleaks on staged changes.
