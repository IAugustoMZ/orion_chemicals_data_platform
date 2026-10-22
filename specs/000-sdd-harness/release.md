# Release and learnings · 000 · The SDD harness

> **Phase 7 · Release & Learn**, closed by **G7 · Results validated** (both of us approve).
> How to fill this file: [lifecycle, phase 7](../../harness/lifecycle.md#phase-7-release-and-learn).
> Written after G6 and the merge; until then the sections below say what will be filled.

## Release

TODO(sdd): After the merge into `main`: the merge commit, `poetry install --with docs` and
`poetry run pre-commit install` done on each of our machines, `docker compose up --build docs`
healthy.

## Observation

TODO(sdd): After using the harness for dossier 001: how long each phase took, how many gate
round-trips, how many build-loop iterations, false positives of `sdd check`.

## Feedback

TODO(sdd): What each of us found clear, heavy or missing while using it.

## Results against the goals

TODO(sdd): One row per PRD goal, with evidence from dossier 001.

| PRD goal | Result | Evidence |
|---|---|---|
| | | |

## Learnings

TODO(sdd): What to change in the harness (each change becomes an enabler dossier).

## Next items

- Native agent hooks for Cursor and Codex (enabler).
- Signed approvals (enabler), if we ever need non-repudiation beyond git history.
- Dossier 001: the first platform feature, chosen from the catalogue's priorities (RT01, RT09,
  RT12, RT20-RT25, RT28-RT29, RT34, RT39).

TODO(sdd): Confirm or reorder after the first real use.
