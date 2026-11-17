# claude-plugins dev tasks. `just` lists them.

[private]
default:
    @{{ just_executable() }} --list --unsorted

# Install the tools from mise.toml and the git hooks
setup:
    mise install
    lefthook install

# Scan the working tree and the git history for secrets
secrets:
    betterleaks dir . --no-banner --redact -v
    betterleaks git . --no-banner --redact -v

# Validate the marketplace and every plugin (needs the claude CLI)
validate:
    claude plugin validate .
    for p in plugins/*/; do claude plugin validate "$p"; done

# Format this justfile
fmt:
    {{ just_executable() }} --fmt

# Fail if the justfile is not formatted
fmt-check:
    {{ just_executable() }} --fmt --check

# Run before pushing
ci: secrets fmt-check validate
