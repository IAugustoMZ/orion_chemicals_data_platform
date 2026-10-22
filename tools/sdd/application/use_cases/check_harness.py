"""Use case: check that the repository is consistent with the harness (`sdd check`).

Application layer. Runs in pre-commit and as a G5 check. It does *not* demand that gates have
passed (work in progress is normal); it reports what is inconsistent:

* dossier errors: G0 failing (unknown RT, a missing rationale for an enabler or for a feature
  outside the catalogue),
  approvals by people who are not in the team;
* dossier warnings: stale approvals or a stale/failed G5 (work needed, not a broken repository),
  and artifacts *written ahead of their gate* (one gate at a time, ADR-0015);
* documentation errors from `LintDocs` (diagram types, logos, links, ADR index);
* generated files out of date (README status, traceability, tool adapters).
"""

from __future__ import annotations

from sdd.application.ports.dossiers import DossierRepository
from sdd.application.ports.reference_data import TeamDirectory
from sdd.application.use_cases.evaluate_dossier import DossierReport, EvaluateDossier
from sdd.application.use_cases.lint_docs import LintDocs
from sdd.application.use_cases.sync_generated import SyncGenerated
from sdd.domain.findings import Finding, Severity
from sdd.domain.gate_status import GateState
from sdd.domain.gates import GateId, get_gate
from sdd.domain.readiness import readiness_problems


class CheckHarness:
    """Collect every consistency finding of the repository."""

    def __init__(
        self,
        evaluator: EvaluateDossier,
        dossiers: DossierRepository,
        team: TeamDirectory,
        lint_docs: LintDocs,
        sync: SyncGenerated,
    ) -> None:
        """Receive the use cases and ports the check combines.

        Args:
            evaluator: evaluates every dossier.
            dossiers: where the artifacts are read from (to spot work written ahead).
            team: the approvers (to spot approvals by unknown people).
            lint_docs: the documentation lint.
            sync: the generated-files reconciliation, run in report-only mode.
        """
        self._evaluator = evaluator
        self._dossiers = dossiers
        self._team = team
        self._lint_docs = lint_docs
        self._sync = sync

    def execute(self) -> tuple[Finding, ...]:
        """Return every finding, dossiers first, then documents, then generated files."""
        members = {member.id for member in self._team.load().members}
        findings: list[Finding] = []
        for report in self._evaluator.all():
            findings.extend(_dossier_findings(report, members))
            findings.extend(self._written_ahead(report))
        findings.extend(self._lint_docs.execute())
        findings.extend(self._sync.execute(write=False).findings())
        return tuple(findings)

    def _written_ahead(self, report: DossierReport) -> list[Finding]:
        """Warn about artifacts that are complete although the gate before them has not passed.

        Why: when an agent drafts every phase before we review the first, approvals turn into
        rubber stamps and an early change ripples through finished documents (ADR-0015).

        Args:
            report: the evaluated dossier.
        """
        findings: list[Finding] = []
        for gate_id, previous in _PREDECESSOR.items():
            if report.status(previous).state is GateState.PASSED:
                continue
            written = [
                name
                for name in get_gate(gate_id).artifacts
                if not readiness_problems(
                    name, self._dossiers.read_artifact(report.dossier, name), ()
                )
            ]
            if written:
                message = (
                    f"{', '.join(written)} written before {previous} passed: review {previous} "
                    f"first, then draft {gate_id} (one gate at a time)"
                )
                where = f"specs/{report.dossier.folder_name}/{written[0]}"
                findings.append(Finding("written-ahead", Severity.WARNING, message, where))
        return findings


_PREDECESSOR: dict[GateId, GateId] = {
    GateId.G2: GateId.G1,
    GateId.G3: GateId.G2,
    GateId.G4: GateId.G3,
    GateId.G6: GateId.G4,
    GateId.G7: GateId.G6,
}
"""For each human gate, the gate that must pass before its artifacts are drafted.

The teaching guide and validation (G6) are written while building, so they wait for G4, not G5.
"""


def _dossier_findings(report: DossierReport, members: set[str]) -> list[Finding]:
    """Return the findings of one dossier.

    Args:
        report: the evaluated dossier.
        members: ids of the current team members.
    """
    where = f"specs/{report.dossier.folder_name}/dossier.yaml"
    findings: list[Finding] = []
    g0 = report.status(GateId.G0)
    if g0.state is GateState.FAILED:
        findings.append(Finding("dossier-context", Severity.ERROR, g0.detail, where))
    for gate_id, approvals in report.dossier.approvals.items():
        for approval in approvals:
            if approval.member not in members:
                findings.append(
                    Finding(
                        "unknown-approver",
                        Severity.ERROR,
                        f"{gate_id} approved by {approval.member!r}, who is not in the team",
                        where,
                    )
                )
    for status in report.statuses:
        if status.state in (GateState.STALE, GateState.FAILED) and status.gate.id is not GateId.G0:
            message = f"{status.gate.id} is {status.state}: {status.detail}"
            findings.append(Finding(f"gate-{status.state}", Severity.WARNING, message, where))
    return findings
