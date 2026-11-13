# ADR-0023: A backlog is approved and built one card at a time

- **Status:** Accepted
- **Date:** 2026-11-12
- **Dossier:** specs/002-harness-item-flow
- **Requirements:** supports RT38 (approvals record actor, time, digest) and RT42; refines [ADR-0003](0003-gates-approved-by-people-bound-to-digests.md) and [ADR-0015](0015-one-gate-at-a-time-reviewed-in-chat.md)

## Context

Until now G2 approved a whole backlog and G5 meant "the dossier's code passes `sdd verify`", with
all work on one spec branch. For a dossier of 23 cards this hides progress, makes every review
huge and freezes cards that will change once earlier ones exist.

## Decision

- **G2 is partial**: the skeleton and the first card in full; other cards are outlines.
- Each card is **refined** with the code that exists, reviewed with us in the chat, and approved
  by both of us, bound to the digest of **that card's section**.
- Work on a card happens on `feat/<id>-<nn>-<slug>` created by `sdd item next` from an updated
  `main`; a card is done when every acceptance criterion has a marked passing test and
  `sdd item verify` passes; the agent commits, pushes and opens a pull request, then **stops**.
- A person merges. `sdd item merged` checks with git that the commit is in `origin/main`.
- G5 passes when every card is merged. A stale G4, G3 or G2 skeleton blocks governed changes on
  item branches. Dossiers without `progress.yaml` keep the old rules.
- The tool never runs `git branch -D`, `git push --force` or `gh pr merge`.

## Alternatives considered

| Option | Review size | Learning feeds the next card | Why it lost (or won) |
|---|---|---|---|
| Whole backlog approved once, one branch | huge | no | the cause of the problem |
| One dossier per card | small | yes | duplicates PRD, spec and gates 23 times |
| Cards approved and built one by one (this ADR) | small | yes | won |

## Consequences

- + Progress is visible per card; each pull request is reviewable.
- − More ceremony per card; `sdd item` automates the mechanical parts.
- − The rule "work only on the dossier's spec branch" (AGENTS.md section 1) is replaced for build
  work by the item branch rule; the documents say so.
