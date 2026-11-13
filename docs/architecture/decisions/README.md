# Architecture Decision Records

Why things are the way they are. One file per decision, numbered, never deleted: a reversed
decision is marked *Superseded by ADR-NNNN* and stays as history. How to write one: skill
`write-adr` and the [template](../../../harness/templates/adr.md). `sdd check` verifies that every
ADR is listed here and has a status and a date.

## Foundation (dossier 000, the harness)

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-spec-driven-development-with-our-own-harness.md) | We practise spec-driven development with our own lightweight harness | Accepted |
| [0002](0002-agents-md-and-agent-skills-are-canonical.md) | AGENTS.md and Agent Skills are the canonical sources; tool files are generated pointers | Accepted |
| [0003](0003-gates-approved-by-people-bound-to-digests.md) | Human gates are approved by both of us, at a terminal, bound to content digests | Accepted |
| [0004](0004-local-enforcement-without-ci.md) | Gates are enforced locally (pre-commit, `sdd`, agent hooks); no CI | Superseded by ADR-0024 |
| [0005](0005-poetry-for-every-python-environment.md) | Poetry manages every Python environment, one project with dependency groups | Accepted |
| [0006](0006-docker-compose-as-the-runtime.md) | Docker Compose is the runtime, instead of Kubernetes | Accepted |
| [0007](0007-clean-architecture-for-all-python-code.md) | All Python code follows clean architecture, enforced by import-linter | Accepted |
| [0008](0008-docs-as-code-with-mkdocs-material.md) | Documentation is code, published with MkDocs + Material from the repository root | Accepted |
| [0009](0009-english-as-the-only-language.md) | English is the only language of the repository | Accepted |
| [0010](0010-every-dossier-has-a-teaching-guide.md) | Every dossier has a teaching guide, stored inside it and approved at G6 | Accepted |
| [0011](0011-requirements-catalogue-as-yaml.md) | The requirements are transcribed into a machine-readable YAML catalogue | Accepted |
| [0012](0012-backlog-as-markdown-in-the-repository.md) | The backlog lives in the repository as Markdown, inside the dossiers | Accepted |
| [0013](0013-mermaid-diagrams-with-official-logos.md) | Diagrams are Mermaid with official logos from a registry, checked by `sdd check` | Accepted |
| [0014](0014-work-outside-the-requirements-catalogue.md) | Work outside the requirements catalogue is allowed, with a rationale | Accepted |
| [0015](0015-one-gate-at-a-time-reviewed-in-chat.md) | One gate at a time, reviewed with us in the chat, approved at the terminal | Accepted |
| [0016](0016-approval-confirmation-is-a-yes-no-prompt.md) | The approval confirmation is a y/N prompt at an interactive terminal | Accepted |
| [0017](0017-backlog-items-are-self-contained-cards.md) | Backlog items are self-contained cards | Accepted |
| [0018](0018-artifacts-are-created-as-gates-pass.md) | Artifacts are created as the gates pass, not all at once | Accepted |

## Time-series source (dossier 001)

| ADR | Decision | Status |
|---|---|---|
| [0019](0019-tssource-package-and-dependencies.md) | The generator is a second clean-architecture package with its own dependency group | Proposed |
| [0020](0020-deterministic-generation-and-simulated-reception-time.md) | Generation is deterministic, and the reception time is simulated | Proposed |
| [0021](0021-output-as-immutable-files-and-segments.md) | The output is a folder of immutable files, with small stream segments | Proposed |
| [0022](0022-hidden-plant-and-site-local-time.md) | The plant stays hidden in `truth/`, and events carry site-local time | Proposed |
| [0023](0023-item-by-item-build-flow.md) | A backlog is approved and built one card at a time | Accepted |
| [0024](0024-ci-with-github-actions-blocks-merge.md) | CI with GitHub Actions blocks the merge (supersedes ADR-0004) | Accepted |
| [0025](0025-pi-like-acquisition-and-quality-codes.md) | The output has the shape of a historian: exception, snapshot, compression, quality codes | Proposed |
| [0026](0026-a-rationale-is-required-for-every-dossier.md) | A rationale is required for every dossier (amends ADR-0014) | Accepted |
| [0027](0027-benchmark-measures-per-second-rates-with-a-bounded-queue.md) | The spike measures per-second rates through a bounded queue and exits 3 below the floor | Proposed |
