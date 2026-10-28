# Harness

The standing rules of this repository, for people and for coding agents. *Harness* is everything
around the AI that makes its work reliable: the instructions it reads (guides), the checks that
judge what it produced (sensors), and the checkpoints where we decide (gates). Agents reach this
folder through [AGENTS.md](../AGENTS.md); people start with **[how it works](how-it-works.md)**.

| File | What it holds | Read it when |
|---|---|---|
| [how-it-works.md](how-it-works.md) | the whole system: actors, workflow, gates, enforcement, with diagrams | first, and whenever something blocks you |
| [constitution.md](constitution.md) | the articles that are never negotiable | before any work |
| [lifecycle.md](lifecycle.md) | the seven phases: inputs, activities (ours and the agents'), outputs, gate | at the start of every phase |
| [gates.md](gates.md) | G0-G7: criteria, evidence, how to approve, what makes a gate stale | before approving |
| [principles.md](principles.md) | coding standards: clean architecture, SOLID, patterns, docstrings, Python | before writing or reviewing code |
| [security.md](security.md) | the security baseline: secrets, least privilege, inputs, containers, threat modelling | when specifying and reviewing |
| [quality.md](quality.md) | testing strategy, the G5 suite, the code review checklist | when building and reviewing |
| [documentation-standard.md](documentation-standard.md) | what every change documents: ADRs, diagrams with official logos, READMEs, teaching guide | with every change |
| [architecture-upkeep.md](architecture-upkeep.md) | the upkeep matrix (if you change X, update Y) and the pre-commit review | before every commit |
| [context-plane.md](context-plane.md) | the governed context: what agents may read and where it lives | when an agent lacks context |
| [ai-control-plane.md](ai-control-plane.md) | model routing, guardrails, cost, audit, loop limits | when configuring or running agents |
| [roles/](roles/README.md) | agent roles (tool-agnostic), generated into Claude Code subagents | when delegating work to an agent |
| [templates/](templates/README.md) | one template per artifact: the definition of ready of each gate | when a dossier is created |
| [team.yaml](team.yaml) | who "we" are and the approval policy | once, then when the team changes |
| [checks.yaml](checks.yaml) | the deterministic suite of gate G5 | when adding a quality check |

Changing anything in this folder is a *governed* change: it needs its own enabler dossier with an
approved specification, like code does. The harness evolves through the same process it imposes.
