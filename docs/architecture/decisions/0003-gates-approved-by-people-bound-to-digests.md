# ADR-0003: Human gates are approved by both of us, at a terminal, bound to content digests

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** RT38 (actor, time, reason, before/after), applied to our own process

## Context

The operating model is "governed by people". In this repository every human role is played by
the mentor and the mentee. An approval must therefore (1) come from one of us and not from an
agent, (2) be about a precise content, and (3) leave an audit trail. Agents run shell commands,
so any approval mechanism based on a command must tell a person from an agent. Approvals that
survive later edits of the approved text would make the gates meaningless.

## Decision

- **Who:** `harness/team.yaml` lists the members and the policy; the default `all` requires both
  of us for every human gate (G1, G2, G3, G4, G6, G7).
- **How:** `poetry run sdd approve <id> <gate> --as <member>` refuses unless standard input is an
  **interactive terminal** and the person types the confirmation `<id> <gate>`. Coding agents run
  commands without a terminal attached, so they cannot approve, in any tool.
- **What:** the approval stores the **SHA-256 digest** of the gate's artifacts (line endings and
  task boxes normalised). The gate state is computed, never stored: if the artifacts change, the
  approval no longer matches and the gate is *stale*.
- **Audit:** each approval records member, UTC time, digest, git identity and an optional note.
- **Defence in depth:** in Claude Code, a PreToolUse hook also blocks `sdd approve` and edits of
  the `approvals:` and `verification:` sections of `dossier.yaml`.

## Alternatives considered

| Option | Why it lost |
|---|---|
| Approval by editing a status field ("approved: true") | any agent can write it; no binding to content |
| Approval by a signed git commit or tag | strong, but needs GPG/SSH signing set up for both of us; still possible later as an extra |
| Approval through pull-request reviews on a hosting platform | needs a server and CI; the repository is local-only (ADR-0004) |
| One approval is enough | contradicts joint decisions; available as policy `any` for exceptional periods |

## Consequences

- + An agent cannot approve by mistake, whatever tool it runs in; an edit after approval is
  visible immediately (`sdd status`, `sdd check`, README status board).
- + The audit trail lives in git with the dossier.
- − It protects against mistakes, not against a person deliberately bypassing it (a person can
  approve without reading). Between two people who trust each other, the audit trail is the
  right control.
- − Editing an approved artifact, even to fix a typo, requires re-approval. That friction is
  intended: we look at every change of an agreement.
