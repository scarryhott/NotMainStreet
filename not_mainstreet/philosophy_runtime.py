from __future__ import annotations

from dataclasses import dataclass

from .coordination import ContinuityConstraint, validate_continuity
from .event_spine import EventSpine
from .governance import SovereigntyContext, sovereignty_weight
from .graphs import LaplacianDiagnostics
from .nodes import NodeState


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    initiator_node_id: str
    dx: float
    dy: float
    noumenal_valid: bool
    phenomenal_valid: bool


@dataclass(frozen=True)
class CycleOutcome:
    committed: bool
    reason: str
    sovereignty: float


def run_cycle(
    spine: EventSpine,
    proposal: Proposal,
    continuity: ContinuityConstraint,
    diagnostics: LaplacianDiagnostics,
    trust_score: float,
    tenure_score: float,
) -> CycleOutcome:
    """Execute one proof-style coordination cycle with explicit seam contracts."""

    node = spine.nodes[proposal.initiator_node_id]
    sov = sovereignty_weight(node.state, SovereigntyContext(trust_score=trust_score, tenure_score=tenure_score))

    # Dual validity gate
    if not (proposal.noumenal_valid and proposal.phenomenal_valid):
        spine.append(
            "ProposalRejected",
            {
                "proposal_id": proposal.proposal_id,
                "reason": "dual_gate_failed",
                "l_diag": {"x": diagnostics.x_energy, "y": diagnostics.y_energy},
            },
        )
        return CycleOutcome(False, "dual_gate_failed", sov)

    # Continuity as enforced constraint (Laplacian remains diagnostic)
    if not validate_continuity(proposal.dx, proposal.dy, continuity):
        spine.append(
            "ProposalRejected",
            {
                "proposal_id": proposal.proposal_id,
                "reason": "continuity_violation",
                "l_diag": {"x": diagnostics.x_energy, "y": diagnostics.y_energy},
            },
        )
        return CycleOutcome(False, "continuity_violation", sov)

    # Verification floor via state gate
    if node.state not in {NodeState.ANCHORED, NodeState.TRUSTED}:
        spine.append(
            "ProposalRejected",
            {
                "proposal_id": proposal.proposal_id,
                "reason": "verification_floor",
                "l_diag": {"x": diagnostics.x_energy, "y": diagnostics.y_energy},
            },
        )
        return CycleOutcome(False, "verification_floor", sov)

    spine.append("ProposalCommitRequested", {"node_id": proposal.initiator_node_id, "proposal_id": proposal.proposal_id})
    spine.append(
        "RelationalArtifactCreated",
        {
            "artifact_id": f"artifact-{proposal.proposal_id}",
            "event_type": "RelationalArtifactCreated",
            "edge_id": f"edge-{proposal.initiator_node_id}",
            "participants": [proposal.initiator_node_id, "community"],
            "region": "local",
            "surplus_metrics": {
                "trust_delta": round(0.1 + trust_score * 0.1, 4),
                "co_learning_score": round(0.1 + tenure_score * 0.1, 4),
                "resource_reuse_unlocked": 0.1,
            },
            "status": "active",
            "policy_version": "policy/v1",
        },
    )
    return CycleOutcome(True, "committed", sov)
