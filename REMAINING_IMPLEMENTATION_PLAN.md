# Remaining Implementation Plan for `kantian-ivi` and `feigenbuam` Integration

## Research status

Direct repository inspection for `kantian-ivi` and `feigenbuam` is currently blocked from this runtime environment (GitHub responses are forbidden without authenticated access in this environment).

Attempted commands:

- `git ls-remote https://github.com/scarryhott/kantian-ivi.git`
- `git ls-remote https://github.com/scarryhott/Kantian-IVI.git`
- `git ls-remote https://github.com/scarryhott/feigenbuam.git`
- `git ls-remote https://github.com/scarryhott/Feigenbuam.git`
- `curl -L -I https://github.com/search?q=kantian-ivi&type=repositories`
- `curl -L -I https://github.com/search?q=feigenbuam&type=repositories`

Despite this, the remaining implementation can be specified concretely with a contract-first plan.

---

## Current baseline already implemented in this repo

- Git-mode orchestrator fan-out to two adapters.
- Deterministic CDM hashing and versioning.
- Inside/outside IVI dual databases.
- Portal API/UI and sync bridge.
- Seam runtime (verification floor, continuity, dual gate, relational artifact emission).

---

## Remaining implementation work (contract-first)

### 1) Finalize target repository identity and ownership

- Confirm canonical URLs and owners for:
  - `kantian-ivi`
  - `feigenbuam`
- Record branch strategy and protected-branch expectations.

### 2) Lock integration contract per target

For each repo, define (and version):

- Delivery mode: `git` (current default) and optional `api`.
- Artifact path conventions.
- Required fields and schema.
- Compatibility matrix by `schema_version`.

### 3) Implement adapter contract serializers

In `not_mainstreet/adapters/`:

- Convert draft payload shape into strict contract serializer classes.
- Add contract validation before publish.
- Add per-target replay cursor metadata.

### 4) Add repository writer/pusher for Git mode

- Stage adapter outputs in a working tree clone.
- Commit with deterministic message template.
- Push via service identity.
- Handle retries and non-fast-forward conflicts.

### 5) Add API mode implementation (optional phase 2)

- HTTP clients with auth plug-ins (token/OIDC).
- Idempotency keys and response auditing.
- Circuit-breaker and backoff policy.

### 6) Build schema contract tests tied to real target schemas

- Pull official schema fixtures from each target repo.
- Validate emitted payloads in CI.
- Snapshot tests for stable serialization.

### 7) Add end-to-end replay verification

- Trigger replay from failed bridge states.
- Confirm no version churn when `cdm_hash` unchanged.
- Confirm cross-target status convergence semantics.

### 8) Add production operations support

- Adapter health dashboard.
- Dead-letter queue for publish failures.
- Runbooks for sync outages and policy migrations.

---

## Immediate unblock checklist (when access is available)

1. Clone both target repos.
2. Extract their current contract files / endpoint docs.
3. Populate `contracts/target_integration_matrix.yaml` with exact paths/schemas/endpoints.
4. Replace placeholder adapter payloads in `not_mainstreet/adapters/*.py` with strict target mappings.
5. Add CI job that validates against pinned target schema commits.


## When Repo Access Becomes Available — Unblock Checklist

Execute in this order:

### Step 1 — Confirm repositories exist and are stable

- URL reachable
- License acceptable
- Maintenance status active

Suggested commands:

- `git ls-remote <repo_url>`
- inspect license file in target repo and record SPDX identifier
- check release/commit recency and open issues for maintenance signal

### Step 2 — Pin exact versions

- Record commit hashes in `contracts/target_integration_matrix.yaml`:
  - `sources.kantian_ivi.pinned.commit`
  - `sources.feigenbuam.pinned.commit`

### Step 3 — Extract schemas

Prefer machine-readable definitions:

- OpenAPI
- JSON Schema
- Protobuf
- Formal spec documents

Record in matrix:

- `schema.format`
- `schema.version`
- `schema.source_ref`

### Step 4 — Implement adapters

- Enforce strict deterministic transformation only.
- Validate output against pinned schemas before publish.
- Fail closed on contract mismatch.

### Step 5 — Run CI validation suite

Must pass before integration is considered complete:

- `python -m unittest discover -s tests -v`
- `python scripts/validate_contract_examples.py`
- `python scripts/verify_integration_readiness.py`


### Validator critical requirement

`pinned_commit` validation MUST confirm remote existence, not just hash shape.

- Preferred: `git ls-remote <url> <hash>` and require a match.
- Fallback: `git fetch --depth=1 origin <hash>` in a temporary repository and require success.
