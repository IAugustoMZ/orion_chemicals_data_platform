# ADR-0014: Work outside the requirements catalogue is allowed, with a rationale

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** RT01-RT42 (how work relates to them); refines [ADR-0011](0011-requirements-catalogue-as-yaml.md)

## Context

The first version of gate G0 said a *feature* must cite at least one RT. We ask for work in
plain words ("we want a CRUD for X"), and some of it serves no requirement in the catalogue: an
admin screen, a convenience feature, an experiment. The only way through G0 was to call such
work an *enabler*, which means tooling and is the wrong label. Or we could cite a loosely
related RT, which corrupts the traceability matrix.

There was also a usability problem. The commands (`sdd new --rt RT01`) made it look as if
people had to know the RTs before starting. Mapping a request to the requirements is
exactly the reading work an agent should do for us.

## Decision

1. **We ask in plain words; the agent maps.** The `sdd-start` skill makes the agent read the
   whole catalogue, classify each RT as served, related but left out, or not related, and
   propose the dossier with that mapping. We confirm it before `sdd new` runs.
2. **A feature may cite no RT.** It is then *outside the catalogue*. G0 passes only if
   `dossier.yaml` states a rationale (why it is worth doing anyway). Its PRD's requirements
   digest lists the RTs considered, why none applies, and the RTs it must still not break.
   We review that list at G1.
3. **It stays visible.** The status board marks such work as `feature (outside RTs)`. The
   traceability matrix lists it in its own section, with the rationale, and it never counts
   towards RT coverage.

## Alternatives considered

| Option | Why it lost |
|---|---|
| Keep "a feature cites ≥ 1 RT" | forces mislabelling (enabler) or false citations; the matrix would lie |
| Add a third kind (`extra`) | another word to learn for the same fact; "a feature with no RT" already says it |
| Let G0 pass any feature silently | work outside the requirements must be a visible, reviewed decision, not an accident |
| Ask people to pick the RTs | the catalogue has 42 entries; reading and mapping them is the agent's job, our job is to check it |

## Consequences

- + Any request can start the same way: ask the agent. The mapping is reviewed at G1, like any
  other part of the PRD.
- + The traceability matrix stays honest: RT coverage only counts real citations, and
  work outside the catalogue is listed separately.
- − A rationale is free text; its quality depends on our review at G1. The agent must still
  list the RTs it considered, so a missed requirement is easy to spot.
