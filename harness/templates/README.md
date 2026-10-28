# Templates

One template per lifecycle artifact. `poetry run sdd new` copies them into a new dossier
`specs/<id>-<slug>/`, replacing `{{title}}`, `{{id}}`, `{{branch}}`, `{{requirements}}` and
`{{requirements_table}}` with what is already known.

Two conventions make the templates the *definition of ready* for each gate:

- **Every `##` heading is a required section.** An artifact can only be approved when it keeps
  all of them (a heading ending in "(optional)" is not required). Add a heading here and it
  becomes required in every future approval: no code change needed.
- **`TODO(sdd)` marks text the author must replace.** `sdd approve` refuses while one remains.

| Template | Phase | Gate | What it captures |
|---|---|---|---|
| [prd.md](prd.md) | 1 Discover | G1 | the need, goals and metrics, scope, the requirements digest |
| [backlog.md](backlog.md) | 2 Plan | G2 | epics, features, work items with EARS acceptance criteria |
| [ux-approach.md](ux-approach.md) | 3 Structure | G3 | how people or systems meet the result; prototype or not |
| [spec.md](spec.md) | 4 Specify | G4 | behaviour, architecture impact, contracts, design, threats, validation plan |
| [plan.md](plan.md) | 4 Specify | G4 | how the build proceeds, files, rollback |
| [tasks.md](tasks.md) | 4 Specify | G4 | the ordered task list and loop limits |
| [validation.md](validation.md) | 5-6 Build, Validate | G6 | G5 result, reviews, functional validation, build log |
| [teaching-guide.md](teaching-guide.md) | 5-6 Build, Validate | G6 | every decision explained for the mentee |
| [release.md](release.md) | 7 Release & Learn | G7 | what was released, results against goals, learnings |
| [adr.md](adr.md) | any | — | an Architecture Decision Record (copied by hand into `docs/architecture/decisions/`) |

The phases and gates are explained in [../lifecycle.md](../lifecycle.md) and
[../gates.md](../gates.md).
