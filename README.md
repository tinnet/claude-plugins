# claude-plugins

My Claude Code plugins, as one marketplace.

```
/plugin marketplace add tinnet/claude-plugins
/plugin install project-tooling@tinnet
```

| Plugin            | What                                                                 | Lives in |
|-------------------|----------------------------------------------------------------------|----------|
| `project-tooling` | Skill: my tooling preferences and must-haves for new repos (mise, just, lefthook, betterleaks, CalVer, CI, releases) with Rust and Java stack guides | here |
| `yt-transcript`   | Skill: clean text transcripts from YouTube videos via yt-dlp         | here |
| `ccline`          | A fast Rust status line for Claude Code                              | [tinnet/ccline](https://github.com/tinnet/ccline) |

Run `/plugin marketplace update tinnet` to pull changes.

## Layout

```
.claude-plugin/marketplace.json   the catalogue
plugins/<name>/                   plugins kept in this repo
  .claude-plugin/plugin.json
  skills/<skill>/SKILL.md
```

Plugins kept here use relative `source` paths. Plugins with their own repo (ccline) are
listed with a `git-subdir` source pointing at that repo.

## Adding a plugin

1. `plugins/<name>/.claude-plugin/plugin.json` and its skills/commands/hooks.
2. An entry in `.claude-plugin/marketplace.json`.
3. Bump the plugin's `version` when its content changes; installs only update when it does.
4. `claude plugin validate .` and `claude plugin validate plugins/<name>`.

## Developing

Tools come from mise, tasks from just: `just setup` installs the tools and the git hooks
(betterleaks secret scan, Conventional Commits, signed commits), `just ci` checks everything.

## Codex

The skills are plain Agent Skills (`SKILL.md`) and work in Codex too. Codex reads
`.claude-plugin/marketplace.json` as a legacy location; if needed, add
`.agents/plugins/marketplace.json` with the in-repo plugins (Codex may not accept the
`git-subdir` source).

## License

MIT
