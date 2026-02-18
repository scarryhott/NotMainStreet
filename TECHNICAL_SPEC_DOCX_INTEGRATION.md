# Technical Specification: Not MainStreet DOCX Integration with `kantian-ivi` and `feigenbuam`

## 1) Purpose

Define an implementation-ready DOCX ingestion and publication layer that:

- Converts source documents into a durable Canonical Document Model (CDM).
- Publishes consistent, replayable outputs to `kantian-ivi` and `feigenbuam`.
- Aligns with Not MainStreet's dual-graph and self-viewing foundations:
  - **Dual validity gate**: proposals must satisfy noumenal and phenomenal constraints.
  - **Failure as signal**: deadlock/infeasibility are diagnostic states, not discarded errors.
  - **Correctness as trajectory**: each processing cycle should increase usable coordination potential.

---

## 2) Source Alignment (Three Input Docs)

This specification integrates three source documents and resolves framing conflicts as follows:

1. **MainStreet_Updated** (build blueprint)
   - Supplies system decomposition and implementation modules.
2. **MainStreet_FrictionSacrifice** (philosophical debt)
   - Adds explicit compensation mechanisms for lost physical verification.
3. **MainStreet_RevisedFoundations** (self-viewing correction)
   - Overrides any static-identity framing: identity is earned through participation.

### 2.1 Normative precedence
- If there is conflict, precedence is:
  1) RevisedFoundations
  2) FrictionSacrifice
  3) Updated

---

## 3) Scope

### In scope
- DOCX ingestion, validation, parsing, normalization, publication.
- Asset extraction and lifecycle management.
- Reference extraction/resolution policies.
- Contracted publication to `kantian-ivi` and `feigenbuam`.
- Replay, idempotency, observability, and audit lineage.

### Out of scope
- Collaborative DOCX editing.
- Non-DOCX parsing (PDF/ODT) beyond extension points.
- End-user UI design (this spec is service/API contract focused).

---

## 4) Architectural Overview

Pipeline:

```text
Ingestion -> Security Gate -> Parse -> Normalize -> Validate ->
State Machine Orchestrator -> Adapter(kantian-ivi) + Adapter(feigenbuam) -> Observe -> Replay
```

### 4.1 Core modules
- `nodes.py`: node identity, participation events, embedding activation gates.
- `graphs.py`: noumenal + phenomenal graph access; dual matrix compatibility checks.
- `governance.py`: sovereignty field calculations `S(i,j,t,c) in [0,1]` with decay rules.
- `coordination.py`: proposal feasibility and cross-graph validity.
- `rewards.py`: integration incentives (Integration Score, LVRR, Trust Premium, Craft Bonus).
- `event_spine.py`: append-only event stream for diagnostics, replay, and continuity analysis.

---

## 5) Canonical Document Model (CDM)

The CDM is the single internal source of truth.

### 5.1 Schema (illustrative)

```json
{
  "schema_version": "cdm/v1",
  "document_id": "string",
  "version": 12,
  "cdm_hash": "sha256",
  "source": {
    "filename": "string",
    "checksum_sha256": "string",
    "uploaded_at": "ISO-8601",
    "uploaded_by": "principal-id"
  },
  "provenance": {
    "parser_version": "string",
    "normalizer_version": "string",
    "adapter_versions": {
      "kantian-ivi": "string",
      "feigenbuam": "string"
    }
  },
  "metadata": {
    "title": "string",
    "authors": ["string"],
    "tags": ["string"],
    "language": "string",
    "summary": "string"
  },
  "structure": {
    "toc": [],
    "hierarchy": []
  },
  "content": {
    "blocks": [
      {
        "block_id": "string",
        "type": "heading|paragraph|list|table|image|reference|footnote|equation",
        "level": 1,
        "text": "string",
        "items": ["string"],
        "table": {"rows": []},
        "image": {"asset_id": "sha256", "alt": "string"}
      }
    ]
  },
  "references": [
    {
      "ref_id": "string",
      "label": "string",
      "target": "string",
      "kind": "internal|external|citation|footnote",
      "resolved": true
    }
  ],
  "assets": [
    {
      "asset_id": "sha256",
      "mime": "string",
      "size_bytes": 1234,
      "dimensions": "optional",
      "source_location": "docx-part-path"
    }
  ]
}
```

