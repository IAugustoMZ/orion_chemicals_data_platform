"""Create a dossier's artifacts from the templates, a gate at a time (ADR-0018).

Application layer. A dossier starts with `dossier.yaml` and `prd.md`; the artifacts of every
later phase appear when the gate before them passes, so the folder shows where the work is and
a file that does not exist cannot be written ahead. This service knows *how* to render and add
the files; `CreateDossier` and `ApproveGate` decide *when*, and `artifacts_after` (domain) decides
*which*. It never overwrites a file: the repository adds only the files that are missing.
"""

from __future__ import annotations

from collections.abc import Mapping

from sdd.application.ports.documents import TemplateLibrary
from sdd.application.ports.dossiers import DossierRepository
from sdd.application.ports.reference_data import RequirementCatalog
from sdd.domain.dossier import Dossier, DossierKind
from sdd.domain.gates import GateId, artifacts_after
from sdd.domain.requirement import Requirement

PROGRESS_FILE = "progress.yaml"
"""Per-card record of ADR-0023, created with the backlog so G2 never changes meaning later."""


class ScaffoldArtifacts:
    """Render the templates of the next artifacts and add the ones that do not exist yet."""

    def __init__(
        self,
        templates: TemplateLibrary,
        requirements: RequirementCatalog,
        dossiers: DossierRepository,
    ) -> None:
        """Receive the ports needed to render and store the artifacts.

        Args:
            templates: the artifact templates.
            requirements: the RT catalogue, to fill the PRD's requirements table.
            dossiers: where the files are added.
        """
        self._templates = templates
        self._requirements = requirements
        self._dossiers = dossiers

    def for_creation(self, dossier: Dossier) -> tuple[str, ...]:
        """Add the artifacts a new dossier starts with (the PRD).

        Args:
            dossier: the dossier just created.

        Returns:
            The names of the files created.
        """
        return self.after(dossier, GateId.G0)

    def after(self, dossier: Dossier, gate_id: GateId) -> tuple[str, ...]:
        """Add the artifacts that appear when `gate_id` passes; existing files stay untouched.

        Args:
            dossier: the dossier whose gate passed.
            gate_id: the gate that has just passed.

        Returns:
            The names of the files created (empty when none is due or all exist already).

        Raises:
            OSError: when a file cannot be written; the files written by this call are removed
                first, so the caller can undo what led here.
        """
        names = artifacts_after(gate_id)
        if gate_id is GateId.G1:
            names = (*names, PROGRESS_FILE)  # the backlog is born with its per-card record
        values = _template_values(dossier, self._requirements.all())
        rendered = {name: self._templates.render(name, values) for name in names}
        return self._dossiers.add_artifacts(dossier, rendered)


def _template_values(dossier: Dossier, catalog: Mapping[str, Requirement]) -> dict[str, str]:
    """Return the ``{{key}}`` values every template may use.

    Args:
        dossier: the dossier the files belong to.
        catalog: the RT catalogue by id.
    """
    return {
        "id": dossier.id,
        "slug": dossier.slug,
        "title": dossier.title,
        "kind": dossier.kind.value,
        "date": dossier.created.isoformat(),
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
        dossier: the dossier (its RT ids are all known).
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
