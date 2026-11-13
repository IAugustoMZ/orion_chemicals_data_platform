# ADR-0024: CI with GitHub Actions blocks the merge

- **Status:** Accepted
- **Date:** 2026-11-12
- **Dossier:** specs/002-harness-item-flow
- **Requirements:** RT42, RT36; supersedes [ADR-0004](0004-local-enforcement-without-ci.md)

## Context

ADR-0004 chose local enforcement because there was no remote. There is one now (GitHub). The new
flow merges pull requests built by an agent, so a check that anyone can skip locally is no longer
a sufficient control. GitHub only stores the repository and runs the checks; it never runs the
generator or receives its data.

## Decision

- One workflow, `.github/workflows/ci.yml`, one required job `quality`, runs on every pull request
  into `main` and every push to `main`.
- It runs, in order, every command of `harness/checks.yaml`, then the proof of the card when the
  branch is a card branch (`sdd item current`, then `sdd item verify`; skipped on any other branch).
  `sdd verify <id> --no-record` exists for a read-only G5 run: it never rewrites `dossier.yaml`.
  A test fails if a command is missing from the workflow.
- The workflow has `permissions: contents: read`, no secret, a timeout, a Poetry cache, a
  concurrency group that cancels outdated runs, and third-party actions pinned to full commit SHAs.
- `.github/` is a governed path.
- **A person** applies the branch protection settings (pull request required, `quality` green, branch
  up to date, no force push, no deletion, administrators included). The agent never does.
- pre-commit stays as the fast local loop; the pipeline is the merge control.

## Alternatives considered

| Option | Cannot be skipped | Cost | Why it lost (or won) |
|---|---|---|---|
| Local hooks only (ADR-0004) | no | none | `--no-verify` and other clones |
| Self-hosted runner | yes | high | out of scope, more attack surface |
| GitHub Actions hosted runner (this ADR) | yes | low | won |

## Consequences

- + RT42 is demonstrable: a deliberate error turns the check red and the merge is blocked.
- − The pipeline needs network (`pip-audit`, action downloads); pinned SHAs must be refreshed on purpose.
- − If branch protection is not applied, the control is not real; [the checklist](../../../harness/ci-protection.md) is
  for a person to apply, and the manual proof is recorded in `validation.md`.
