"""Session 6 verification: monotonic downstream, correct column naming."""

import geopandas as gpd
import pytest

from src.geo.chainage import PROCESSED_DIR


@pytest.fixture(scope="module")
def chainage_gdf():
    path = PROCESSED_DIR / "chainage.geojson"
    if not path.exists() or "hydraulic_sensitivity_index" not in gpd.read_file(path).columns:
        pytest.skip("run `python -m src.scoring.hydraulic` first")
    return gpd.read_file(path)


def test_hydraulic_index_is_monotonic_downstream(chainage_gdf):
    idx = chainage_gdf.sort_values("chainage_m")["hydraulic_sensitivity_index"]
    assert (idx.diff().dropna() >= -1e-9).all()


def test_hydraulic_column_naming_discipline(chainage_gdf):
    # Pack §6 Session 6: never afflux, never flood_risk.
    forbidden = {"afflux", "flood_risk"}
    assert forbidden.isdisjoint(chainage_gdf.columns)
