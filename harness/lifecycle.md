# Lifecycle: the seven phases

One section per phase of the operating model, from business intent to measurable impact. Each
section is a reference card: why the phase exists, what goes in, who does what, what comes out,
and the gate that closes it. In every phase, **"we" are the mentor and the mentee**: we play all
the human roles of the operating model (stakeholder, product owner, designer, tech lead, QA).

The overview diagram is in [how-it-works.md](how-it-works.md#2-the-workflow-end-to-end); the
gate criteria are in [gates.md](gates.md).

**One gate at a time.** The agent drafts a phase's artifact only after the previous human gate
passed. At the end of each human phase it runs the skill `sdd-review-gate`: it briefs us in the
chat, asks specific questions we cannot answer without reading, applies our changes, and stops.
We then approve, each at our own terminal, and the agent confirms with `sdd status` before it
starts the next phase ([ADR-0015](../docs/architecture/decisions/0015-one-gate-at-a-time-reviewed-in-chat.md)).

## Phase 0: Context

*From a need to a dossier that knows its requirements.*

- **Inputs:** a need, told in plain words ("we want a CRUD for X"); the catalogue
  `docs/requirements/rt-catalog.yaml`. We do not have to name RTs.
- **Agents** (skill `sdd-start`): read the whole catalogue (`poetry run sdd rt`), map the
  request to the RTs it serves and the related ones it leaves out, or say that it is *outside
  the catalogue* and propose why it is worth doing anyway; propose the title and slug; once we
  agree, run `sdd new` and create the branch.
- **We:** confirm the mapping (or the rationale) and the scope in one sentence.
- **Output:** `specs/<id>-<slug>/` created by `poetry run sdd new`, branch `spec/<id>-<slug>`.
- **Gate:** **G0 · Context** (automatic): every cited RT exists; an enabler, and a feature that
  cites no RT, state their rationale
  ([ADR-0014](../docs/architecture/decisions/0014-work-outside-the-requirements-catalogue.md)).

## Phase 1: Discover

*From a need to a validated product intent.*

- **Inputs:** the need and the results we expect, the RTs, anything already known (notes,
  interviews, data samples).
- **Agents:** analyse the inputs, synthesise them, and draft `prd.md`: requirements digest,
  problem, measurable goals, users and scenarios, scope in and out, constraints, risks and open
  questions. Skill: `sdd-discover`; role: [product analyst](roles/product-analyst.md).
- **We:** share the need and the expected results; correct the draft; agree on what success
  means.
- **Output:** a validated PRD (scope, goals, success metrics, constraints).
- **Gate:** **G1 · PRD validated** (validate and align).

## Phase 2: Plan

*From product intent to a prioritised backlog.*

- **Inputs:** the approved PRD.
- **Agents:** propose epics, features and work items (PBIs), each with acceptance criteria in
  EARS notation and the RTs it contributes to; propose an order with its reasons. Skill:
  `sdd-plan`; role: [backlog planner](roles/backlog-planner.md).
- **We:** review, adjust and prioritise; split items that are too big.
- **Output:** an approved backlog in `backlog.md` (the backlog lives in the repository, ADR-0012).
- **Gate:** **G2 · Backlog approved**.

## Phase 3: Structure

*The right interface approach for each item.*

- **Inputs:** the approved backlog.
- **Agents:** decide whether a prototype is needed and why; describe how people or systems will
  meet the result (API, CLI, dataset, dashboard); when needed, build a coded prototype with a
  mocked back end. Skill: `sdd-structure`; role: [UX designer](roles/ux-designer.md).
- **We:** validate the approach, and its usability only when it matters.
- **Output:** an approved approach in `ux-approach.md` (with a prototype when needed).
- **Gate:** **G3 · Approach approved**.

## Phase 4: Specify

*An execution-ready specification per item.*

- **Inputs:** PRD, backlog and approach (approved); the ADRs; the codebase.
- **Agents:** collect the context (requirements, ADRs, modules, contracts) and write the
  execution spec: numbered EARS behaviours, architecture impact before/after with logos,
  contracts and data, design (classes, patterns, SOLID), STRIDE threat model, validation plan,
  ADR drafts, documentation impact; then `plan.md` and `tasks.md`. Skill: `sdd-specify`; role:
  [spec architect](roles/spec-architect.md).
- **We:** review and adjust the architecture decisions; make sure the validation plan proves
  every RT's "how we verify it".
- **Output:** the execution specification: scope, behaviour, affected components, validation
  plan. ADRs move from *Proposed* to *Accepted*.
- **Gate:** **G4 · Specification approved for execution**. From now on, code may change.

## Phase 5: Build

*Agentic implementation with deterministic validation.*

- **Inputs:** the approved spec, plan and tasks; branch `spec/<id>-<slug>`.
- **Agents:** plan, implement, test and loop: one task at a time, code + tests + documentation +
  diagrams, then `poetry run sdd verify <id>`; on failure fix and verify again, up to the loop
  limit; keep the build log in `validation.md`. Skill: `sdd-build`; roles:
  [implementer](roles/implementer.md), [verifier](roles/verifier.md).
- **We:** monitor progress and resolve issues when the agent escalates.
- **Output:** candidate code with tests and evidence on the branch.
- **Gate:** **G5 · Deterministic checks passed** (automatic, bound to the governed code).

## Phase 6: Validate

*Human review and independent validation.*

- **Inputs:** the branch with G5 passed.
- **Agents:** an *independent* reviewer (not the implementer) reviews code, architecture and
  security against the spec; a QA agent runs the functional and exploratory validation; the
  teacher completes the teaching guide. Skill: `sdd-validate`; roles:
  [reviewer](roles/reviewer.md), [QA explorer](roles/qa-explorer.md),
  [teacher](roles/teacher.md).
- **We:** review the diff (`git diff main...spec/<id>-<slug>`), validate on the branch
  (functional and exploratory), read the teaching guide until it teaches.
- **Output:** `validation.md` and `teaching-guide.md` complete; all checks done; ready to merge.
- **Gate:** **G6 · Approved for merge**. Then `git merge --no-ff` into `main`.

## Phase 7: Release and learn

*Deploy, monitor and incorporate feedback.*

- **Inputs:** the merged change.
- **Agents:** deploy to the target environment (`docker compose up`), monitor telemetry, analyse
  usage and feedback, draft `release.md`. Skill: `sdd-release`; role:
  [release steward](roles/release-steward.md).
- **We:** validate the business results against the PRD's goals and prioritise the next items.
- **Output:** software running locally with observability; learnings recorded; lessons about
  the process turned into a harness change (its own enabler dossier).
- **Gate:** **G7 · Results validated**.
