from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DensityCertificate:
    """Network-shareable locational proof without disclosing exact coordinates."""

    cell_commitment: str
    density_band: str
    verified: bool
    population_floor: int


@dataclass(frozen=True)
class GridCell:
    x: int
    y: int


def _meters_per_degree_lat() -> float:
    return 111_320.0


def _meters_per_degree_lon(lat_deg: float) -> float:
    # cosine-scaled approximation is sufficient for local density grids.
    return 111_320.0 * max(0.01, math.cos(math.radians(lat_deg)))


def quantize_location(lat: float, lon: float, cell_size_m: float = 500.0) -> GridCell:
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        raise ValueError("invalid latitude/longitude")
    if cell_size_m <= 0:
        raise ValueError("cell_size_m must be > 0")

    x = int(math.floor((lat * _meters_per_degree_lat()) / cell_size_m))
    y = int(math.floor((lon * _meters_per_degree_lon(lat)) / cell_size_m))
    return GridCell(x=x, y=y)


def cell_commitment(cell: GridCell, epoch_salt: str) -> str:
    payload = f"{cell.x}:{cell.y}:{epoch_salt}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _density_band(count: int) -> str:
    if count < 5:
        return "sparse"
    if count < 20:
        return "moderate"
    return "dense"


def build_density_certificate(
    subject_lat: float,
    subject_lon: float,
    peer_locations: list[tuple[float, float]],
    *,
    min_k: int,
    cell_size_m: float,
    epoch_salt: str,
) -> DensityCertificate:
    """Create k-anonymous density proof for dual-matrix phenomenal gating.

    Returns only commitment + density class + threshold result.
    Exact location/cell indices are never emitted.
    """

    cell = quantize_location(subject_lat, subject_lon, cell_size_m=cell_size_m)
    same_cell = 0
    for lat, lon in peer_locations:
        if quantize_location(lat, lon, cell_size_m=cell_size_m) == cell:
            same_cell += 1

    # include subject itself as one local participant.
    population_floor = same_cell + 1
    return DensityCertificate(
        cell_commitment=cell_commitment(cell, epoch_salt),
        density_band=_density_band(population_floor),
        verified=population_floor >= min_k,
        population_floor=population_floor,
    )
