# ADR-0017: Backlog items are self-contained cards

- **Status:** Accepted
- **Date:** 2026-10-28
- **Dossier:** specs/000-sdd-harness
- **Requirements:** none: process decision; refines [ADR-0012](0012-backlog-as-markdown-in-the-repository.md)

## Context

The first backlog of dossier 000 described each item with a title and acceptance criteria. That
says when the work is *done* but not *what* to build or *how*. Anyone who picks up the item, a
person or a coding agent starting a fresh session, has to rediscover the context from the PRD,
the chat and the code, and may rediscover it differently. Items are built in the order of the
backlog by sessions that do not share memory, so what is not written in the card is lost.

## Decision

Every work item (PBI) is a **self-contained card**. Besides the feature, the RTs it serves, its
size and acceptance criteria in EARS, it carries: **Depends on**, **Context** (why it exists),
**What** (observable deliverables: commands, files, formats, exit codes), **How** (layers,
modules, classes, ports, steps and edge cases, by real name and path), **Out of scope** and
**Verification** (the tests and commands that prove each criterion). The test is a *cold
reader*: someone who has read only the card, `AGENTS.md` and `harness/principles.md` can build
it without asking. The template (`harness/templates/backlog.md`), the role `backlog-planner`,
the skill `sdd-plan` and the acceptance-criteria primer say so, and `sdd approve G2` refuses a
backlog that leaves any of these fields as `TODO(sdd)`.

## Alternatives considered

| Option | Cost of writing | Cost of building | Why it lost (or won) |
|---|---|---|---|
| Title and acceptance criteria only | lowest | high: context is rediscovered, often differently | too little for a fresh agent session |
| A separate design document per item | high | medium | duplicates the spec (G4); two places to keep in step |
| Self-contained cards (this ADR) | medium | lowest | won: the card is reviewed at G2, while changing it is cheap |

## Consequences

- + A fresh session can build an item from the card; reviews at G2 judge the plan, not only the
  intent.
- + The *how* is reviewed by us before the spec exists, so design disagreements surface early.
- − Longer backlogs, and a *how* that may turn out wrong. The spec (G4) is where the design is
  finalised; a card that disagrees with the spec is fixed in the backlog first.
- Revisit if cards are routinely rewritten at G4: it would mean the *how* belongs only in the
  spec.
