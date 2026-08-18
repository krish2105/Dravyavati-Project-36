"""Session 4 verification: railway crossings ~2±1, confidence tags on
power/military layers."""

import pandas as pd
import pytest

from src.scoring.composite import PROCESSED_DIR


@pytest.fixture(scope="module")
def chainage_gdf():
    path = PROCESSED_DIR / "chainage_risk.parquet"
    if not path.exists():
        pytest.skip("run `python -m src.scoring.composite` first")
    return pd.read_parquet(path)


def test_railway_crossings_near_expected_count(chainage_gdf):
    # Pack §6 Session 4: "railway crossings detected = 2 ± 1" means distinct
    # crossing events, not raw scored segments — one crossing's 150m buffer
    # can span several consecutive 100m segments. Count contiguous clusters.
    ordered = chainage_gdf.sort_values("chainage_m").reset_index(drop=True)
    crossing = ordered["railway_crossing_score"] == 3
    clusters = (crossing != crossing.shift()).cumsum()[crossing].nunique()
    assert 1 <= clusters <= 3


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
