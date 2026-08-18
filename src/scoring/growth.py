"""Built-up growth pressure per chainage — Phase 1b.

Samples the Sentinel-2 NDBI change raster (2018 -> current) inside each
segment's 100 m buffer. This is the pack §4 "built-up change since 2018"
layer: where habitation has encroached along the channel since the
rejuvenation project, land acquisition gets harder over time, not easier.

Confidence is **low** by construction and stays low in the output:
NDBI is a proxy index, not a land-cover classification, and bare soil in
this region can mimic built-up signal. The *difference* between epochs is
more trustworthy than either absolute value, which is why only the
difference is scored.
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask

from src.geo.validation import require_working_crs

REPO_ROOT = Path(__file__).resolve().parents[2]
NDBI_CHANGE_PATH = REPO_ROOT / "data" / "raw" / "sentinel2_ndbi_change.tif"

GROWTH_BUFFER_M = 100

# NDBI change thresholds. Chosen from the observed distribution rather than
# from literature: this is a relative screening signal, and a published
# absolute NDBI threshold wouldn't transfer to a two-date difference anyway.
GROWTH_STRONG = 0.10
GROWTH_MODERATE = 0.05
GROWTH_SLIGHT = 0.02


def _growth_to_score(delta: float) -> int:
    if not np.isfinite(delta):
        return 0
    if delta >= GROWTH_STRONG:
        return 3
    if delta >= GROWTH_MODERATE:
        return 2
    if delta >= GROWTH_SLIGHT:
        return 1
    return 0


@require_working_crs
def score_builtup_growth(segments: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add mean NDBI change + a 0-3 growth-pressure score per chainage."""
    out = segments.copy()

    if not NDBI_CHANGE_PATH.exists():
        out["builtup_ndbi_change"] = np.nan
        out["builtup_growth_score"] = 0
        out["builtup_growth_confidence"] = "low"
        return out

    with rasterio.open(NDBI_CHANGE_PATH) as src:
        buffers = segments.to_crs(src.crs).geometry.buffer(GROWTH_BUFFER_M)
        deltas = []
        for geom in buffers:
            try:
                patch, _ = rio_mask(src, [geom], crop=True, filled=True, nodata=np.nan)
                values = patch[0]
                finite = values[np.isfinite(values)]
                deltas.append(float(finite.mean()) if finite.size else np.nan)
            except ValueError:
                # Buffer falls outside the raster footprint entirely.
                deltas.append(np.nan)

    out["builtup_ndbi_change"] = deltas
    out["builtup_growth_score"] = [_growth_to_score(d) for d in deltas]
    out["builtup_growth_confidence"] = "low"
    return out


if __name__ == "__main__":
    from src.geo.chainage import load_alignment_working_crs, segment_chainage

    alignment = load_alignment_working_crs()
    segments = segment_chainage(alignment)
    scored = score_builtup_growth(segments)

    series = scored["builtup_ndbi_change"]
    print(f"segments: {len(scored)}, with data: {series.notna().sum()}")
    print(f"NDBI change per segment — min {series.min():.3f}, median {series.median():.3f}, max {series.max():.3f}")
    print("growth score distribution:", scored["builtup_growth_score"].value_counts().sort_index().to_dict())
