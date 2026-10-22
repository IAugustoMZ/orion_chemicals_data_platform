"""Adapter of the `TemplateLibrary` port: the Markdown templates in `harness/templates/`.

Infrastructure layer. Placeholders are ``{{key}}``; a deliberately tiny syntax (no logic, no
loops) so templates stay readable by people and by agents. Unknown keys are left untouched, so
a template can show ``{{example}}`` text without breaking.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

_PLACEHOLDER = re.compile(r"\{\{\s*(?P<key>[a-z_]+)\s*\}\}")


class FileTemplateLibrary:
    """Read and render templates from a folder."""

    def __init__(self, folder: Path) -> None:
        """Remember the folder.

        Args:
            folder: absolute path of `harness/templates/`.
        """
        self._folder = folder

    def text(self, name: str) -> str:
        """Return the raw template.

        Args:
            name: file name, e.g. "spec.md".
        """
        return (self._folder / name).read_text(encoding="utf-8")

    def render(self, name: str, values: Mapping[str, str]) -> str:
        """Return the template with every known ``{{key}}`` replaced.

        Args:
            name: file name, e.g. "spec.md".
            values: placeholder values.
        """
        return _PLACEHOLDER.sub(lambda m: values.get(m.group("key"), m.group(0)), self.text(name))
