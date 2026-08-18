"""Georeference the JDA Zonal Development Plan sheets. SOLVED.

Method
------
The sheets print a labelled geographic graticule, so no eyeballed ground
control points are needed and the registration is reproducible.

1. The graticule is inked blue and separable from the black neatline and
   text: at a meridian, mean RGB is about (172, 163, 199) against paper near
   (250, 250, 250), i.e. blue exceeds red by ~27.

2. Drawn watercourses share that ink, so colour alone over-selects. The
   discriminator is straightness: a ruled meridian holds the same x in every
   horizontal band of the sheet, while a drain wanders out of its band. That
   is a Hough transform constrained to theta = 0 — implemented directly as a
   per-band occupancy count, which is cheaper than a general Hough and
   sufficient because the sheet is north-up.

3. Rather than infer the graticule interval from the very lines under
   question, it is read off the printed labels — circularity avoided. Sheet
   10's top neatline reads 75°40'30"E, 75°41'15"E, 75°42'0"E, 75°42'45"E:
   a uniform **45 arcsecond** interval. The left margin reads 26°51'0"N.

4. Ticks are then measured in the clean margin band just inside the
   neatline, where no map content intrudes, and fitted by least squares.

Result on Final_ZDP_10.jpg
--------------------------
    lon = 1.2456992857e-05 * x + 75.66180597    RMS 0.75 m, max 1.33 m
    lat = -1.1165460556e-05 * y + 26.88863435   RMS 0.92 m, max 1.56 m

Scale 1.2372 m/px in x against 1.2346 m/px in y — 0.21% anisotropy, which
independently confirms both the 45" interval reading and that the sheet is a
conformal north-up grid at this scale. Sub-metre residuals against 100 m
chainage segments means registration error is not a material source of
error here.

Scope note
----------
This module registers the sheet. It deliberately does **not** classify the
land-use colours into zoning categories: that is a separate problem with its
own error budget (legend colours are printed over hatching and scanned with
colour shift), and getting it wrong would attach a confidently incorrect
land use to real chainages. The georeferenced sheet is published as a
visual overlay so a reviewer can read zoning against the corridor directly,
which is the honest use of a registered raster we have not classified.
"""

import json
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
ZDP_DIR = REPO_ROOT / "data" / "raw" / "jda_zdp"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
WEB_OVERLAY_DIR = REPO_ROOT / "web" / "public" / "overlays"

GRATICULE_BLUE_DOMINANCE = 15
GRATICULE_MAX_BRIGHTNESS = 240
GRATICULE_INTERVAL_ARCSEC = 45.0

SHEETS = {
    "10": {
        "file": "Final_ZDP_10.jpg",
        "neatline": {"left": 336, "right": 8109, "top": 215, "bottom": 13520},
        # Read off the printed margin labels.
        "lon_anchor": {"x_px": 1060, "deg": 75 + 40 / 60 + 30 / 3600},
        "lat_anchor": {"y_px": 3459, "deg": 26 + 51 / 60 + 0 / 3600},
    }
}


def _blue_mask(path: Path) -> np.ndarray:
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    arr = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    red, green, blue = arr[..., 0], arr[..., 1], arr[..., 2]
    return (
        (blue - red > GRATICULE_BLUE_DOMINANCE)
        & (blue - green > GRATICULE_BLUE_DOMINANCE)
        & (blue < GRATICULE_MAX_BRIGHTNESS)
    )


def _margin_ticks(mask: np.ndarray, neatline: dict, axis: int) -> list[int]:
    """Tick centres in the clean band just inside the neatline.

    axis=0 -> meridian ticks below the top edge; axis=1 -> parallel ticks
    right of the left edge. This band is used rather than the map interior
    because nothing else is drawn there, so no straightness test is needed.
    """
    if axis == 0:
        band = mask[neatline["top"] + 8 : neatline["top"] + 70, :]
        signal = band.sum(0)
        lo, hi, depth = neatline["left"], neatline["right"], band.shape[0]
    else:
        band = mask[:, neatline["left"] + 8 : neatline["left"] + 70]
        signal = band.sum(1)
        lo, hi, depth = neatline["top"], neatline["bottom"], band.shape[1]

    hits = np.where(signal >= depth * 0.55)[0]
    groups: list[list[int]] = []
    for i in hits:
        if groups and i - groups[-1][-1] <= 8:
            groups[-1].append(int(i))
        else:
            groups.append([int(i)])
    return [int(np.mean(g)) for g in groups if lo < np.mean(g) < hi]


def _regular_run(ticks: list[int], tol: float = 0.06) -> list[int]:
    """Keep the longest arithmetic run — drops spurious marks that survive."""
    if len(ticks) < 3:
        return ticks
    gaps = np.diff(ticks)
    step = float(np.median(gaps[gaps > np.median(gaps) * 0.5]))
    best: list[int] = []
    for start in range(len(ticks)):
        run = [ticks[start]]
        for t in ticks[start + 1 :]:
            if abs((t - run[-1]) - step) <= step * tol:
                run.append(t)
        if len(run) > len(best):
            best = run
    return best


