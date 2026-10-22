"""Infrastructure layer of the SDD harness: adapters that implement the application's ports.

YAML files, git, subprocesses and the terminal live here and nowhere else. Each adapter
honours its port's documented contract (Liskov substitution), which is what allows the unit
tests to swap them for in-memory fakes. Only `sdd.bootstrap` instantiates these classes.
"""
