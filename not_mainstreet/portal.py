from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .database import EngineDatabases, initialize_databases, run_query
from .edge_proposal import (
    What,
    When,
    Where,
    Who,
    Why,
    build_edge_proposal,
    proposal_to_dict,
)


@dataclass(frozen=True)
class Submission:
    user_id: str
    title: str
    body: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def submit_to_portal(submission: Submission, cfg: EngineDatabases = EngineDatabases()) -> int:
    initialize_databases(cfg)
    run_query(
        cfg.outside_path,
        """
        INSERT INTO portal_submissions (user_id, title, body, submitted_at, processed)
        VALUES (?, ?, ?, ?, 0)
        """,
        (submission.user_id, submission.title, submission.body, _now()),
    )
    row = run_query(cfg.outside_path, "SELECT id FROM portal_submissions ORDER BY id DESC LIMIT 1")
    return int(row[0]["id"])


def submit_edge_intake(
    *,
    proposal_id: str,
    tenant_id: str,
    community_id: str,
    session_id: str,
    who: dict[str, Any],
    why: dict[str, Any],
    what: dict[str, Any],
    where: dict[str, Any],
    when: dict[str, Any],
    thread_ref: str,
    idempotency_key: str | None = None,
    cfg: EngineDatabases = EngineDatabases(),
) -> dict[str, Any]:
    initialize_databases(cfg)

    if idempotency_key:
        existing = run_query(
            cfg.outside_path,
            "SELECT payload_json, evaluation_json FROM edge_proposals WHERE tenant_id = ? AND idempotency_key = ? LIMIT 1",
            (tenant_id, idempotency_key),
        )
        if existing:
            return {
                "proposal": json.loads(existing[0]["payload_json"]),
                "evaluation": json.loads(existing[0]["evaluation_json"]),
                "idempotent_replay": True,
            }

    proposal, evaluation = build_edge_proposal(
        proposal_id=proposal_id,
        tenant_id=tenant_id,
        community_id=community_id,
        session_id=session_id,
        who=Who(**who),
        why=Why(**why),
        what=What(**what),
        where=Where(**where),
        when=When(**when),
        thread_ref=thread_ref,
    )

    payload = proposal_to_dict(proposal)
    evaluation_payload = {
        "gate_results": {
            "gate_outcome": evaluation.gate_results.gate_outcome,
            "noumenal": evaluation.gate_results.noumenal,
            "phenomenal": evaluation.gate_results.phenomenal,
            "missing_fields": [s.__dict__ for s in evaluation.gate_results.missing_fields],
            "conflicts": [s.__dict__ for s in evaluation.gate_results.conflicts],
            "policy_blocks": [s.__dict__ for s in evaluation.gate_results.policy_blocks],
            "feasibility_blocks": [s.__dict__ for s in evaluation.gate_results.feasibility_blocks],
        },
        "routing_class": evaluation.routing_class,
        "routing_confidence": evaluation.routing_confidence,
        "routing_alternatives": [a.__dict__ for a in evaluation.routing_alternatives],
        "needs_disambiguation": evaluation.needs_disambiguation,
        "next_actions": evaluation.next_actions,
    }

    run_query(
        cfg.outside_path,
        """
        INSERT OR REPLACE INTO edge_proposals
        (proposal_id, tenant_id, community_id, idempotency_key, payload_json, evaluation_json,
         gate_outcome, routing_class, status, proposal_version, engine_version, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            proposal.proposal_id,
            proposal.tenant_id,
            proposal.community_id,
            idempotency_key,
            json.dumps(payload),
            json.dumps(evaluation_payload),
            proposal.gate_results.gate_outcome,
            proposal.routing_class,
            proposal.status,
            proposal.proposal_version,
            proposal.engine_version,
            proposal.created_at,
            proposal.updated_at,
        ),
    )

    return {"proposal": payload, "evaluation": evaluation_payload, "idempotent_replay": False}


def list_edge_intake(
    cfg: EngineDatabases = EngineDatabases(),
    *,
    tenant_id: str | None = None,
    gate_outcome: str | None = None,
    routing_class: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    initialize_databases(cfg)
    clauses = []
    params: list[Any] = []

    if tenant_id:
        clauses.append("tenant_id = ?")
        params.append(tenant_id)
    if gate_outcome:
        clauses.append("gate_outcome = ?")
        params.append(gate_outcome)
    if routing_class:
        clauses.append("routing_class = ?")
        params.append(routing_class)

    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        SELECT proposal_id, tenant_id, community_id, payload_json, evaluation_json, status,
               routing_class, gate_outcome, created_at, updated_at
        FROM edge_proposals
        {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    rows = run_query(cfg.outside_path, sql, params)
    out = []
    for r in rows:
        item = dict(r)
        item["payload"] = json.loads(item.pop("payload_json"))
        item["evaluation"] = json.loads(item.pop("evaluation_json"))
        out.append(item)
    return out


def list_unprocessed(cfg: EngineDatabases = EngineDatabases()) -> list[dict[str, Any]]:
    initialize_databases(cfg)
    rows = run_query(
        cfg.outside_path,
        "SELECT id, user_id, title, body, submitted_at FROM portal_submissions WHERE processed = 0 ORDER BY id ASC",
    )
    return [dict(r) for r in rows]


def sync_submission_to_engine(submission_id: int, cfg: EngineDatabases = EngineDatabases()) -> str:
    initialize_databases(cfg)
    rows = run_query(
        cfg.outside_path,
        "SELECT id, user_id, title, body, submitted_at FROM portal_submissions WHERE id = ?",
        (submission_id,),
    )
    if not rows:
        raise ValueError(f"submission {submission_id} not found")

    rec = dict(rows[0])
    proposal_id = f"proposal-{submission_id}"
    payload = {
        "proposal_id": proposal_id,
        "source": "outside_portal",
        "submission": rec,
    }
    run_query(
        cfg.inside_path,
        "INSERT INTO engine_events (event_type, payload_json, created_at) VALUES (?, ?, ?)",
        ("PortalSubmissionSynced", json.dumps(payload), _now()),
    )
    run_query(
        cfg.outside_path,
        "UPDATE portal_submissions SET processed = 1 WHERE id = ?",
        (submission_id,),
    )
    run_query(
        cfg.outside_path,
        "INSERT INTO proposal_bridge (submission_id, proposal_id, status, synced_at) VALUES (?, ?, ?, ?)",
        (submission_id, proposal_id, "synced", _now()),
    )
    return proposal_id


def render_portal_html(cfg: EngineDatabases = EngineDatabases()) -> str:
    pending = list_unprocessed(cfg)
    items = "".join(
        f"<li><b>#{p['id']}</b> {p['title']} — {p['user_id']}</li>" for p in pending
    ) or "<li>No pending submissions</li>"
    return f"""<!doctype html>
<html>
  <head><meta charset='utf-8'><title>NotMainStreet Portal</title></head>
  <body>
    <h1>NotMainStreet Portal Interface</h1>
    <p>Outside/inside IVI bridge is active.</p>
    <h2>Pending submissions</h2>
    <ul>{items}</ul>
  </body>
</html>"""
