# Implementation plan · 000 · The SDD harness

> Part of **Phase 4 · Specify** and approved with the spec at **G4**. The plan says *how* the
> build will proceed; the spec says *what* it must achieve.

## Approach

Domain first, because every other part evaluates it: gates, dossiers, approvals and digests as
pure, tested Python. Then the use cases against ports, tested with fakes; then the adapters,
tested against real files, git and subprocesses; then the CLI. The documents come next (harness,
templates, skills, roles), because the generators and rules read them; the dossier and the
teaching material last, since they describe the rest. Each step leaves the suite green.

## Where the build stands

This is the bootstrap dossier: steps 1 to 12 below were carried out before this plan was
approved (the harness could not govern its own creation), so the code, tests and documents
already exist and the suite is green (116 tests, coverage 96 % against the 85 % threshold). What
remains after G4 is steps 13 to 16. Steps 1 to 12 are kept so the plan still reads as the story
of the build, and so the teaching guide can follow it.

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
13. **`y/N` approval prompt (test first).** Rewrite the three tests of B05 (see the validation
    plan), then change `HumanConfirmation.confirm(summary)`, `TerminalConfirmation` (prompt
    `Approve? [y/N]: `, accept `y`/`yes` in any case), `ApproveGate._confirm` (no `expected`
    text; message `approval cancelled; nothing saved`), `FakeConfirmation` in
    `tests/sdd/fakes.py`, and the docstrings that mention the phrase. *(B05, ADR-0016)*
14. **Files appear as gates pass (test first).** Domain: `artifacts_after(gate)` in
    `domain/gates.py`, tested for every gate (G5 skipped, G7 nothing). Application:
    `ScaffoldArtifacts` (moves the template values and the requirements table out of
    `create_dossier.py`) and the port method `DossierRepository.add_artifacts`, which writes only
    the files that do not exist. Infrastructure: `YamlDossierRepository.add_artifacts`. Then
    `CreateDossier` creates `dossier.yaml` and `prd.md` only, `ApproveGate` scaffolds the next
    gate's files when the gate turns passed, and the CLI prints one `created:` line per file. The
    step is all-or-nothing: `add_artifacts` removes what it wrote if a write fails, and
    `ApproveGate` saves the dossier as it was before the approval and re-raises.
    Adapt the tests that assumed nine files. Check that a missing artifact reads as "not
    complete" in `EvaluateDossier` and in `CheckHarness`, without a crash. *(B01, B19, ADR-0018)*
15. **Backlog card test.** Add the test of B15 in `tests/sdd/test_domain.py`; it passes at once
    because the template was already changed (the test pins the format). *(B15, ADR-0017)*
16. **Documentation left, then verify.** Docstrings that still mention the typed phrase or the
    nine artifacts, ADR-0016, ADR-0017 and ADR-0018 set to *Accepted* in their files and in the
    index, re-read the teaching guide, run `poetry run sdd sync`, then `poetry run sdd verify
    000` (G5), and record the build log and the manual evidence (B12, B17) in `validation.md`.
    The other documents were updated while preparing G4 (see "Documentation impact" in the spec).

## Files to create or change

- **domain:** `tools/sdd/domain/*.py` (12 modules)
- **application:** `tools/sdd/application/{evidence.py, ports/*, use_cases/*, doc_rules/*, generators/*}`
- **infrastructure:** `tools/sdd/infrastructure/*.py` (10 modules)
- **composition and interface:** `tools/sdd/{config.py, bootstrap.py}`, `tools/sdd/interfaces/cli/{app.py, presenters.py}`
- **agent guard:** `tools/agent_hooks/agent_guard.py`, `.claude/settings.json`
- **tests:** `tests/sdd/*`, `tests/agent_hooks/*`
- **changed by steps 13 to 16:** `tools/sdd/application/ports/{environment.py, dossiers.py}`,
  `tools/sdd/application/scaffold_artifacts.py` (new),
  `tools/sdd/application/use_cases/{approve_gate.py, create_dossier.py}`,
  `tools/sdd/infrastructure/{terminal_confirmation.py, yaml_dossier_repository.py}`,
  `tools/sdd/domain/{errors.py, gates.py}`, `tools/sdd/bootstrap.py`,
  `tools/sdd/interfaces/cli/app.py`,
  `tests/sdd/{fakes.py, test_use_cases.py, test_infrastructure.py, test_domain.py, test_cli.py}`,
  ADR-0016, ADR-0017, ADR-0018 (status), the ADR index, `validation.md`, `teaching-guide.md`
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
- The `y/N` change touches the one place that keeps agents out of approvals. Mitigation: the
  terminal test stays first and untouched, its test (`test_terminal_requires_a_tty`) is not
  modified, and `test_agents_without_terminal_are_refused` must still pass unchanged.
- Creating files at approval time must never destroy work. Mitigation: `add_artifacts` writes
  only missing files, with a test; dossier 000 already has every file and must come out of the
  change untouched.
- Editing any of the three files of this specification after G4 makes G4 stale. If the build
  finds the spec wrong, we stop and change the spec, as AGENTS.md says.
