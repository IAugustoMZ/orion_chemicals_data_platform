"""Use cases: one class per thing a person or an agent asks the harness to do.

Each use case receives its ports in `__init__` (constructor injection, wired by
`sdd.bootstrap`) and exposes one public method that runs it. None of them prints: they return
values or raise typed errors, and the command line decides how to show them.
"""
