"""Use case: start a new spec dossier from the templates (`sdd new`).

Application layer. Creating a dossier is the first act of every piece of work: it assigns the
next id, records the requirements the work serves, and creates
`specs/<id>-<slug>/` with `dossier.yaml` and the PRD, pre-filled with what is already known
(title, branch, the cited RTs with their verification method). The later artifacts appear as
the gates pass (ADR-0018).
"""

from __future__ import annotations

from dataclasses import dataclass

from sdd.application.ports.dossiers import DossierRepository
from sdd.application.ports.environment import Clock
from sdd.application.ports.reference_data import RequirementCatalog
from sdd.application.scaffold_artifacts import ScaffoldArtifacts
from sdd.domain.dossier import Dossier, DossierKind
from sdd.domain.errors import InvalidDossierError, UnknownRequirementError


@dataclass(frozen=True)
class NewDossier:
    """What a person or an agent provides to start a dossier.

    Attributes:
        title: human title of the work.
        slug: kebab-case short name (folder and branch are derived from it).
        kind: feature or enabler.
        requirements: RT ids the work serves.
        rationale: why the work is worth doing (mandatory for every dossier, ADR-0026).
    """

    title: str
    slug: str
    kind: DossierKind
    requirements: tuple[str, ...]
    rationale: str


class CreateDossier:
    """Create `specs/<id>-<slug>/` with `dossier.yaml` and `prd.md`."""

    def __init__(
        self,
        dossiers: DossierRepository,
        scaffold: ScaffoldArtifacts,
        requirements: RequirementCatalog,
        clock: Clock,
    ) -> None:
        """Receive the ports needed to create a dossier.

        Args:
            dossiers: where the dossier is created.
            scaffold: renders and adds the PRD.
            requirements: the RT catalogue, to validate citations.
            clock: today's date for the metadata.
        """
        self._dossiers = dossiers
        self._scaffold = scaffold
        self._requirements = requirements
        self._clock = clock

    def execute(self, request: NewDossier) -> Dossier:
        """Create the dossier and return it.

        Args:
            request: the new dossier's description.

        Raises:
            UnknownRequirementError: when an RT id is not in the catalogue.
            InvalidDossierError: when the slug or title is malformed, or the rationale is blank.
        """
        if not request.rationale.strip():
            raise InvalidDossierError("a dossier must state its rationale: pass --rationale")
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
        self._dossiers.create(dossier, {})
        self._scaffold.for_creation(dossier)
        return dossier

    def _next_id(self) -> str:
        """Return the id after the highest existing one ("000" for the first dossier)."""
        existing = [int(dossier_id) for dossier_id in self._dossiers.ids()]
        return f"{max(existing, default=-1) + 1:03d}"
