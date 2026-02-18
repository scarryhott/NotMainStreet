from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .nodes import NodeRecord, NodeState


@dataclass
class Event:
    event_type: str
    payload: dict[str, Any]
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )


class EventSpine:
    """Append-only event spine with node-state enforcement for commit actions."""

    def __init__(self) -> None:
        self.events: list[Event] = []
        self.nodes: dict[str, NodeRecord] = {}

    def append(self, event_type: str, payload: dict[str, Any]) -> Event:
        event = Event(event_type=event_type, payload=payload)
        self.events.append(event)
        self._apply(event)
        return event

    def _apply(self, event: Event) -> None:
        if event.event_type == "NodeRegistered":
            node_id = event.payload["node_id"]
            self.nodes[node_id] = NodeRecord(node_id=node_id, state=NodeState.POTENTIAL)
            return

        if event.event_type == "NodeTransitioned":
            node = self.nodes[event.payload["node_id"]]
            node.transition(NodeState(event.payload["next_state"]))
            return

        if event.event_type == "ProposalCommitRequested":
            node = self.nodes[event.payload["node_id"]]
            if not node.can_commit:
                raise PermissionError(
                    f"node {node.node_id} in state {node.state} cannot progress intent->commit"
                )

    def for_type(self, event_type: str) -> list[Event]:
        return [e for e in self.events if e.event_type == event_type]
