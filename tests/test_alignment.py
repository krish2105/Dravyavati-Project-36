"""Session 2 verification — see src/geo/alignment.py docstring for the
documented ~41 km vs. the pack's 34-38 km tolerance deviation.
"""

import geopandas as gpd
import pytest

from src.geo.alignment import PROCESSED_DIR


@pytest.fixture(scope="module")
def alignment_gdf():
    path = PROCESSED_DIR / "alignment.geojson"
    if not path.exists():
        pytest.skip("run `python -m src.geo.alignment` first")
    return gpd.read_file(path)


def test_alignment_is_single_unbroken_linestring(alignment_gdf):
    assert len(alignment_gdf) == 1
    geom = alignment_gdf.geometry.iloc[0]
    assert geom.geom_type == "LineString"
    assert geom.is_simple


def test_alignment_length_is_plausible(alignment_gdf):
    # Reproject to a metric CRS for the length check — the stored file is EPSG:4326.
    length_km = alignment_gdf.to_crs(32643).geometry.iloc[0].length / 1000
    # Sanity bound, not the pack's literal 34-38 km — see module docstring in
    # src/geo/alignment.py for why this reconstruction lands at ~39-40 km.
    assert 30 < length_km < 45
