# Templates

One template per lifecycle artifact. The harness copies each one into the dossier
`specs/<id>-<slug>/` at the moment its phase can start, not before: `poetry run sdd new` copies
the PRD, and every approval that turns a gate *passed* copies the templates of the next gate
([ADR-0018](../../docs/architecture/decisions/0018-artifacts-are-created-as-gates-pass.md)). It
replaces `{{title}}`, `{{id}}`, `{{branch}}`, `{{requirements}}` and `{{requirements_table}}`
with what is already known, and never overwrites a file that exists.

Two conventions make the templates the *definition of ready* for each gate:

- **Every `##` heading is a required section.** An artifact can only be approved when it keeps
  all of them (a heading ending in "(optional)" is not required). Add a heading here and it
  becomes required in every future approval: no code change needed.
- **`TODO(sdd)` marks text the author must replace.** `sdd approve` refuses while one remains.

| Template | Phase | Gate | Created when | What it captures |
|---|---|---|---|---|
| [prd.md](prd.md) | 1 Discover | G1 | `sdd new` | the need, goals and metrics, scope, the requirements digest |
| [backlog.md](backlog.md) | 2 Plan | G2 | G1 passes | epics, features, self-contained work items with EARS acceptance criteria |
| [ux-approach.md](ux-approach.md) | 3 Structure | G3 | G2 passes | how people or systems meet the result; prototype or not |
| [spec.md](spec.md) | 4 Specify | G4 | G3 passes | behaviour, architecture impact, contracts, design, threats, validation plan, as tables |
| [plan.md](plan.md) | 4 Specify | G4 | G3 passes | how the build proceeds, files, rollback |
| [tasks.md](tasks.md) | 4 Specify | G4 | G3 passes | the ordered task list and loop limits |
| [validation.md](validation.md) | 5-6 Build, Validate | G6 | G4 passes | G5 result, reviews, functional validation, build log |
| [teaching-guide.md](teaching-guide.md) | 5-6 Build, Validate | G6 | G4 passes | every decision explained for the mentee |
| [release.md](release.md) | 7 Release & Learn | G7 | G6 passes | what was released, results against goals, learnings |
| [adr.md](adr.md) | any | — | by hand | an Architecture Decision Record (copied by hand into `docs/architecture/decisions/`) |

The phases and gates are explained in [../lifecycle.md](../lifecycle.md) and
[../gates.md](../gates.md).
