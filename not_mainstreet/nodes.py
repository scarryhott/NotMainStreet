from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NodeState(str, Enum):
    POTENTIAL = "potential"
    ANCHORED = "anchored"
    TRUSTED = "trusted"


TRANSITIONS: dict[NodeState, set[NodeState]] = {
    NodeState.POTENTIAL: {NodeState.ANCHORED},
    NodeState.ANCHORED: {NodeState.POTENTIAL, NodeState.TRUSTED},
    NodeState.TRUSTED: {NodeState.ANCHORED},
}

COMMIT_ELIGIBLE = {NodeState.ANCHORED, NodeState.TRUSTED}


@dataclass
class NodeRecord:
    node_id: str
    state: NodeState = NodeState.POTENTIAL

    def transition(self, next_state: NodeState) -> None:
        allowed = TRANSITIONS[self.state]
        if next_state not in allowed:
            raise ValueError(f"invalid transition: {self.state} -> {next_state}")
        self.state = next_state

    @property
    def can_commit(self) -> bool:
        return self.state in COMMIT_ELIGIBLE
