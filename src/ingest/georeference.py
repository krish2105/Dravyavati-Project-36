"""Georeferencing the JDA Zonal Development Plan sheets — in progress.

Status: the blocker has moved, and moved favourably, but this is NOT finished
and no zoning attribute is attached to any chainage yet.

What was established
--------------------
The earlier assessment ("scans with no coordinate system, needs hand-picked
control points") was wrong in an important way. The ZDP sheets carry a
**labelled geographic graticule** — a meridian tick reading 75°40'30"E is
printed on the top neatline of Final_ZDP_10.jpg, with its line running down
the map — and a **graphic scale bar** (…1.3 … 1.95, kilometres) in the title
block. A sheet with a labelled graticule is georeferenceable to survey
precision from the sheet alone. No eyeballed control points are required.

Measured so far, on Final_ZDP_10.jpg (10800 x 14706 px):
  neatline   left x=336, right x=8109, top y=215, bottom y=13520
  meridian   75°40'30"E at x ≈ 1065 (pixel signature below)

The graticule is drawn in a blue-dominant ink distinguishable from the black
neatline and text: at the meridian, mean RGB ≈ (172, 163, 199), i.e. B−R ≈ 27
and B−G ≈ 36 against a paper background near (250, 250, 250).

Why it is not finished
----------------------
Detecting the graticule by that colour signature also selects drawn
watercourses and minor roads, which are inked in a similar blue. Column
coverage for true graticule lines is not separable from those features by a
simple threshold — see `detect_graticule_candidates` below, which returns
roughly twenty candidate meridians where only a handful are real.

Completing this needs one of:
  * reading two or more graticule labels off the neatline to fix the
    interval (likely 2'30"), then keeping only candidate lines that fall on
    that spacing — the labels are legible in native-resolution crops of the
    neatline margin;
  * or a Hough transform restricted to full-height straight segments, which
    separates ruled graticule from meandering drainage geometrically.

Either is a contained piece of work. It was not rushed to completion here
because a transform fitted from mis-identified lines would assign wrong land
use to real chainages while looking entirely plausible — the failure mode
CLAUDE.md invariants 1 and 2 exist to prevent, and the one that would do most
damage to this project's credibility if it reached a reviewer.

No zoning layer is exported until a transform exists **and** its RMS
residual is published alongside it.
"""

from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
ZDP_DIR = REPO_ROOT / "data" / "raw" / "jda_zdp"

# Measured on Final_ZDP_10.jpg. Re-measure per sheet; these are not universal.
SHEET_10 = {
    "file": "Final_ZDP_10.jpg",
    "size_px": (10800, 14706),
    "neatline": {"left": 336, "right": 8109, "top": 215, "bottom": 13520},
    "known_meridian": {"label": "75°40'30\"E", "degrees": 75 + 40 / 60 + 30 / 3600, "x_px": 1065},
    "scale_bar_labels_km": [1.3, 1.95],
}

# Graticule ink versus paper, measured at the known meridian.
GRATICULE_BLUE_DOMINANCE = 18
GRATICULE_MAX_BRIGHTNESS = 235


def detect_graticule_candidates(sheet_path: Path, neatline: dict) -> tuple[list[int], list[int]]:
    """Return candidate meridian/parallel pixel positions.

    Honest about its own precision: this over-selects, because drawn
    watercourses share the graticule's blue ink. Callers must disambiguate
    against a known graticule interval before fitting any transform.
    """
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None
    arr = np.asarray(Image.open(sheet_path).convert("RGB")).astype(np.int16)
    red, green, blue = arr[..., 0], arr[..., 1], arr[..., 2]

    is_graticule_ink = (
        (blue - red > GRATICULE_BLUE_DOMINANCE)
        & (blue - green > GRATICULE_BLUE_DOMINANCE)
        & (blue < GRATICULE_MAX_BRIGHTNESS)
    )

    interior = is_graticule_ink[
        neatline["top"] + 30 : neatline["bottom"] - 30,
        neatline["left"] + 30 : neatline["right"] - 30,
    ]

    def ridges(signal: np.ndarray, min_fraction: float, gap: int) -> list[int]:
        threshold = signal.max() * min_fraction
        hits = np.where(signal > threshold)[0]
        groups: list[list[int]] = []
        for i in hits:
            if not groups or i - groups[-1][-1] > gap:
                groups.append([int(i)])
            else:
                groups[-1].append(int(i))
        return [int(np.mean(g)) for g in groups]

    meridians = [x + neatline["left"] + 30 for x in ridges(interior.sum(0), 0.45, 80)]
    parallels = [y + neatline["top"] + 30 for y in ridges(interior.sum(1), 0.45, 80)]
    return meridians, parallels


if __name__ == "__main__":
    path = ZDP_DIR / SHEET_10["file"]
    if not path.exists():
        raise SystemExit("Run `python -m src.ingest.zoning` first to fetch the sheets.")
    meridians, parallels = detect_graticule_candidates(path, SHEET_10["neatline"])
    print(f"{len(meridians)} candidate meridians, {len(parallels)} candidate parallels")
    print("Over-selected — drainage shares the graticule's ink. See module docstring.")
    print("No transform fitted, no zoning exported.")
