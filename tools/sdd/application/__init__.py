"""Application layer of the SDD harness: use cases, the ports they need, and their rules.

A *use case* is one thing a person or an agent asks the harness to do (create a dossier, approve
a gate, verify the code, check the repository). A *port* is a `typing.Protocol` that describes
what the use case needs from the outside world (files, git, a terminal) without saying how it is
done. Adapters in `sdd.infrastructure` implement the ports; `sdd.bootstrap` plugs them in.
This is the dependency-inversion principle: policy does not depend on detail.
"""
