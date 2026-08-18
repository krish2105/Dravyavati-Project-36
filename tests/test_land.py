"""Session 5 verification: dense-urban vs peri-urban habitation gradient."""

import geopandas as gpd
import pytest

from src.geo.chainage import PROCESSED_DIR


@pytest.fixture(scope="module")
def chainage_gdf():
    path = PROCESSED_DIR / "chainage.geojson"
    if not path.exists() or "habitation_proximity_score" not in gpd.read_file(path).columns:
        pytest.skip("run `python -m src.scoring.land` first")
    return gpd.read_file(path)


def test_habitation_scores_are_in_range(chainage_gdf):
    assert chainage_gdf["habitation_proximity_score"].between(0, 3).all()
    assert chainage_gdf["land_availability_score"].between(0, 3).all()


def test_habitation_gradient_exists(chainage_gdf):
    # Not a hard "must be exactly Mansarovar = 3" check (that needs a real
    # geocoded spot-check, done manually per pack §6 Session 5) — but a flat
    # score across every segment would mean the buffer geometry is broken.
    assert chainage_gdf["habitation_proximity_score"].nunique() > 1