### 5.2 Identity and version semantics
- `document_id`: stable logical identity.
- `version`: monotonic integer assigned by orchestrator per `document_id`.
- `cdm_hash`: hash of normalized CDM content (excluding operational timestamps).
- If `cdm_hash` is unchanged, publication is idempotent and does not increment `version`.
- Formatting-only DOCX deltas that do not change normalized CDM must not churn versions.

### 5.3 Schema evolution policy
- CDM versions are explicit (`schema_version`).
- Backward compatibility guaranteed within major version.
- Breaking changes require migration playbook and adapter compatibility matrix.

---

## 6) Asset Service Specification

DOCX embedded assets are first-class entities.

### 6.1 Extraction coverage
- Images, charts (rendered fallback), equations (MathML/text fallback), OLE placeholders, hyperlinks, footnotes/endnotes.

### 6.2 Storage and addressing
- Content-addressable object store using SHA-256 as `asset_id`.
- Deduplicated storage across documents/versions.
- Metadata persisted: MIME, bytes, dimensions (if media), source docx part, extraction status.

### 6.3 Access policy
- Private by default.
- Signed URL access when downstream systems require retrieval.
- Retention follows document lifecycle policy.

### 6.4 Limits
- Max DOCX size: 50 MB (configurable).
- Max single embedded asset: 10 MB (configurable).
- Parsing timeout: 30 seconds/doc typical path; hard timeout 120 seconds.

---

## 7) Security and Content Controls

### 7.1 Mandatory controls
- Antivirus scan prior to parsing.
- Macro policy: reject or strip VBA macros (default: reject with actionable diagnostic).
- External links: sanitize and classify (`trusted`, `untrusted`, `blocked`).
- Metadata scrubbing option for author/revision history.
- PII handling hooks (classification tags and downstream redaction contract).

### 7.2 Trust-preserving framing
In line with FrictionSacrifice:
- Security checks are compensatory friction that replace lost physical verification.
- Rejections are auditable state transitions, not silent drops.

---

## 8) Reference Resolution Rules

Supported references:
- Internal anchors/bookmarks.
- Cross-document links.
- Citations, footnotes, endnotes, bibliography fields.

Resolution behavior:
- Internal references must resolve at parse time or emit `broken_internal_reference` diagnostics.
- External links are retained with trust classification and optional allowlist filtering.
- Cross-document links unresolved at ingest are marked `deferred` and eligible for replay resolution.

---

## 9) Integration Contract: `kantian-ivi`

### 9.1 Responsibility
User-facing rendering/interaction contract for structured documents.

### 9.2 Output requirements
- Preserve heading hierarchy + anchors.
- Preserve inline semantics (bold/italic/code).
- Preserve tables and asset bindings.
- Include dual-graph validation metadata when relevant to community coordination modules.

### 9.3 Delivery modes
- API mode: `POST /documents`, `PUT /documents/{id}`.
- Git mode: artifact path contract (e.g., `content/docs/{document_id}.json`).

### 9.4 Failure semantics
- 4xx contract mismatch -> terminal for that attempt, diagnostic retained.
- 5xx/transport -> retry with exponential backoff + jitter.

---

## 10) Integration Contract: `feigenbuam`

### 10.1 Responsibility
Search, indexing, graph analytics, and semantic retrieval payloads.

### 10.2 Output requirements
- Heading-aware chunking.
- Reference graph extraction.
- Search fields (title, summary, tags, chunked body).
- Optional enrichment hooks (embeddings/topic labels) behind feature flag.

### 10.3 Delivery modes
- API mode: bulk upsert with idempotency key.
- Git mode: artifact path contract (e.g., `index/documents/{document_id}-{version}.json`).

### 10.4 Failure semantics
- Payload errors retained with diagnostics; source document remains replayable.
- Partial success is permitted with per-target status accounting.

