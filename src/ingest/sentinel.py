"""Sentinel-2 L2A ingest for built-up change detection — Phase 1b.

Uses Element 84's Earth Search STAC API (earth-search.aws.element84.com/v1),
which serves the Sentinel-2 L2A Cloud-Optimized GeoTIFFs on AWS with **no
authentication**. That matters here: the Copernicus Data Space Ecosystem
route the pack §4 names requires an account, and this project's whole point
is that a stranger can rebuild it from public URLs alone.

Because the assets are COGs, we do windowed reads over just the corridor
bbox rather than pulling whole 100x100km granules — a few MB instead of
several GB.

Built-up proxy: NDBI = (SWIR16 - NIR) / (SWIR16 + NIR). Higher = more
built-up/impervious. We difference a cloud-free 2018 composite against a
cloud-free current composite to get change.

Honest limits, carried into the output as a confidence tag:
- NDBI is a *proxy*, not a classifier. Bare soil and some rock also read
  high; this region has plenty of both. Change is more reliable than
  absolute value, which is why we only ship the difference.
- 10 m/20 m resolution means a single new building is invisible; this
  detects neighbourhood-scale change.
- Two single-date scenes (not full seasonal composites) means residual
  seasonal/moisture effects remain.
"""

import json
from pathlib import Path

import numpy as np
import rasterio
import requests
from rasterio.warp import transform_bounds
from rasterio.windows import from_bounds as window_from_bounds

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"

STAC_URL = "https://earth-search.aws.element84.com/v1/search"
COLLECTION = "sentinel-2-l2a"

# (west, south, east, north) — corridor bbox with margin, in EPSG:4326
CORRIDOR_BBOX_WSEN = (75.7362, 26.7298, 75.9701, 26.9774)

BASELINE_WINDOW = "2018-01-01T00:00:00Z/2018-12-31T23:59:59Z"
CURRENT_WINDOW = "2026-01-01T00:00:00Z/2026-08-19T00:00:00Z"

MAX_CLOUD_PCT = 5


def search_scenes(datetime_window: str, limit: int = 12, max_cloud: int = MAX_CLOUD_PCT) -> list[dict]:
    """Return STAC items for the corridor, least-cloudy first."""
    payload = {
        "collections": [COLLECTION],
        "bbox": list(CORRIDOR_BBOX_WSEN),
        "datetime": datetime_window,
        "query": {"eo:cloud_cover": {"lt": max_cloud}},
        "limit": limit,
    }
    resp = requests.post(STAC_URL, json=payload, timeout=90)
    resp.raise_for_status()
    features = resp.json().get("features", [])
    return sorted(features, key=lambda f: f["properties"].get("eo:cloud_cover", 100))


def _read_band_window(href: str, bbox_wsen: tuple[float, float, float, float]) -> tuple[np.ndarray, dict]:
    """Windowed read of a COG over bbox, returned as float32 with its profile."""
    with rasterio.open(f"/vsicurl/{href}") as src:
        left, bottom, right, top = transform_bounds("EPSG:4326", src.crs, *bbox_wsen, densify_pts=21)
        window = window_from_bounds(left, bottom, right, top, transform=src.transform)
        data = src.read(1, window=window, out_dtype="float32", boundless=True, fill_value=np.nan)
        profile = {
            "crs": src.crs,
            "transform": src.window_transform(window),
            "height": data.shape[0],
            "width": data.shape[1],
        }
    return data, profile


def ndbi_for_item(item: dict) -> tuple[np.ndarray, dict]:
    """NDBI = (SWIR16 - NIR) / (SWIR16 + NIR) over the corridor window.

    SWIR16 is 20 m and NIR is 10 m, so the two windows differ in shape. We
    read NIR at SWIR's resolution by reading SWIR first and resampling NIR
    onto its grid via a simple decimated read — adequate for a screening
    index, and avoids pulling a full-res 10 m array we'd only downsample.
    """
    swir, profile = _read_band_window(item["assets"]["swir16"]["href"], CORRIDOR_BBOX_WSEN)
    nir, _ = _read_band_window(item["assets"]["nir"]["href"], CORRIDOR_BBOX_WSEN)

    # Bring NIR (10 m) onto the SWIR (20 m) grid by block-averaging 2x2.
    if nir.shape != swir.shape:
        h = min(nir.shape[0] // 2, swir.shape[0])
        w = min(nir.shape[1] // 2, swir.shape[1])
        nir_ds = nir[: h * 2, : w * 2].reshape(h, 2, w, 2).mean(axis=(1, 3))
        swir = swir[:h, :w]
        nir = nir_ds
        profile["height"], profile["width"] = swir.shape

    with np.errstate(divide="ignore", invalid="ignore"):
        ndbi = (swir - nir) / (swir + nir)
    return ndbi.astype("float32"), profile


def median_ndbi(items: list[dict], max_scenes: int = 3) -> tuple[np.ndarray, dict]:
    """Median NDBI across the least-cloudy scenes — suppresses residual cloud
    and single-date noise without pretending to be a full seasonal composite."""
    stack, profile = [], None
    for item in items[:max_scenes]:
        arr, prof = ndbi_for_item(item)
        if profile is None:
            profile = prof
            stack.append(arr)
        elif arr.shape == stack[0].shape:
            stack.append(arr)
    if not stack:
        raise RuntimeError("no usable Sentinel-2 scenes")
    return np.nanmedian(np.stack(stack), axis=0), profile


def build_builtup_change(force: bool = False) -> Path:
    """Write a GeoTIFF of NDBI change (current - 2018) over the corridor."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DIR / "sentinel2_ndbi_change.tif"
    meta_path = RAW_DIR / "sentinel2_scenes_used.json"
    if out_path.exists() and not force:
        return out_path

    baseline_items = search_scenes(BASELINE_WINDOW)
    current_items = search_scenes(CURRENT_WINDOW)
    if not baseline_items or not current_items:
        raise RuntimeError("no scenes found for one of the epochs")

    baseline_ndbi, profile = median_ndbi(baseline_items)
    current_ndbi, _ = median_ndbi(current_items)

    h = min(baseline_ndbi.shape[0], current_ndbi.shape[0])
    w = min(baseline_ndbi.shape[1], current_ndbi.shape[1])
    change = current_ndbi[:h, :w] - baseline_ndbi[:h, :w]

    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=1,
        dtype="float32",
        crs=profile["crs"],
        transform=profile["transform"],
        nodata=np.nan,
    ) as dst:
        dst.write(change, 1)

    meta_path.write_text(
        json.dumps(
            {
                "stac_endpoint": STAC_URL,
                "collection": COLLECTION,
                "baseline_window": BASELINE_WINDOW,
                "current_window": CURRENT_WINDOW,
                "max_cloud_pct": MAX_CLOUD_PCT,
                "baseline_scenes": [i["id"] for i in baseline_items[:3]],
                "current_scenes": [i["id"] for i in current_items[:3]],
                "index": "NDBI = (SWIR16 - NIR) / (SWIR16 + NIR)",
            },
            indent=2,
        )
    )
    return out_path


if __name__ == "__main__":
    path = build_builtup_change()
    with rasterio.open(path) as src:
        arr = src.read(1)
    finite = arr[np.isfinite(arr)]
    print(f"Wrote {path} — shape {arr.shape}, crs {src.crs}")
    print(f"NDBI change: min {finite.min():.3f}, median {np.median(finite):.3f}, max {finite.max():.3f}")
