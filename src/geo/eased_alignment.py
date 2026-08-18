"""Curve-eased alignment variant — resolves the 41.2 km vs ~36 km gap.

The channel-following reconstruction measures 41.2 km against a publicly
reported ~36 km. That was recorded as an open discrepancy. It is not an
error in either figure: it is the measurable cost of tracing a river's
medial axis instead of easing curves the way a designed alignment must.

This module quantifies that. Starting from the channel centreline resampled
at 50 m, it applies iterative Laplacian easing and records, at each stage,
the three quantities that actually trade against each other: corridor
length, departure from the channel, and compliance with the IRC:86-2018
minimum horizontal curve radius (150 m at 60 km/h, 4% super-elevation).

Measured result
---------------
    easing     length     drift    vertices below 150 m R    p5 radius
    none       41.13 km     0 m         28 / 824              466 m
    250        38.09 km   432 m          7 / 824             1304 m
    1000       36.43 km   875 m         11 / 824             2594 m
    2000       35.33 km  1240 m         12 / 824             3072 m

At 1000 iterations the alignment reaches **36.43 km**, which is the reported
project length, and does so while improving curvature compliance from 28
non-compliant vertices to 11 of 824. The price is a departure from the
mapped channel of up to 875 m.

That is the finding, and it is more useful than either number alone: a
~36 km corridor along this river is achievable, but implies leaving the
channel by up to about 875 m to cut meanders. Whether that departure is
acceptable is a design and land-acquisition question this atlas does not
answer.

Both alignments are exported. The channel-following one remains the basis
for constraint scoring, because it is the one derived purely from public
geometry with no easing assumptions layered on top. The eased variant is
published alongside it for comparison, not substituted for it.

Note on the minimum-radius statistic: raw min() over all vertices is
dominated by a few near-degenerate triples and moves erratically under
easing. The honest summary is the distribution — the count below the IRC
threshold and the 5th-percentile radius — which is what is reported above.
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
from shapely.geometry import LineString

from src.constants import STORAGE_CRS, WORKING_CRS
from src.geo.curvature import _circumradius

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

RESAMPLE_STEP_M = 50.0
IRC86_MIN_RADIUS_M = 150.0
EASING_ITERATIONS = 1000
REPORTED_LENGTH_KM = 36.0


def _resample(line: LineString, step: float = RESAMPLE_STEP_M) -> LineString:
    n = int(line.length // step)
    return LineString([line.interpolate(i * step) for i in range(n + 1)] + [line.interpolate(line.length)])


def _ease_once(coords: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    out = coords.copy()
    out[1:-1] = coords[1:-1] + alpha * ((coords[:-2] + coords[2:]) / 2 - coords[1:-1])
    return out


def _radii(coords: np.ndarray) -> np.ndarray:
    return np.array(
        [_circumradius(tuple(coords[i - 1]), tuple(coords[i]), tuple(coords[i + 1]))
         for i in range(1, len(coords) - 1)]
    )


def profile_easing(line: LineString, stages: tuple[int, ...] = (0, 250, 1000, 2000)) -> list[dict]:
    """The length / drift / compliance trade-off at each easing stage."""
    base = _resample(line)
    coords = np.array(base.coords, float)
    rows, done = [], 0
    for target in stages:
        while done < target:
            coords = _ease_once(coords)
            done += 1
        eased = LineString(coords)
        r = _radii(coords)
        rows.append(
            {
                "easing_iterations": target,
                "length_km": round(eased.length / 1000, 3),
                "drift_m": round(eased.hausdorff_distance(base), 1),
                "vertices_below_irc_min": int((r < IRC86_MIN_RADIUS_M).sum()),
                "vertices_total": int(len(r)),
                "p5_radius_m": round(float(np.percentile(r, 5)), 1),
                "median_radius_m": round(float(np.median(r)), 1),
            }
        )
    return rows


def build_eased(line: LineString, iterations: int = EASING_ITERATIONS) -> tuple[LineString, dict]:
    base = _resample(line)
    coords = np.array(base.coords, float)
    for _ in range(iterations):
        coords = _ease_once(coords)
    eased = LineString(coords)
    r = _radii(coords)
    return eased, {
        "easing_iterations": iterations,
        "length_km": round(eased.length / 1000, 3),
        "drift_from_channel_m": round(eased.hausdorff_distance(base), 1),
        "vertices_below_irc_min": int((r < IRC86_MIN_RADIUS_M).sum()),
        "vertices_total": int(len(r)),
        "p5_radius_m": round(float(np.percentile(r, 5)), 1),
        "irc86_min_radius_m": IRC86_MIN_RADIUS_M,
    }


if __name__ == "__main__":
    channel = gpd.read_file(PROCESSED_DIR / "alignment.geojson").to_crs(WORKING_CRS).geometry.iloc[0]

    table = profile_easing(channel)
    eased, stats = build_eased(channel)

    gpd.GeoDataFrame(
        {"name": ["Dravyavati corridor (curve-eased variant)"], **{k: [v] for k, v in stats.items()}},
        geometry=[eased],
        crs=WORKING_CRS,
    ).to_crs(STORAGE_CRS).to_file(PROCESSED_DIR / "alignment_eased.geojson", driver="GeoJSON")

    report = {
        "channel_following_km": round(channel.length / 1000, 3),
        "eased_km": stats["length_km"],
        "reported_project_km": REPORTED_LENGTH_KM,
        "gap_explained": (
            "The eased variant reaches the reported project length, at the cost of departing the "
            f"mapped channel by up to {stats['drift_from_channel_m']} m to cut meanders."
        ),
        "selected_for_scoring": "channel_following",
        "why": (
            "Scoring stays on the channel-following alignment because it is derived purely from public "
            "geometry with no easing assumptions layered on top. The eased variant is published for "
            "comparison, not substituted."
        ),
        "trade_off": table,
        **stats,
    }
    (PROCESSED_DIR / "alignment_easing_report.json").write_text(json.dumps(report, indent=1))
    (REPO_ROOT / "web" / "public" / "data" / "alignment_easing.json").write_text(json.dumps(report, indent=1))

    print(f"channel-following {report['channel_following_km']} km -> eased {stats['length_km']} km "
          f"(reported ~{REPORTED_LENGTH_KM} km)")
    print(f"drift {stats['drift_from_channel_m']} m | below IRC min: "
          f"{stats['vertices_below_irc_min']}/{stats['vertices_total']} | p5 radius {stats['p5_radius_m']} m")
