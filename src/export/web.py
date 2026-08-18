"""parquet -> web assets for the viewer.

Emits three files into web/public/data/:
  chainage_risk.geojson   the scored corridor geometry
  analytics.json          derived summaries the UI charts read directly
  feature_importance.json the neural surrogate's permutation importances
"""

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
PARQUET_PATH = PROCESSED_DIR / "chainage_risk.parquet"
WEB_DATA_DIR = REPO_ROOT / "web" / "public" / "data"

CONSTRAINTS = [
    ("railway_crossing", "Railway crossing"),
    ("metro_interface", "Metro interface"),
    ("existing_elevated_structure", "Existing elevated structure"),
    ("major_arterial_crossing", "Major arterial crossing"),
    ("restricted_military_area", "Restricted / military area"),
    ("entry_exit_feasibility", "Entry–exit feasibility"),
    ("curve_severity", "Curve severity"),
    ("eht_line_crossing", "EHT line crossing"),
    ("dam_check_structure", "Dam / check structure"),
    ("land_availability", "Land availability"),
    ("habitation_proximity", "Habitation proximity"),
    ("builtup_growth", "Built-up growth since 2018"),
    ("hydraulic_sensitivity", "Hydraulic sensitivity"),
]


def _col_for(key: str) -> str:
    return "hydraulic_sensitivity_index" if key == "hydraulic_sensitivity" else f"{key}_score"


def _clusters(flags: pd.Series) -> int:
    return int((flags != flags.shift()).cumsum()[flags].nunique()) if flags.any() else 0


def build_analytics(df: pd.DataFrame) -> dict:
    df = df.sort_values("chainage_m").reset_index(drop=True)

    # Co-occurrence: how often does each constraint pair fire together?
    active = {}
    for key, _ in CONSTRAINTS:
        col = _col_for(key)
        if col not in df.columns:
            continue
        values = df[col].fillna(0)
        active[key] = (values * 3 >= 2).to_numpy() if key == "hydraulic_sensitivity" else (values >= 2).to_numpy()

    keys = list(active.keys())
    matrix = [[int((active[a] & active[b]).sum()) for b in keys] for a in keys]

    # Hotspot corridors as chainage ranges.
    corridors = []
    if "hotspot_corridor_id" in df.columns:
        for cid, group in df[df["hotspot_corridor_id"] >= 0].groupby("hotspot_corridor_id"):
            drivers = sorted(
                (
                    (label, float(group[_col_for(key)].mean() * (3 if key == "hydraulic_sensitivity" else 1)))
                    for key, label in CONSTRAINTS
                    if _col_for(key) in group.columns
                ),
                key=lambda kv: -kv[1],
            )[:3]
            corridors.append(
                {
                    "id": int(cid),
                    "start_m": int(group["chainage_m"].min()),
                    "end_m": int(group["chainage_m"].max() + 100),
                    "segments": int(len(group)),
                    "mean_composite": round(float(group["composite_score"].mean()), 3),
                    "top_drivers": [{"label": label, "mean_score": round(score, 2)} for label, score in drivers],
                }
            )
    corridors.sort(key=lambda c: -c["mean_composite"])

    profile = [
        {
            "chainage_m": int(row.chainage_m),
            "composite": round(float(row.composite_score), 4),
            "p05": round(float(getattr(row, "composite_mc_p05", np.nan)), 4),
            "p95": round(float(getattr(row, "composite_mc_p95", np.nan)), 4),
            "band": row.severity_band,
            "robust": bool(row.robust_hotspot),
            "anomaly": bool(getattr(row, "is_anomalous", False)),
        }
        for row in df.itertuples()
    ]

    return {
        "generated_from": "data/processed/chainage_risk.parquet",
        "corridor": {
            "length_km": round(float(df["segment_length_m"].sum() / 1000), 2),
            "segments": int(len(df)),
            "constraint_count": len(CONSTRAINTS),
        },
        "severity": df["severity_band"].value_counts().to_dict(),
        "robust_hotspots": int(df["robust_hotspot"].sum()),
        "anomalies": int(df["is_anomalous"].sum()) if "is_anomalous" in df.columns else 0,
        "uncertainty": {
            "mean_ci_width": round(float(df["composite_mc_width"].mean()), 4)
            if "composite_mc_width" in df.columns
            else None,
        },
        "crossings": {
            "railway": _clusters(df["railway_crossing_score"] == 3),
            "major_arterial": _clusters(df["major_arterial_crossing_score"] == 3),
            "dam_check_structure": _clusters(df["dam_check_structure_score"] == 3),
            "eht_line": _clusters(df["eht_line_crossing_score"] == 3),
            "cross_drainage": _clusters(df["cross_drainage_candidate"] == True)  # noqa: E712
            if "cross_drainage_candidate" in df.columns
            else 0,
        },
        "metro": df["metro_interface_status"].value_counts().to_dict()
        if "metro_interface_status" in df.columns
        else {},
        "irc86": {
            "min_radius_m": int(df["irc86_min_radius_m"].iloc[0]) if "irc86_min_radius_m" in df.columns else None,
            "segments_below": int((df["curve_severity_score"] == 3).sum()),
        },
        "land": {
            "mean_unbuilt_pct": round(float((1 - df["land_availability_frac_built"].mean()) * 100), 2),
            "buildings_within_100m": int(df["habitation_building_count"].sum()),
            "segments_with_buildings": int((df["habitation_building_count"] > 0).sum()),
        },
        "cooccurrence": {"labels": [dict(CONSTRAINTS)[k] for k in keys], "matrix": matrix},
        "hotspot_corridors": corridors,
        "profile": profile,
    }


def export_for_web() -> list[Path]:
    gdf = gpd.read_parquet(PARQUET_PATH)
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    written = []

    geo_path = WEB_DATA_DIR / "chainage_risk.geojson"
    gdf.to_file(geo_path, driver="GeoJSON")
    written.append(geo_path)

    analytics_path = WEB_DATA_DIR / "analytics.json"
    analytics_path.write_text(json.dumps(build_analytics(pd.DataFrame(gdf.drop(columns="geometry"))), indent=1))
    written.append(analytics_path)

    importance_csv = PROCESSED_DIR / "feature_importance.csv"
    if importance_csv.exists():
        imp = pd.read_csv(importance_csv)
        label_by_col = {_col_for(k): label for k, label in CONSTRAINTS}
        imp["label"] = imp["feature"].map(label_by_col).fillna(imp["feature"])
        importance_path = WEB_DATA_DIR / "feature_importance.json"
        importance_path.write_text(
            json.dumps(
                {
                    "surrogate_r2": round(float(imp["surrogate_r2"].iloc[0]), 4),
                    "features": [
                        {
                            "label": row.label,
                            "importance": round(float(row.importance_mean), 5),
                            "std": round(float(row.importance_std), 5),
                        }
                        for row in imp.itertuples()
                    ],
                },
                indent=1,
            )
        )
        written.append(importance_path)

    return written


if __name__ == "__main__":
    for path in export_for_web():
        print(f"Wrote {path.relative_to(REPO_ROOT)} ({path.stat().st_size / 1024:.0f} KB)")
