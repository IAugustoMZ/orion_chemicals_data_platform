"""Interfaces layer of the SDD harness: how people and agents talk to it.

Today there is one interface, the `sdd` command line (`cli/`). It turns arguments into calls of
the use cases built by `sdd.bootstrap`, and results or typed errors into text and exit codes.
"""
