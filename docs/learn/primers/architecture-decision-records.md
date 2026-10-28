# Primer: architecture decision records (ADRs)

## Why record decisions

Six months from now someone (maybe you) will ask "why PostgreSQL and not X?" or "why do approvals
need a terminal?". Without a record, the answer is lost, and the decision is either defended by
habit or reversed by ignorance. An ADR (Michael Nygard's format) is a short file that captures
**one** decision at the moment it is made.

## The anatomy

| Section | Question it answers |
|---|---|
| Status, date | Is it in force? Since when? Was it replaced, and by what? |
| Context | Which forces made a decision necessary: requirements, constraints, unknowns? |
| Decision | What did we decide, in one or two active sentences? |
| Alternatives considered | What else was weighed, and why did each lose? |
| Consequences | What becomes easier, what harder, and what would make us revisit it? |

## Rules that make them useful

- **One decision per ADR**, numbered, never deleted. Reversing a decision is a *new* ADR; the old
  one becomes *Superseded by ADR-NNNN* and stays as history.
- **Alternatives are mandatory.** A decision without alternatives is a statement, not a decision.
- **Write the bad consequences too.** They are what a future reader needs most.
- **Proposed → Accepted at G4.** In this repository ADRs are drafted while specifying and accepted
  with the specification.
- **Link them** from the spec, the teaching guide and the architecture pages.

## A worked example

Read [ADR-0003](../../architecture/decisions/0003-gates-approved-by-people-bound-to-digests.md):
the context (agents run shell commands; approvals must be about precise content), the decision
(terminal-only approval bound to digests), four alternatives with why each lost, and the honest
limit (it protects against mistakes, not against deliberate cheating).

## Exercise

Pick a decision in the harness that has no ADR yet (for example: "approvals are stored in
`dossier.yaml`, not in a separate file") and draft one with the [template](../../../harness/templates/adr.md).
Discuss which alternative you would have chosen.
