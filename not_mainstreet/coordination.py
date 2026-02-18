from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContinuityConstraint:
    epsilon_x: float
    epsilon_y: float

    def __post_init__(self) -> None:
        if self.epsilon_x <= 0 or self.epsilon_y <= 0:
            raise ValueError("epsilon_x and epsilon_y must be > 0")


def validate_continuity(dx: float, dy: float, constraint: ContinuityConstraint) -> bool:
    """Return True if per-step embedding movement is within configured bounds."""
    return abs(dx) <= constraint.epsilon_x and abs(dy) <= constraint.epsilon_y
