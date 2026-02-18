from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .database import EngineDatabases, initialize_databases, run_query


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
