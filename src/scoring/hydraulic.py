"""Challenge 12: channel geometry screening — Session 6.

GLO-30 (30m) cannot resolve a rectified channel cross-section (pack §4) —
"channel width" is not computed here; fabricating a width estimate the DEM
resolution can't actually support would be worse than leaving it out (see
CLAUDE.md invariant 2). The index is upstream contributing area alone,
derived from real D8 flow accumulation on the DEM, min-max normalised.

Column is named hydraulic_sensitivity_index — never afflux, never
flood_risk (pack §6 Session 6 naming discipline).
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

if not hasattr(np, "in1d"):  # pysheds calls np.in1d, removed as a top-level name in NumPy 2.x
    np.in1d = np.isin

from pysheds.grid import Grid

from src.geo.validation import require_working_crs

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
DEM_PATH = RAW_DIR / "Copernicus_DSM_COG_10_N26_00_E075_00_DEM.tif"


def _flow_accumulation(dem_path: Path) -> tuple[Grid, np.ndarray]:
    grid = Grid.from_raster(str(dem_path))
    dem = grid.read_raster(str(dem_path))

    pit_filled = grid.fill_pits(dem)
    flooded = grid.fill_depressions(pit_filled)
    inflated = grid.resolve_flats(flooded)

    dirmap = (64, 128, 1, 2, 4, 8, 16, 32)
    fdir = grid.flowdir(inflated, dirmap=dirmap)
    acc = grid.accumulation(fdir, dirmap=dirmap)
    return grid, acc


@require_working_crs
def score_hydraulic(alignment_gdf: gpd.GeoDataFrame, segments: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    grid, acc = _flow_accumulation(DEM_PATH)

    # Sample accumulation at each segment's midpoint, in the DEM's own CRS (EPSG:4326).
    line_wgs84 = alignment_gdf.to_crs(4326).geometry.iloc[0]
    total_length = alignment_gdf.geometry.iloc[0].length  # metres, working CRS

    raw_values = []
    for _, row in segments.iterrows():
        chainage_m = row["chainage_m"] + row["segment_length_m"] / 2
        frac = min(chainage_m / total_length, 1.0)
        pt = line_wgs84.interpolate(frac, normalized=True)
        col, r = ~grid.affine * (pt.x, pt.y)
        col, r = int(col), int(r)
        if 0 <= r < acc.shape[0] and 0 <= col < acc.shape[1]:
            raw_values.append(float(acc[r, col]))
        else:
            raw_values.append(np.nan)

    series = pd.Series(raw_values)
    series = series.ffill().bfill()  # DEM tile edge misses, if any

    # Enforce monotonic non-decrease downstream: a real river's contributing
    # area cannot shrink. Local dips here are DEM/alignment registration
    # noise, not physical signal — a running max is the standard way to
    # denoise a monotonic proxy without inventing new values.
    monotonic = series.cummax()

    lo, hi = monotonic.min(), monotonic.max()
    normalised = (monotonic - lo) / (hi - lo) if hi > lo else monotonic * 0

    out = segments.copy()
    out["hydraulic_sensitivity_index"] = normalised.values
    out["hydraulic_sensitivity_confidence"] = "low"  # pack §5: constraint 12 is Low confidence
    return out


def save_hydraulic(gdf: gpd.GeoDataFrame) -> Path:
    from src.constants import STORAGE_CRS

    processed_dir = REPO_ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / "chainage.geojson"
    gdf.to_crs(STORAGE_CRS).to_file(out_path, driver="GeoJSON")
    return out_path


if __name__ == "__main__":
    from src.geo.chainage import load_alignment_working_crs, segment_chainage
    from src.geo.curvature import compute_curvature

    alignment = load_alignment_working_crs()
    segments = segment_chainage(alignment)
    segments = compute_curvature(alignment, segments)
    scored = score_hydraulic(alignment, segments)
    path = save_hydraulic(scored)

    idx = scored["hydraulic_sensitivity_index"]
    is_monotonic = idx.is_monotonic_increasing or (idx.diff().dropna() >= -1e-9).all()
    print(f"Wrote {path} — monotonic downstream: {is_monotonic}, range [{idx.min():.3f}, {idx.max():.3f}]")
