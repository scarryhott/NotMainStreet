from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


VALID_SCOPES = {"household", "block", "town", "region"}
VALID_STATUSES = {"draft", "submitted", "gated", "matched", "scheduled", "completed"}
VALID_EDGE_CLASSES = {
    "service_request",
    "commerce_exchange",
    "governance_petition",
    "volunteer_task",
    "meetup_coordination",
}

FAILURE_CODES = {
    "MISSING_FIELD",
    "CONFLICT",
    "POLICY_BLOCK",
    "FEASIBILITY_BLOCK",
}


@dataclass(frozen=True)
class Who:
    user_id: str
    roles: list[str]
    reputation_ref: str


@dataclass(frozen=True)
class Why:
    goal: str
    constraints: list[str]
    values: list[str]
    urgency: str


@dataclass(frozen=True)
class What:
    category: str
    description: str
    budget: float | None
    requirements: list[str]


@dataclass(frozen=True)
class Where:
    scope_level: str
    geo: str
    service_area: str
    constraints: list[str]


@dataclass(frozen=True)
class When:
    window: str
    trigger_conditions: list[str]
    deadline: str


@dataclass(frozen=True)
class FailureSignal:
    code: str
    field: str
    message: str


@dataclass(frozen=True)
class GateResults:
    gate_outcome: str  # pass|fail|partial
    noumenal: bool
    phenomenal: bool
    missing_fields: list[FailureSignal]
    conflicts: list[FailureSignal]
    policy_blocks: list[FailureSignal]
    feasibility_blocks: list[FailureSignal]


@dataclass(frozen=True)
class RoutingAlternative:
    edge_class: str
    confidence: float


@dataclass(frozen=True)
class EdgeProposal:
    proposal_id: str
    tenant_id: str
    community_id: str
    session_id: str
    who: Who
    why: Why
    what: What
    where: Where
    when: When
    status: str
    gate_results: GateResults
    routing_class: str
    routing_confidence: float
    routing_alternatives: list[RoutingAlternative]
    needs_disambiguation: bool
    thread_ref: str
    proposal_version: int
    engine_version: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class IntakeEvaluation:
    gate_results: GateResults
    routing_class: str
    routing_confidence: float
    routing_alternatives: list[RoutingAlternative]
    needs_disambiguation: bool
    next_actions: list[str]



def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _missing(field: str, message: str) -> FailureSignal:
    return FailureSignal(code="MISSING_FIELD", field=field, message=message)


def _conflict(field: str, message: str) -> FailureSignal:
    return FailureSignal(code="CONFLICT", field=field, message=message)


def _policy(field: str, message: str) -> FailureSignal:
    return FailureSignal(code="POLICY_BLOCK", field=field, message=message)


def _feasibility(field: str, message: str) -> FailureSignal:
    return FailureSignal(code="FEASIBILITY_BLOCK", field=field, message=message)


def evaluate_dual_gate(who: Who, why: Why, what: What, where: Where, when: When) -> GateResults:
    missing_fields: list[FailureSignal] = []
    conflicts: list[FailureSignal] = []
    policy_blocks: list[FailureSignal] = []
    feasibility_blocks: list[FailureSignal] = []

    # missing-field checks (failure-as-signal)
    if not who.user_id:
        missing_fields.append(_missing("who.user_id", "WHO user identity is required"))
    if not why.goal:
        missing_fields.append(_missing("why.goal", "WHY goal is required"))
    if not what.description:
        missing_fields.append(_missing("what.description", "WHAT description is required"))
    if where.scope_level not in VALID_SCOPES:
        missing_fields.append(_missing("where.scope_level", "WHERE scope_level must be one of household|block|town|region"))
    if not when.window:
        missing_fields.append(_missing("when.window", "WHEN window is required"))

    # noumenal checks
    noumenal = True
    if not why.values:
        policy_blocks.append(_policy("why.values", "Intent requires at least one value commitment"))
        noumenal = False
    if "banned" in (r.lower() for r in who.roles):
        policy_blocks.append(_policy("who.roles", "Actor role is not permitted for this action"))
        noumenal = False

    # phenomenal checks
    phenomenal = True
    if where.scope_level == "household" and what.category == "governance":
        conflicts.append(_conflict("where.scope_level+what.category", "Governance requests cannot be household-only"))
        phenomenal = False
    if what.budget is not None and what.budget < 0:
        feasibility_blocks.append(_feasibility("what.budget", "Budget cannot be negative"))
        phenomenal = False

    if missing_fields:
        noumenal = False
        phenomenal = False

    if noumenal and phenomenal:
        gate_outcome = "pass"
    elif not noumenal and not phenomenal:
        gate_outcome = "fail"
    else:
        gate_outcome = "partial"

    return GateResults(
        gate_outcome=gate_outcome,
        noumenal=noumenal,
        phenomenal=phenomenal,
        missing_fields=missing_fields,
        conflicts=conflicts,
        policy_blocks=policy_blocks,
        feasibility_blocks=feasibility_blocks,
    )


