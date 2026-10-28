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
| [0004](0004-local-enforcement-without-ci.md) | Gates are enforced locally (pre-commit, `sdd`, agent hooks); no CI | Accepted |
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
