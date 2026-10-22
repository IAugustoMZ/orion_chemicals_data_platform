"""Composition root: the only place where adapters are created and wired into use cases.

Everything above this module (the command line) receives ready-made use cases; everything below
it (use cases, domain) receives ports. Swapping an adapter (say, storing dossiers elsewhere) is
a change to this file only. Tests build the use cases directly with fakes instead.
"""

from __future__ import annotations

from dataclasses import dataclass

from sdd.application.doc_rules.adr import AdrRule
from sdd.application.doc_rules.links import LocalLinkRule
from sdd.application.doc_rules.mermaid import MermaidDiagramTypeRule, MermaidLogoRule
from sdd.application.generators.adapters import AdapterGenerator
from sdd.application.generators.status import StatusGenerator
from sdd.application.generators.traceability import TraceabilityGenerator
from sdd.application.ports.environment import HumanConfirmation
from sdd.application.ports.reference_data import RequirementCatalog
from sdd.application.use_cases.approve_gate import ApproveGate
from sdd.application.use_cases.check_harness import CheckHarness
from sdd.application.use_cases.create_dossier import CreateDossier
from sdd.application.use_cases.evaluate_dossier import EvaluateDossier
from sdd.application.use_cases.guard_commit import GuardCommit
from sdd.application.use_cases.lint_docs import LintDocs
from sdd.application.use_cases.sync_generated import SyncGenerated
from sdd.application.use_cases.verify_quality import VerifyQuality
from sdd.config import Settings
from sdd.infrastructure.file_document_store import FileDocumentStore
from sdd.infrastructure.file_template_library import FileTemplateLibrary
from sdd.infrastructure.git import listed_files
from sdd.infrastructure.git_workspace import GitWorkspace
from sdd.infrastructure.subprocess_check_runner import SubprocessCheckRunner
from sdd.infrastructure.system_clock import SystemClock
from sdd.infrastructure.terminal_confirmation import TerminalConfirmation
from sdd.infrastructure.yaml_dossier_repository import YamlDossierRepository
from sdd.infrastructure.yaml_reference_data import (
    YamlLogoRegistry,
    YamlQualityCheckCatalog,
    YamlRequirementCatalog,
    YamlTeamDirectory,
)


@dataclass(frozen=True)
class Harness:
    """The use cases the command line can call, already wired.

    Attributes:
        settings: the locations in use.
        requirements: the RT catalogue (for `sdd rt`).
        evaluate: gate evaluation (read model).
        create: `sdd new`.
        approve: `sdd approve`.
        verify: `sdd verify`.
        guard: `sdd guard-commit`.
        check: `sdd check`.
        sync: `sdd sync`.
    """

    settings: Settings
    requirements: RequirementCatalog
    evaluate: EvaluateDossier
    create: CreateDossier
    approve: ApproveGate
    verify: VerifyQuality
    guard: GuardCommit
    check: CheckHarness
    sync: SyncGenerated


def build_harness(settings: Settings, confirmation: HumanConfirmation | None = None) -> Harness:
    """Create every adapter and wire every use case.

    Args:
        settings: where the harness files live.
        confirmation: the human-confirmation adapter (default: the interactive terminal).

    Returns:
        The wired harness.
    """
    root = settings.root
    dossiers = YamlDossierRepository(root, settings.specs_dir)
    requirements = YamlRequirementCatalog(settings.path(settings.requirements_file))
    team = YamlTeamDirectory(settings.path(settings.team_file))
    templates = FileTemplateLibrary(settings.path(settings.templates_dir))
    workspace, clock = GitWorkspace(root), SystemClock()
    store = FileDocumentStore(root, listed_files)
    evaluate = EvaluateDossier(dossiers, requirements, team, workspace)
    rules = (
        MermaidDiagramTypeRule(),
        MermaidLogoRule(
            YamlLogoRegistry(settings.path(settings.logos_file)).logos(),
            settings.strict_logo_paths,
        ),
        LocalLinkRule(store),
        AdrRule(store, settings.decisions_dir),
    )
    sync = SyncGenerated(
        store,
        (
            StatusGenerator(evaluate),
            TraceabilityGenerator(evaluate, requirements),
            AdapterGenerator(store),
        ),
    )
    return Harness(
        settings=settings,
        requirements=requirements,
        evaluate=evaluate,
        create=CreateDossier(dossiers, templates, requirements, clock),
        approve=ApproveGate(
            dossiers,
            evaluate,
            team,
            templates,
            workspace,
            confirmation or TerminalConfirmation(),
            clock,
        ),
        verify=VerifyQuality(
            dossiers,
            evaluate,
            YamlQualityCheckCatalog(settings.path(settings.checks_file)),
            SubprocessCheckRunner(root, listed_files),
            workspace,
            clock,
        ),
        guard=GuardCommit(workspace, evaluate),
        check=CheckHarness(
            evaluate, dossiers, team, LintDocs(store, rules, settings.lint_excluded), sync
        ),
        sync=sync,
    )
