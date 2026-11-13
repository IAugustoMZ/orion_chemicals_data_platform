"""Collect the evidence a dossier's gates are evaluated on.

Application layer. Gate evaluation itself is a pure domain function
(`sdd.domain.gate_status.evaluate_gates`); this module gathers its inputs through the ports:
the current digest of each human gate's artifacts, the digest of the governed code, and the
problems with the dossier's requirement citations (gate G0).
"""

from __future__ import annotations

from collections.abc import Mapping

from sdd.application.ports.dossiers import DossierRepository
from sdd.application.ports.progress import ProgressRepository
from sdd.domain.card_digest import backlog_without_card_bodies, card_sections
from sdd.domain.digest import digest_texts
from sdd.domain.dossier import Dossier, DossierKind
from sdd.domain.gate_status import GateEvidence
from sdd.domain.gates import GATES, GateDefinition, GateId, GateKind, all_artifacts
from sdd.domain.requirement import RT_ID_PATTERN, Requirement


def artifact_digest(
    dossier: Dossier,
    gate: GateDefinition,
    dossiers: DossierRepository,
    per_card: bool = False,
) -> str:
    """Return the current digest of a gate's artifacts (a missing file counts as empty).

    Args:
        dossier: the dossier.
        gate: the gate whose artifacts are digested.
        dossiers: where the artifacts are read from.
        per_card: true for a dossier with `progress.yaml`: G2 then judges the backlog without
            the bodies of its cards but the first, because each card is approved on its own.
    """
    texts = []
    for name in gate.artifacts:
        text = dossiers.read_artifact(dossier, name) or ""
        if per_card and gate.id is GateId.G2 and name == "backlog.md":
            text = backlog_without_card_bodies(text)
        texts.append((name, text))
    return digest_texts(texts)


def _per_card(
    dossier: Dossier, gate: GateDefinition, dossiers: DossierRepository, stored: object | None
) -> bool:
    """Decide whether a gate is judged per card (G2 on a dossier that has `progress.yaml`).

    A G2 approval given before the dossier had cards, bound to the whole backlog, keeps that
    meaning: creating `progress.yaml` later must not make it stale.

    Args:
        dossier: the dossier.
        gate: the gate being digested.
        dossiers: where the artifacts are read from.
        stored: the stored progress, or None.
    """
    if stored is None or gate.id is not GateId.G2:
        return False
    whole = artifact_digest(dossier, gate, dossiers, per_card=False)
    reduced = artifact_digest(dossier, gate, dossiers, per_card=True)
    bound = {a.digest for a in dossier.approvals_for(GateId.G2)}
    return not (whole in bound and reduced not in bound)


def context_problems(
    dossier: Dossier, catalog: Mapping[str, Requirement], dossiers: DossierRepository
) -> tuple[str, ...]:
    """Return why gate G0 (requirements read and cited) fails; empty when it passes.

    Rules: every RT in `dossier.yaml` and every RT mentioned in an artifact must exist in the
    catalogue; an enabler, and a feature that cites no RT (outside the catalogue, ADR-0014),
    state their rationale.

    Args:
        dossier: the dossier.
        catalog: the requirement catalogue by id.
        dossiers: where the artifacts are read from.
    """
    problems: list[str] = []
    mentioned = set(dossier.requirements)
    for name in all_artifacts():
        mentioned.update(RT_ID_PATTERN.findall(dossiers.read_artifact(dossier, name) or ""))
    unknown = sorted(rt for rt in mentioned if rt not in catalog)
    if unknown:
        problems.append(f"unknown requirements cited: {', '.join(unknown)}")
    if dossier.needs_rationale and not dossier.rationale.strip():
        problems.append(_MISSING_RATIONALE[dossier.kind])
    return tuple(problems)


_MISSING_RATIONALE: Mapping[DossierKind, str] = {
    DossierKind.ENABLER: "an enabler must state its rationale in dossier.yaml",
    DossierKind.FEATURE: (
        "a feature that cites no RT is outside the catalogue: cite the RTs it serves, "
        "or state in dossier.yaml's rationale why it is worth doing anyway"
    ),
}
"""The G0 problem reported when a mandatory rationale is empty, per kind."""


def collect_evidence(
    dossier: Dossier,
    dossiers: DossierRepository,
    catalog: Mapping[str, Requirement],
    governed_digest: str,
    progress: ProgressRepository | None = None,
) -> GateEvidence:
    """Gather everything `evaluate_gates` needs for one dossier.

    Args:
        dossier: the dossier.
        dossiers: where the artifacts are read from.
        catalog: the requirement catalogue by id.
        governed_digest: the digest of the governed code, computed once by the caller.
        progress: where `progress.yaml` is read; None keeps the rules of a dossier without cards.
    """
    stored = progress.load(dossier.id) if progress else None
    digests = {
        gate.id: artifact_digest(
            dossier, gate, dossiers, _per_card(dossier, gate, dossiers, stored)
        )
        for gate in GATES
        if gate.kind is GateKind.HUMAN
    }
    unmerged = None
    if stored is not None:
        backlog = dossiers.read_artifact(dossier, "backlog.md") or ""
        unmerged = stored.unmerged(tuple(card_sections(backlog)))
    return GateEvidence(
        digests, governed_digest, context_problems(dossier, catalog, dossiers), unmerged
    )
