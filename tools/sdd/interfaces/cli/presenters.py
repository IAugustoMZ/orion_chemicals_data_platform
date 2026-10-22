"""Text rendering of the harness's results for the terminal.

Interfaces layer. Output is plain ASCII on purpose: it must read the same in Windows consoles,
in agent transcripts and in pre-commit logs. (The Markdown documents use symbols instead.)
"""

from __future__ import annotations

from collections.abc import Iterable

from sdd.application.use_cases.evaluate_dossier import DossierReport
from sdd.domain.approval import CheckOutcome, Verification
from sdd.domain.findings import Finding
from sdd.domain.quality import QualityCheck
from sdd.domain.requirement import Requirement


def report_lines(report: DossierReport) -> list[str]:
    """Render one dossier: header, one line per gate, and the next step.

    Args:
        report: the evaluated dossier.
    """
    dossier = report.dossier
    lines = [
        f"{dossier.id}  {dossier.title}  [{dossier.kind.value}]  branch {dossier.branch_name}",
        f"     serves: {', '.join(dossier.requirements) or '(no RT)'}",
    ]
    for status in report.statuses:
        gate = status.gate
        label = f"{gate.id} {gate.phase_name}"
        lines.append(f"  {label:<20} {status.state.value:<8} {status.detail}")
    current = report.current
    if current is None:
        lines.append("  -> done: every gate passed")
    else:
        lines.append(f"  -> next: {current.gate.id} {current.gate.title}: {current.detail}")
    return lines


def finding_lines(findings: Iterable[Finding]) -> list[str]:
    """Render findings, one per line: severity, rule, location, message.

    Args:
        findings: the findings to show.
    """
    return [
        f"{f.severity.value.upper():<8} {f.rule:<18} {f.location or '-'}  {f.message}"
        for f in findings
    ]


def check_progress(check: QualityCheck, outcome: CheckOutcome | None) -> str:
    """Render one step of `sdd verify`.

    Args:
        check: the check running or finished.
        outcome: None while it starts, the outcome once it finished.
    """
    if outcome is None:
        return f"  .. {check.id:<14} {check.title}"
    verdict = "PASS" if outcome.passed else "FAIL"
    text = f"  {verdict} {check.id}"
    if not outcome.passed:
        text += "\n" + "\n".join(f"       | {line}" for line in outcome.summary.splitlines())
    return text


def verification_line(verification: Verification) -> str:
    """Render the verdict of `sdd verify`.

    Args:
        verification: the saved verification.
    """
    if verification.passed:
        return f"G5 passed at commit {verification.commit}"
    return f"G5 failed: {', '.join(verification.failed_checks)}"


def requirement_lines(requirement: Requirement) -> list[str]:
    """Render one requirement for `sdd rt`.

    Args:
        requirement: the RT.
    """
    flag = " (priority)" if requirement.priority else ""
    return [
        f"{requirement.id}  [{requirement.category}, phase {requirement.phase.value}]{flag}",
        f"  must hold: {requirement.statement}",
        f"  verify:    {requirement.verification}",
    ]
