#!/usr/bin/env python3
"""Validate contract examples against implementation rules without external deps."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def _parse_dt(value: str) -> None:
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_anchor_event(doc: dict) -> None:
    required = {
        "event_type",
        "node_id",
        "verification_class",
        "evidence_pointer",
        "witnesses",
        "signer",
        "occurred_at",
        "policy_version",
    }
    assert set(doc) == required, f"anchor_event keys mismatch: {set(doc)}"
    assert doc["event_type"] == "AnchorEvent"
    assert doc["verification_class"] in {
        "presence_check",
        "signed_witness",
        "local_asset_ping",
        "other_policy_approved",
    }
    assert isinstance(doc["witnesses"], list)
    assert all(isinstance(x, str) and x for x in doc["witnesses"])
    _parse_dt(doc["occurred_at"])


def validate_relational_artifact(doc: dict) -> None:
    required = {
        "artifact_id",
        "event_type",
        "edge_id",
        "participants",
        "region",
        "surplus_metrics",
        "created_at",
        "status",
        "policy_version",
    }
    assert set(doc) == required, f"relational_artifact keys mismatch: {set(doc)}"
    assert doc["event_type"] == "RelationalArtifactCreated"
    assert isinstance(doc["participants"], list) and len(doc["participants"]) >= 2
    assert doc["status"] in {"active", "decayed", "revoked"}
    metrics = doc["surplus_metrics"]
    assert set(metrics) == {"trust_delta", "co_learning_score", "resource_reuse_unlocked"}
    assert all(isinstance(metrics[k], (int, float)) for k in metrics)
    _parse_dt(doc["created_at"])


def validate_continuity_constraint(doc: dict) -> None:
    required = {"epsilon_x", "epsilon_y", "policy_version"}
    assert set(doc) == required, f"continuity keys mismatch: {set(doc)}"
    assert isinstance(doc["epsilon_x"], (int, float)) and doc["epsilon_x"] > 0
    assert isinstance(doc["epsilon_y"], (int, float)) and doc["epsilon_y"] > 0




def validate_cdm(doc: dict) -> None:
    required = {"schema_version", "document_id", "metadata", "content"}
    assert required.issubset(doc.keys()), f"cdm missing keys: {required - set(doc.keys())}"
    assert isinstance(doc["document_id"], str) and doc["document_id"]
    assert isinstance(doc["schema_version"], str) and doc["schema_version"]
    assert isinstance(doc["metadata"], dict)
    assert isinstance(doc["content"], dict)

def validate_node_state_machine(doc: dict) -> None:
    assert doc["states"] == ["potential", "anchored", "trusted"]
    assert doc["commit_eligible_states"] == ["anchored", "trusted"]
    expected = {
        "potential": ["anchored"],
        "anchored": ["potential", "trusted"],
        "trusted": ["anchored"],
    }
    assert doc["allowed_transitions"] == expected


def main() -> None:
    validate_anchor_event(_load("examples/anchor_event.example.json"))
    validate_relational_artifact(_load("examples/relational_artifact.example.json"))
    validate_continuity_constraint(_load("examples/continuity_constraint.example.json"))
    validate_node_state_machine(_load("contracts/node_state_machine.json"))
    validate_cdm(_load("examples/cdm.example.json"))
    print("All contract examples validated successfully.")


if __name__ == "__main__":
    main()
