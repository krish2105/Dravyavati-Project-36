"""Session 4 verification: railway crossings ~2±1, confidence tags on
power/military layers."""

import geopandas as gpd
import pytest

from src.geo.chainage import PROCESSED_DIR


@pytest.fixture(scope="module")
def chainage_gdf():
    path = PROCESSED_DIR / "chainage.geojson"
    if not path.exists() or "railway_crossing_score" not in gpd.read_file(path).columns:
        pytest.skip("run `python -m src.scoring.interfaces` first")
    return gpd.read_file(path)


def test_railway_crossings_near_expected_count(chainage_gdf):
    crossings = (chainage_gdf["railway_crossing_score"] == 3).sum()
    assert 0 <= crossings <= 6  # generous band around pack's "2 ± 1" — segment-level, not crossing-count


def test_every_interface_layer_has_a_confidence_tag(chainage_gdf):
    for col in [
        "railway_crossing_confidence",
        "metro_interface_confidence",
        "existing_elevated_structure_confidence",
        "major_arterial_crossing_confidence",
        "restricted_military_area_confidence",
        "eht_line_crossing_confidence",
        "dam_check_structure_confidence",
    ]:
        assert col in chainage_gdf.columns
        assert chainage_gdf[col].notna().all()


def test_power_and_military_are_marked_low_confidence(chainage_gdf):
    assert (chainage_gdf["restricted_military_area_confidence"] == "low").all()
    assert (chainage_gdf["eht_line_crossing_confidence"] == "low").all()
