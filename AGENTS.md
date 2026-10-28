# AGENTS.md: instructions for coding agents

This repository is built with **spec-driven development (SDD)**, governed by two people: the
mentor and the mentee ("we", listed in `harness/team.yaml`). These instructions apply to every
coding agent (Claude Code, Cursor, Codex, GitHub Copilot, Gemini CLI, ...). They are the
canonical source; tool-specific files only point here. The full picture for people is in
[harness/how-it-works.md](harness/how-it-works.md).

## 1. Read before you act, in this order

1. **The requirements.** [docs/requirements/README.md](docs/requirements/README.md) and the
   catalogue `docs/requirements/rt-catalog.yaml` (RT01-RT42, transcribed from
   `Requisitos_Tecnicos_Orion_Chemicals.pdf`). Every piece of work is checked against all of
   them and cites the ones it serves (see "Starting work" below). `poetry run sdd rt` prints
   every RT; `poetry run sdd rt RT09` prints one.
2. **The constitution.** [harness/constitution.md](harness/constitution.md): the articles that
   are never negotiable.
3. **Where the work is.** `poetry run sdd status` shows every dossier (spec folder) and its next
   gate. Work only on the dossier of the current branch (`spec/<id>-<slug>`).
4. **The phase you are in.** [harness/lifecycle.md](harness/lifecycle.md) for what the phase
   needs, and the matching skill in `.agents/skills/` (`sdd-discover` ... `sdd-release`).

## 2. The lifecycle and its gates

| Phase | You (the agent) produce | Gate | Closed by |
|---|---|---|---|
| 0 Context | the requirement citations in `dossier.yaml` | **G0** | `sdd` (automatic) |
| 1 Discover | `prd.md` draft from our inputs | **G1** PRD validated | us |
| 2 Plan | `backlog.md`: epics, features, items with EARS criteria | **G2** Backlog approved | us |
| 3 Structure | `ux-approach.md`: prototype or not, and why | **G3** Approach approved | us |
| 4 Specify | `spec.md`, `plan.md`, `tasks.md`, draft ADRs | **G4** Spec approved | us |
| 5 Build | code + tests + docs, in a loop with `sdd verify` | **G5** Checks passed | `sdd verify` |
| 6 Validate | `validation.md`, `teaching-guide.md`, independent review | **G6** Approved for merge | us |
| 7 Release & Learn | `release.md`: results and learnings | **G7** Results validated | us |

**Starting work.** We ask in plain words ("we want a CRUD for X") and do not name RTs. You read
the whole catalogue, map the request to the RTs it serves and the related ones it leaves out,
and propose the dossier (skill `sdd-start`). If no RT applies, say so: the work is *outside the
catalogue*, which is allowed with a rationale and the list of RTs you considered
([ADR-0014](docs/architecture/decisions/0014-work-outside-the-requirements-catalogue.md)).
Once we agree, you run `poetry run sdd new "Title" --slug kebab-name --rt RTnn` (or
`--rationale "why"` instead of `--rt`) and switch to the branch it prints. Fill each artifact by
replacing every `TODO(sdd)` and keeping every `##` section of its template.

## 3. Hard rules (the agent guard and pre-commit enforce most of them)

- **Never approve.** Do not run `sdd approve`, do not edit `approvals:` or `verification:` in a
  `dossier.yaml`. When a gate is ready, run the skill `sdd-review-gate` and ask us to approve.
- **One gate at a time.** Draft an artifact only after the gate before it passed (check with
  `sdd status`, not with our word). Never write the PRD, backlog, approach and spec in one go:
  review each with us in the chat (briefing plus specific questions), wait for the answers,
  and stop until we approved at our terminals ([ADR-0015](docs/architecture/decisions/0015-one-gate-at-a-time-reviewed-in-chat.md)).
- **No governed change before G4.** Code, tests, `docker/`, `compose.yaml`, `pyproject.toml`,
  `harness/`, `.agents/`, `.claude/` change only on the dossier's branch after G4 passed.
  Documentation and dossier artifacts can be written at any time.
- **Never bypass the gates.** No `--no-verify`, no `pre-commit uninstall`, no forced pushes, no
  editing `.pre-commit-config.yaml`, `.claude/settings.json`, `harness/team.yaml` or
  `tools/agent_hooks/`.
- **Never touch secrets.** No `.env` (except `.env.example`), nothing under `deploy/secrets/`,
  no keys. Credentials never appear in code or documents (RT36).
- **Stay in scope.** Build what `spec.md` says. If the spec is wrong or incomplete, stop, propose
  the change to the spec and wait: editing an approved spec makes G4 stale, on purpose.
- **Loop limit.** In the build loop, after **3** consecutive failing `sdd verify` runs on the
  same task, stop and ask us ([AI control plane](harness/ai-control-plane.md)).

## 4. How code is written here

- Python only through **Poetry** (`poetry install`, `poetry run ...`); never `pip install` into
  the project, never another environment manager.
- **Clean architecture and SOLID** as in [harness/principles.md](harness/principles.md):
  `domain` <- `application` <- `infrastructure` / `interfaces`, wired only in `bootstrap.py`;
  ports are `typing.Protocol`s; `lint-imports` enforces the layers.
- **Every module, class and function has a docstring** stating the why and the contract.
  Type-annotate everything (`mypy --strict`). Small files, one concept each.
- **Security and quality** as in [harness/security.md](harness/security.md) and
  [harness/quality.md](harness/quality.md). Tests come with the code, never after.
- **English only**, in code, comments, documents and commit messages.
- **Runtime is Docker Compose** (`compose.yaml`); no Kubernetes.

## 5. Documentation is part of the change (Definition of Done)

Every change updates, in the same branch
([architecture-upkeep.md](harness/architecture-upkeep.md)):

- an **ADR** in `docs/architecture/decisions/` for every decision made or reversed;
- the **architecture pages** and their **Mermaid diagrams, with the official logo of every tool**
  (registry: `docs/architecture/logos/registry.yaml`;
  [documentation standard](harness/documentation-standard.md));
- the **root README** and component READMEs, then `poetry run sdd sync`;
- the dossier's **teaching guide**: a detailed, didactic explanation of every decision, from the
  architecture down to classes, abstractions and patterns, with diagrams.

## 6. Commands

```bash
poetry install --with docs          # once
poetry run sdd status               # where every spec is
poetry run sdd rt RT01 RT09         # read requirements
poetry run sdd rt                   # every requirement (read them all before proposing)
poetry run sdd new "Title" --slug x --rt RT01
poetry run sdd new "Title" --slug x --rationale "why"   # outside the catalogue
poetry run sdd verify <id>          # gate G5: the deterministic suite
poetry run sdd check                # consistency of dossiers, docs, logos, links, ADRs
poetry run sdd sync                 # regenerate README status, traceability, tool adapters
poetry run pre-commit run --all-files
```

## 7. When you finish a turn

Report what changed, which gate is next, what you need from us, and anything you could not
verify. Never claim a gate passed that `sdd status` does not show as passed.
