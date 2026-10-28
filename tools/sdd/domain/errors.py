"""Typed errors of the SDD harness.

Domain layer. Every rule violation the harness can detect has its own exception class, so the
command line (interfaces layer) can map each one to a clear message and an exit code without
parsing strings. All of them derive from `SddError`, which callers may catch as a family.
"""


class SddError(Exception):
    """Base class of every error the harness raises on purpose."""


class InvalidDossierError(SddError):
    """A dossier (a spec folder) breaks an invariant: bad id, bad slug, malformed metadata."""


class DossierNotFoundError(SddError):
    """No dossier with the requested id exists under `specs/`."""


class UnknownRequirementError(SddError):
    """A dossier cites an RT id that is not in `docs/requirements/rt-catalog.yaml`."""


class InvalidGateError(SddError):
    """The text given as a gate id is not one of G0-G7."""


class GateKindError(SddError):
    """The operation does not apply to this kind of gate (e.g. approving an automated gate)."""


class GateOrderError(SddError):
    """A gate was requested before every earlier gate of the lifecycle had passed."""


class GateNotReadyError(SddError):
    """The artifacts of a gate are incomplete (missing sections or `TODO(sdd)` placeholders).

    Attributes:
        problems: one human-readable line per problem found, in file order.
    """

    def __init__(self, problems: tuple[str, ...]) -> None:
        """Keep the individual problems so the caller can print them as a list.

        Args:
            problems: the readiness problems; must not be empty.
        """
        super().__init__("; ".join(problems))
        self.problems = problems


class UnknownMemberError(SddError):
    """The approver named on the command line is not a member listed in `harness/team.yaml`."""


class InvalidTeamError(SddError):
    """`harness/team.yaml` is malformed: no members, duplicated ids, unknown policy."""


class HumanConfirmationRequiredError(SddError):
    """An approval was attempted without an interactive terminal.

    Approvals are made by people (ADR-0003). Coding agents run commands without a terminal
    attached, so the harness refuses to record an approval when it cannot ask a human to type
    the confirmation.
    """


class ApprovalDeclinedError(SddError):
    """The person at the terminal did not type the expected confirmation text."""
