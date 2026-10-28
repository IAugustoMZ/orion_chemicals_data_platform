# Implementation plan · 000 · The SDD harness

> Part of **Phase 4 · Specify** and approved with the spec at **G4**. The plan says *how* the
> build will proceed; the spec says *what* it must achieve.

## Approach

Domain first, because every other part evaluates it: gates, dossiers, approvals and digests as
pure, tested Python. Then the use cases against ports, tested with fakes; then the adapters,
tested against real files, git and subprocesses; then the CLI. The documents come next (harness,
templates, skills, roles), because the generators and rules read them; the dossier and the
teaching material last, since they describe the rest. Each step leaves the suite green.

## Steps

1. Project skeleton: `pyproject.toml` (Poetry, groups, tool configuration, import contracts),
   `.gitignore`, `.gitattributes`, `.editorconfig`. *(B07 prerequisites)*
2. Requirement catalogue `rt-catalog.yaml` from the PDF (42 entries). *(B02, G0)*
3. Domain: errors, gates, digest, team, requirement, approval, quality, dossier, gate status,
   governance, findings, readiness. *(B03, B04)*
4. Application: ports; evidence; use cases create, evaluate, approve, verify, guard. *(B01-B08)*
5. Application: documentation rules (mermaid, links, ADR), generators (status, traceability,
   adapters), lint, sync, check. *(B09, B10)*
6. Infrastructure adapters, configuration, composition root, Typer CLI. *(B01-B10)*
7. Agent guard and `.claude/settings.json`. *(B11)*
8. Tests for every step above (unit, integration, end to end), coverage ≥ 85 %.
9. Harness documents, templates, team and checks files, logo registry (URLs verified).
10. AGENTS.md, CLAUDE.md, GEMINI.md, Copilot and Cursor pointers; skills; roles; `sdd sync`.
11. pre-commit configuration, `.secrets.baseline`, Compose service and docs image, `mkdocs.yml`.
    *(B12)*
12. Documentation: requirements, research, architecture, ADRs, learning path, primers,
    tutorials, root README, CONTRIBUTING; this dossier's artifacts and teaching guide.

## Files to create or change

- **domain:** `tools/sdd/domain/*.py` (12 modules)
- **application:** `tools/sdd/application/{evidence.py, ports/*, use_cases/*, doc_rules/*, generators/*}`
- **infrastructure:** `tools/sdd/infrastructure/*.py` (10 modules)
- **composition and interface:** `tools/sdd/{config.py, bootstrap.py}`, `tools/sdd/interfaces/cli/{app.py, presenters.py}`
- **agent guard:** `tools/agent_hooks/agent_guard.py`, `.claude/settings.json`
- **tests:** `tests/sdd/*`, `tests/agent_hooks/*`
- **docker and config:** `compose.yaml`, `docker/docs.Dockerfile`, `.dockerignore`, `mkdocs.yml`,
  `.pre-commit-config.yaml`, `.secrets.baseline`, `pyproject.toml`, `poetry.lock`, `poetry.toml`
- **harness:** `harness/*.md`, `harness/templates/*`, `harness/roles/*`, `harness/team.yaml`,
  `harness/checks.yaml`; `.agents/skills/*`; generated `.claude/`, `.cursor/commands/`, `.github/prompts/`
- **docs:** `docs/requirements/*`, `docs/research/*`, `docs/architecture/**`, `docs/learn/**`,
  `docs/tutorials/*`; `README.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `CONTRIBUTING.md`

## Rollback

Delete the branch `spec/000-sdd-harness`: nothing outside the repository is changed (no data, no
services left running besides the optional docs container, removed with `docker compose down`).

## Risks during the build

- Windows specifics (line endings, executable resolution, console encoding): `.gitattributes`
  forces LF; checks resolve commands with `shutil.which`; CLI output is ASCII.
- Logo URLs disappearing from CDNs: every URL checked with an HTTP request; OpenAI's logo was
  removed from the live Simple Icons CDN and is pinned to a release.
- Mermaid renderers refusing HTML labels: verified with Mermaid's own renderer (images shown).
