# ADR-0008: Documentation is code, published with MkDocs + Material from the repository root

- **Status:** Accepted
- **Date:** 2026-10-21
- **Dossier:** specs/000-sdd-harness
- **Requirements:** RT32 (documented interfaces), supports all

## Context

The repository is mostly documents (harness, dossiers, ADRs, teaching guides) and they are read
in three places: GitHub, editors and, for learning, a browsable site with search and navigation.
Documents must stay next to the code they describe and be reviewed with it.

## Decision

- All documentation is Markdown in the repository, reviewed in the same branch as the code.
- **MkDocs with Material for MkDocs** publishes the repository as a site. With the `same-dir`
  plugin, `docs_dir` is the repository root, so every relative link works the same on GitHub,
  in editors and on the site, and the root README is the home page.
- The site runs with `poetry run mkdocs serve` or `docker compose up docs`; `mkdocs build --strict`
  is a G5 check, so broken anchors fail the suite.
- Mermaid diagrams render natively (`pymdownx.superfences` custom fence).

## Alternatives considered

| Option | Why it lost |
|---|---|
| Markdown on GitHub only | no search, no navigation, no learning path; not local |
| Zensical (successor of Material, reads `mkdocs.yml`) | young; feature parity unclear at the time of writing; the natural exit path (see consequences) |
| Docusaurus, Sphinx | Node toolchain or reStructuredText; less natural for a Markdown-first repository |
| A `docs/` folder only (no same-dir) | harness and dossiers would need copying or link rewriting |

## Consequences

- + One source, three readers; links validated by `sdd check` and by the strict build.
- − Material for MkDocs is in maintenance mode (critical fixes only, support announced for at
  least twelve months from its last feature release). We pin `^9.7` and **revisit this ADR** when
  that support ends or a needed fix is missing; the planned exit is Zensical, which reads the
  same `mkdocs.yml`.
