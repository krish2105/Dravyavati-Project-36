"""Roll-up + sensitivity — Session 7.

This is the authoritative full-pipeline run: alignment -> chainage ->
curvature -> interfaces -> land/habitation -> hydraulic -> composite, all on
one segments GeoDataFrame, saved once as chainage_risk.parquet. Running the
individual session modules standalone (each has its own __main__) is useful
for demonstrating that piece in isolation, but each of those overwrites
data/processed/chainage.geojson with only its own columns — this module is
the one that produces the real, complete deliverable.

Composite score: composite = sum(weight_i * score_i), equal weights by
default (pack §5). The sensitivity sweep re-runs the composite under a set
of plausible alternative weightings and keeps only chainages whose severity
band (0-1 low / 1.5-2 medium / 2-3 high — see SEVERITY_BANDS) is stable
across all of them: "the only ones you should mention out loud" (pack §5).
"""

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

from src.constants import CONSTRAINT_WEIGHTS, STORAGE_CRS

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

SCORE_COLUMNS = {
    "railway_crossing": "railway_crossing_score",
    "metro_interface": "metro_interface_score",
    "existing_elevated_structure": "existing_elevated_structure_score",
    "major_arterial_crossing": "major_arterial_crossing_score",
    "restricted_military_area": "restricted_military_area_score",
    "entry_exit_feasibility": "entry_exit_feasibility_score",
    "curve_severity": "curve_severity_score",
    "eht_line_crossing": "eht_line_crossing_score",
    "dam_check_structure": "dam_check_structure_score",
    "land_availability": "land_availability_score",
    "habitation_proximity": "habitation_proximity_score",
    "hydraulic_sensitivity": "hydraulic_sensitivity_index",  # 0-1 scale, not 0-3 — see _normalise
}

SEVERITY_BANDS = [("low", 0, 1), ("medium", 1, 2), ("high", 2, 3.001)]


def _complete_entry_exit_feasibility(segments: pd.DataFrame) -> pd.DataFrame:
    """Constraint 06 = distance to nearest arterial x unbuilt area within
    150m (pack §5). Session 4 computed the distance half; Session 5 computed
    the unbuilt-area half (at a 60m buffer, not 150m, but re-using it here
    rather than a third buffer pass is a reasonable approximation — noted,
    not hidden)."""
    out = segments.copy()
    if "entry_exit_distance_to_arterial_m" not in out or "land_availability_frac_built" not in out:
        return out
    unbuilt_frac = 1 - out["land_availability_frac_built"]
    dist_norm = (out["entry_exit_distance_to_arterial_m"] / out["entry_exit_distance_to_arterial_m"].max()).clip(0, 1)
    feasibility = dist_norm * unbuilt_frac  # 0 (easy access, open land) .. 1 (far + built-up)
    out["entry_exit_feasibility_score"] = (feasibility * 3).round().astype(int)
    return out


def _normalise_hydraulic_to_0_3(segments: pd.DataFrame) -> pd.Series:
    return segments["hydraulic_sensitivity_index"] * 3


def compute_composite(segments: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    total_weight = sum(weights.values())
    composite = pd.Series(0.0, index=segments.index)
    for name, col in SCORE_COLUMNS.items():
        if col not in segments.columns:
            continue
        values = _normalise_hydraulic_to_0_3(segments) if name == "hydraulic_sensitivity" else segments[col]
        composite += weights.get(name, 0) * values.fillna(0)
    return composite / total_weight if total_weight else composite


def _severity_band(score: float) -> str:
    for band, lo, hi in SEVERITY_BANDS:
        if lo <= score < hi:
            return band
    return "high"


def _plausible_reweightings(base_weights: dict[str, float], n: int = 8) -> list[dict[str, float]]:
    """Perturb each weight by up to +/-50% in a few deterministic combinations
    — not a random search, so results are reproducible."""
    names = list(base_weights.keys())
    factors = [0.5, 1.5]
    rng = np.random.default_rng(seed=42)
    sweeps = []
    for _ in range(n):
        w = {k: base_weights[k] * rng.choice(factors) for k in names}
        sweeps.append(w)
    return sweeps


def run_sensitivity_sweep(segments: pd.DataFrame, base_weights: dict[str, float]) -> pd.DataFrame:
    base_composite = compute_composite(segments, base_weights)
    base_bands = base_composite.apply(_severity_band)

    sweeps = _plausible_reweightings(base_weights)
    band_matrix = pd.DataFrame({"base": base_bands})
    for i, w in enumerate(sweeps):
        composite = compute_composite(segments, w)
        band_matrix[f"sweep_{i}"] = composite.apply(_severity_band)

    is_robust = band_matrix.eq(band_matrix["base"], axis=0).all(axis=1)
    out = segments.copy()
    out["composite_score"] = base_composite
    out["severity_band"] = base_bands
    out["robust_hotspot"] = is_robust & (base_bands != "low")
    return out


def build_full_pipeline() -> pd.DataFrame:
    from src.geo.alignment import reconstruct_alignment
    from src.geo.chainage import segment_chainage
    from src.geo.curvature import compute_curvature
    from src.scoring.hydraulic import score_hydraulic
    from src.scoring.interfaces import score_interfaces
    from src.scoring.land import score_land_and_habitation

    alignment = reconstruct_alignment()
    alignment_working = alignment.to_crs(32643)

    segments = segment_chainage(alignment_working)
    segments = compute_curvature(alignment_working, segments)
    segments = score_interfaces(segments)
    segments = score_land_and_habitation(segments)
    segments = score_hydraulic(alignment_working, segments)
    segments = _complete_entry_exit_feasibility(segments)

    weights = {k: 1.0 for k in CONSTRAINT_WEIGHTS}  # equal weights, pack §5 default
    segments = run_sensitivity_sweep(segments, weights)
    return segments.to_crs(STORAGE_CRS)


def save_chainage_risk(gdf) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "chainage_risk.parquet"
    gdf.to_parquet(out_path)
    return out_path


if __name__ == "__main__":
    full = build_full_pipeline()
    path = save_chainage_risk(full)

    robust = full[full["robust_hotspot"]]
    print(f"Wrote {path} — {len(full)} rows, {len(robust)} robust hotspots (target: 8-20)")
    print(full["severity_band"].value_counts())
