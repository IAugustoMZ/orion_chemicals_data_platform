# ADR-0016: The approval confirmation is a y/N prompt at an interactive terminal

- **Status:** Accepted
- **Date:** 2026-10-28
- **Dossier:** specs/000-sdd-harness
- **Requirements:** supports RT38 (actor, time, reason); refines [ADR-0003](0003-gates-approved-by-people-bound-to-digests.md)

## Context

[ADR-0003](0003-gates-approved-by-people-bound-to-digests.md) made `sdd approve` refuse unless
standard input is an interactive terminal *and* the person types the phrase `<id> <gate>` (for
example `001 G4`). Two safeguards were stacked: the terminal test, which keeps agents out, and
the typed phrase, meant to slow a person down.

During the G3 review of dossier 000 we chose, between the two prompts, the lighter one. The
terminal test is what stops an agent: agents run commands with no terminal on standard input, so
a plain pipe cannot reach the prompt. A pseudo-terminal wrapper could still create a terminal;
that residual risk is covered by the agent guard (which blocks `sdd approve` in agent commands)
and by the audit trail, not by the prompt. The phrase adds friction for a person who
has just reviewed the artifact in the chat and is about to approve anyway (the review itself is
the engagement check, [ADR-0015](0015-one-gate-at-a-time-reviewed-in-chat.md)).

## Decision

After the summary (dossier, gate, artifacts, digest, approver) `sdd approve` asks
`Approve? [y/N]`. Only `y` or `yes` (any case) approves; anything else, including an empty
answer, cancels and records nothing. The refusal when standard input is not an interactive
terminal is unchanged and still happens before anything is shown.

## Alternatives considered

| Option | Safety against agents | Friction for us | Why it lost (or won) |
|---|---|---|---|
| Type `<id> <gate>` (ADR-0003) | same (terminal test) | higher | the extra typing protects against nothing the terminal test does not already stop |
| `y/N` (this ADR) | same | lower | won: the review in the chat is where we engage; the prompt only confirms |
| No prompt, the command approves at once | same | lowest | a mistyped command would record an approval; one explicit `y` is cheap insurance |

## Consequences

- + Approving is one keystroke after reading the summary.
- + The `HumanConfirmation` port gets simpler: `confirm(summary) -> bool` (no `expected` text).
- − A reflex `y` is easier than a typed phrase. The digest in the summary, the review in the chat
  and the audit trail (member, time, digest, note in git) are the controls against that.
- Revisit if an approval is ever recorded that nobody remembers reviewing.
