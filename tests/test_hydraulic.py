"""Session 6 verification: monotonic downstream, correct column naming."""

import pandas as pd
import pytest

from src.scoring.composite import PROCESSED_DIR


@pytest.fixture(scope="module")
def chainage_gdf():
    path = PROCESSED_DIR / "chainage_risk.parquet"
    if not path.exists():
        pytest.skip("run `python -m src.scoring.composite` first")
    return pd.read_parquet(path)


def test_hydraulic_index_is_monotonic_downstream(chainage_gdf):
    idx = chainage_gdf.sort_values("chainage_m")["hydraulic_sensitivity_index"]
    assert (idx.diff().dropna() >= -1e-9).all()


def test_hydraulic_column_naming_discipline(chainage_gdf):
    # Pack §6 Session 6: never afflux, never flood_risk.
    forbidden = {"afflux", "flood_risk"}
    assert forbidden.isdisjoint(chainage_gdf.columns)
