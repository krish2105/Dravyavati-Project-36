"""Session 3 verification: segment count, no null radii, plausible curvature."""

import geopandas as gpd
import pytest

from src.geo.chainage import PROCESSED_DIR


@pytest.fixture(scope="module")
def chainage_gdf():
    path = PROCESSED_DIR / "chainage.geojson"
    if not path.exists():
        pytest.skip("run `python -m src.geo.curvature` first")
    return gpd.read_file(path)


def test_segment_count_matches_length(chainage_gdf):
    alignment_length_m = gpd.read_file(PROCESSED_DIR / "alignment.geojson").to_crs(32643).geometry.iloc[0].length
    expected = alignment_length_m / 100
    assert abs(len(chainage_gdf) - expected) <= 2


def test_no_null_radii(chainage_gdf):
    assert chainage_gdf["radius_m"].isna().sum() == 0


def test_curvature_distribution_is_plausible(chainage_gdf):
    # A river-following alignment should show real sub-500m radii, not read
    # as an almost-entirely-straight line.
    under_500 = (chainage_gdf["radius_m"] < 500).sum()
    assert under_500 > 0
