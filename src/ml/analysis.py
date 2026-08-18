"""Machine-learning layer over the chainage constraint matrix.

Design rule for everything in this module: no model here predicts a quantity
we have no ground truth for. There is no observed traffic count, no tendered
cost, no gauged flood record in this repository, so nothing here outputs a
traffic volume, a cost, or a flood depth. Every method below is either
unsupervised (finds structure that is already in the data) or a surrogate
that explains the composite score we computed ourselves. That is what keeps
the output defensible to an engineer who asks "where did this number come
from".

Four methods:

1. Monte Carlo uncertainty  — the composite is a weighted sum of scores with
   known confidence tiers. Sampling weight and score perturbation thousands
   of times turns "composite = 0.42" into "0.42, 90% CI [0.31, 0.55]", which
   is the honest form of the same statement.

2. DBSCAN hotspot corridors — hotspots arrive as isolated 100 m segments.
   Engineering decisions are made over contiguous stretches. Clustering along
   chainage turns scattered segments into named corridors with an extent.

3. Isolation Forest anomaly detection — finds chainages whose *combination*
   of constraints is unusual, even when no single constraint is extreme. A
   segment that is mid-range on eight things at once is a real design problem
   that a per-constraint threshold never surfaces.

4. Neural surrogate + permutation importance — a small MLP is fitted to
   reproduce the composite from the constraint vector, then each feature is
   shuffled to measure how much the surrogate degrades. This answers "which
   constraint is actually driving the ranking", which is the question a
   reviewer asks immediately after seeing a ranked list.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
from sklearn.inspection import permutation_importance
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

RANDOM_SEED = 42

CONSTRAINT_SCORE_COLUMNS = [
    "railway_crossing_score",
    "metro_interface_score",
    "existing_elevated_structure_score",
    "major_arterial_crossing_score",
    "restricted_military_area_score",
    "eht_line_crossing_score",
    "dam_check_structure_score",
    "curve_severity_score",
    "entry_exit_feasibility_score",
    "land_availability_score",
    "habitation_proximity_score",
    "builtup_growth_score",
]

# Confidence tier -> how much we let a score wobble in the Monte Carlo.
# A "low" confidence layer (OSM power lines, NDBI proxy) is allowed to be
# wrong by a whole point; a "high" one barely moves.
CONFIDENCE_SIGMA = {"high": 0.15, "medium": 0.45, "low": 1.0}


def _feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    cols = [c for c in CONSTRAINT_SCORE_COLUMNS if c in df.columns]
    matrix = df[cols].fillna(0).to_numpy(dtype=float)
    if "hydraulic_sensitivity_index" in df.columns:
        hydraulic = (df["hydraulic_sensitivity_index"].fillna(0) * 3).to_numpy(dtype=float)
        matrix = np.column_stack([matrix, hydraulic])
        cols = cols + ["hydraulic_sensitivity_index"]
    return matrix, cols


def _sigma_for(df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    """Per-column, per-row perturbation scale from each layer's confidence tag."""
    sigmas = np.zeros((len(df), len(cols)))
    for j, col in enumerate(cols):
        base = col.replace("_score", "").replace("_index", "")
        conf_col = f"{base}_confidence"
        if conf_col in df.columns:
            sigmas[:, j] = df[conf_col].map(CONFIDENCE_SIGMA).fillna(0.45).to_numpy()
        else:
            sigmas[:, j] = 0.45
    return sigmas