def route_edge_class(what: What, why: Why) -> tuple[str, float, list[RoutingAlternative], bool]:
    c = what.category.lower().strip()
    scores = {
        "service_request": 0.2,
        "commerce_exchange": 0.2,
        "governance_petition": 0.2,
        "volunteer_task": 0.2,
        "meetup_coordination": 0.2,
    }

    if c in {"service", "repair", "care"}:
        scores["service_request"] = 0.92
    elif c in {"commerce", "market", "sale"}:
        scores["commerce_exchange"] = 0.92
    elif c in {"governance", "petition", "policy"}:
        scores["governance_petition"] = 0.92
    elif c in {"volunteer", "mutual_aid"}:
        scores["volunteer_task"] = 0.92
    elif c in {"event", "meetup"}:
        scores["meetup_coordination"] = 0.92
    elif "volunteer" in why.goal.lower():
        scores["volunteer_task"] = 0.75
    else:
        scores["service_request"] = 0.55
        scores["commerce_exchange"] = 0.45

    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    primary_class, primary_score = ordered[0]
    alternatives = [RoutingAlternative(edge_class=k, confidence=v) for k, v in ordered[:3]]
    needs_disambiguation = primary_score < 0.7
    return primary_class, primary_score, alternatives, needs_disambiguation


def next_actions(gate: GateResults, edge_class: str, needs_disambiguation: bool) -> list[str]:
    if gate.gate_outcome == "pass":
        actions = [
            f"route to edge class: {edge_class}",
            "begin locality-weighted candidate matching",
            "notify user and relevant coordinators",
        ]
        if needs_disambiguation:
            actions.insert(0, "ask one clarifying question to confirm routing class")
        return actions

    actions: list[str] = []
    for signal in gate.missing_fields:
        actions.append(f"collect missing field -> {signal.field}")
    for _ in gate.conflicts:
        actions.append("resolve conflicting fields before routing")
    for _ in gate.policy_blocks:
        actions.append("review policy/ethos trust requirements")
    for _ in gate.feasibility_blocks:
        actions.append("adjust feasibility constraints (budget/location/time)")
    return actions or ["request clarification"]


def build_edge_proposal(
    proposal_id: str,
    tenant_id: str,
    community_id: str,
    session_id: str,
    who: Who,
    why: Why,
    what: What,
    where: Where,
    when: When,
    thread_ref: str,
    *,
    proposal_version: int = 1,
    engine_version: str = "ivi-engine/v1",
) -> tuple[EdgeProposal, IntakeEvaluation]:
    gate = evaluate_dual_gate(who, why, what, where, when)
    routing_class, routing_confidence, routing_alternatives, needs_disambiguation = route_edge_class(what, why)
    suggestions = next_actions(gate, routing_class, needs_disambiguation)

    now = _now()
    status = "gated" if gate.gate_outcome == "pass" else "submitted"
    proposal = EdgeProposal(
        proposal_id=proposal_id,
        tenant_id=tenant_id,
        community_id=community_id,
        session_id=session_id,
        who=who,
        why=why,
        what=what,
        where=where,
        when=when,
        status=status,
        gate_results=gate,
        routing_class=routing_class,
        routing_confidence=routing_confidence,
        routing_alternatives=routing_alternatives,
        needs_disambiguation=needs_disambiguation,
        thread_ref=thread_ref,
        proposal_version=proposal_version,
        engine_version=engine_version,
        created_at=now,
        updated_at=now,
    )
    return proposal, IntakeEvaluation(
        gate_results=gate,
        routing_class=routing_class,
        routing_confidence=routing_confidence,
        routing_alternatives=routing_alternatives,
        needs_disambiguation=needs_disambiguation,
        next_actions=suggestions,
    )


def proposal_to_dict(p: EdgeProposal) -> dict[str, Any]:
    return asdict(p)
