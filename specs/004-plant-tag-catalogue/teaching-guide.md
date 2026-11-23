# Teaching guide · 004 · Plant and tag catalogue

## 1. The problem in plain words

A fixture is generated data used to exercise software under known conditions. This card makes a
fixture for five fictional industrial sites. Each site contains areas, such as numbered production
sections. Equipment holds instruments, meaning individual points that can report a measurement
or status. A periodic point arrives on a schedule. A laboratory point comes from a sample, and a
report-by-exception point reports when a condition changes.

The private plant records how those points relate to each other. This lets an evaluator count what
the generator created and use the relationships as a reference for later catalogue work.

## 2. Requirements served

RT17 needs sampling expectations. Periodic points declare their interval and the other policies
carry a null interval (B03, AC5). RT28 needs credible source sizing inputs. The generator counts
points by site and scan class so a planner can measure the fixture composition (B01, AC1).
Repeatable IDs and a private plant establish the reference that later cards use for RT09.
See the [traceability matrix](../../docs/requirements/traceability.md).

## 3. Architecture before and after

```mermaid
flowchart LR
    subgraph "Before"
        OldCommand["Source CLI"] --> Existing["Benchmark and civil-time operations"]
    end
    subgraph "After"
        Command["Source CLI"] --> ExistingUseCases["Benchmark and civil-time operations"]
        Command --> Build["BuildPlant"]
        Build --> Builder["PlantBuilder"]
        Build --> Port["PlantWriter"]
        Adapter["PlantJsonWriter"] -. implements .-> Port
        Adapter --> File["truth/plant.json"]
    end
```

The CLI now calls the plant use case for the new command. The use case builds the model then
passes it to the writer port. Bootstrap injects the adapter, which writes one private file.

## 4. Decisions and the alternatives that lost

[ADR-0031](../../docs/architecture/decisions/0031-separate-the-consumer-catalogue-from-plant-truth.md)
sets the sharing boundary. The evaluator keeps topology and the reference. Subsequent cards
use a separate dataset for consumers. The implementation plan records how the plant is encoded.

| Choice | Benefit | Cost |
|---|---|---|
| Private, versioned plant file | The evaluator can inspect and reproduce the reference independently | The operator must keep the output directory private |
| Topology carried with consumer records | Consumers would have more context in one dataset | Consumers would also receive the relationships that the exercise asks them to infer |
| Seeded digest over structural segments | IDs reproduce independently of process or write order | Changing a structural path changes that entity's ID |

## 5. The design: layers, classes and patterns

```mermaid
classDiagram
    BuildPlant --> PlantBuilder
    BuildPlant --> PlantWriter
    PlantJsonWriter ..|> PlantWriter
    PlantBuilder --> Plant
    Plant *-- Site
    Plant *-- Area
    Plant *-- Equipment
    Plant *-- Instrument
    Plant *-- ControlLoop
    Plant *-- Stream
    Plant *-- Driver
    Plant *-- InventoryCount
```

| Unit | Responsibility |
|---|---|
| Plant and its frozen records | Carry ordered entities with IDs, policy and counts |
| SiteProfile and EquipmentTemplate | Declare the fixture shape and repeatable equipment measurements |
| PlantBuilder | Bind template points to units, attach IDs and resolve relationships |
| BuildPlant | Ask the builder for the plant and publish it through the writer port |
| PlantWriter | Specify the return path and error contract for a complete write |
| PlantJsonWriter | Encode JSON, enforce the file rules and replace the destination |

| Principle | Application |
|---|---|
| Single responsibility | The writer knows output paths. The builder knows relationships and scan rules. |
| Open/closed | Profile and template values determine the inventory without branching on every equipment class. |
| Liskov substitution | Any writer honoring the path and handled-error contract can serve the use case. |
| Interface segregation | The port exposes one write operation. |
| Dependency inversion | Application owns the port and bootstrap supplies its implementation. |

## 6. How it behaves at runtime

