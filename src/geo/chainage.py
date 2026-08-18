"""Segment the corridor into 100 m chainage units — Session 3.

chainage_m is the primary key (CLAUDE.md invariant 5): one row per 100 m
segment, keyed on the segment's start distance along the alignment.
"""

import math
from pathlib import Path

import geopandas as gpd
from shapely.ops import substring

from src.constants import CHAINAGE_STEP_M, STORAGE_CRS, WORKING_CRS
from src.geo.validation import require_working_crs

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"


@require_working_crs
def segment_chainage(alignment_gdf: gpd.GeoDataFrame, step_m: int = CHAINAGE_STEP_M) -> gpd.GeoDataFrame:
    """Split the single alignment LineString into step_m segments."""
    line = alignment_gdf.geometry.iloc[0]
    total_length = line.length
    n_segments = math.ceil(total_length / step_m)

    rows = []
    for i in range(n_segments):
        start_d = i * step_m
        end_d = min((i + 1) * step_m, total_length)
        segment_geom = substring(line, start_d, end_d)
        rows.append(
            {
                "chainage_m": start_d,
                "segment_length_m": end_d - start_d,
                "geometry": segment_geom,
            }
        )
    return gpd.GeoDataFrame(rows, crs=alignment_gdf.crs)


def load_alignment_working_crs() -> gpd.GeoDataFrame:
    path = PROCESSED_DIR / "alignment.geojson"
    return gpd.read_file(path).to_crs(WORKING_CRS)


def save_chainage(gdf: gpd.GeoDataFrame) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "chainage.geojson"
    gdf.to_crs(STORAGE_CRS).to_file(out_path, driver="GeoJSON")
    return out_path


if __name__ == "__main__":
    alignment = load_alignment_working_crs()
    segments = segment_chainage(alignment)
    path = save_chainage(segments)
    print(f"Wrote {path} — {len(segments)} segments (~{alignment.geometry.iloc[0].length / 100:.1f} expected)")
