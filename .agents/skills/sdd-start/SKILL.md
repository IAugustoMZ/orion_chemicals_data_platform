---
name: sdd-start
description: Phase 0 of spec-driven development. Use when we ask for something in plain words (a feature, a CRUD, an idea, a fix), or ask "where are we?". Reads the whole requirements catalogue, maps the request to the RTs it serves (or marks it outside the catalogue), proposes the dossier, creates it and its branch, and reports the next gate.
---

# Start or resume work (phase 0 · gate G0)

We describe what we want in plain words ("we want a CRUD for X"). We do **not** name RTs:
mapping the request to the requirements is your job. Phase reference:
[lifecycle, phase 0](../../../harness/lifecycle.md#phase-0-context).

## Steps

1. **Orient.** Run `poetry run sdd status`. If the current branch is `spec/<id>-<slug>` and the
   request belongs to that dossier, that dossier is the work: report its next gate and switch to
   the skill of that phase.
2. **Read the whole catalogue** before proposing anything: `docs/requirements/README.md`, then
   `poetry run sdd rt` (every RT, not only the ones that look related). Consult the PDF
   `docs/requirements/Requisitos_Tecnicos_Orion_Chemicals.pdf` when a statement is ambiguous.
3. **Map the request to the requirements.** For each RT decide: *served* (the work makes it
   hold, at least in part), *related but left out* (say why), or *not related*. Also note the
   RTs the work must not break even if it does not serve them (for example RT01, read-only
   access; RT36, no credentials in code).
4. **Propose the dossier** to us in one short message, and wait for our confirmation:
   - title and kebab-case slug;
   - kind: `feature` (platform behaviour) or `enabler` (tooling or foundations);
   - the RTs served, each with one line on why, and the related RTs left out;
   - **if no RT is served**, say so plainly: the work is *outside the catalogue*
     ([ADR-0014](../../../docs/architecture/decisions/0014-work-outside-the-requirements-catalogue.md)).
     Propose the rationale (why it is worth doing anyway) and list the RTs you considered.
     It is allowed; we decide.
5. **Create it** once we agree (you run these commands, not us):

   ```bash
   # serves RTs
   poetry run sdd new "Title" --slug the-slug --rt RT01 --rt RT02
   # outside the catalogue: no --rt, a rationale instead
   poetry run sdd new "Title" --slug the-slug --rationale "why it is worth doing"
   # an enabler
   poetry run sdd new "Title" --slug the-slug --kind enabler --rationale "why"
   git switch -c spec/<id>-the-slug
   ```

6. **Check G0:** `poetry run sdd status <id>` shows G0 passed. If not, fix `dossier.yaml`
   (an unknown RT, or a missing rationale).
7. Continue with `sdd-discover`. The PRD's "Requirements digest" records the mapping of step 3,
   so we review it at G1.

## Done when

The dossier exists, G0 passed, the branch is checked out, we confirmed the RT mapping (or the
rationale for working outside the catalogue), and we know which phase is next.
