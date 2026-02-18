# NotMainStreet

NotMainStreet is a conceptual and technical architecture for local coordination between human communities and AI assistants, framed as a proof-style/global algorithm system (dual-graph validity, sovereignty fields, and auditable event trajectories).

## Repository contents

This repository currently contains:

- Foundation documents:
  - `MainStreet_Updated.docx`
  - `MainStreet_RevisedFoundations.docx`
  - `MainStreet_FrictionSacrifice.docx`
- Canonical technical spec:
  - `TECHNICAL_SPEC_DOCX_INTEGRATION.md`
- Implementation scaffolding:
  - `not_mainstreet/`
  - `contracts/`, `examples/`, `scripts/`, `tests/`, `fixtures/docx/`

## Canonical technical specification

The authoritative integration spec is:

- `TECHNICAL_SPEC_DOCX_INTEGRATION.md`

It defines normative precedence and implementation contracts for DOCX -> CDM -> adapter publication.

## Implementation roadmap

1. DOCX ingestion pipeline (`docx_ingest.py`) with security and checksum registration.
2. Deterministic canonicalization and CDM registration (`canonicalization.py`, `cdm.py`).
3. Adapter fan-out publication (`adapters/kantian_ivi.py`, `adapters/feigenbuam.py`) in **Git mode first**.
4. Orchestration, replay, and invariant enforcement (`orchestrator.py`, `event_spine.py`, `coordination.py`, `philosophy_runtime.py`).
5. CI and contract checks (`tests/`, `scripts/validate_contract_examples.py`).

## Local checks

- `python -m unittest discover -s tests -v`
- `python scripts/validate_contract_examples.py`


### Philosophy runtime checks

- `python -m unittest tests.test_philosophy_runtime -v`


## Portal interface and databases

- Outside portal DB: `data/outside_portal.db` (community submissions).
- Inside IVI DB: `data/inside_ivi.db` (engine events + relational artifacts).
- Bridge runtime: `not_mainstreet/portal.py` + `not_mainstreet/database.py`.
- Test: `python -m unittest tests.test_portal_database -v`.

- Run portal API/UI server: `python scripts/run_portal.py --host 127.0.0.1 --port 8765`


## Remaining implementation planning

- Cross-repo implementation plan: `REMAINING_IMPLEMENTATION_PLAN.md`
- Target integration matrix template: `contracts/target_integration_matrix.yaml`

- Verify external integration readiness (after matrix is filled): `python scripts/verify_integration_readiness.py`

- Validate target integration matrix schema: `python scripts/validate_target_integration_matrix.py`

- Locational density privacy checks: `python -m unittest tests.test_location_privacy -v`

- Assistant refinement endpoint (OpenClaw/Purple pattern): `POST /api/assistant/refine` via `not_mainstreet/portal_server.py`.


## Empathy system soul

- Manifesto document: `EMPATHY_MANIFESTO.md`
- Empathy endpoint: `POST /api/assistant/empathy`

- Security-as-field framing: see `EMPATHY_MANIFESTO.md` and spec section "Security as Living Field Condition".
