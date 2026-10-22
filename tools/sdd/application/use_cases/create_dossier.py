"""Use case: start a new spec dossier from the templates (`sdd new`).

Application layer. Creating a dossier is the first act of every piece of work: it assigns the
next id, records the requirements the work serves, and copies one template per lifecycle
artifact into `specs/<id>-<slug>/`, pre-filled with what is already known (title, branch, the
cited RTs with their verification method).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date

from sdd.application.ports.documents import TemplateLibrary
from sdd.application.ports.dossiers import DossierRepository
from sdd.application.ports.environment import Clock
from sdd.application.ports.reference_data import RequirementCatalog
from sdd.domain.dossier import Dossier, DossierKind
from sdd.domain.errors import UnknownRequirementError
from sdd.domain.gates import all_artifacts
from sdd.domain.requirement import Requirement


@dataclass(frozen=True)
class NewDossier:
    """What a person or an agent provides to start a dossier.

    Attributes:
        title: human title of the work.
        slug: kebab-case short name (folder and branch are derived from it).
        kind: feature or enabler.
        requirements: RT ids the work serves.
        rationale: why the work is worth doing (mandatory for enablers and for features that
            cite no RT).
    """

    title: str
    slug: str
    kind: DossierKind
    requirements: tuple[str, ...]
    rationale: str = ""


class CreateDossier:
    """Create `specs/<id>-<slug>/` with `dossier.yaml` and one artifact per phase."""

    def __init__(
        self,
        dossiers: DossierRepository,
        templates: TemplateLibrary,
        requirements: RequirementCatalog,
        clock: Clock,
    ) -> None:
        """Receive the ports needed to create a dossier.

        Args:
            dossiers: where the dossier is created.
            templates: the artifact templates.
            requirements: the RT catalogue, to validate citations and pre-fill the PRD.
            clock: today's date for the metadata.
        """
        self._dossiers = dossiers
        self._templates = templates
        self._requirements = requirements
        self._clock = clock

    def execute(self, request: NewDossier) -> Dossier:
        """Create the dossier and return it.

        Args:
            request: the new dossier's description.

        Raises:
            UnknownRequirementError: when an RT id is not in the catalogue.
            InvalidDossierError: when the slug or title is malformed.
        """
        catalog = self._requirements.all()
        unknown = [rt for rt in request.requirements if rt not in catalog]
        if unknown:
            raise UnknownRequirementError(f"not in the catalogue: {', '.join(unknown)}")
        dossier = Dossier(
            id=self._next_id(),
            slug=request.slug,
            title=request.title,
            kind=request.kind,
            requirements=request.requirements,
            rationale=request.rationale,
            created=self._clock.now().date(),
        )
        values = _template_values(dossier, catalog, dossier.created)
        artifacts = {name: self._templates.render(name, values) for name in all_artifacts()}
        self._dossiers.create(dossier, artifacts)
        return dossier

    def _next_id(self) -> str:
        """Return the id after the highest existing one ("000" for the first dossier)."""
        existing = [int(dossier_id) for dossier_id in self._dossiers.ids()]
        return f"{max(existing, default=-1) + 1:03d}"


def _template_values(
    dossier: Dossier, catalog: Mapping[str, Requirement], today: date
) -> dict[str, str]:
    """Return the ``{{key}}`` values every template may use.

    Args:
        dossier: the new dossier.
        catalog: the RT catalogue by id.
        today: the creation date.
    """
    return {
        "id": dossier.id,
        "slug": dossier.slug,
        "title": dossier.title,
        "kind": dossier.kind.value,
        "date": today.isoformat(),
        "branch": dossier.branch_name,
        "requirements": ", ".join(dossier.requirements) or "none",
        "requirements_table": _requirements_table(dossier, catalog),
    }


_NO_RT: Mapping[DossierKind, str] = {
    DossierKind.ENABLER: "_No RT cited: this is an enabler; see the rationale in `dossier.yaml`._",
    DossierKind.FEATURE: (
        "_No RT cited: this feature is **outside the requirements catalogue** (ADR-0014). The "
        "rationale in `dossier.yaml` says why it is worth doing; the text below lists the RTs "
        "that were considered and why none of them applies._"
    ),
}
"""What the PRD says in place of the requirements table when no RT is cited, per kind."""


def _requirements_table(dossier: Dossier, catalog: Mapping[str, Requirement]) -> str:
    """Render the cited RTs as a Markdown table: statement and how we verify it.

    Args:
        dossier: the new dossier (its RT ids are all known).
        catalog: the RT catalogue by id.
    """
    if not dossier.requirements:
        return _NO_RT[dossier.kind]
    rows = ["| RT | Phase | What must hold | How we verify it |", "|---|---|---|---|"]
    for rt in dossier.requirements:
        requirement = catalog[rt]
        rows.append(
            f"| {rt} | {requirement.phase.value} | {requirement.statement} "
            f"| {requirement.verification} |"
        )
    return "\n".join(rows)