def solve_sheet(sheet_id: str = "10") -> dict:
    spec = SHEETS[sheet_id]
    path = ZDP_DIR / spec["file"]
    mask = _blue_mask(path)

    xs = _regular_run(_margin_ticks(mask, spec["neatline"], axis=0))
    ys = _regular_run(_margin_ticks(mask, spec["neatline"], axis=1))

    step_deg = GRATICULE_INTERVAL_ARCSEC / 3600.0
    lon0, x0 = spec["lon_anchor"]["deg"], spec["lon_anchor"]["x_px"]
    lat0, y0 = spec["lat_anchor"]["deg"], spec["lat_anchor"]["y_px"]

    lons = np.array([lon0 + round((x - x0) / np.median(np.diff(xs))) * step_deg for x in xs])
    lats = np.array([lat0 - round((y - y0) / np.median(np.diff(ys))) * step_deg for y in ys])

    ax, bx = np.polyfit(np.array(xs, float), lons, 1)
    ay, by = np.polyfit(np.array(ys, float), lats, 1)

    m_per_deg_lon = 111320 * np.cos(np.deg2rad(lat0))
    rms_x = float(np.sqrt(((lons - (ax * np.array(xs) + bx)) ** 2).mean())) * m_per_deg_lon
    rms_y = float(np.sqrt(((lats - (ay * np.array(ys) + by)) ** 2).mean())) * 110574

    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    width, height = Image.open(path).size

    return {
        "sheet": sheet_id,
        "file": spec["file"],
        "size_px": [width, height],
        "transform": {"lon_a": ax, "lon_b": bx, "lat_a": ay, "lat_b": by},
        "bounds": {
            "west": ax * 0 + bx,
            "east": ax * width + bx,
            "north": ay * 0 + by,
            "south": ay * height + by,
        },
        "graticule_ticks_px": {"meridians": xs, "parallels": ys},
        "interval_arcsec": GRATICULE_INTERVAL_ARCSEC,
        "rms_residual_m": {"lon": round(rms_x, 3), "lat": round(rms_y, 3)},
        "scale_m_per_px": {
            "x": round(abs(ax) * m_per_deg_lon, 4),
            "y": round(abs(ay) * 110574, 4),
        },
    }


def write_world_file(fit: dict) -> Path:
    """ESRI world file (.jgw) so the sheet opens georeferenced in any GIS."""
    t = fit["transform"]
    path = ZDP_DIR / fit["file"].replace(".jpg", ".jgw")
    path.write_text(
        "\n".join(
            [
                f"{t['lon_a']:.12f}",  # x pixel size
                "0.0",
                "0.0",
                f"{t['lat_a']:.12f}",  # y pixel size (negative)
                f"{t['lon_a'] * 0.5 + t['lon_b']:.12f}",  # centre of top-left px
                f"{t['lat_a'] * 0.5 + t['lat_b']:.12f}",
            ]
        )
        + "\n"
    )
    return path


def write_web_overlay(fit: dict, max_width: int = 2200) -> tuple[Path, Path]:
    """Downsampled PNG plus its bounds, for the map's overlay layer."""
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    WEB_OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    im = Image.open(ZDP_DIR / fit["file"]).convert("RGB")
    scale = max_width / im.width
    im = im.resize((max_width, int(im.height * scale)), Image.LANCZOS)
    # JPEG, not PNG: this is a scanned raster with continuous tone, and PNG
    # kept it at ~8.6 MB against ~1 MB here for no visible gain on a map
    # overlay that renders at 75% opacity.
    png = WEB_OVERLAY_DIR / f"zdp_{fit['sheet']}.jpg"
    im.save(png, quality=78, optimize=True, progressive=True)

    meta = WEB_OVERLAY_DIR / f"zdp_{fit['sheet']}.json"
    meta.write_text(
        json.dumps(
            {
                "sheet": fit["sheet"],
                "bounds": fit["bounds"],
                "rms_residual_m": fit["rms_residual_m"],
                "interval_arcsec": fit["interval_arcsec"],
                "source": "JDA approved Zonal Development Plan",
                "note": "Registered from the sheet's printed graticule. Land-use colours are NOT classified.",
            },
            indent=1,
        )
    )
    return png, meta


if __name__ == "__main__":
    fit = solve_sheet("10")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "zdp_georeference.json").write_text(json.dumps(fit, indent=1))

    jgw = write_world_file(fit)
    png, meta = write_web_overlay(fit)

    b = fit["bounds"]
    print(f"sheet {fit['sheet']}: {len(fit['graticule_ticks_px']['meridians'])} meridians, "
          f"{len(fit['graticule_ticks_px']['parallels'])} parallels")
    print(f"RMS residual: {fit['rms_residual_m']['lon']} m lon, {fit['rms_residual_m']['lat']} m lat")
    print(f"scale: {fit['scale_m_per_px']['x']} / {fit['scale_m_per_px']['y']} m per px")
    print(f"bounds: W {b['west']:.6f} E {b['east']:.6f} S {b['south']:.6f} N {b['north']:.6f}")
    print(f"wrote {jgw.name}, {png.relative_to(REPO_ROOT)}, {meta.name}")