---

## 11) Ordering, Consistency, and Fan-out Model

Publication uses **independent fan-out** (recommended):
- `kantian-ivi` and `feigenbuam` are independently retried and independently replayable.
- No cross-target distributed transaction.
- Global document status is complete only when both targets reach success (or policy-approved terminal state).

Rationale:
- Maximizes availability.
- Prevents one target outage from blocking the other.

---

## 12) Workflow State Machine

```text
UPLOADED
-> SECURITY_VALIDATED
-> PARSED
-> CDM_VALID
-> PUBLISH_PENDING
-> PUBLISHED_KANTIAN_IVI (optional intermediate)
-> PUBLISHED_FEIGENBUAM (optional intermediate)
-> COMPLETE

Failure branches:
FAILED_SECURITY | FAILED_PARSE | FAILED_CDM_VALIDATION |
FAILED_PUBLISH_KANTIAN_IVI | FAILED_PUBLISH_FEIGENBUAM
```

State properties:
- Every transition appends to `event_spine`.
- Failure states are replayable where safe.
- Continuity gaps are marked unknown (never treated as neutral no-op).

---

## 13) Observability and Lineage

### 13.1 Metrics
- `ingest_success_total`, `ingest_failure_total`
- `parse_duration_ms`
- `publish_duration_ms{target}`
- `publish_failures_total{target}`
- `replay_total`
- `state_transition_total{from,to}`

### 13.2 Logs and traces
- Correlation ID across full pipeline.
- Structured taxonomy: `validation_error`, `contract_error`, `transport_error`, `security_error`.
- Include parser/adapter versions for reproducibility.

### 13.3 Alerts
- Per-target failure rate threshold.
- Queue/backlog saturation.
- Replay storm / rate-limit activation.

---

## 14) Testing Strategy

1. **Unit tests**
   - Parse blocks, assets, references, footnotes, equations.
   - Version semantics and idempotency checks.
2. **Contract tests**
   - Validate emitted payloads against `kantian-ivi` and `feigenbuam` schemas.
3. **Integration tests**
   - End-to-end ingest with representative DOCX corpus.
4. **Failure injection**
   - API 5xx/timeouts; malformed payloads; broken references.
5. **Security tests**
   - Macro-bearing DOCX, malicious links, metadata scrubbing.
6. **Load tests**
   - Large document and replay burst scenarios with backpressure assertions.

---

## 15) Rate Limiting, Backpressure, and Capacity

- Token-bucket upload rate limits per tenant/project.
- Queue depth thresholds trigger controlled admission.
- Replay jobs are priority-limited to avoid starving new ingest.
- Parser workers scale horizontally; memory limits enforce safe failover.

---

## 16) Rollout Plan

1. **Pilot (<=300 users)**
   - Single-neighborhood deployment, baseline observability, manual replay.
2. **Multi-community mesh**
   - Enable dual-target fan-out and policy automation.
3. **Regional scale**
   - Harden SLOs, backpressure, and lineage audits.
4. **Formal verification track**
   - Lean proofs for invariants (idempotency, monotonic versioning, replay safety).
5. **Federation readiness**
   - Multi-domain contracts and governance interoperability.

---

## 17) Open Decisions

- Confirm exact endpoint/auth contracts for both target repos.
- Confirm whether `feigenbuam` spelling is canonical repository name.
- Finalize PII classification obligations per deployment jurisdiction.
- Finalize accepted DOCX feature subset for GA.

---

## 18) Acceptance Criteria

- DOCX ingest produces valid CDM with deterministic `cdm_hash`.
- Asset extraction, deduplication, and access controls are enforced.
- Independent publication to `kantian-ivi` and `feigenbuam` is observable and replayable.
- State machine transitions are auditable through `event_spine`.
- Security controls (macro policy, link sanitization, metadata handling) are enforced.
- Reprocessing same normalized content is idempotent (no unintended version churn).

---

## 19) Seam Resolution Addendum (Verification Floor, Laplacian Role, Relational Surplus)

This section is normative and closes the three previously unresolved seams.

