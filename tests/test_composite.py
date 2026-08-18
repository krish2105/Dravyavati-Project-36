"""Session 7 verification: schema, no nulls, robust-hotspot count in range."""

import pandas as pd
import pytest

from src.scoring.composite import PROCESSED_DIR, SCORE_COLUMNS


@pytest.fixture(scope="module")
def risk_df():
    path = PROCESSED_DIR / "chainage_risk.parquet"
    if not path.exists():
        pytest.skip("run `python -m src.scoring.composite` first")
    return pd.read_parquet(path)


def test_one_row_per_segment(risk_df):
    assert risk_df["chainage_m"].is_unique


def test_every_score_paired_with_confidence(risk_df):
    for name, score_col in SCORE_COLUMNS.items():
        confidence_col = f"{name}_confidence"
        if score_col in risk_df.columns:
            assert confidence_col in risk_df.columns, f"{score_col} has no paired confidence column"


def test_no_nulls_in_composite(risk_df):
    assert risk_df["composite_score"].notna().all()


def test_robust_hotspot_count_is_discriminating(risk_df):
    count = risk_df["robust_hotspot"].sum()
    # Pack §7: 8-20 is healthy; 100 means no discrimination, 2 means degenerate
    # weights.
    assert 8 <= count <= 20
