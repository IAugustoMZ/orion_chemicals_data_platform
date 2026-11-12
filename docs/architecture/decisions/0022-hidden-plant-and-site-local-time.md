# ADR-0022: The plant stays hidden in `truth/`, and events carry site-local time

- **Status:** Proposed
- **Date:** 2026-11-12
- **Dossier:** specs/001-timeseries-source
- **Requirements:** RT09, RT12, RT07, RT38

## Context

A later model must rebuild the plant structure from names, descriptors, units and signal
behaviour, and be scored against the truth. If the structure leaks, or if the model trains on
test answers, its score means nothing. Separately, the platform must prove that it standardises
time (RT12); a generator that hands over UTC would remove the exercise.

## Decision

- The plant model and every answer exist only under `truth/`. Inside it, `training_labels` holds
  the answers a model may learn from (convention tags of the training sites), `evaluation_key`
  holds the answers it is scored against (dialect and ad hoc tags, and every tag of the hold-out
  site), `split.json` names the hold-out site and the rule, and `plant.json` serves final scoring.
- Nothing outside `truth/` carries a truth field name or a surrogate id. Event ids are opaque
  hashes. The site contract is built without importing the plant entities. `leakcheck` proves it.
- Each site writes its **three timestamps in its own representation**, with no UTC helper field.
  If the first ingestion finds this too hard, we add help then and treat it as learning
  (mentor decision, 2026-11-05).
- The configuration actor in the audit log is a label: no identity system exists and none is
  claimed.

## Alternatives considered

| Option | Honest model score | Exercises RT12 | Why it lost (or won) |
|---|---|---|---|
| One answer file for all tags | no (train and test mixed) | n/a | allows accidental leakage into training |
| Structure in the catalogue | no | n/a | defeats the purpose |
| UTC helper field in every event | n/a | no | removes the exercise |
| Split truth, opaque ids, raw site time (this ADR) | yes | yes | won |

## Consequences

- + The leak guarantee is a test, not a promise.
- − The first ingestion has real work to do on time and identity.
- − The audit actor can be mistyped; that limit is documented, not hidden.
