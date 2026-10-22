# Documentation standard

Documentation is part of the change (Constitution, article VI). This page says *what* every
change documents and *how*. [architecture-upkeep.md](architecture-upkeep.md) says *which*
documents a given change touches.

## What every change documents

| Document | Where | Required when |
|---|---|---|
| Architecture Decision Record | `docs/architecture/decisions/NNNN-title.md` | a decision is made or reversed (technology, structure, pattern, process) |
| Architecture pages and diagrams | `docs/architecture/` | structure, data flow, deployment or a dependency changes |
| Component README | next to the component (`src/<package>/README.md`) | a component is added or its usage changes |
| Root README | `README.md` | what the platform is, does or how to start it changes; status blocks via `sdd sync` |
| Teaching guide | `specs/<id>-<slug>/teaching-guide.md` | **always**, for every dossier |
| Glossary | `docs/learn/glossary.md` | a new term appears |

## Diagrams and official logos

All diagrams are **Mermaid**, embedded in Markdown, so they render on GitHub, in the MkDocs
site and in editors, and they are diffable in review.

- **Every node that represents a tool or technology carries its official logo**, embedded as an
  image in the node label. Logos come from the registry
  [`docs/architecture/logos/registry.yaml`](../docs/architecture/logos/registry.yaml) (Simple
  Icons first, Devicon when Simple Icons does not carry the brand):

  ```text
  DB[("<img src='https://cdn.simpleicons.org/postgresql/4169E1' width='32' height='32'/><br/>PostgreSQL 16<br/>catalog")]
  ```

- A new tool in a diagram means a new registry entry in the same change.
- `sdd check` (rule `mermaid-logo`) reports flowchart nodes that name a registered tool without an
  image: an **error** in `docs/architecture/` and the root README, a **warning** elsewhere.
- Quote every label (`A["text"]`); use `<br/>` for line breaks; keep one idea per node.
- Pick the diagram type that answers the question:

| Question | Diagram |
|---|---|
| What are the parts and how do they connect? | `flowchart` with logos (architecture, deployment) |
| In what order do things happen? | `sequenceDiagram` |
| What states can it be in? | `stateDiagram-v2` |
| What are the classes and their relations? | `classDiagram` |
| What data is stored and how is it related? | `erDiagram` |
| How does a user move through it? | `journey` |

## ADRs

- Copy [templates/adr.md](templates/adr.md). Number sequentially; never reuse or delete a number.
- Status *Proposed* while the spec is being written, *Accepted* at G4, *Superseded by ADR-NNNN*
  when reversed (the old ADR stays, as history).
- Every ADR is linked from `docs/architecture/decisions/README.md` (`sdd check` verifies it) and
  from the spec and teaching guide of its dossier.
- An ADR must let a reader disagree: it states the context, the alternatives and why each lost,
  and the consequences, including the bad ones.

## The teaching guide

The teaching guide is the didactic record of a dossier, written for the mentee who was not in the
room. It is stored **inside the dossier** (`specs/<id>-<slug>/teaching-guide.md`) so it is
created, reviewed and approved with the change it explains (ADR-0010), and the documentation site
assembles all guides into a curriculum ([learning path](../docs/learn/README.md)).

Its fourteen sections are fixed by [the template](templates/teaching-guide.md) and checked at G6.
What makes a guide good:

- **Every decision has its justification**, at every level: why this architecture, why this
  library, why this class exists, why this abstraction, why this pattern, what we gave up.
- **Heavy use of diagrams**: architecture before/after (with logos), class diagrams, sequences of
  the main flows, state machines, data models. Each diagram is narrated.
- **The code tour matches the diff**: files in reading order, short snippets, the "why" of every
  non-obvious line.
- **It is honest**: what went wrong first, what is not tested, what we would do differently.
- **It teaches actively**: a "run it yourself" exercise and questions for the mentee.
- **No undefined term**: every domain and technical term is explained or in the glossary.

The test of a good guide: could the mentee rebuild the feature, and defend its decisions, from
the guide alone?

## The root README

The root README is the front door, written for someone who has never seen the repository:

- what this is and why it exists, in a few sentences;
- **"start here" paths by reader** (learner, stakeholder, developer, coding agent);
- the lifecycle at a glance and the **status board** of every spec (generated: `<!-- sdd:status -->`
  block) and the **requirements coverage** (generated: `<!-- sdd:coverage -->` block);
- the architecture at a glance, with logos;
- a quick start of three commands;
- a map of where everything lives.

The generated blocks are rewritten by `poetry run sdd sync`; never edit inside them.

## Style

- English, plain and direct; short sentences; active voice.
- One `#` title per file; `##` for sections; tables for comparisons; lists for steps.
- Relative links between documents (they work on GitHub, in editors and on the site); `sdd check`
  reports broken ones.
- Lines wrapped at about 99 characters in Markdown sources.
