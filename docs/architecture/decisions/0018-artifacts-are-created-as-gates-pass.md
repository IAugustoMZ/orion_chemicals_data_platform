# ADR-0018: Artifacts are created as the gates pass, not all at once

- **Status:** Accepted
- **Date:** 2026-10-28
- **Dossier:** specs/000-sdd-harness
- **Requirements:** none: process decision; refines [ADR-0015](0015-one-gate-at-a-time-reviewed-in-chat.md)

## Context

`sdd new` used to create the dossier folder with all nine artifacts at once, each one a template
full of `TODO(sdd)` placeholders. [ADR-0015](0015-one-gate-at-a-time-reviewed-in-chat.md) asks for
one gate at a time, but the folder invited the opposite: the spec, plan and tasks sat there from
day one, and the only defence against writing them early was a warning (`written-ahead`) after
the fact. A file that does not exist cannot be written ahead. The dossier folder should also
tell the truth about where the work is: what is there has been reached.

## Decision

A dossier starts with `dossier.yaml` and `prd.md`. When an approval turns a gate *passed*, the
harness creates, from their templates, the artifacts of the next gate that has artifacts, and
prints their names. Nothing is created by hand and nothing is created in bulk.

| When this happens | the harness creates |
|---|---|
| `sdd new` | `dossier.yaml`, `prd.md` |
| G1 passes | `backlog.md` |
| G2 passes | `ux-approach.md` |
| G3 passes | `spec.md`, `plan.md`, `tasks.md` |
| G4 passes | `validation.md`, `teaching-guide.md` (the build writes both; G5 is automatic and has no file) |
| G6 passes | `release.md` |

A file that already exists is never overwritten (the bootstrap dossier 000 has all of them). The
`written-ahead` warning stays for files created by hand. The mapping is derived from the gate
definitions (`GateDefinition.artifacts`), so changing which files a gate judges changes when
they appear.

## Alternatives considered

| Option | Stops writing ahead | Keeps the folder honest | Why it lost (or won) |
|---|---|---|---|
| All nine files at `sdd new` (before) | no, only warns afterwards | no: empty templates look like pending work | the cause of the problem |
| An agent copies each template by hand | no: depends on the agent remembering | yes | the harness is meant to make the right thing the default |
| Create at the first approval of a gate | partly | yes | with two approvers the gate has not passed yet; the next phase must not start |
| Create when the gate passes (this ADR) | yes: the file is absent | yes | won |

## Consequences

- + The folder shows the lifecycle: what exists has been reached.
- + `written-ahead` cannot happen through the normal flow.
- + Late templates always come from the current template version.
- − `ApproveGate` now has two jobs (record, then scaffold). The scaffolding is a separate
  application service used by `CreateDossier` and `ApproveGate`, so each class keeps one reason
  to change.
- − An approval that passes a gate also writes files, so the two must succeed or fail together.
  `add_artifacts` removes the files it wrote if one write fails, and `ApproveGate` then saves
  the dossier as it was before the approval and re-raises: a failed scaffolding leaves neither
  an approval nor a stray file, and we simply run the approval again (decided at the G4
  review).
- Revisit if we find ourselves creating files by hand often.
