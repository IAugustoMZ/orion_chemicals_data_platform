"""Adapter of the `AcStatusReader` port: run the tests marked ``ac`` and read the JUnit report.

Infrastructure layer. A test names the criterion it proves with
``@pytest.mark.ac("PBI-002-02:AC1")``; `tests/conftest.py` copies each marker into the JUnit
report as a ``<property name="ac">``. This adapter runs only the marked tests, without coverage
(a subset can never reach the coverage floor), and folds the report into one verdict per id.
"""

from __future__ import annotations

import subprocess  # nosec B404 # running the marked tests is the purpose of this adapter
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree  # nosec B405 # parses a report this adapter just wrote

_TIMEOUT_SECONDS = 900


class PytestAcStatusReader:
    """Run ``pytest -m ac`` in the repository root and read which criteria passed."""

    def __init__(self, root: Path) -> None:
        """Remember the repository root.

        Args:
            root: absolute path of the repository root.
        """
        self._root = root

    def read(self) -> dict[str, bool]:
        """Run the marked tests.

        Returns:
            Marker id to true when every test carrying it passed; ids with no test are absent.
        """
        with tempfile.TemporaryDirectory() as folder:
            report = Path(folder) / "ac.xml"
            command = [
                sys.executable,
                "-m",
                "pytest",
                "-m",
                "ac",
                "-q",
                "--no-cov",
                "-p",
                "no:cacheprovider",
                f"--junitxml={report}",
            ]
            subprocess.run(  # noqa: S603  # nosec B603 # argument list, no shell, fixed command
                command,
                cwd=self._root,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_SECONDS,
                check=False,
            )
            return parse_report(report) if report.is_file() else {}


def parse_report(report: Path) -> dict[str, bool]:
    """Fold a JUnit report into one verdict per criterion id.

    Args:
        report: the XML file written by pytest.

    Returns:
        Marker id to true when every test carrying it passed (skipped counts as not passed).
    """
    verdict: dict[str, bool] = {}
    tree = ElementTree.parse(report)  # noqa: S314  # nosec B314 # report written by our own run
    for case in tree.iter("testcase"):
        passed = case.find("failure") is None
        passed = passed and case.find("error") is None and case.find("skipped") is None
        for prop in case.iter("property"):
            if prop.get("name") == "ac":
                key = str(prop.get("value"))
                verdict[key] = verdict.get(key, True) and passed
    return verdict
