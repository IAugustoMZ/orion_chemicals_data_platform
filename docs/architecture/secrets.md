# Secrets register

Runtime secrets live as files in `deploy/secrets/`, which is **git-ignored** and mounted into
services as Docker Compose `secrets:` (RT36, [security.md](../../harness/security.md#2-secrets-rt36)).
Coding agents are blocked from reading or writing that folder (permission rule in
`.claude/settings.json` and the agent guard), so its documentation lives here instead.

There are no secrets yet. Each dossier that introduces one adds a row below, in the same change:

| File in `deploy/secrets/` | Used by | What it is | How to create it | Rotation | Revocation |
|---|---|---|---|---|---|
| | | | | | |

Rule for every row: rotating the secret means replacing the file and restarting the service,
**never changing code** (the RT36 verification: "replace a test credential without changing code").
