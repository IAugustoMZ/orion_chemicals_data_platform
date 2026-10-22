# Security baseline

The security rules every specification, implementation and review applies. They come from the
requirements (RT01, RT35-RT38, RT41), from the references the catalogue cites (NIST SP 800-82
for operational technology, NIST SP 800-53 for access, audit and continuity) and from OWASP
practice. This is a local research platform, but it is built as if the data were real: the
habits are the point.

## 1. Industrial systems are read-only (RT01)

- Every integration with an industrial source uses an authorised **read** interface. No
  credential that can issue commands or change the industrial system is ever configured.
- Each integration's spec includes a test that **a write attempt is denied**.
- Simulated sources in Docker Compose expose the same read-only contract as the real ones.

## 2. Secrets (RT36)

- **No credential in code, configuration files, documents, test data or images.** detect-secrets
  runs in pre-commit and in G5 (`.secrets.baseline` holds reviewed false positives only).
- Runtime secrets are **Docker Compose secrets** read from files under `deploy/secrets/`
  (git-ignored, off-limits to agents; each one is documented in the
  [secrets register](../docs/architecture/secrets.md)) or environment variables documented in
  `.env.example` with placeholder values.
- Every secret has a written procedure for use, **rotation and revocation**; rotating one must
  not need a code change (the RT36 verification).
- Agents never read or write secret files (the agent guard blocks it).

## 3. Least privilege (RT35)

- Every technical identity (service, job, database role) and every human profile gets only the
  permissions its function needs. Specs list the identities they introduce and their grants.
- Database access from services goes through views and routines of a dedicated schema, with roles
  that hold no table privileges (the pattern of the reference platform).
- Containers run as a non-root user, with all Linux capabilities dropped, `no-new-privileges`,
  a read-only root filesystem where possible, and ports bound to `127.0.0.1` only.

## 4. Inputs and outputs

- Every input from outside the process (HTTP, files, messages, environment) is validated at the
  boundary (interfaces layer) into typed values before it reaches a use case.
- Queries are parameterised; identifiers come from a whitelist; subprocesses get argument lists,
  never a shell string.
- Errors returned to callers never include stack traces, credentials or internal paths.
- YAML is parsed with `yaml.safe_load` only; nothing is deserialised with `pickle` or `eval`.

## 5. Audit (RT38)

Changes to mappings, rules, permissions and manual reprocessing record **actor, time, reason and
before/after**. The harness applies the same idea to itself: every approval records the member,
the UTC time, the digest of what was approved, the git identity and an optional note.

## 6. Data protection (RT37) and continuity (RT41)

- Connections and storage use protection compatible with the data's classification; the
  classification of each dataset is stated in the spec that introduces it.
- Backups and restore tests of data and metadata are specified before any real operation; the
  acceptable loss and recovery time are agreed with us first.

## 7. Supply chain

- Dependencies are pinned in `poetry.lock`; `pip-audit` runs in G5.
- Container base images are official and pinned to a version (`python:3.12-slim`); a spec that
  adds an image names its source.
- Agent-facing configuration (`.claude/settings.json`, skills, hooks) is governed: it changes
  only through a dossier, and the guardrail files only by people.

## 8. Threat modelling in every spec

Every `spec.md` has a STRIDE table. Ask, for each new component, interface or data flow:

| Letter | Threat | Typical question here |
|---|---|---|
| S | Spoofing | Can something pretend to be a source, a user or a service? |
| T | Tampering | Can received data, a rule or an approval be altered unnoticed? |
| R | Repudiation | Could someone deny a change? Is it in the audit record? |
| I | Information disclosure | Can restricted data or a credential leak through logs, errors or exports? |
| D | Denial of service | Can a large query or a stuck source exhaust the platform? (RT06, RT31) |
| E | Elevation of privilege | Can a read-only identity write? Can an agent approve? |

The review in phase 6 verifies every row (`validation.md`, "Security review").
