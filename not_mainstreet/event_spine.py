from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .database import run_query
from .nodes import NodeRecord, NodeState


VALID_VERIFICATION_CLASSES = {
    "presence_check",
    "signed_witness",
    "local_asset_ping",
    "other_policy_approved",
}


@dataclass
class Event:
    event_type: str
    payload: dict[str, Any]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )


class EventSpine:
    """Append-only event spine with node-state enforcement for commit actions."""

    def __init__(self, *, inside_db_path: str | None = None) -> None:
        self.events: list[Event] = []
        self.nodes: dict[str, NodeRecord] = {}
        self.inside_db_path = inside_db_path

    def append(self, event_type: str, payload: dict[str, Any]) -> Event:
        event = Event(event_type=event_type, payload=payload)
        self.events.append(event)
        self._persist(event)
        self._apply(event)
        return event

    def _persist(self, event: Event) -> None:
        if not self.inside_db_path:
            return
        run_query(
            self.inside_db_path,
            "INSERT INTO engine_events (event_type, payload_json, created_at) VALUES (?, ?, ?)",
            (event.event_type, json.dumps(event.payload), event.timestamp),
        )

    def _apply(self, event: Event) -> None:
        if event.event_type == "NodeRegistered":
            node_id = event.payload["node_id"]
            self.nodes[node_id] = NodeRecord(node_id=node_id, state=NodeState.POTENTIAL)
            return

        if event.event_type == "NodeTransitioned":
            node = self.nodes[event.payload["node_id"]]
            node.transition(NodeState(event.payload["next_state"]))
            return

        if event.event_type == "AnchorEvent":
            self._apply_anchor_event(event.payload)
            return

        if event.event_type == "ProposalCommitRequested":
            node = self.nodes[event.payload["node_id"]]
            if not node.can_commit:
                raise PermissionError(
                    f"node {node.node_id} in state {node.state} cannot progress intent->commit"
                )

    def _apply_anchor_event(self, payload: dict[str, Any]) -> None:
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
        missing = sorted(required - set(payload))
        if missing:
            raise ValueError(f"AnchorEvent missing required fields: {', '.join(missing)}")
        if payload["event_type"] != "AnchorEvent":
            raise ValueError("AnchorEvent.event_type must be 'AnchorEvent'")
        if payload["verification_class"] not in VALID_VERIFICATION_CLASSES:
            raise ValueError("AnchorEvent.verification_class is invalid")
        if not isinstance(payload["witnesses"], list) or not all(isinstance(w, str) and w for w in payload["witnesses"]):
            raise ValueError("AnchorEvent.witnesses must be a non-empty string list")
        if not payload["node_id"] or payload["node_id"] not in self.nodes:
            raise ValueError("AnchorEvent.node_id must reference a registered node")
        datetime.fromisoformat(payload["occurred_at"].replace("Z", "+00:00"))

        node = self.nodes[payload["node_id"]]
        if node.state == NodeState.POTENTIAL:
            self.append("NodeTransitioned", {"node_id": node.node_id, "next_state": NodeState.ANCHORED.value})

    def for_type(self, event_type: str) -> list[Event]:
        return [e for e in self.events if e.event_type == event_type]
