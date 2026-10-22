# Architecture

What exists today, how it is organised, and the shape of the platform it is meant to build. The
container-level view of what runs is in [deployment.md](deployment.md); every *why* is an ADR in
[decisions/](decisions/README.md).

## 1. The repository today: a harness, not yet a platform

Dossier 000 built the spec-driven development harness. No platform feature exists yet: each one
will arrive through its own dossier, starting from the requirements.

```mermaid
flowchart LR
    WE["👥 Mentor + mentee<br/>decide every human gate"]
    subgraph agents["Coding agents (tool-agnostic)"]
        CC["<img src='https://cdn.simpleicons.org/claude/D97757' width='28' height='28'/><br/>Claude Code"]
        CU["<img src='https://cdn.simpleicons.org/cursor/000000' width='28' height='28'/><br/>Cursor"]
        CX["<img src='https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/openai.svg' width='28' height='28'/><br/>Codex"]
        CP["<img src='https://cdn.simpleicons.org/githubcopilot/000000' width='28' height='28'/><br/>GitHub Copilot"]
        GE["<img src='https://cdn.simpleicons.org/googlegemini/8E75B2' width='28' height='28'/><br/>Gemini CLI"]
    end
    subgraph guides["Canonical guides"]
        AG["AGENTS.md<br/>constitution · lifecycle · gates"]
        SK["Agent Skills<br/>.agents/skills/"]
        RO["Roles + templates<br/>harness/"]
    end
    subgraph knowledge["Governed context"]
        RQ[("Requirements<br/>RT01-RT42 catalogue")]
        SP[("Dossiers<br/>specs/NNN-slug/")]
        AD[("ADRs + architecture<br/>docs/architecture/")]
    end
    subgraph sensors["Enforcement (local, ADR-0004)"]
        SDD["<img src='https://cdn.simpleicons.org/python/3776AB' width='28' height='28'/><br/>sdd CLI (Python, Typer)<br/>gates · approvals · verify · check · sync"]
        PC["<img src='https://cdn.simpleicons.org/precommit/FAB040' width='28' height='28'/><br/>pre-commit<br/>guard · ruff · mypy · pytest · sdd check"]
        HK["Agent guard<br/>PreToolUse hook"]
        GT["<img src='https://cdn.simpleicons.org/git/F05032' width='28' height='28'/><br/>Git<br/>branch spec/NNN-slug"]
    end
    subgraph runtime["Local runtime (ADR-0006)"]
        DC["<img src='https://cdn.simpleicons.org/docker/2496ED' width='28' height='28'/><br/>Docker Compose<br/>project orion"]
        MK["<img src='https://cdn.simpleicons.org/materialformkdocs/526CFE' width='28' height='28'/><br/>MkDocs site<br/>127.0.0.1:8000"]
    end
    PO["<img src='https://cdn.simpleicons.org/poetry/60A5FA' width='28' height='28'/><br/>Poetry<br/>one environment, groups dev · docs"]

    agents -->|read first| guides
    agents -->|read| knowledge
    agents -->|write artifacts, code| SP
    agents -->|run| SDD
    HK -.->|blocks approvals, bypasses, secrets| agents
    WE -->|sdd approve at a terminal| SDD
    SDD -->|evaluates and records evidence| SP
    SDD -->|validates citations| RQ
    PC -->|on every commit| GT
    PC --> SDD
    PO -->|runs| SDD
    PO -->|runs| PC
    DC --> MK
    MK -->|publishes| knowledge
```

- **Guides** are what agents read before acting; **sensors** check what they produced; **we**
  decide. The full mechanism is in [harness/how-it-works.md](../../harness/how-it-works.md).
- The `sdd` CLI is the only component with code. It reads and writes plain files (YAML and
  Markdown) and calls git; it has no server and no database.
- The documentation site is the only container today.

## 2. Module map of `tools/`

```mermaid
flowchart TB
    subgraph sdd["tools/sdd: clean architecture (ADR-0007)"]
        direction TB
        IF["interfaces/cli<br/>app.py (Typer commands) · presenters.py"]
        BO["bootstrap.py<br/>composition root"]
        subgraph infra["infrastructure: adapters"]
            I1["yaml_dossier_repository · dossier_mapper"]
            I2["yaml_reference_data<br/>catalogue · team · checks · logos"]
            I3["<img src='https://cdn.simpleicons.org/git/F05032' width='20' height='20'/><br/>git · git_workspace · file_document_store"]
            I4["subprocess_check_runner · terminal_confirmation<br/>file_template_library · system_clock"]
        end
        subgraph app["application"]
            UC["use_cases<br/>create · evaluate · approve · verify<br/>guard_commit · check_harness · lint_docs · sync_generated"]
            PT["ports (Protocols)<br/>dossiers · reference_data · environment · documents"]
            DR["doc_rules (strategies)<br/>diagram types · logos · links · ADRs"]
            GN["generators (strategies)<br/>status · traceability · adapters"]
            EV["evidence.py"]
        end
        subgraph dom["domain: pure, standard library only"]
            D1["gates · gate_status · dossier · approval"]
            D2["team · requirement · quality · governance"]
            D3["digest · readiness · findings · errors"]
        end
        IF --> BO --> infra --> app --> dom
    end
    AH["tools/agent_hooks/agent_guard.py<br/>standard library only, run by the hook"]
```

