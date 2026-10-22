# Governed context plane

What an agent knows determines what it builds. The *governed context plane* is the corporate
knowledge agents are allowed and expected to read, kept in known places so that every phase
starts from the same facts. In the operating model this plane spans the whole lifecycle: every
phase reads from it and writes back to it.

## Where each kind of context lives

| Context (operating model) | In this repository | Read in phases | Written in phases |
|---|---|---|---|
| **Work items** (backlog, items, PRs) | dossiers `specs/<id>-<slug>/`, `backlog.md`, git branches `spec/*`, `sdd status` | all | 0-7 |
| **Requirements** | `docs/requirements/` (PDF + `rt-catalog.yaml`, `sdd rt`) | 0, 1, 4, 6 | never (only corrected against the PDF) |
| **Codebase** (repository context) | the code; module map in [docs/architecture/README.md](../docs/architecture/README.md) | 4, 5, 6 | 5 |
| **Architecture** (patterns, guides) | `docs/architecture/`, ADRs, [principles.md](principles.md), [security.md](security.md) | 3, 4, 5, 6 | 4 (ADRs), 5 (pages) |
| **Design system** (tokens, components, patterns) | introduced by the first spec with a user interface | 3, 5 | 3, 5 |
| **Documentation** (product, technology, domain) | `docs/`, teaching guides, glossary, component READMEs | all | 5, 6, 7 |
| **APIs and data** (schemas, contracts) | the "contracts and data" section of each spec; contract files next to the component | 4, 5, 6 | 4, 5 |
| **Test infrastructure** (Playwright, test data) | `tests/`, fixtures, `harness/checks.yaml` | 4, 5, 6 | 5 |
| **Observability** (metrics, logs) | introduced with the platform (OpenTelemetry is a candidate, RT39-RT40) | 7 | 5 (instrumentation) |
| **Security and policies** (compliance, guardrails) | [security.md](security.md), [constitution.md](constitution.md), the agent guard | all | through an enabler dossier only |

## Rules

- **Agents read the plane before proposing.** Every skill starts by reading the requirements and
  the dossier; the spec's "context collected" section lists what was read.
- **The plane is versioned with the code.** Everything above is in git, so the context an agent
  used for a decision can be reconstructed from the commit.
- **External context is cited, not copied blindly.** Documentation fetched from the internet or
  through an MCP server is summarised with its source URL and date in the spec.
- **MCP servers are optional accelerators**, never the only source: a fact that matters is
  written into the repository. When a tool offers MCP access (to documentation, a database, a
  browser), the spec says which servers were used.
- **Restricted data stays out of prompts.** Credentials and data classified as restricted never
  enter the context of an agent (RT35-RT36).