Follow the [publication sequence](../../docs/architecture/README.md#32-private-plant-inventory).
The command validates the seed and resolves the destination before invoking the use case. The
builder materializes the ordered plant in memory. The writer stages the document in the same
directory as the target, closes it and replaces the target. Only then does the CLI print the
path. If replacement fails, the writer removes the staging file and the command reports failure.

## 7. Data and contracts

See the [entity relationships](../../docs/architecture/README.md#32-private-plant-inventory)
and the [versioned JSON contract](../../src/tssource/README.md#private-plant-fixture). The builder
binds each equipment ID to an area and each point ID to equipment. The relationship check
resolves loop roles, flows and drivers by ID. The inventory counts emitted instruments. Scan
class determines the interval, including null for lab and exception classes.

## 8. Code tour

1. [Bootstrap](../../src/tssource/bootstrap.py) returns
   `BuildPlant(PlantBuilder(), PlantJsonWriter())`.
2. [CLI](../../src/tssource/interfaces/cli/app.py) uses `seed` when supplied and reads settings
   for defaults. It translates writer errors into stderr and exit 1.
3. [Use case](../../src/tssource/application/plant.py) composes one operation,
   `self._writer.write(self._builder.build(seed), output_folder)`.
4. [Profiles](../../src/tssource/domain/plant/profiles.py) set units per area and share control
   points across classes. Analyser houses carry five lab points each.
5. [Builder](../../src/tssource/domain/plant/builder.py) hashes version, seed, kind, site and path.
   Each element is a separate JSON value, so one segment cannot join accidentally with the next.
6. [Writer](../../src/tssource/infrastructure/plant_json.py) uses `staged.replace(target)`
   to publish the versioned document in a single filesystem operation.

## 9. Security

There are no credentials in the fixture. Keep the destination and its parents under operator
control. The writer rejects symlink redirection at the two fixed output components and uses
mode `0600` for the staged file. Generation is bounded by the declared profiles. The command
uses existing dependencies, and the writer uses the standard library.

## 10. How we tested it

The [domain tests](../../tests/tssource/domain/test_plant_builder.py) count instruments directly,
resolve references and compare ordered models over fixed seeds (AC1–AC5, RT17 and RT28).
The [CLI tests](../../tests/tssource/test_plant_cli.py) compare bytes, check the output footprint
and mode, reject invalid input and symlinks, and inject a failed replacement (AC2 and AC6, RT28).

## 11. Run it yourself

```bash
poetry run tssource plant build --seed 42 --out data/ts_source/seed-42
poetry run tssource plant build --seed 101 --out data/ts_source/seed-101
poetry run pytest --no-cov -q tests/tssource/domain/test_plant_builder.py tests/tssource/test_plant_cli.py
```

Inspect `inventory` in both files. Their counts match. Corresponding equipment and instrument
IDs differ. Rerun either command with its original seed and compare the file bytes.

## 12. Pitfalls and what we would do differently

Changing display codes and changing structural identity are different operations. Preserve the
structural segments if an ID should remain stable. Keep the same seed and fixture version when
comparing output between runs. The fixture uses a fixed layout and its inventory is an input to
sizing, separate from measured ingestion capacity.

## 13. Questions for the mentee

1. Why include entity kind and site in the ID input?
2. Which code would you change to add a new lab analyte?
3. How would treating lab points as periodic distort expected event counts?
4. Why is staging done in the destination directory?
5. If replacing the file fails, how do the CLI and filesystem tell the operator what happened?
6. Which relationships would give away answers in a tag-matching exercise?

## 14. Glossary

| Term | Meaning |
|---|---|
| Control loop | A measurement, controller and final element associated to regulate a process |
| Driver | A shared influence on equipment in an area |
| Fixture | Repeatable generated input for a test or exercise |
| Scan class | A point's sampling policy |
| Stream | A directed material flow between pieces of equipment |
| Surrogate ID | An identifier derived independently of display names |
