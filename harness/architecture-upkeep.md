# Keeping architecture and documentation current

**Rule: documentation never lags the code.** If a change touches an item of the first column,
the second column is updated *in the same branch*, before G6.

## Upkeep matrix

| If you change… | Update |
|---|---|
| A package, module, layer or port (add, move, remove, rename) | the module map in [docs/architecture/README.md](../docs/architecture/README.md); the import-linter contracts in `pyproject.toml` |
| A runtime flow (request path, load, job, approval) | the flow diagrams (sequence/state) in the architecture page or the component README |
| Deployment: `compose.yaml`, a Dockerfile, a volume, a port, a network | [docs/architecture/deployment.md](../docs/architecture/deployment.md) (diagram with logos), the root README quick start if commands changed |
| A dependency (library, database, tool) or a choice between alternatives | a new ADR (or mark the old one *Superseded*); a logo registry entry if it appears in diagrams |
| A data model (table, column, constraint, file schema) | the data model section (`erDiagram`) of the component's documentation and the spec's contracts |
| A public interface (API endpoint, CLI command, dataset contract) | the component README; the contract file; the version (RT32) |
| Security: a role, grant, secret or exposed port | [security.md](security.md) if a rule changed; the component's access model; the [secrets register](../docs/architecture/secrets.md) |
| The harness: a gate, rule, template, skill, role, check | the harness page concerned, [how-it-works.md](how-it-works.md) if the workflow changed, `poetry run sdd sync` (adapters) |
| The `sdd` tool | the teaching guide of dossier 000 (or of the enabler dossier that changes it), the harness pages that describe the behaviour |
| What the platform is or how to start it | the root README |
| Any dossier | its teaching guide; `poetry run sdd sync` (README status, traceability) |

## Review before every commit

The documents describe the **branch**, not the last file you touched. Before committing:

1. **List what the branch changed:**

   ```bash
   git diff --stat main...HEAD   # committed on this branch
   git status --short            # staged or modified now
   ```

2. **Map each changed path to the matrix above** and open the documents it names.
3. **Compare, do not trust memory:** read the module map against the tree
   (`git ls-files tools src`), the deployment page against `compose.yaml`, the ADR index against
   the decisions folder.
4. **Edit the documents in the same commit** as the code, then `poetry run sdd sync`.
5. **Let the machine confirm:** `poetry run sdd check` (pre-commit runs it too).

If nothing needed changing, say so in the commit message ("architecture and docs unchanged").

## Checklist before asking for G6

- [ ] Every row of the matrix that applies is done.
- [ ] ADRs exist for every decision made or reversed, linked from the index.
- [ ] Diagrams show every tool with its official logo; `sdd check` reports no `mermaid-logo` error.
- [ ] Docstrings for every new module, class and function.
- [ ] The root README is true; `poetry run sdd sync --check` is clean.
- [ ] The teaching guide is complete and matches the diff.
- [ ] `poetry run sdd verify <id>`: G5 passed and not stale.
