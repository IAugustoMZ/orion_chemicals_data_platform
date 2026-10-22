# ADR-0004: Gates are enforced locally (pre-commit, `sdd`, agent hooks); no CI

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** RT42

## Context

The system runs only locally for now. A CI server would be the usual place to enforce quality
gates, but there is none, and adding one would mean a hosting decision we do not need yet. The
gates still have to be deterministic and hard to skip by accident.

## Decision

- **pre-commit** (installed per clone with `poetry run pre-commit install`) runs on every commit:
  the commit guard (`sdd guard-commit`: governed files only on a spec branch whose G4 passed),
  ruff, mypy, import-linter, pytest, detect-secrets, `sdd sync` and `sdd check`.
- **`sdd verify <id>`** runs the complete suite of `harness/checks.yaml` and records the result as
  gate G5, bound to the digest of the governed code.
- **Agent hooks** (Claude Code) block `--no-verify` and `pre-commit uninstall`.
- The same commands are the future CI's job definition: adding CI later means calling
  `sdd verify` and `pre-commit run --all-files` on a server.

## Alternatives considered

| Option | Why it lost |
|---|---|
| GitHub Actions or Azure Pipelines now | no remote yet; a hosting decision out of scope |
| Only instructions to run the checks | not deterministic; agents and people forget |
| A git `pre-push` hook only | runs too late; a commit with broken rules already exists |

## Consequences

- + Feedback in seconds, on the machine where the change is made, for people and agents alike.
- + No infrastructure to maintain.
- − Anyone can uninstall pre-commit or commit with `--no-verify` outside an agent: the history is
  then the control. Revisit when the repository gets a remote and more contributors.
