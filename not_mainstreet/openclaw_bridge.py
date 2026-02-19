from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class UserContext:
    user_id: str
    intent: str
    region_hint: str
    density_band: str


@dataclass(frozen=True)
class RefinementProposal:
    title: str
    rationale: str
    patch_outline: list[str]
    generated_at: str


class PurpleMechanismClient(Protocol):
    """Minimal protocol for feigenbuam purple-mechanism integrations."""

    def fetch_relevant_information(self, ctx: UserContext) -> list[str]: ...

    def learn_user_profile(self, ctx: UserContext) -> dict[str, str]: ...

    def propose_code_refinements(self, ctx: UserContext, facts: list[str]) -> RefinementProposal: ...


class LocalPurpleMechanism:
    """Local stand-in for feigenbuam purple mechanism hooks.

    This is deterministic and dependency-free for IVI network bootstrap.
    """

    def fetch_relevant_information(self, ctx: UserContext) -> list[str]:
        return [
            f"intent:{ctx.intent}",
            f"region:{ctx.region_hint}",
            f"density:{ctx.density_band}",
            "policy:prefer privacy-preserving locational commitments",
        ]

    def learn_user_profile(self, ctx: UserContext) -> dict[str, str]:
        return {
            "user_id": ctx.user_id,
            "preference": "coordination-first",
            "risk_mode": "conservative" if ctx.density_band == "sparse" else "normal",
        }

    def propose_code_refinements(self, ctx: UserContext, facts: list[str]) -> RefinementProposal:
        patch_outline = [
            "add feature-flagged adapter contract hardening for feigenbuam Purple hooks",
            "add replay-safe telemetry event for assistant-driven suggestions",
            "add policy check requiring human approval before auto-merge",
        ]
        return RefinementProposal(
            title=f"openclaw refinement for {ctx.region_hint}",
            rationale="; ".join(facts[:3]),
            patch_outline=patch_outline,
            generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )


class OpenClawBridge:
    def __init__(self, purple_client: PurpleMechanismClient | None = None) -> None:
        self.purple_client = purple_client or LocalPurpleMechanism()

    def run_refinement_cycle(self, ctx: UserContext) -> tuple[list[str], dict[str, str], RefinementProposal]:
        facts = self.purple_client.fetch_relevant_information(ctx)
        profile = self.purple_client.learn_user_profile(ctx)
        proposal = self.purple_client.propose_code_refinements(ctx, facts)
        return facts, profile, proposal
