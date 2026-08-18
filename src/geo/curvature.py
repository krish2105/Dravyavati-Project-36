"""Radius of curvature per segment — Session 3.

Three-point circumscribed-circle method: for each chainage point, the
circumradius of the triangle formed by it and its two neighbours (one
chainage step back, one forward) approximates the local radius of curvature.
Straight stretches produce a very large (not infinite, not null) radius —
STRAIGHT_RADIUS_M — per CLAUDE.md invariant 6 (no nulls hiding as missing
data).
"""

import math
from pathlib import Path

import geopandas as gpd

from src.constants import STORAGE_CRS, WORKING_CRS
from src.geo.validation import require_working_crs

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

STRAIGHT_RADIUS_M = 100_000.0
"""Reported radius for a chainage triple that's effectively collinear."""


def _circumradius(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    side_a = math.hypot(b[0] - c[0], b[1] - c[1])
    side_b = math.hypot(a[0] - c[0], a[1] - c[1])
    side_c = math.hypot(a[0] - b[0], a[1] - b[1])
    twice_area = abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
    if twice_area < 1e-6:
        return STRAIGHT_RADIUS_M
    radius = (side_a * side_b * side_c) / (2 * twice_area)
    return min(radius, STRAIGHT_RADIUS_M)


@require_working_crs
def compute_curvature(alignment_gdf: gpd.GeoDataFrame, segments_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add radius_m to segments_gdf, one value per chainage_m row."""
    line = alignment_gdf.geometry.iloc[0]
    total_length = line.length
    chainages = segments_gdf["chainage_m"].tolist()

    # One extra point past the last segment's start, so the last segment has a "next" neighbour.
    sample_distances = chainages + [total_length]
    points = [line.interpolate(min(d, total_length)) for d in sample_distances]

    radii = []
    n = len(points)
    for i in range(len(segments_gdf)):
        i_prev = max(i - 1, 0)
        i_next = min(i + 1, n - 1)
        a, b, c = points[i_prev], points[i], points[i_next]
        radii.append(_circumradius((a.x, a.y), (b.x, b.y), (c.x, c.y)))

    out = segments_gdf.copy()
    out["radius_m"] = radii
    return out


def save_curvature(gdf: gpd.GeoDataFrame) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "chainage.geojson"
    gdf.to_crs(STORAGE_CRS).to_file(out_path, driver="GeoJSON")
    return out_path


if __name__ == "__main__":
    from src.geo.chainage import load_alignment_working_crs, segment_chainage

    alignment = load_alignment_working_crs()
    segments = segment_chainage(alignment)
    with_curvature = compute_curvature(alignment, segments)
    path = save_curvature(with_curvature)

    null_count = with_curvature["radius_m"].isna().sum()
    under_500 = (with_curvature["radius_m"] < 500).sum()
    print(f"Wrote {path} — {len(with_curvature)} segments, {null_count} null radii, {under_500} with radius < 500m")
