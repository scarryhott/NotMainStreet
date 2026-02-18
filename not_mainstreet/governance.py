from __future__ import annotations

from dataclasses import dataclass

from .nodes import NodeState


@dataclass(frozen=True)
class SovereigntyContext:
    trust_score: float
    tenure_score: float


def sovereignty_weight(state: NodeState, context: SovereigntyContext) -> float:
    """Compute a bounded governance influence scalar S(i,j,t,c) in [0,1]."""
    state_base = {
        NodeState.POTENTIAL: 0.0,
        NodeState.ANCHORED: 0.25,
        NodeState.TRUSTED: 0.5,
    }[state]
    raw = state_base + (0.35 * context.trust_score) + (0.15 * context.tenure_score)
    return max(0.0, min(1.0, raw))
