"""The gate catalogue: the eight checkpoints that close the phases of our SDD lifecycle.

Domain layer. A *phase* is a stretch of work (discover, plan, structure, specify, build,
validate, release); a *gate* is the checkpoint that closes it. Human gates are closed by our
approvals (both of us, see `team.py`); automated gates are closed by a machine check. The
catalogue mirrors the target operating model in `harness/lifecycle.md` and must change together
with it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from sdd.domain.errors import InvalidGateError


class GateId(StrEnum):
    """Identifier of a gate, ordered like the lifecycle (G0 first, G7 last)."""

    G0 = "G0"
    G1 = "G1"
    G2 = "G2"
    G3 = "G3"
    G4 = "G4"
    G5 = "G5"
    G6 = "G6"
    G7 = "G7"


class GateKind(StrEnum):
    """Who closes a gate."""

    HUMAN = "human"
    """Closed when every required team member approved the current artifacts."""

    AUTOMATED = "automated"
    """Closed by a deterministic check that the harness runs itself."""


@dataclass(frozen=True)
class GateDefinition:
    """One checkpoint of the lifecycle.

    Attributes:
        id: the gate identifier (G0-G7).
        phase: number of the phase the gate closes (0 = context, 1-7 as in the operating model).
        phase_name: short name of that phase ("Discover", "Plan", ...).
        title: what passing the gate means, in a few words.
        kind: whether people or a machine close it.
        artifacts: file names, inside the dossier folder, whose content the gate judges. Their
            digest is what an approval is bound to; an empty tuple means the gate judges
            something else (the requirement references for G0, the code for G5).
    """

    id: GateId
    phase: int
    phase_name: str
    title: str
    kind: GateKind
    artifacts: tuple[str, ...]


GATES: tuple[GateDefinition, ...] = (
    GateDefinition(GateId.G0, 0, "Context", "Requirements read and cited", GateKind.AUTOMATED, ()),
    GateDefinition(GateId.G1, 1, "Discover", "PRD validated", GateKind.HUMAN, ("prd.md",)),
    GateDefinition(GateId.G2, 2, "Plan", "Backlog approved", GateKind.HUMAN, ("backlog.md",)),
    GateDefinition(
        GateId.G3, 3, "Structure", "Approach approved", GateKind.HUMAN, ("ux-approach.md",)
    ),
    GateDefinition(
        GateId.G4,
        4,
        "Specify",
        "Specification approved for execution",
        GateKind.HUMAN,
        ("spec.md", "plan.md", "tasks.md"),
    ),
    GateDefinition(GateId.G5, 5, "Build", "Deterministic checks passed", GateKind.AUTOMATED, ()),
    GateDefinition(
        GateId.G6,
        6,
        "Validate",
        "Approved for merge",
        GateKind.HUMAN,
        ("validation.md", "teaching-guide.md"),
    ),
    GateDefinition(
        GateId.G7, 7, "Release & Learn", "Results validated", GateKind.HUMAN, ("release.md",)
    ),
)
"""The lifecycle, in order. Order matters: a gate can only pass after every earlier one."""


def parse_gate_id(text: str) -> GateId:
    """Turn user input such as "g4" or "G4" into a `GateId`.

    Args:
        text: the gate as typed by a person or an agent; case and surrounding spaces ignored.

    Returns:
        The matching gate identifier.

    Raises:
        InvalidGateError: when the text is not one of G0-G7.
    """
    try:
        return GateId(text.strip().upper())
    except ValueError as error:
        raise InvalidGateError(f"unknown gate {text!r}; expected one of G0-G7") from error


def get_gate(gate_id: GateId) -> GateDefinition:
    """Return the definition of a gate.

    Args:
        gate_id: the gate to look up.

    Returns:
        Its entry in `GATES` (always found: `GateId` and `GATES` list the same gates).
    """
    return next(gate for gate in GATES if gate.id is gate_id)


def gates_before(gate_id: GateId) -> tuple[GateDefinition, ...]:
    """Return every gate that must have passed before `gate_id` can pass, in lifecycle order.

    Args:
        gate_id: the gate being requested.

    Returns:
        The gates strictly earlier in the lifecycle (empty for G0).
    """
    position = [gate.id for gate in GATES].index(gate_id)
    return GATES[:position]


def all_artifacts() -> tuple[str, ...]:
    """Return every artifact file name of the lifecycle, in the order the phases produce them.

    Returns:
        The concatenation of each gate's `artifacts`, without duplicates.
    """
    names: list[str] = []
    for gate in GATES:
        names.extend(name for name in gate.artifacts if name not in names)
    return tuple(names)
