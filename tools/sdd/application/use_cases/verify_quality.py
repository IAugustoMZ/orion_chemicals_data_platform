"""Use case: run the deterministic quality suite and record gate G5 (`sdd verify`).

Application layer. G5 is the machine's gate: formatting, lint, types, layer contracts, tests,
security scans and the harness's own consistency, as listed in `harness/checks.yaml`. The agent
that builds is expected to run this in a loop until it passes (bounded by the loop limit in
`harness/ai-control-plane.md`). The result is bound to the digest of the governed code, so any
later code change makes G5 stale.
"""

from __future__ import annotations

from collections.abc import Callable

from sdd.application.ports.dossiers import DossierRepository
from sdd.application.ports.environment import CheckRunner, Clock, Workspace
from sdd.application.ports.reference_data import QualityCheckCatalog
from sdd.application.use_cases.evaluate_dossier import EvaluateDossier
from sdd.domain.approval import CheckOutcome, Verification
from sdd.domain.errors import GateOrderError
from sdd.domain.gate_status import GateState
from sdd.domain.gates import GateId, gates_before
from sdd.domain.quality import QualityCheck

ProgressCallback = Callable[[QualityCheck, CheckOutcome | None], None]
"""Called before (outcome None) and after each check, so the CLI can show progress."""


class VerifyQuality:
    """Run every check of the suite and save the verification in the dossier."""

    def __init__(
        self,
        dossiers: DossierRepository,
        evaluator: EvaluateDossier,
        checks: QualityCheckCatalog,
        runner: CheckRunner,
        workspace: Workspace,
        clock: Clock,
    ) -> None:
        """Receive the ports a verification needs.

        Args:
            dossiers: where the verification is saved.
            evaluator: to require that G0-G4 passed.
            checks: the suite.
            runner: runs one check.
            workspace: governed digest and HEAD commit.
            clock: the verification time.
        """
        self._dossiers = dossiers
        self._evaluator = evaluator
        self._checks = checks
        self._runner = runner
        self._workspace = workspace
        self._clock = clock

    def execute(self, dossier_id: str, progress: ProgressCallback | None = None) -> Verification:
        """Run the suite for a dossier whose specification was approved.

        Args:
            dossier_id: three-digit dossier id.
            progress: optional observer of each check (before and after it runs).

        Returns:
            The saved verification; check `passed` for the verdict.

        Raises:
            GateOrderError: when a gate before G5 has not passed (build only after G4).
        """
        report = self._evaluator.one(dossier_id)
        for earlier in gates_before(GateId.G5):
            status = report.status(earlier.id)
            if status.state is not GateState.PASSED:
                raise GateOrderError(f"G5 needs {earlier.id} passed; it is {status.state}")
        outcomes: list[CheckOutcome] = []
        for check in self._checks.all():
            if progress:
                progress(check, None)
            outcome = self._runner.run(check)
            outcomes.append(outcome)
            if progress:
                progress(check, outcome)
        verification = Verification(
            verified_at=self._clock.now(),
            digest=self._workspace.governed_digest(),
            commit=self._workspace.head_commit(),
            results=tuple(outcomes),
        )
        self._dossiers.save(report.dossier.with_verification(verification))
        return verification
