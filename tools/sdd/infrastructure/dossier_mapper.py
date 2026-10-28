"""Mapping between the `Dossier` aggregate and the plain data of `dossier.yaml`.

Infrastructure layer. Kept apart from the repository (single responsibility): the repository
knows *where* dossiers are stored, this module knows *how* they are represented. Timestamps are
stored as ISO-8601 strings in UTC; gate keys are written in lifecycle order.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sdd.domain.approval import Approval, CheckOutcome, Verification
from sdd.domain.dossier import Dossier, DossierKind
from sdd.domain.errors import InvalidDossierError
from sdd.domain.gates import GATES, GateId


def to_data(dossier: Dossier) -> dict[str, Any]:
    """Return the plain-data form of a dossier, ready for `yaml.safe_dump`.

    Args:
        dossier: the dossier.
    """
    approvals = {
        gate.id.value: [_approval_data(a) for a in dossier.approvals_for(gate.id)]
        for gate in GATES
        if dossier.approvals_for(gate.id)
    }
    return {
        "id": dossier.id,
        "slug": dossier.slug,
        "title": dossier.title,
        "kind": dossier.kind.value,
        "created": dossier.created,
        "requirements": list(dossier.requirements),
        "rationale": dossier.rationale,
        "approvals": approvals,
        "verification": _verification_data(dossier.verification),
    }


def from_data(data: Any) -> Dossier:
    """Build a dossier from the plain data loaded from `dossier.yaml`.

    Args:
        data: the parsed YAML document.

    Raises:
        InvalidDossierError: when a field is missing or has the wrong type.
    """
    if not isinstance(data, dict):
        raise InvalidDossierError("dossier.yaml must be a mapping")
    try:
        raw_id = data["id"]
        return Dossier(
            id=f"{raw_id:03d}" if isinstance(raw_id, int) else str(raw_id),
            slug=str(data["slug"]),
            title=str(data["title"]),
            kind=DossierKind(data.get("kind", DossierKind.FEATURE.value)),
            requirements=tuple(str(rt) for rt in data.get("requirements") or ()),
            rationale=str(data.get("rationale") or ""),
            created=_date(data["created"]),
            approvals={
                GateId(gate): tuple(_approval(a) for a in approvals)
                for gate, approvals in (data.get("approvals") or {}).items()
            },
            verification=_verification(data.get("verification")),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidDossierError(f"malformed dossier.yaml: {error}") from error


def _approval_data(approval: Approval) -> dict[str, str]:
    """Return the plain-data form of an approval.

    Args:
        approval: the approval.
    """
    return {
        "member": approval.member,
        "at": approval.approved_at.isoformat(),
        "digest": approval.digest,
        "git_identity": approval.git_identity,
        "note": approval.note,
    }


def _approval(data: dict[str, Any]) -> Approval:
    """Build an approval from its plain data.

    Args:
        data: one entry of an ``approvals.<gate>`` list.
    """
    return Approval(
        member=str(data["member"]),
        approved_at=datetime.fromisoformat(str(data["at"])),
        digest=str(data["digest"]),
        git_identity=str(data.get("git_identity", "")),
        note=str(data.get("note") or ""),
    )


def _verification_data(verification: Verification | None) -> dict[str, Any] | None:
    """Return the plain-data form of a verification (None stays None).

    Args:
        verification: the latest G5 verification, if any.
    """
    if verification is None:
        return None
    return {
        "at": verification.verified_at.isoformat(),
        "digest": verification.digest,
        "commit": verification.commit,
        "results": [
            {"check": r.check_id, "passed": r.passed, "summary": r.summary}
            for r in verification.results
        ],
    }


def _verification(data: dict[str, Any] | None) -> Verification | None:
    """Build a verification from its plain data.

    Args:
        data: the ``verification`` mapping, or None.
    """
    if not data:
        return None
    return Verification(
        verified_at=datetime.fromisoformat(str(data["at"])),
        digest=str(data["digest"]),
        commit=str(data.get("commit", "")),
        results=tuple(
            CheckOutcome(str(r["check"]), bool(r["passed"]), str(r.get("summary", "")))
            for r in data.get("results") or ()
        ),
    )


def _date(value: Any) -> date:
    """Accept a YAML date or an ISO string.

    Args:
        value: the ``created`` field.
    """
    return value if isinstance(value, date) else date.fromisoformat(str(value))
