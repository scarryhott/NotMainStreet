from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LaplacianDiagnostics:
    """Telemetry-only smoothness metrics for noumenal/phenomenal embeddings."""

    x_energy: float
    y_energy: float


def l_diag(x_energy: float, y_energy: float) -> LaplacianDiagnostics:
    if x_energy < 0 or y_energy < 0:
        raise ValueError("Laplacian energies must be non-negative")
    return LaplacianDiagnostics(x_energy=x_energy, y_energy=y_energy)
