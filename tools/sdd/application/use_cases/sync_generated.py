"""Use case: bring every generated document up to date (`sdd sync`) or report drift.

Application layer. Runs every `Generator`, compares its output with the files on disk and
either writes the differences (``write=True``) or reports them as error findings, which is what
`sdd check` does in pre-commit: a commit with an outdated README status or adapter fails.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sdd.application.generators import GeneratedFile, Generator
from sdd.application.generators.text_tools import replace_block
from sdd.application.ports.documents import DocumentStore
from sdd.domain.findings import Finding, Severity


@dataclass(frozen=True)
class SyncResult:
    """What a sync found or did.

    Attributes:
        changed: paths whose content differs from the generated one (written when writing).
        removed: orphan files in generated folders (removed when writing).
        problems: findings that writing cannot fix (e.g. missing block markers).
    """

    changed: tuple[str, ...]
    removed: tuple[str, ...]
    problems: tuple[Finding, ...]

    def findings(self) -> tuple[Finding, ...]:
        """Return drift as error findings (used by `sdd check`), plus the problems."""
        drift = tuple(
            Finding("generated-drift", Severity.ERROR, "out of date: run `sdd sync`", path)
            for path in (*self.changed, *self.removed)
        )
        return drift + self.problems


class SyncGenerated:
    """Run the generators and reconcile the files on disk with their output."""

    def __init__(self, store: DocumentStore, generators: Sequence[Generator]) -> None:
        """Receive the store and the generators.

        Args:
            store: the repository's files.
            generators: every generator, in the order their output is applied.
        """
        self._store = store
        self._generators = tuple(generators)

    def execute(self, write: bool) -> SyncResult:
        """Compute (and optionally write) every generated file.

        Args:
            write: true to update the files; false to only report what differs.
        """
        expected: dict[str, str] = {}
        problems: list[Finding] = []
        for generated in self._all_outputs():
            current = expected.get(generated.path, self._store.read(generated.path) or "")
            content = self._apply(generated, current, problems)
            if content is not None:
                expected[generated.path] = content
        changed = tuple(p for p, c in expected.items() if self._store.read(p) != c)
        orphans = self._orphans(set(expected))
        if write:
            for path in changed:
                self._store.write(path, expected[path])
            for path in orphans:
                self._store.remove(path)
        return SyncResult(changed, orphans, tuple(problems))

    def _all_outputs(self) -> tuple[GeneratedFile, ...]:
        """Return the outputs of every generator, in order."""
        return tuple(f for generator in self._generators for f in generator.generate())

    @staticmethod
    def _apply(generated: GeneratedFile, current: str, problems: list[Finding]) -> str | None:
        """Return the file's new content, or None (with a problem) when a block is missing.

        Args:
            generated: one generator output.
            current: the file's current (or already partly regenerated) content.
            problems: collects the problems found.
        """
        if generated.block is None:
            return generated.content
        updated = replace_block(current, generated.block, generated.content)
        if updated is None:
            problems.append(
                Finding(
                    "generated-block",
                    Severity.ERROR,
                    f"markers <!-- sdd:{generated.block}:start/end --> not found",
                    generated.path,
                )
            )
        return updated

    def _orphans(self, produced: set[str]) -> tuple[str, ...]:
        """Return files in generated folders that no generator produced any more.

        Args:
            produced: every path generated in this run.
        """
        prefixes = tuple(p for g in self._generators for p in g.owned_prefixes())
        if not prefixes:
            return ()
        return tuple(
            path
            for prefix in prefixes
            for path in self._store.paths(prefix=prefix)
            if path not in produced
        )
