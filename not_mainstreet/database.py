from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class EngineDatabases:
    inside_path: str = "data/inside_ivi.db"
    outside_path: str = "data/outside_portal.db"


def _connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_databases(cfg: EngineDatabases = EngineDatabases()) -> None:
    inside_schema = """
    CREATE TABLE IF NOT EXISTS engine_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS relational_artifacts (
        artifact_id TEXT PRIMARY KEY,
        edge_id TEXT NOT NULL,
        participants_json TEXT NOT NULL,
        surplus_metrics_json TEXT NOT NULL,
        status TEXT NOT NULL,
        policy_version TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """

    outside_schema = """
    CREATE TABLE IF NOT EXISTS portal_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        submitted_at TEXT NOT NULL,
        processed INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS edge_proposals (
        proposal_id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        community_id TEXT NOT NULL,
        idempotency_key TEXT,
        payload_json TEXT NOT NULL,
        evaluation_json TEXT NOT NULL,
        gate_outcome TEXT NOT NULL,
        routing_class TEXT NOT NULL,
        status TEXT NOT NULL,
        proposal_version INTEGER NOT NULL,
        engine_version TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_edge_proposals_tenant_idempotency
      ON edge_proposals (tenant_id, idempotency_key)
      WHERE idempotency_key IS NOT NULL;

    CREATE INDEX IF NOT EXISTS idx_edge_proposals_tenant_created
      ON edge_proposals (tenant_id, created_at DESC);

    CREATE INDEX IF NOT EXISTS idx_edge_proposals_tenant_gate
      ON edge_proposals (tenant_id, gate_outcome);

    CREATE INDEX IF NOT EXISTS idx_edge_proposals_tenant_routing
      ON edge_proposals (tenant_id, routing_class);

    CREATE TABLE IF NOT EXISTS proposal_bridge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER NOT NULL,
        proposal_id TEXT NOT NULL,
        status TEXT NOT NULL,
        synced_at TEXT NOT NULL,
        FOREIGN KEY(submission_id) REFERENCES portal_submissions(id)
    );
    """

    with _connect(cfg.inside_path) as conn:
        conn.executescript(inside_schema)
    with _connect(cfg.outside_path) as conn:
        conn.executescript(outside_schema)


def run_query(path: str, sql: str, params: Iterable[object] = ()) -> list[sqlite3.Row]:
    with _connect(path) as conn:
        cur = conn.execute(sql, tuple(params))
        rows = cur.fetchall()
        conn.commit()
        return rows