| Package | Responsibility | Depends on |
|---|---|---|
| `sdd.domain` | the lifecycle's concepts and rules: gates, states, approvals, digests, readiness, governance | standard library |
| `sdd.application` | use cases; ports; documentation rules and generators as strategies | `domain` |
| `sdd.infrastructure` | YAML, Markdown files, git, subprocesses, the terminal, the clock | `application`, `domain`, PyYAML |
| `sdd.bootstrap` | builds adapters and wires use cases | all of the above |
| `sdd.interfaces.cli` | the `sdd` commands (Typer); maps errors to exit codes | `bootstrap`, `application`, `domain` |
| `agent_hooks` | the PreToolUse guard for coding agents | standard library |

The class-by-class explanation, with every decision justified, is the
[teaching guide of dossier 000](../../specs/000-sdd-harness/teaching-guide.md).

## 3. What we keep from the reference platform

The industrial data platform we studied (Kairon) contributes its *high-level architecture*, not
its technology choices:

| Reference practice | Kept as |
|---|---|
| Many small packages, each in `domain / application / infrastructure / interfaces` with one `bootstrap.py` | [principles.md](../../harness/principles.md) §1, enforced by import-linter |
| A `harness/` folder of standing rules, pointed to by the agent file | `harness/`, `AGENTS.md` |
| An upkeep matrix and a review of the whole branch before each commit | [architecture-upkeep.md](../../harness/architecture-upkeep.md), skill `commit-review` |
| ADRs for every decision, numbered, never deleted | [decisions/](decisions/README.md) |
| The README as a product page; architecture with official logos under `docs/architecture/` | [documentation standard](../../harness/documentation-standard.md) |
| Services reach the database through views and routines, as roles with no table privilege | [security.md](../../harness/security.md) §3 |
| One Poetry project with a dependency group per component; one Dockerfile per image | ADR-0005, `docker/` |
| Kubernetes (kind + Helm) | **replaced by Docker Compose** (ADR-0006) |

## 4. Where the platform is heading (candidates, not decisions)

The requirements describe a data platform for industrial sources. The picture below groups them
into the usual building blocks with *candidate* technologies; every box becomes real only through
a feature dossier and an ADR, and any candidate can lose to an alternative there.

```mermaid
flowchart LR
    SRC["Industrial sources<br/>historian · maintenance · documents<br/>read-only (RT01)"]
    subgraph ingest["Ingestion (RT01-RT08)"]
        CON["Source contracts<br/>owner · fields · limits (RT02)"]
        EXT["<img src='https://cdn.simpleicons.org/python/3776AB' width='28' height='28'/><br/>Extractors (Python)<br/>checkpoints · retries · 3 timestamps"]
    end
    subgraph preserve["Preservation (RT20-RT27)"]
        RAW[("<img src='https://cdn.simpleicons.org/minio/C72E49' width='28' height='28'/><br/>Raw zone (MinIO candidate)<br/>immutable, integrity hash")]
    end
    subgraph model["Identity, model, quality (RT09-RT19)"]
        CAT[("<img src='https://cdn.simpleicons.org/postgresql/4169E1' width='28' height='28'/><br/>Catalog (PostgreSQL candidate)<br/>source+code identity · rules · audit")]
        PUB[("<img src='https://cdn.simpleicons.org/apacheparquet/50ABF1' width='28' height='28'/><br/>Published datasets (Parquet candidate)<br/>declared grain · versions")]
    end
    subgraph serve["Consumption (RT31-RT34)"]
        API["<img src='https://cdn.simpleicons.org/fastapi/009688' width='28' height='28'/><br/>Query API (FastAPI candidate)<br/>versioned OpenAPI contract"]
    end
    subgraph ops["Operations (RT35-RT42)"]
        OBS["<img src='https://cdn.simpleicons.org/opentelemetry/425CC7' width='28' height='28'/><br/>OpenTelemetry (candidate)<br/>loads · delays · failures"]
    end
    SRC --> CON --> EXT --> RAW --> CAT
    RAW --> PUB
    CAT --> PUB --> API
    EXT -.-> OBS
    API -.-> OBS
```

The order of the first dossiers should follow the catalogue's priorities: access (RT01),
identity (RT09), time (RT12), reconstruction (RT20-RT25), scale (RT28-RT29), value (RT34) and
load observability (RT39).
