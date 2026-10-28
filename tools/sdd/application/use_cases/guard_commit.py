"""Use case: refuse a commit that changes governed files without an approved spec.

Application layer, run by pre-commit (`sdd guard-commit <staged files>`). It is the mechanical
form of the Constitution's article III: behaviour changes only after we approved *what* to build
(gate G4). Documentation and dossiers are never blocked, so we can always discuss and specify.
"""

from __future__ import annotations

from collections.abc import Sequence

from sdd.application.ports.environment import Workspace
from sdd.application.use_cases.evaluate_dossier import EvaluateDossier
from sdd.domain.errors import DossierNotFoundError
from sdd.domain.findings import Finding, Severity
from sdd.domain.gate_status import GateState
from sdd.domain.gates import GateId
from sdd.domain.governance import is_governed, spec_id_from_branch

_RULE = "commit-guard"
_SHOWN = 5


class GuardCommit:
    """Check the staged paths against the current branch and its dossier's gate G4."""

    def __init__(self, workspace: Workspace, evaluator: EvaluateDossier) -> None:
        """Receive the ports the guard reads from.

        Args:
            workspace: gives the current branch.
            evaluator: gives the state of the branch's dossier.
        """
        self._workspace = workspace
        self._evaluator = evaluator

    def execute(self, paths: Sequence[str]) -> tuple[Finding, ...]:
        """Return an error finding when the commit is not allowed, else nothing.

        Args:
            paths: the repository-relative paths staged for commit.
        """
        governed = sorted(p for p in paths if is_governed(p))
        if not governed:
            return ()
        files = ", ".join(governed[:_SHOWN]) + (" ..." if len(governed) > _SHOWN else "")
        branch = self._workspace.current_branch()
        dossier_id = spec_id_from_branch(branch)
        if dossier_id is None:
            return (
                _error(
                    f"governed files changed on branch {branch!r} ({files}); governed changes "
                    "happen only on a spec/<id>-<slug> branch whose G4 passed"
                ),
            )
        try:
            g4 = self._evaluator.one(dossier_id).status(GateId.G4)
        except DossierNotFoundError:
            return (_error(f"branch {branch!r} names dossier {dossier_id}, which does not exist"),)
        if g4.state is not GateState.PASSED:
            return (
                _error(
                    f"dossier {dossier_id}: G4 is {g4.state} ({g4.detail}); approve the "
                    f"specification before committing governed files ({files})"
                ),
            )
        return ()


def _error(message: str) -> Finding:
    """Build an error finding of this rule.

    Args:
        message: what is wrong and how to proceed.
    """
    return Finding(_RULE, Severity.ERROR, message)
