# ADR-0015: One gate at a time, reviewed with us in the chat, approved at the terminal

- **Status:** Accepted
- **Date:** 2026-10-22
- **Dossier:** specs/000-sdd-harness
- **Requirements:** supports RT38 (changes record actor, time and reason); refines [ADR-0003](0003-gates-approved-by-people-bound-to-digests.md)

## Context

After the first build, our first approval attempt exposed a weakness we had not designed for.
The agent had drafted the artifacts of every phase (PRD, backlog, approach, specification)
before we looked at the first. Approving then becomes a ceremony: nothing proves that we read
anything (*automation bias*), and a change at G1 ripples through three finished documents, so
we are tempted to accept instead of asking for it. A digest proves *what* was approved, not
that anyone understood it.

## Decision

1. **One gate at a time.** The agent drafts the artifact of a phase only after the gate before
   it passed. `sdd check` reports an artifact that is complete while the previous human gate has
   not passed (`written-ahead`, a warning). Skills tell agents not to start the next phase
   until `sdd status` shows the gate passed.
2. **The review happens in the chat.** At the end of each human phase the agent follows the
   skill `sdd-review-gate`: it briefs us in pieces (what we commit to, decisions and rejected
   alternatives, what it assumed or invented, risks), then asks three to five questions that
   cannot be answered with "yes" (a choice, a cut, a spot check, a consequence). It does not
   continue until we answered, and applies the changes we ask for.
3. **The approval is still recorded at a terminal, by each of us.** After the review the agent
   proposes a `--note` summarising our answers, and the two `sdd approve` commands. It verifies
   with `sdd status` that the gate passed before starting the next phase.

## Alternatives considered

| Option | Why it lost |
|---|---|
| Keep drafting everything first, approve at the end | the weakness we found: rubber stamps, expensive changes |
| Record approvals from the chat (the agent runs `sdd approve` on our "approved") | nothing then distinguishes our word from an agent claiming it; one chat is one person, and there are two of us; it reverses ADR-0003 and Article II |
| One of us records both approvals | the second approval would rest on the first person's word |
| Block agents from editing later artifacts with a hook | the hook is standard-library only and cannot compute gate states; a warning in `sdd check` plus the skills are enough for now (follow-up if needed) |

## Consequences

- + Each approval follows an exchange about the content; the note keeps a trace of it.
- + Changes are cheap: only the artifact under review exists.
- + The terminal step still proves a person, not an agent, gave the approval, and it keeps the
  mentee's own approval.
- − More round-trips with the agent; accepted, the slowness is the point.
- − `written-ahead` is a warning, not a block, and questions cannot prove understanding: they
  make skimming harder, not impossible. The mentor's judgement remains the real control.