### 19.1 Verification floor via tiered anchoring

Define explicit node lifecycle states:

```text
NodeState = { potential, anchored, trusted }
```

State semantics:
- `potential`: node exists only in the noumenal graph; eligible for observation, not for initiating intent->commit transitions.
- `anchored`: node has at least one verifiable physical trace and is placed in phenomenal space with low sovereignty weight.
- `trusted`: node has accrued trust through interactions/attestations/resource transfers and receives expanded gate permissions.

Required transitions:
- `potential -> anchored`: requires `AnchorEvent` with valid evidence pointer.
- `anchored -> trusted`: requires trust accrual threshold policy.
- `trusted -> anchored` or `anchored -> potential`: allowed through decay/revocation policy with audit trail.

Operational enforcement:
- `event_spine.py` MUST enforce that only `anchored` or `trusted` nodes can progress proposals from intent to commit.
- `governance.py` MUST compute sovereignty as a function of state and trust history.

### 19.2 Anchor event contract

Add a first-class event schema:

```json
{
  "event_type": "AnchorEvent",
  "node_id": "string",
  "verification_class": "presence_check|signed_witness|local_asset_ping|other_policy_approved",
  "evidence_pointer": "uri-or-content-address",
  "witnesses": ["principal-id"],
  "signer": "principal-id",
  "occurred_at": "ISO-8601",
  "policy_version": "string"
}
```

Validation rules:
- Missing `evidence_pointer` => reject transition.
- Unknown `verification_class` => reject unless policy explicitly allows.
- All rejections MUST be persisted as diagnosable events (never silent).

### 19.3 Laplacian separation: diagnostic vs continuity constraint

Split operator responsibilities into two explicit objects:

1. `L_diag` (diagnostic only, in `graphs.py`)
   - Computed continuously for topology health.
   - Reported via telemetry (e.g., smoothness/drift indicators).
   - Never directly used as optimization objective unless policy explicitly opts in.

2. `C_continuity` (enforced constraint, in `coordination.py`)
   - Per-step embedding movement bounds:
     - `||Δx_i|| <= ε_x` (noumenal)
     - `||Δy_i|| <= ε_y` (phenomenal)
   - Violations are policy failures during proposal validation.

Objective framing:

```text
minimize  alpha * ||A - f(X)||^2 + beta * Penalty(C_continuity violations)
telemetry reports x^T L_diag x as health metric
```

Policy bridge (optional):
- Governance MAY condition gate openings on diagnostic thresholds (e.g., smoothness < theta), but this is a policy layer, not a mathematical identity.

### 19.4 Relational surplus as first-class object ("1+1=3")

Introduce `RelationalArtifact` in the event spine.

Creation rule:
- Create on successful assignment commit with legitimacy checks passed.

Schema:

```json
{
  "artifact_id": "string",
  "event_type": "RelationalArtifactCreated",
  "edge_id": "string",
  "participants": ["node-id"],
  "region": "locality-id",
  "surplus_metrics": {
    "trust_delta": 0.0,
    "co_learning_score": 0.0,
    "resource_reuse_unlocked": 0.0
  },
  "created_at": "ISO-8601",
  "status": "active|decayed|revoked",
  "policy_version": "string"
}
```

Graph extension:
- Model as bipartite augmentation: `actor nodes <-> relational artifact nodes`.
- Artifacts are referenceable capabilities for future coordination.
- Artifacts have lifecycle controls (decay, renewal, revocation).

Rewards/governance usage:
- `rewards.py` MAY compute surplus dividend from active artifact set.
- `governance.py` MAY require specific artifact classes before high-risk task gates open.

### 19.5 Minimal contract changes required for implementation readiness

The following are mandatory additions:
- `NodeState` and transition events persisted in `event_spine`.
- `AnchorEvent` schema + validation rules.
- `ContinuityConstraint` parameters (`ε_x`, `ε_y`) + enforcement point in coordination validation.
- `RelationalArtifact` schema + lifecycle rules + queryability for rewards/governance.

These additions resolve the contradictions without changing the core IVI / Not MainStreet philosophy.

