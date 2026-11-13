# Roadmap · the time-series source, split into dossiers

> Decision of the mentor (2026-11-13): a specification is one file of at most 50 lines. The
> original backlog of dossier 001 (21 open cards, 9 features) cannot be specified in that size, so
> the need is split into smaller dossiers. This file is the map: which dossier carries which cards,
> in which order, and what each inherits. It is a plan, not a gate; each dossier is opened with
> `sdd new` when its turn comes, and numbers are assigned then.

The full text of every card, before the split, is in `main` at commit `42547d0`:
`git show 42547d0:specs/001-timeseries-source/backlog.md`. Each new dossier copies its cards from
there and refines them at its own G2, so nothing is written twice.

## The dossiers, in the order we open them

| Order | Dossier (working name) | Cards | RTs served | Waits for | Inherits |
|---|---|---|---|---|---|
| 1 | **001 Global time core** (this folder) | 05 | RT07, RT12 | 003 (merged) | none |
| 2 | Plant and tag catalogue | 06, 07 | RT09, RT17, RT28 | 003 | none |
| 3 | Signals and signal faults | 09, 10 | RT17, RT28 | plant | none |
| 4 | Answer key and leak guard | 08 | RT09, RT38 | plant | none |
| 5 | PI-like acquisition (may split into 11-12 and 13-14) | 11, 12, 13, 14 | RT07, RT12, RT17, RT23, RT28, RT29 | time core, plant, signals | none |
| 6 | Writers, layout and safe service | 15 | RT01, RT36, RT28, RT29 | 003, acquisition (first slice) | 003 findings 3, 4, 9, 10; accept or amend ADR-0028; first re-measure with the real signal model |
| 7 | Source contract per site | 16 | RT02, RT09, RT17 | time core, catalogue, acquisition | none |
| 8 | Governance and observability | 17, 18, 19 | RT38, RT39, RT40, RT09, RT29 | acquisition, writers, signals | none |
| 9 | Measured and reproducible | 20, 21 | RT28, RT29, RT23, RT07, RT12, RT30 | all above | 003 finding 11; the re-measure finished (two runs per format at least); the RT29 delay measurement |

Cards 01, 02, 22 and 23 went to dossier 002; cards 03 and 04 were delivered by dossier 003.

## Rules for the split

- Every RT of the original dossier stays covered: RT02 by the contract dossier, RT07 and RT12 by
  the time core (and again by acquisition and the final dossier), RT09 by catalogue, answer key
  and contract, RT17 by plant, signals and acquisition, RT23 by acquisition, RT28 and RT29 by the
  catalogue, writers and the final dossier, RT38 to RT40 by answer key and governance.
- A dossier is specified only after the dossiers it waits for are merged, so a spec never
  describes code that does not exist.
- If a dossier's spec still does not fit in 50 lines, it is split again; the roadmap is amended.
- The hidden plant model, the 5 fictional sites, the messy catalogue and the "scaling beyond the
  default plant is cut first" decisions of the first PRD apply to all of them.
- The ground rules of the first backlog (package `tssource`, determinism with a spawned
  `SeedSequence`, a synthetic marker, tests under `tests/tssource`) are copied into each new
  backlog.