def monte_carlo_uncertainty(df: pd.DataFrame, n_runs: int = 5000) -> pd.DataFrame:
    """Composite confidence interval from joint weight + score uncertainty."""
    rng = np.random.default_rng(RANDOM_SEED)
    matrix, cols = _feature_matrix(df)
    sigmas = _sigma_for(df, cols)
    n_features = matrix.shape[1]

    draws = np.empty((n_runs, len(df)), dtype=np.float32)
    for i in range(n_runs):
        # Weights wander around equal-weight; scores wander by their confidence.
        weights = rng.uniform(0.65, 1.35, size=n_features)
        perturbed = np.clip(matrix + rng.normal(0, sigmas), 0, 3)
        draws[i] = (perturbed @ weights) / weights.sum()

    out = df.copy()
    out["composite_mc_mean"] = draws.mean(axis=0)
    out["composite_mc_p05"] = np.percentile(draws, 5, axis=0)
    out["composite_mc_p95"] = np.percentile(draws, 95, axis=0)
    out["composite_mc_width"] = out["composite_mc_p95"] - out["composite_mc_p05"]
    return out


def cluster_hotspot_corridors(df: pd.DataFrame, eps_m: float = 600, min_samples: int = 2) -> pd.DataFrame:
    """Group robust hotspots into contiguous corridors along chainage."""
    out = df.copy()
    out["hotspot_corridor_id"] = -1

    hotspots = out[out.get("robust_hotspot", False) == True]  # noqa: E712
    if len(hotspots) < min_samples:
        return out

    coords = hotspots[["chainage_m"]].to_numpy(dtype=float)
    labels = DBSCAN(eps=eps_m, min_samples=min_samples).fit_predict(coords)
    out.loc[hotspots.index, "hotspot_corridor_id"] = labels
    return out


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> pd.DataFrame:
    """Flag chainages whose constraint *combination* is unusual."""
    matrix, _ = _feature_matrix(df)
    scaled = StandardScaler().fit_transform(matrix)

    model = IsolationForest(contamination=contamination, random_state=RANDOM_SEED, n_estimators=300)
    labels = model.fit_predict(scaled)

    out = df.copy()
    # sklearn returns -1 for outliers; invert so higher = more anomalous.
    out["anomaly_score"] = -model.score_samples(scaled)
    out["is_anomalous"] = labels == -1
    return out


def surrogate_importance(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit a small neural net to the composite, then rank features by
    permutation importance. Returns (df unchanged, importance table)."""
    matrix, cols = _feature_matrix(df)
    target = df["composite_score"].to_numpy(dtype=float)

    scaler = StandardScaler().fit(matrix)
    scaled = scaler.transform(matrix)

    model = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation="relu",
        random_state=RANDOM_SEED,
        max_iter=2000,
        early_stopping=True,
    ).fit(scaled, target)

    result = permutation_importance(model, scaled, target, n_repeats=20, random_state=RANDOM_SEED)
    importance = (
        pd.DataFrame(
            {
                "feature": cols,
                "importance_mean": result.importances_mean,
                "importance_std": result.importances_std,
            }
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )
    importance["surrogate_r2"] = model.score(scaled, target)
    return df, importance


def run_all(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = monte_carlo_uncertainty(df)
    df = cluster_hotspot_corridors(df)
    df = detect_anomalies(df)
    df, importance = surrogate_importance(df)
    return df, importance


if __name__ == "__main__":
    import geopandas as gpd

    gdf = gpd.read_parquet(PROCESSED_DIR / "chainage_risk.parquet")
    enriched, importance = run_all(gdf)

    enriched.to_parquet(PROCESSED_DIR / "chainage_risk.parquet")
    importance.to_csv(PROCESSED_DIR / "feature_importance.csv", index=False)

    n_corridors = enriched.loc[enriched["hotspot_corridor_id"] >= 0, "hotspot_corridor_id"].nunique()
    print(f"Monte Carlo: mean CI width {enriched['composite_mc_width'].mean():.3f}")
    print(f"Hotspot corridors: {n_corridors} from {int(enriched['robust_hotspot'].sum())} robust segments")
    print(f"Anomalies: {int(enriched['is_anomalous'].sum())} segments")
    print(f"Surrogate R^2: {importance['surrogate_r2'].iloc[0]:.3f}")
    print("Top drivers:")
    for _, row in importance.head(5).iterrows():
        print(f"  {row['feature']:<38} {row['importance_mean']:.4f}")
