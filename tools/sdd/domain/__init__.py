"""Domain layer of the SDD harness: the lifecycle's concepts as pure, immutable Python.

Nothing here performs I/O or imports a third-party package (enforced by import-linter, see
`pyproject.toml`). Every other layer of `sdd` depends on this package; it depends on nothing but
the standard library. That is what makes the rules of the lifecycle testable in milliseconds.
"""
