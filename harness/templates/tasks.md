# Tasks · {{id}} · {{title}}

> Part of **Phase 4 · Specify** and approved with the spec at **G4**. During the build, tick the
> boxes: ticking does not invalidate G4 (the digest ignores the box state), but rewording,
> adding or removing a task does, on purpose.

## Tasks

TODO(sdd): One task per line, in build order, test first. Reference the SPEC behaviour and the
plan step. Keep each task to one reviewable change.

- [ ] T01 · TODO(sdd) *(SPEC-{{id}}-B01, plan step 1)*

## Loop limits

The build agent runs `poetry run sdd verify {{id}}` after each task. After **3** consecutive
failing verifications on the same task it stops and asks us
([AI control plane](../../harness/ai-control-plane.md#loop-limits-and-escalation)).

TODO(sdd): Keep the default or state a different limit for this dossier, with the reason.
