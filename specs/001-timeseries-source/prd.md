# PRD · 001 · Time-series source: global plant data generator

> **Phase 1 · Discover**, closed by **G1 · PRD validated** (both of us approve).
> Dossier `specs/001-timeseries-source/` · branch `spec/001-timeseries-source` · kind **feature** · created 2026-11-04.
> How to fill this file: [lifecycle, phase 1](../../harness/lifecycle.md#phase-1-discover).

## Requirements digest

The technical requirements this work serves, read from `docs/requirements/` (gate G0 checks that
every RT cited here exists):

| RT | Phase | What must hold | How we verify it |
|---|---|---|---|
| RT02 | P | Each source shall have an integration contract with an owner, interface, fields, identifier, time reference, extraction limits, frequency and available history. | Check the contract against examples from the source before enabling the load. |
| RT07 | P | When available, the occurrence time, the update time at the source and the reception time shall be stored separately. | Receive today an old record that was corrected; verify the three timestamps. |
| RT09 | P | Original identifiers shall be stored with their source; the combination source + code shall never point to two pieces of equipment at the same time. | Try to insert a conflicting mapping and verify that it is rejected. |
| RT12 | P | Interpretable timestamps shall be standardised in UTC, preserving the original representation and time zone/offset when known; ambiguities shall be flagged. | Test two time zones and one record with an ambiguous time. |
| RT17 | P | Completeness shall only be computed when the expected frequency or quantity is defined. | Do not apply the same denominator to a periodic tag and to a report-by-exception tag. |
| RT23 | P | Late data shall be placed in its occurrence period and identify the derived results that must be updated. | Simulate a six-hour interruption, recover the period and check the aggregates. |
| RT28 | P | Sizing shall declare tags, frequencies, average size, history, concurrency and growth, separating measurement from projection. | A capacity spreadsheet with traceable inputs and a matching test. |
| RT29 | P | The prototype shall measure sustained throughput, load duration, delay between availability and publication, and resources used. | A trial on the chosen slice with the distribution and the p95, not only the mean. |
| RT38 | P | Changes to mappings, rules, permissions and manual reprocessing shall record actor, time, reason and before/after when applicable. | Make a change and reconstruct it from the audit log. |
| RT39 | P | Each load shall expose its run, state, times, volumes, period covered and cause of error. | Simulate an unexpectedly empty load, a failure and a partial success. |
| RT40 | P | Operations shall track delay, backlog, failures, pending identity issues, quality and duration per source. | Cause an interruption and locate the source, period and step. |
| RT42 | P | Changes to integrations and rules shall pass automated validation of contracts, exceptions and regression before publication. | Introduce an incompatibility, observe a controlled failure, then fix it. |

**What this means in plain words.** The platform cannot prove it handles identity, time, late
data and scale until something produces data that behaves like a global, imperfect industrial
historian. This work is that producer: a **continuous stream source** for the platform's
time-series requirements. It does not deliver the platform's own handling of those requirements
(that is the job of the ingestion and quality features that come next), but it makes each of them
testable: RT09 through tags that repeat across sites, RT12 and RT07 through plants in different
time zones, RT17 through periodic and report-by-exception tags, RT23 through interruptions and
late bursts, RT28 and RT29 through a configurable, measurable load. RT02 is served by a written
contract per site. Governance, lineage and observability of the generator itself apply three
requirements to our own runs: RT38 (a change to the plant configuration, the fault rules or the
naming convention records who, when, why and before/after), RT39 (each run exposes its id, state,
times, volumes, period covered and cause of error) and RT40 (delay, backlog, failures and
duration per site are tracked, so an interruption can be located by site, period and step). The
"pending identity issues" part of RT40 does not apply: the source has no identity mapping to
resolve. RT42 applies to the changes we make to the generator and its rules: a continuous
integration pipeline runs every automated check on each pull request, and the merge into `main`
is blocked unless it passes (we introduce a failing change on purpose, see it blocked, then fix
it). The same dossier also changes how a large backlog is built: one item at a time, each on its
own branch, approved on its own and merged by a person before the next one is refined, so that
what we learn from one item shapes the next.

**Related RTs left out, and why.**
- RT08 (the ingestion mechanism supports batch, continuous arrival or trigger): it is about the
  ingestion mechanism, not the source. This source is a stream and nothing else, so it does not
  demonstrate any batch pattern; the demonstration belongs to the ingestion feature.
- RT10 (unknown tags stay pending), RT13 (original value, unit and quality kept), RT14 (quality
  rules), RT18 (observed versus estimated) and RT22 (correction precedence) are about how the
  platform *treats* the data. The generator produces the situations they need (unknown or renamed
  tags, units that change, bad quality, interpolated points, corrected lab results) but we do not
  cite them, because we only deliver the producer.
- RT03 to RT06 and RT20 to RT25 (except RT23) belong to ingestion and storage. RT30 is touched
  only to say what we do not claim: a scale test here does not prove industrial capacity (the PDF
  is explicit about this).

**RTs this work must not break.** RT01 (read-only: consumers of this source can only read, and
nothing in it can command a system) and RT36 (no credentials in code, compose files or output).

## Problem

Orion Chemicals is the fictional company this repository builds a data platform for; its plants
in several countries are simulated, like everything else here. The team that builds the platform
(the mentor and the mentee) has no plant to connect to, and a platform tested on tidy toy data
fails on the first realistic file. The questions the team cannot answer today are concrete: how
does the platform behave when the same tag name (`TIC-101`) exists at three sites for three
different pieces of equipment? When a US Gulf Coast server stores local time without an offset
and the clocks change at night? When a sensor freezes, a value is missing, or the link to a plant
drops for six hours and then returns a burst of old data? How many tags and how much data per day
can it carry, and how late does it get?

A second need sits behind the first. The company wants, later, a machine learning model that
looks at tag names, descriptors, units and the behaviour of the signals, and works out the plant
structure on its own: which equipment and which measurement each tag belongs to, and how the
pieces of equipment relate. Such a model needs examples where the answer is known: many tags that
follow the company's naming convention to learn from, and many that do not, with the true answer
(and the true plant structure) kept aside to measure how well the model does. Nobody can label
that by hand, and the structure must not be visible to the model in the data it is given.

Without a realistic, labelled source, every later feature is tested on toy data and the
contextualisation model has nothing to learn from or be measured on.

## Goals and success metrics

Targets marked *proposed* are our starting point; the measured values (RT28, RT29) replace them
once we have run the generator, and we agree on the final targets then.

| Goal | Metric | Baseline today | Target | How we measure |
|---|---|---|---|---|
| A realistic plant and catalogue that hides its own structure and still allows training a model later | tags in the default catalogue over 5 sites; tags with a complete answer key (asset, equipment, loop, measurement, unit, canonical name, conformity tier, violation types); convention-following tags; plant structure visible outside `truth/` | none | at least 1,000 tags (planned about 2,050; larger sizes only as a projection, never generated); answer key for 100% of tags; the mix stays realistic (most tags conform, a sizeable minority do not); floors, not targets: 1,000 convention-following tags, 10 per equipment class, 20 examples of each violation type; **zero** plant-structure fields outside `truth/` | `catalog/` content; test that counts tags per site, scan class, tier, equipment class and violation type; test that fails if any field of `truth/` appears in the catalogue, stream, lab or archive files; sizing spreadsheet separating the measured default plant from the projection (RT28) |
| Realistic, reproducible data problems | injected faults (signal, acquisition, tag and metadata, timestamp problems) that appear in the truth labels; identical results for the same seed; events per second per 1,000 tags after the exception filter | no source | 100% of injected faults labelled with type, tag, start and end; two runs with the same seed and period produce identical stream and truth files; between 5 and 50 events/s per 1,000 tags (about 11 to 103 events/s for 2,050 tags), the band the commercial references below show | test comparing file digests of two runs; test that every fault class of the specification occurs at least once in a 30-day backfill; RT29 trial script: rate per scan class and in total, in a 24-hour real-time run |
| Throughput and delay that never limit the platform's tests | events per second written in backfill (sustained, with the distribution and p95, not the mean); delay between the event time and the record being readable in the output folder (p50, p95) in real time; CPU and memory of the container | none | at least 25,000 events/s sustained in backfill, the rate a commercial collector was tested at (150,000 events/s is a stretch we measure and report, not promise); *proposed*: p95 delay under 5 seconds, our own figure because no commercial reference exists for it | RT29 trial script writing a report with the distribution and resources |
| Governed, traceable and observable runs (RT38, RT39, RT40) | share of output files that carry a run id and the synthetic marker; archive records that can be traced to the stream events they came from and to the run (seed, configuration digest, versions); configuration changes that can be reconstructed with actor, time, reason and before/after; what the run report shows for an empty run, a failed run, a partial run and an injected six-hour interruption | none | 100% of files; 100% of archive records; 100% of configuration changes; each of the four run outcomes is reported with its state, times, volumes, period and cause, and the interruption is located by site, period and step | tests over a short run and over runs that are empty, failed, partial and interrupted; a trace test that picks an archive record and walks back to the run; a test that changes a rule and reconstructs the change from the audit log |

**Where the delivery targets come from.** There is no vendor benchmark that fits our case, so we
anchor on the figures that exist and say how strong each is; we re-check them in the
specification. An AVEVA sizing note gives about [50 events/s per 1,000 tags for an average
customer, and an example of 160,678 tags at 848 to 1,339 events/s](https://docs.aveva.com/bundle/pi-cloud-connect/page/performance-and-throughput.html)
(that example is about 5 to 8 events/s per 1,000 tags, which gives the lower end of our band).
That page also says one PI Cloud Connect node sustains about 8,000 events/s. A [GE Vernova
collector for PI is documented as tested up to 25,000 events/s](https://gevernova.com/software/documentation/historian/version71/c_configuring_osi_data_archive.html),
which is our floor for backfill. A reseller page quotes [AVEVA Historian at 150,000 values/s
sustained, with bursts of 3 million](https://becolve.com/en/productos-industria/aveva-historian-historian-client-web/),
which is the weakest source (not AVEVA's own), so it is a stretch only. Open-source time-series
database benchmarks run by their vendors (hundreds of thousands to millions of rows per second)
use computer-monitoring data, not industrial data, so we do not use them as targets.

## Users and scenarios

- **Data engineer (the mentee, then the team), building ingestion.** Points an extraction job at
  the output folder and has to deal with five sites that represent time differently, tags that
  collide across sites, bursts after outages and files that arrive late. The scenario that
  matters: start the generator with a seed, let it run, interrupt the link for six hours at one
  site, resume, and check that the recovered period lands in the right place (RT23).
- **Data scientist, training the contextualisation model.** Trains on the convention-following
  tags using their answer key, then asks the model to explain the tags that do not follow it and
  to rebuild the plant structure (equipment, loops, areas) from names, descriptors, units and the
  behaviour of the signals alone, and scores the result against the answer key kept under
  `truth/`. The generator must never put the structure or the answer in the stream or in the
  catalogue it exposes; the only way to see relations is through the data (for example two signals
  that move together).
- **Reliability or platform engineer, testing quality and scale.** Needs frozen sensors, drifts,
  spikes, bad quality and saturation at known moments, to check whether a quality rule detects
  them (and which it confuses with a real process change), and to run a throughput trial.
  The mentor uses the same data to demonstrate, in sessions with the mentee, why each rule exists.
- **Data steward and operator of the generator (the mentor).** Needs to know which run produced
  a file, with which seed, configuration and versions of the generator, the plant model and the
  naming convention; to see whether a run is healthy while it runs; and to be sure that nobody
  mistakes the files for real industrial data.

## Scope

### In scope

- A **generator service** (code, tests, documentation, a Docker Compose service) that produces,
  for the five sites of the fictional company (Brazil, US Gulf Coast, Belgium, China, India) in
  different time zones, a continuous time-series stream and irregular laboratory results, writes
  them to a local folder, and runs in real time or faster than real time (the same stream, written
  ahead of the clock, which also serves to produce a past period).
- A **plant model kept internal**: sites, areas, equipment and instruments, from which a
  catalogue of at least 1,000 tags is derived, with scan classes from 1 second to 15 minutes and
  report-by-exception tags (RT17, RT28). The model is the answer key: it is written only under
  `truth/`, and what consumers receive are tags, descriptors, units, values, quality and
  timestamps, never the structure.
- A **realistic catalogue**: tags that follow the company's naming convention, tags that follow a
  local site dialect, and ad hoc tags that follow nothing, with messy metadata (descriptors in
  English and Portuguese, units spelt in several ways, empty fields, the same name at several
  sites, renamed tags) (RT09).
- **Signal behaviour and problems**: realistic process behaviour (setpoint and grade changes,
  trips, slow degradation), signal problems (noise, spikes, drift, bias, steps, trends,
  saturation, oscillation) and acquisition problems (missing data, frozen sensors, bad quality,
  late and out-of-order data after interruptions, duplicates).
- **A PI-like acquisition pipeline**: exception filtering, a snapshot, compression into an
  archive, and store-and-forward after outages, so that the output has the shape of what a
  historian really holds (RT23).
- **Time realism**: sites with different zones, daylight saving rules, misconfigured clocks,
  several timestamp representations, and three timestamps per event (RT07, RT12).
- **Governance**: a source contract per site (RT02) that does not reveal the plant structure; the
  naming convention and the contract as versioned documents with an owner and a change process;
  every file marked synthetic; the settings of each run recorded; an audit log of changes to the
  plant configuration, the fault rules and the convention, with actor, time, reason and
  before/after (RT38).
- **Lineage**: a manifest per run (run id, generator version, seed, configuration digest, plant
  model and convention versions, mode, period, outcome); a run id and source event ids in every
  record, so an archive record walks back to the stream events and the run, and every truth label
  points to the events it describes.
- **Observability**: metrics (events per second per site and scan class, scheduler lag, queue
  depth, write latency, backlog after an interruption, dropped events, faults injected), logs that
  carry the run id, a health signal for the container, and a run report at the end that exposes
  the run, its state, times, volumes, period covered and cause of error (RT39), and the delay,
  backlog, failures and duration per site (RT40).
- A **sizing and measurement report** (RT28, RT29).
- A **documented tag naming convention** and the answer key that follows it.
- **Four harness changes** carried by this dossier, built only after G4 because they touch
  governed code:
  - the generated status table links a teaching guide only when the file exists, so that
    `sdd check` passes for a new dossier;
  - `sdd new` asks for the rationale of every dossier and G0 refuses an empty one (today only
    enablers and work outside the catalogue need it, which let this dossier start without one);
  - an **item-by-item build flow**: each backlog item is refined with the context of the earlier
    ones, approved on its own, built on its own branch from an up-to-date `main` until all its
    acceptance criteria are met, committed, pushed and offered as a pull request; the agent then
    waits for a person to merge it, syncs with `main`, deletes the other local branches and
    starts the next item. The backlog approval (G2) is therefore partial: the skeleton and the
    first item;
  - a **continuous integration pipeline** (GitHub Actions) that runs every quality check on each
    pull request, and, with the branch protection settings applied by a person, blocks the merge
    unless it passes (RT42).

### Out of scope

- Any connection to a real historian or industrial system, and any real data of any company:
  none exists in this repository.
- A physical process simulator. Signals come from statistical and behavioural models, not from
  mass and energy balances.
- Consuming the data: extraction, ingestion, storage, quality rules, queries, the platform's
  catalogue. Each is a later feature. Batch interfaces too: this source only streams.
- Kafka or any message broker; an HTTP read API. The output is a local folder for now.
- The machine learning model itself; this work provides its data and its answer key only.
- Proving industrial-scale capacity (RT30): scale tests here show the generator's limits, not
  the platform's.
- Generating more tags than the default plant (the 15,000-tag scenario of the requirements PDF,
  process sharding): cut first, by our decision. The sizing report projects that scale on paper
  and labels it a projection (RT28).

## Constraints and assumptions

- Local only for the generator: it runs with Docker Compose, with no cloud and no hosted service
  for running it or holding its data (decision). The one hosted service is GitHub, which stores
  the repository and runs the checks of the pipeline (decision, 2026-11-04); it never runs the
  generator and never receives its data. Python through Poetry only; everything in English
  except the deliberately Portuguese descriptors in the data (decisions).
- The generator holds no credentials and cannot change any system (RT01, RT36): it only writes
  files in a mounted folder, and its container follows the hardening baseline in `compose.yaml`.
- Decision (mentor, 2026-11-04): Orion Chemicals, its five sites and all of their data are
  fictional. The sites are chosen because their time rules differ; the zones and daylight saving
  rules are real-world rules applied to invented plants. Every tag, value, name and fault is
  invented.
- Decision (mentor, 2026-11-04): the plant model is hidden. A later model will try to rebuild it
  from the data, so it exists only in `truth/`.
- Decision (mentor, 2026-11-04): the four harness changes above are part of this dossier, not a
  separate one.
- Decision (mentor, 2026-11-04): the backlog is approved one item at a time. G2 is a partial
  approval; only the first item is reviewed in full, the others are outlines that are refined and
  approved before each is built.
- Context: this is the first real use of the harness, and dossier 000 still waits for its last gate
  (G7). What was clear, heavy or missing while working on this dossier is recorded as we go, and
  feeds the `release.md` of dossier 000.
- Assumption: the daylight saving rules we reproduce (for example Brazil ending daylight saving
  time in 2019, different dates in the US and the EU, a UTC+5:30 offset in India) are checked
  against the time zone database during the specification.
- Assumption: the TEP-style units are inspiration for structure and signal organisation only;
  no TEP data is loaded or replayed. The equipment instrument sets come from public engineering
  practice and are verified in the specification.
- Assumption: a local disk holds the generated data. A month of the default plant must fit in a
  size we declare in the sizing report (RT28).
- Constraint: tag counts and scan classes per site are our estimates, to be replaced by the
  measured values after the first trial.

## Risks and open questions

| Risk or question | Impact | Mitigation or owner |
|---|---|---|
| Synthetic data is too regular, so a model that learns our generator's rules looks better than it would on tags from a real plant | a future model's score is optimistic: it shows the method works, not that it generalises beyond this simulation | randomise dialects per site, keep whole sites as a hold-out set, add ad hoc tags with no pattern; we accept that everything here is simulated, so a check on real industrial data is outside this project (owner: mentor) |
| The hidden structure leaks: through metadata, file layout, the contract, or through a signal that copies another exactly | the model is scored on what it was given, not what it inferred | the leak test of the first goal; relations appear only as realistic statistical behaviour, never as a copy; a review of every field of the contract (owner: mentee) |
| The data is too clean or too messy to be useful | tests that pass trivially, or tests nobody can interpret | fault and conformity rates configurable, defaults agreed with us at the review of the specification (owner: mentor) |
| Python cannot sustain the event rate | the generator limits the tests instead of the platform | vectorised generation, one scheduler per site; measure early with the RT29 trial and record the limit (owner: mentee) |
| The commercial references are weak: vendor sizing notes, a collector test and a reseller claim, none measured on our workload | a target that is too easy or impossible | re-check each source in the specification, state its strength in the sizing report, and revisit the targets after the first measured trial (owner: mentor) |
| Open question: what delivery delay is acceptable? No commercial figure exists, so 5 seconds is ours | wrong target accepted | agree the final value after the first measured trial (owner: mentor) |
| Daylight saving and zone rules reproduced wrongly | the platform is tested against a false reality | take rules from the time zone database, test the gap and overlap hours of each rule (owner: mentee) |
| Generated data grows without limit on the local disk | the machine fills up | rotation by date, a declared size per simulated day, a retention setting (owner: mentee) |
| Generated files could be mistaken for data from a real plant | a decision taken on invented data | every file states that it is synthetic; the catalogue carries a generator marker in its metadata (owner: mentor) |
| The pipeline exists but the GitHub branch protection is not applied, so a merge is not really blocked | RT42 is claimed but not true | the pipeline card ends with a checklist of the settings; we apply them and prove them with a deliberately failing change (owner: mentor) |
| Refining an item after earlier ones are built shows that the approved specification (G4) is wrong or incomplete | the specification must change, on purpose: editing it makes G4 stale, and no code is written until it is refined and approved again (by our rule, 2026-11-05) | the build of that item stops until we re-approve; the cost is a review, not rework of wrong code | the agent stops, proposes the change to the specification in the chat, edits `spec.md`, `plan.md` or `tasks.md` (which makes G4 stale), and waits for our new approvals; a change of approach or of order goes back to G3 or G2 the same way (owner: mentee) |

## Review notes (optional)

_Nothing needed to approve. The approval itself records who approved which exact text and when.
Add a line here (or use `--note` when approving) only for a decision worth remembering, such as
a risk we accept or a change we asked for._
