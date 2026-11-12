# Execution specification · 002 · Harness: item-by-item flow and CI
> **Phase 4 · Specify**, closed by **G4** (both approve spec, plan, tasks). Detail lives in the [backlog](backlog.md); rows link to it.
## Context collected
| Source | Where | What it contributed |
|---|---|---|
| RT42, RT38; PRD, backlog, approach; ADR-0003, 0004, 0015, 0018; `principles.md`, `security.md` | this folder, repo | blocking pipeline, per-card record, five cards, digest-bound gates, layers |
## Behaviour
| ID | Behaviour (EARS) | RT | Backlog criteria |
|---|---|---|---|
| SPEC-002-B01 | Where a dossier has no `teaching-guide.md`, the status table shall show `not yet`, so `sdd check` has no broken link. | RT42 | PBI-002-01 AC1-3 |
| SPEC-002-B02 | If a card is not approved for its current digest or an AC lacks a passing marked test, then `sdd item verify` shall refuse and list it; G5 passes when every card is `merged`. | RT38, RT42 | PBI-002-02 AC1-4 |
| SPEC-002-B03 | When `sdd item next` runs on a clean tree after a merged card, it shall branch from an updated `main`; otherwise it shall change nothing and exit non-zero. | RT38 | PBI-002-03 AC1-2 |
| SPEC-002-B04 | If the commit is not in `origin/main`, `item merged` shall refuse; the guard shall refuse governed changes on a card branch unless the card is approved and the spec fresh; the tool shall never run `branch -D`, `push --force` or `gh pr merge`. | RT38 | PBI-002-03 AC3-6 |
| SPEC-002-B05 | When a pull request opens into `main`, job `quality` shall run every `checks.yaml` command with read-only permissions, no secret and pinned actions, and fail if one fails. | RT42, RT36 | PBI-002-04 AC1-6 |
| SPEC-002-B06 | If `sdd new` has no rationale, it shall create nothing and exit 2; G0 shall fail for an empty one. | RT38 | PBI-002-05 AC1-3 |
## Architecture impact
| Component | Change | Layer | Why |
|---|---|---|---|
| `item_progress`, `card_digest`, `ApproveItem`, `VerifyItem`, `NextItem`, `MarkItemMerged`, `verify_quality` | added | domain, application | per-card flow |
| `yaml_progress_repository`, `git_cli_repository`, CLI group `item`, `.github/workflows/ci.yml` | added | infrastructure, interfaces, repository | adapters, commands, merge control |
| `evaluate_dossier`, status generator, `guard_commit`, `governance`, `create_dossier` | changed | application, domain | link, guard, `.github/`, rationale |
No new dependency (git CLI; GitHub-hosted runner). Layers are unchanged: see ADR-0023, ADR-0024.
## Contracts and data
| Contract | Shape | Producer | Consumers | Versioning |
|---|---|---|---|---|
| `progress.yaml` | per card: state, approvals + digest, branch, commit, PR, merge time | `sdd` only | `sdd`, people | `version: 1`; absent file keeps old rules |
| `sdd item *`, `sdd verify --no-record` | text on stdout; exit 0 ok, 1 refused, 2 usage | `sdd` | agent, CI | additive only |
## Design
| Pattern or principle | Where | Why |
|---|---|---|
| Ports and adapters (`ProgressRepository`, `GitRepository`, `AcStatusReader`) | application / infrastructure | git and YAML stay replaceable; domain stays pure (D, I); state machine `ItemState` forbids illegal transitions (S, O) |
## Security and threat model
| Threat (STRIDE) | Mitigation | Verified by |
|---|---|---|
| Tampering: edit `progress.yaml`, skip hooks, force-push | digest-bound approvals; CI; argument lists, forbidden commands | B02, B04, B05 tests |
| Elevation: workflow token or unpinned action | `contents: read`, no secret, SHA pins | B05 test |
## Validation plan
| Behaviour or RT | Level | Evidence |
|---|---|---|
| B01-B06 | unit, integration (temporary git repository with bare remote) | tests named in each backlog card |
| RT42 | manual, by us | deliberate error: red, merge blocked, fix, green (PBI-002-04 AC5, `validation.md`) |
## Architecture decisions
| ADR | Decision | Status | Refines or supersedes |
|---|---|---|---|
| 0023 item-by-item flow | one card, one branch, one approval | Proposed | ADR-0003, ADR-0015 |
| 0024 CI blocks merge | GitHub Actions job `quality` | Proposed | supersedes ADR-0004 |
## Documentation impact
AGENTS.md, lifecycle, gates, how-it-works, quality, security, deployment, README, skill `sdd-next-item`, teaching guide, then `sdd sync`.
## Out of scope
Merging and branch protection (a person); deployment, self-hosted runners; judging rationale quality.
