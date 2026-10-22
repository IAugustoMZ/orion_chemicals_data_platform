# Requirements

**Start every piece of work here** (Constitution, article I). The technical requirements of the
Orion Chemicals case are the fixed point everything else is measured against.

| File | What it is |
|---|---|
| [Requisitos_Tecnicos_Orion_Chemicals.pdf](Requisitos_Tecnicos_Orion_Chemicals.pdf) | the source document (Portuguese): catalogue RT01-RT42, derived from RQ01-RQ25 and the Business Case Canvas, 28 September 2026 |
| [rt-catalog.yaml](rt-catalog.yaml) | the same 42 requirements, machine-readable, with an English translation next to the original text (ADR-0011) |
| [traceability.md](traceability.md) | generated: every RT, the dossiers that cite it and how far it got |

`poetry run sdd rt` prints them; `poetry run sdd rt RT09 RT12` prints a few.

## How to read a requirement

Each RT is a **verifiable property**, not a solution. It has:

- a **statement**: what must hold;
- a **way to verify it** ("forma de verificar"): the test or demonstration that proves it, which
  becomes a test in the dossier's validation plan;
- a **phase**: **P** for the prototype, **A** for the later operational expansion;
- the **business requirements (RQs)** it derives from.

The PDF is explicit that the choice of product, database or orchestrator remains an
architecture decision: requirements never name a technology, ADRs do.

## The five groups

| Group | RTs | In one sentence |
|---|---|---|
| 01 · Integration and ingestion | RT01-RT08 | read-only access with a contract per source; loads that record what was asked and received, resume safely, retry with limits and keep three timestamps |
| 02 · Identity, model and quality | RT09-RT19 | original identifiers with their source, no presumed associations, declared grain, UTC with the original preserved, versioned quality rules, schema evolution, the same rules for every consumer |
| 03 · Preservation, corrections and reprocessing | RT20-RT27 | raw input kept apart from results, idempotent reprocessing, documented correction precedence, late data in its period, recorded reprocessing, validated publication, retention |
| 04 · Capacity, consumption and value | RT28-RT34 | sizing that separates measurement from projection, measured throughput and delay (p95), bounded queries, versioned contracts, ML datasets without leakage, measured investigation time |
| 05 · Security, operations and delivery | RT35-RT42 | least privilege, no credentials in code, protection by classification, audit of every change, observable loads and sources, tested backups, automated contract and regression validation |

## What to tackle first

The catalogue asks to prioritise **RT01, RT09, RT12, RT20-RT25, RT28-RT29, RT34 and RT39** to
discover the access, identity, time, reconstruction, scale and value risks early. They are marked
★ in the [traceability matrix](traceability.md).

## Context that is not a requirement yet

From the PDF, to keep in mind when specifying:

- End-to-end latency, query times, concurrency, recovery, retention and budget are **still to be
  agreed** after the sources and the users' decisions are inventoried. "A batch every five
  minutes" is a hypothesis, not an availability SLA.
- Scale: 15,000 tags at 1 Hz would mean 1.296 billion observations a day (about 233 billion over
  180 days). That is an illustrative scenario, not a confirmed volume. The proposed slice of
  **100 pieces of equipment and 500 tags** needs actually measured frequencies.
- Next review: define for each RT an owner, its dependencies, an executable test and a target
  value where limits are missing.
