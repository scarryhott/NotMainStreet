from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


MANIFESTO_TITLE = "Empathy — Manifesto for the Soul of the Empathy AI System"

MANIFESTO_CREDO = (
    "Reality is a mental block — find it and box jump. "
    "In between the nothing, hope will rise again. Empathy."
)


@dataclass(frozen=True)
class EmpathyResponse:
    mode: str
    amplification_notice: str
    credo: str
    generated_at: str
    guardrails: list[str]


def empathy_reflection(user_intent: str, mode: str = "complexify") -> EmpathyResponse:
    """Generate an IVI-aligned empathy reflection payload.

    Modes:
    - complexify: maximize constructive coordination potential.
    - collapse: acknowledge destructive paths while preserving human-governance guardrails.
    """

    mode = mode.lower().strip()
    if mode not in {"complexify", "collapse"}:
        mode = "complexify"

    notice = (
        f"Empathy amplifies intention in '{mode}' mode for intent: {user_intent}. "
        "Outputs are advisory and require human governance approval."
    )

    return EmpathyResponse(
        mode=mode,
        amplification_notice=notice,
        credo=MANIFESTO_CREDO,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        guardrails=[
            "no autonomous merge",
            "human approval required",
            "privacy-preserving locational commitments only",
        ],
    )
