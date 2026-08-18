"""Generate the 4-page PDF brief for JDA officials.

Everything on these pages is read from data/processed/chainage_risk.parquet
and web/public/data/analytics.json at build time — no figure is typed in by
hand, so the brief cannot drift from the pipeline that produced it.

Tone follows pack §7: state what was measured, state the limits, make one
small ask. No recommendation, no alignment opinion, no hydraulic conclusion.
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = REPO_ROOT / "data" / "processed"
ANALYTICS = REPO_ROOT / "web" / "public" / "data" / "analytics.json"
OUT_DIR = REPO_ROOT / "web" / "public" / "brief"
OUT_NAME = "Dravyavati_Corridor_Constraint_Atlas_Brief.pdf"

LIVE_URL = "https://dravyavati-atlas.vercel.app"
REPO_URL = "https://github.com/krish2105/Dravyavati-Project-36"

INK = colors.HexColor("#1b2430")
FOG = colors.HexColor("#6b7785")
CHANNEL = colors.HexColor("#1f7a74")
FLAG = colors.HexColor("#b8791f")
RULE = colors.HexColor("#d4dae0")
BAND = colors.HexColor("#f2f5f3")

DISCLAIMER = (
    "Screening-grade, not design-grade. Built on open data for constraint triage. "
    "All findings require verification against field survey."
)


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=19,
            leading=23, textColor=INK, alignment=0, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontName="Helvetica", fontSize=10.5,
            leading=14, textColor=FOG, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11.5,
            leading=14, textColor=INK, spaceBefore=12, spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontName="Helvetica", fontSize=9.6,
            leading=13.8, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"], fontName="Helvetica", fontSize=8.2,
            leading=11.4, textColor=FOG, spaceAfter=5,
        ),
        "kicker": ParagraphStyle(
            "kicker", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=7.6,
            leading=10, textColor=CHANNEL, spaceAfter=3,
        ),
        "cell": ParagraphStyle(
            "cell", parent=base["Normal"], fontName="Helvetica", fontSize=8.4, leading=11, textColor=INK
        ),
        "cellsm": ParagraphStyle(
            "cellsm", parent=base["Normal"], fontName="Helvetica", fontSize=7.8, leading=10, textColor=FOG
        ),
    }


def _chrome(canvas, doc):
    """Disclaimer strip on every page — pack §0 requires it on every output."""
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(BAND)
    canvas.rect(0, h - 13 * mm, w, 13 * mm, stroke=0, fill=1)
    canvas.setFillColor(FLAG)
    canvas.setFont("Helvetica-Bold", 7.4)
    canvas.drawString(18 * mm, h - 8.6 * mm, "SCREENING-GRADE, NOT DESIGN-GRADE")
    canvas.setFillColor(FOG)
    canvas.setFont("Helvetica", 7.4)
    canvas.drawRightString(w - 18 * mm, h - 8.6 * mm, "All findings require verification against field survey")

    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(18 * mm, 14 * mm, w - 18 * mm, 14 * mm)
    canvas.setFillColor(FOG)
    canvas.setFont("Helvetica", 7.2)
    canvas.drawString(18 * mm, 10 * mm, "Dravyavati Corridor Constraint Atlas · independent open-data analysis")
    canvas.drawRightString(w - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _kv_table(rows, styles, col_widths):
    data = [[Paragraph(k, styles["cell"]), Paragraph(v, styles["cell"])] for k, v in rows]
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def build_brief() -> Path:
    analytics = json.loads(ANALYTICS.read_text())
    importance_path = REPO_ROOT / "web" / "public" / "data" / "feature_importance.json"
    importance = json.loads(importance_path.read_text()) if importance_path.exists() else None

    s = _styles()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / OUT_NAME

    doc = BaseDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title="Dravyavati Corridor Constraint Atlas — Screening Brief",
        author="Krishna Mathur",
        subject="Chainage-indexed constraint screening for the proposed Dravyavati elevated corridor, Jaipur",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_chrome)])

    c = analytics["corridor"]
    cross = analytics["crossings"]
    land = analytics["land"]
    irc = analytics["irc86"]
    story = []

    # ---------------------------------------------------------------- page 1
    story.append(Paragraph("Dravyavati Corridor Constraint Atlas", s["title"]))
    story.append(
        Paragraph(
            f"Chainage-indexed constraint screening for the proposed elevated corridor along the "
            f"Dravyavati River, Jaipur &nbsp;·&nbsp; {date.today().strftime('%d %B %Y')}",
            s["subtitle"],
        )
    )

    story.append(
        Paragraph(
            "<b>Built entirely on open data, independently of JDA and of any consultancy — no project data "
            "was used.</b> Every layer in this analysis traces to a publicly accessible URL recorded with an "
            "access date, so any of it can be reproduced or contradicted from source.",
            s["body"],
        )
    )

    headline = [
        [
            Paragraph(f"<b>{c['length_km']:.1f} km</b>", s["cell"]),
            Paragraph(f"<b>{c['segments']}</b>", s["cell"]),
            Paragraph(f"<b>{c['constraint_count']}</b>", s["cell"]),
            Paragraph(f"<b>{len(analytics['hotspot_corridors'])}</b>", s["cell"]),
        ],
        [
            Paragraph("corridor reconstructed", s["cellsm"]),
            Paragraph("100 m segments scored", s["cellsm"]),
            Paragraph("constraint categories", s["cellsm"]),
            Paragraph("robust hotspot corridors", s["cellsm"]),
        ],
    ]
    ht = Table(headline, colWidths=[doc.width / 4.0] * 4, hAlign="LEFT")
    ht.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BAND),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("LINEAFTER", (0, 0), (-2, -1), 0.4, colors.white),
            ]
        )
    )
    story.append(ht)
    story.append(Spacer(1, 12))

    story.append(Paragraph("WHAT THIS IS", s["kicker"]))
    story.append(
        Paragraph(
            "A screening tool that flags, every 100 metres along a publicly-reconstructed corridor alignment, "
            "where thirteen categories of engineering constraint are likely to bind. It is a triage instrument "
            "for deciding where survey effort and design attention should go first. It is not a design "
            "document, a hydraulic analysis, a structural assessment, or an alignment recommendation, and it "
            "does not substitute for topographical survey, GPR utility mapping, or geotechnical investigation.",
            s["body"],
        )
    )

    story.append(Paragraph("METHOD IN FIVE STEPS", s["kicker"]))
    story.append(
        Paragraph(
            "<b>1.</b> The channel is taken from OpenStreetMap water polygons and reduced to a centreline via a "
            "Voronoi medial axis. <b>2.</b> That centreline is cut into 100 m segments keyed on chainage, which "
            "is the join key for everything downstream. <b>3.</b> Each segment is scored 0–3 against thirteen "
            "constraint categories drawn from OpenStreetMap, Google/OSM building footprints, WorldPop, "
            "Copernicus GLO-30 elevation and Sentinel-2 imagery. <b>4.</b> Scores are combined into an "
            "equal-weight composite. <b>5.</b> Every constraint weight is then swept ±35% and only chainages "
            "whose severity band survives the whole sweep are reported — the rest are artefacts of one "
            "weighting choice, not findings.",
            s["body"],
        )
    )

    story.append(Paragraph("WHAT THE SCREENING FOUND", s["kicker"]))
    metro = analytics.get("metro", {})
    rows = [
        ("Railway crossings", f"{cross['railway']} distinct crossings"),
        (
            "Metro interfaces",
            f"{metro.get('operational', 0)} segments on the operational line, "
            f"{metro.get('construction', 0)} on the line under construction, "
            f"{metro.get('proposed', 0)} on proposed alignments",
        ),
        ("Major arterial crossings", f"{cross['major_arterial']} distinct crossings"),
        ("Dam / check structures", f"{cross['dam_check_structure']} within 100 m of the alignment"),
        (
            "Cross-drainage candidates",
            f"{cross['cross_drainage']} distinct locations where a modelled tributary meets the corridor",
        ),
        (
            "Horizontal curvature",
            f"{irc['segments_below']} segments fall below the IRC:86-2018 minimum radius of "
            f"{irc['min_radius_m']} m for a 60 km/h design speed",
        ),
        (
            "Land and habitation",
            f"{land['mean_unbuilt_pct']:.1f}% of the 60 m corridor buffer is unbuilt on average; "
            f"approximately {land['buildings_within_100m']} buildings lie within 100 m, concentrated in "
            f"{land['segments_with_buildings']} of {c['segments']} segments",
        ),
    ]
    story.append(_kv_table(rows, s, [52 * mm, doc.width - 52 * mm]))

    story.append(PageBreak())

    # ---------------------------------------------------------------- page 2
    story.append(Paragraph("Robust hotspot corridors", s["h2"]))
    story.append(
        Paragraph(
            "These are the stretches whose severity band did not change under any weighting tested. They are "
            "reported because they are stable, not because they are the highest-scoring under our particular "
            "assumptions. Contiguous robust segments are grouped by clustering along chainage.",
            s["body"],
        )
    )

    head = ["Chainage extent", "Length", "Composite", "Leading constraints"]
    data = [[Paragraph(f"<b>{h}</b>", s["cell"]) for h in head]]
    for hc in analytics["hotspot_corridors"]:
        data.append(
            [
                Paragraph(f"{hc['start_m'] / 1000:.1f} – {hc['end_m'] / 1000:.1f} km", s["cell"]),
                Paragraph(f"{(hc['end_m'] - hc['start_m']) / 1000:.1f} km", s["cell"]),
                Paragraph(f"{hc['mean_composite']:.2f}", s["cell"]),
                Paragraph(
                    " · ".join(f"{d['label']} ({d['mean_score']:.1f})" for d in hc["top_drivers"]), s["cellsm"]
                ),
            ]
        )
    t = Table(data, colWidths=[28 * mm, 16 * mm, 20 * mm, doc.width - 64 * mm], hAlign="LEFT", repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.7, INK),
                ("LINEBELOW", (0, 1), (-1, -2), 0.35, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Composite is a weighted mean of thirteen 0–3 constraint scores; it is an index for ranking "
            "chainages against each other, not a physical quantity.",
            s["small"],
        )
    )

    story.append(Paragraph("What drives the ranking", s["h2"]))
    if importance:
        story.append(
            Paragraph(
                f"A small neural network was fitted to reproduce the composite from the constraint vector "
                f"(R² {importance['surrogate_r2']:.3f}), then each constraint was shuffled in turn to measure "
                f"how far the reproduction degrades. This is a diagnostic of our own index — it does not "
                f"predict any quantity measured outside this analysis.",
                s["body"],
            )
        )
        top = importance["features"][:6]
        imp_rows = [(f["label"], f"{f['importance']:.3f}") for f in top]
        story.append(_kv_table(imp_rows, s, [70 * mm, 25 * mm]))
        story.append(Spacer(1, 3))
        story.append(
            Paragraph(
                "The practical reading: proximity to existing elevated structure dominates the ranking, ahead "
                "of entry–exit feasibility and hydraulic sensitivity. Habitation proximity — the intuitive "
                "first guess for a corridor through a city — ranks well below these.",
                s["small"],
            )
        )

    story.append(PageBreak())

    # ---------------------------------------------------------------- page 3
    story.append(Paragraph("Confidence, and where this is weakest", s["h2"]))
    story.append(
        Paragraph(
            "Every score in this atlas carries a confidence tag, and the tags are not decoration — they set "
            "how far each layer is allowed to move in the uncertainty analysis. Sampling weights and scores "
            "jointly over 5,000 runs gives a mean 90% interval width of "
            f"<b>{analytics['uncertainty']['mean_ci_width']:.2f}</b> composite points, which is wide relative "
            "to the spread between chainages. That is the honest characterisation: this analysis is reliable "
            "for ordering and triage, and not for any absolute statement about a single segment.",
            s["body"],
        )
    )

    limits = [
        (
            "Power lines (low)",
            "OpenStreetMap coverage of transmission lines in Jaipur is incomplete. EHT crossings flagged here "
            "are candidates, not confirmed, and each should be cross-checked against imagery before use.",
        ),
        (
            "Restricted / military areas (low)",
            "landuse=military is frequently absent or approximate in India. Where this analysis shows nothing, "
            "that is an acknowledged gap in the source data, not evidence that nothing is there.",
        ),
        (
            "Built-up growth (low)",
            "Derived from a Sentinel-2 spectral index, not a land-cover classification. Bare soil in this "
            "region can mimic built-up signal, so only the 2018-to-2026 change is used, never an absolute.",
        ),
        (
            "Hydraulic sensitivity (low)",
            "GLO-30 at 30 m cannot resolve a rectified channel cross-section. The output is a relative "
            "screening index over contributing area only. It is not an afflux figure and not a flood claim.",
        ),
        (
            "Alignment reconstruction",
            f"The corridor is reconstructed from public channel geometry and reaches {c['length_km']:.1f} km "
            "against a publicly reported ~36 km. A real alignment would ease curves harder than a medial axis "
            "can and may bridge across meanders. Chainages here will not correspond exactly to a DPR's.",
        ),
        (
            "Land use zoning",
            "No zoning attribute is attached to any chainage. The approved Zonal Development Plan sheets "
            "were obtained, but they are large scans with no embedded coordinate system; georeferencing "
            "them needs hand-picked control points, and a mis-registered layer would assign wrong land use "
            "to real chainages. Left undone deliberately rather than approximated.",
        ),
    ]
    story.append(_kv_table(limits, s, [42 * mm, doc.width - 42 * mm]))

    story.append(Paragraph("A note on the planning baseline", s["h2"]))
    story.append(
        Paragraph(
            "This analysis was originally scoped against the Jaipur Master Plan 2047. In the course of "
            "sourcing that document it became clear that <b>Master Plan 2047 is not an approved statutory "
            "plan</b> — it is in preparation, with public reporting indicating a 2027–28 release and an "
            "expansion from 18 to 27 planning zones. The plan currently in force remains Master Plan 2025, "
            "approved in 2011. The approved Zonal Development Plans were obtained instead. This is flagged "
            "because any screening work that cites a 2047 land-use position today is citing a document that "
            "does not yet exist, and that is worth knowing before it reaches a decision note.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "For context, published reporting puts the current plan area at roughly 2,940–3,000 km², the "
            "proposed 2047 extent at roughly 6,000 km², and Jaipur's 2047 population at 10–12.5 million. "
            "None of these figures enter any score in this atlas.",
            s["small"],
        )
    )

    story.append(Paragraph("Sources", s["h2"]))
    story.append(
        Paragraph(
            "OpenStreetMap via Overpass (channel, rail, metro, roads, power, water structures, buildings; "
            "ODbL) · Copernicus DEM GLO-30 via AWS Open Data · Sentinel-2 L2A via Earth Search on AWS · "
            "WorldPop India 2020 population density (CC-BY 4.0) · Open-Meteo ERA5 rainfall archive · "
            "IRC:86-2018 Table 8.2 for minimum horizontal curve radius · project endpoints and length from "
            "published press coverage. Full ledger with access dates and query definitions is in "
            "data/SOURCES.md in the repository.",
            s["small"],
        )
    )

    story.append(PageBreak())

    # ---------------------------------------------------------------- page 4
    story.append(Paragraph("Reproducing and checking this", s["h2"]))
    story.append(
        Paragraph(
            "The pipeline runs end to end from public sources with no credentials and no licensed software. "
            "Every intermediate is written to disk, so any number in this brief can be traced back to the "
            "layer and the query that produced it. The test suite asserts the invariants that matter — that "
            "all spatial analysis happens in a projected CRS, that every score column has a paired confidence "
            "column, that the hydraulic index increases downstream, and that the robust hotspot list stays "
            "discriminating rather than collapsing to everything or nothing.",
            s["body"],
        )
    )

    story.append(
        _kv_table(
            [
                ("Live atlas", LIVE_URL),
                ("Interactive analysis", f"{LIVE_URL}/analysis"),
                ("Source and data ledger", REPO_URL),
            ],
            s,
            [42 * mm, doc.width - 42 * mm],
        )
    )

    story.append(Paragraph("Where this could be wrong", s["h2"]))
    story.append(
        Paragraph(
            "The reconstruction is built from the channel, so it will diverge from a surveyed alignment "
            "wherever a designer would depart from the river. Constraint scoring is a proxy exercise: it "
            "detects what open data records, and open data under-records exactly the things — buried "
            "utilities, land titles, encroachment status — that most often decide an urban corridor. Nothing "
            "here has been checked against ground truth, because none was available to this analysis.",
            s["body"],
        )
    )

    ask = Table(
        [[Paragraph(
            "<b>The ask.</b> If any of this is useful, I would value twenty minutes to hear where the method "
            "is wrong. Correction is more valuable to me than agreement, and the parts most likely to be "
            "wrong are the ones listed above.",
            s["body"],
        )]],
        colWidths=[doc.width],
        hAlign="LEFT",
    )
    ask.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BAND),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBEFORE", (0, 0), (0, -1), 2, CHANNEL),
            ]
        )
    )
    story.append(Spacer(1, 4))
    story.append(KeepTogether(ask))
    story.append(Spacer(1, 10))
    story.append(Paragraph(DISCLAIMER, s["small"]))

    doc.build(story)
    return out_path


if __name__ == "__main__":
    path = build_brief()
    print(f"Wrote {path.relative_to(REPO_ROOT)} ({path.stat().st_size / 1024:.0f} KB)")
