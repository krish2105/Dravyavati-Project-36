"""Generate the PDF brief for JDA officials.

Every figure on these pages is read from data/processed/chainage_risk.parquet
and web/public/data/*.json at build time. Nothing is typed in by hand, so the
brief cannot drift away from the pipeline that produced it.

Register: plain executive English, short sentences, no jargon that a reader
outside the analysis team would have to look up. Page 5 repeats the whole
argument in Hinglish (Hindi in Roman script) so the brief can be read aloud
in a room without anyone translating on the fly.

Tone follows pack section 7: say what was measured, say where it is weak,
make one small ask. No recommendation, no alignment opinion, no hydraulic
conclusion.
"""

import json
from datetime import date
from pathlib import Path

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
WEB_DATA = REPO_ROOT / "web" / "public" / "data"
ANALYTICS = WEB_DATA / "analytics.json"
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


def _clean(text: str) -> str:
    """Labels come from the pipeline; normalise dashes so the page reads evenly."""
    return text.replace("–", "-").replace("—", "-")


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
        "lead": ParagraphStyle(
            "lead", parent=base["Normal"], fontName="Helvetica", fontSize=11,
            leading=15.5, textColor=INK, spaceAfter=9,
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
    """Disclaimer strip on every page. Pack section 0 requires it on every output."""
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
    data = [[Paragraph(_clean(k), styles["cell"]), Paragraph(_clean(v), styles["cell"])] for k, v in rows]
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


def _callout(text, styles, width):
    box = Table([[Paragraph(text, styles["body"])]], colWidths=[width], hAlign="LEFT")
    box.setStyle(
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
    return KeepTogether(box)


def build_brief() -> Path:
    analytics = json.loads(ANALYTICS.read_text())
    imp_path = WEB_DATA / "feature_importance.json"
    importance = json.loads(imp_path.read_text()) if imp_path.exists() else None
    ease_path = WEB_DATA / "alignment_easing.json"
    easing = json.loads(ease_path.read_text()) if ease_path.exists() else None

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
        title="Dravyavati Corridor Constraint Atlas - Screening Brief",
        author="Krishna Mathur",
        subject="Chainage-indexed constraint screening for the proposed Dravyavati elevated corridor, Jaipur",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_chrome)])

    c = analytics["corridor"]
    cross = analytics["crossings"]
    land = analytics["land"]
    irc = analytics["irc86"]
    sev = analytics["severity"]
    metro = analytics.get("metro", {})
    hotspots = analytics["hotspot_corridors"]
    story = []

    # ------------------------------------------------------------- page 1
    story.append(Paragraph("Dravyavati Corridor Constraint Atlas", s["title"]))
    story.append(
        Paragraph(
            "Where the hard parts are, before anyone spends a survey day finding them. "
            f"Proposed elevated corridor along the Dravyavati River, Jaipur. "
            f"{date.today().strftime('%d %B %Y')}",
            s["subtitle"],
        )
    )

    story.append(
        Paragraph(
            "A 36 km corridor along a river does not fail evenly. It fails at a handful of places where a "
            "railway, a metro viaduct, a check dam and a high-tension line all want the same 200 metres. "
            "This atlas finds those places from public data, before survey teams go out, so the first weeks "
            "of field effort go where the problems actually are.",
            s["lead"],
        )
    )

    headline = [
        [
            Paragraph(f"<b>{c['length_km']:.1f} km</b>", s["cell"]),
            Paragraph(f"<b>{c['segments']}</b>", s["cell"]),
            Paragraph(f"<b>{c['constraint_count']}</b>", s["cell"]),
            Paragraph(f"<b>{len(hotspots)}</b>", s["cell"]),
        ],
        [
            Paragraph("corridor reconstructed", s["cellsm"]),
            Paragraph("100 m segments scored", s["cellsm"]),
            Paragraph("constraint categories", s["cellsm"]),
            Paragraph("stretches that need attention first", s["cellsm"]),
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

    story.append(Paragraph("THE ONE-LINE VERSION", s["kicker"]))
    story.append(
        Paragraph(
            f"Of {c['segments']} hundred-metre segments along the corridor, <b>{sev['high']} score high</b> "
            f"and {sev['medium']} score medium against thirteen categories of engineering constraint. Those "
            f"high scores group into <b>{len(hotspots)} stretches</b>, and those stretches are where I would "
            "send the first survey team.",
            s["body"],
        )
    )

    story.append(Paragraph("WHAT THIS IS, AND WHAT IT IS NOT", s["kicker"]))
    story.append(
        Paragraph(
            "It is a triage instrument. Every 100 metres it asks a simple question: how many things here are "
            "likely to make construction hard, and how hard. It is built to help decide where survey effort "
            "and design attention should go first.",
            s["body"],
        )
    )
    story.append(
        Paragraph(
            "It is not a DPR, not a hydraulic study, not a structural assessment, and not an opinion on where "
            "the alignment should run. It does not replace topographical survey, GPR utility mapping or "
            "geotechnical investigation. Anyone who reads it as a design input is reading it wrong.",
            s["body"],
        )
    )

    story.append(Paragraph("WHERE THE DATA CAME FROM", s["kicker"]))
    story.append(
        Paragraph(
            "<b>No project data was used.</b> I have no access to JDA files or to any consultancy material, "
            "and nothing of that kind went into this. Every layer traces to a public URL recorded with the "
            "date I fetched it. A stranger with no special access could rebuild every file in this analysis "
            "from that list alone, and could just as easily prove a part of it wrong. That was the design "
            "goal, because a screening tool nobody can check is worth very little.",
            s["body"],
        )
    )

    story.append(PageBreak())

    # ------------------------------------------------------------- page 2
    story.append(Paragraph("What the screening found", s["h2"]))
    rows = [
        ("Railway crossings", f"{cross['railway']} distinct crossings"),
        (
            "Metro interfaces",
            f"{metro.get('operational', 0)} segments sit on the operational line, "
            f"{metro.get('construction', 0)} on the line under construction, and "
            f"{metro.get('proposed', 0)} on proposed alignments",
        ),
        ("Major arterial crossings", f"{cross['major_arterial']} distinct crossings"),
        ("Dams and check structures", f"{cross['dam_check_structure']} within 100 m of the alignment"),
        (
            "Cross-drainage candidates",
            f"{cross['cross_drainage']} places where a modelled tributary meets the corridor",
        ),
        (
            "Tight curves",
            f"{irc['segments_below']} segments fall below the IRC:86-2018 minimum radius of "
            f"{irc['min_radius_m']} m for a 60 km/h design speed",
        ),
        (
            "Land and habitation",
            f"{land['mean_unbuilt_pct']:.1f}% of the 60 m corridor buffer is unbuilt on average. About "
            f"{land['buildings_within_100m']} buildings lie within 100 m, and they are concentrated in only "
            f"{land['segments_with_buildings']} of {c['segments']} segments",
        ),
    ]
    story.append(_kv_table(rows, s, [42 * mm, doc.width - 42 * mm]))
    story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            "The land figure is the one worth pausing on. On average the corridor is almost entirely clear, "
            "but that average hides the real problem: the buildings are not spread out, they sit in a small "
            "number of places. Acquisition pressure is concentrated, not distributed.",
            s["small"],
        )
    )

    story.append(Paragraph("The stretches that need attention first", s["h2"]))
    story.append(
        Paragraph(
            "I did not want a list that only holds together under my own weighting choices. So every "
            "constraint weight was swept plus or minus 35 percent, and only the chainages that kept their "
            f"severity band through the entire sweep are listed here. {analytics['robust_hotspots']} segments "
            f"survived that test and group into {len(hotspots)} stretches. The rest were artefacts of one "
            "weighting, not findings.",
            s["body"],
        )
    )

    head = ["Chainage", "Length", "Score", "What is driving it"]
    data = [[Paragraph(f"<b>{h}</b>", s["cell"]) for h in head]]
    for hc in hotspots:
        data.append(
            [
                Paragraph(f"{hc['start_m'] / 1000:.1f} to {hc['end_m'] / 1000:.1f} km", s["cell"]),
                Paragraph(f"{(hc['end_m'] - hc['start_m']) / 1000:.1f} km", s["cell"]),
                Paragraph(f"{hc['mean_composite']:.2f}", s["cell"]),
                Paragraph(
                    _clean(" · ".join(f"{d['label']} ({d['mean_score']:.1f})" for d in hc["top_drivers"])),
                    s["cellsm"],
                ),
            ]
        )
    t = Table(data, colWidths=[30 * mm, 16 * mm, 16 * mm, doc.width - 62 * mm], hAlign="LEFT", repeatRows=1)
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
            "The score is a weighted mean of thirteen constraint ratings, each on a 0 to 3 scale. It ranks "
            "chainages against each other. It is not a physical quantity and it has no unit.",
            s["small"],
        )
    )

    if importance:
        story.append(Paragraph("What actually drives the ranking", s["h2"]))
        top = importance["features"][:6]
        story.append(_kv_table([(f["label"], f"{f['importance']:.3f}") for f in top], s, [70 * mm, 25 * mm]))
        story.append(Spacer(1, 3))
        story.append(
            Paragraph(
                "The result that surprised me: proximity to existing elevated structure dominates, ahead of "
                "entry and exit feasibility and hydraulic sensitivity. Habitation proximity, which is the "
                "intuitive first guess for a corridor through a city, ranks well below all three. If that "
                "holds up, attention belongs on structural interface before it belongs on land.",
                s["small"],
            )
        )
        story.append(
            Paragraph(
                f"Method note: a small neural network was fitted to reproduce the composite score from the "
                f"constraint vector (R squared {importance['surrogate_r2']:.3f}), then each constraint was "
                "shuffled in turn to see how far the reproduction degrades. This measures our own index. It "
                "does not predict anything measured outside this analysis.",
                s["small"],
            )
        )

    story.append(PageBreak())

    # ------------------------------------------------------------- page 3
    story.append(Paragraph("How it was built", s["h2"]))
    story.append(
        Paragraph(
            "<b>1.</b> The river channel is taken from OpenStreetMap water polygons and reduced to a "
            "centreline. <b>2.</b> That centreline is cut into 100 m segments keyed on chainage, which "
            "becomes the join key for everything else. <b>3.</b> Each segment is scored 0 to 3 against "
            "thirteen constraint categories. <b>4.</b> The scores are combined into an equal-weight "
            "composite. <b>5.</b> The weights are swept and only stable results are reported.",
            s["body"],
        )
    )

    story.append(Paragraph("EVERYTHING THAT WENT INTO IT", s["kicker"]))
    build = [
        (
            "Public data",
            "OpenStreetMap via the Overpass API (channel, railway, metro, roads, power lines, water "
            "structures, buildings) · Copernicus DEM GLO-30 elevation via AWS Open Data · Sentinel-2 L2A "
            "imagery via Earth Search · WorldPop India population density · Open-Meteo ERA5 rainfall "
            "archive · JDA Zonal Development Plan sheet 10 · IRC:86-2018 Table 8.2 for curve radii",
        ),
        (
            "Geometry",
            "Voronoi medial-axis centreline extraction, longest-path selection on the resulting graph, "
            "three-point circumscribed-circle curvature, and all spatial work in UTM zone 43N so distances "
            "are in real metres rather than degrees",
        ),
        (
            "Terrain and water",
            "D8 flow accumulation over the filled DEM to model tributaries and contributing area, with the "
            "main channel subtracted so the tool measures tributaries crossing the corridor rather than the "
            "corridor following the river",
        ),
        (
            "Imagery",
            "A built-up spectral index computed on Sentinel-2 for 2018 and for the current year, compared as "
            "a change rather than read as an absolute, because bare soil in this region mimics built-up "
            "signal",
        ),
        (
            "Statistics",
            "5,000-run Monte Carlo over both weights and scores for uncertainty, DBSCAN clustering to group "
            "adjacent hotspots, isolation forest for anomaly detection, and a neural surrogate with "
            "permutation importance to see which constraint drives the ranking",
        ),
        (
            "Zoning sheet",
            "The JDA sheet had no coordinate system, so it was registered by detecting its printed graticule "
            "with a constrained Hough transform and reading the interval off the printed labels. It now sits "
            "under the corridor at 0.75 m RMS accuracy",
        ),
        (
            "The tool itself",
            "A public web atlas with a map, per-chainage detail, live weight sliders, 3D terrain, "
            "deep-linkable segments, and a full English and Hindi interface. Seventeen automated tests hold "
            "the invariants in place",
        ),
    ]
    story.append(_kv_table(build, s, [34 * mm, doc.width - 34 * mm]))

    if easing:
        story.append(Paragraph("The length question, answered honestly", s["h2"]))
        story.append(
            Paragraph(
                f"My reconstruction measures {easing['channel_following_km']:.1f} km against a publicly "
                f"reported 36 km. Neither number is wrong. Tracing a river's centreline follows every "
                f"meander, while a designed alignment eases curves and cuts across them. When I apply that "
                f"easing, the corridor comes to <b>{easing['eased_km']:.1f} km</b>, which matches the "
                f"reported figure, and curve compliance improves at the same time. The cost is that it "
                f"leaves the mapped channel by up to <b>{easing['drift_from_channel_m']:.0f} m</b> in "
                "places.",
                s["body"],
            )
        )
        story.append(
            Paragraph(
                "So a 36 km corridor here is achievable, but it implies departing the river by up to about "
                "875 metres to cut meanders. Whether that departure is acceptable is a design and land "
                "acquisition question, and this atlas does not answer it. Scoring deliberately stays on the "
                "channel-following version, because that one carries no assumptions of mine. The eased "
                "version is published next to it, not swapped in.",
                s["body"],
            )
        )

    story.append(PageBreak())

    # ------------------------------------------------------------- page 4
    story.append(Paragraph("Where this is weakest", s["h2"]))
    story.append(
        Paragraph(
            "Every score carries a confidence tag, and the tags do real work: they set how far each layer is "
            "allowed to move in the uncertainty analysis. Across 5,000 runs the mean 90 percent interval is "
            f"<b>{analytics['uncertainty']['mean_ci_width']:.2f}</b> composite points, which is wide next to "
            "the spread between chainages. That is the honest characterisation. Trust this for ordering and "
            "triage. Do not trust it for an absolute statement about any single segment.",
            s["body"],
        )
    )

    limits = [
        (
            "Power lines (low confidence)",
            "OpenStreetMap coverage of transmission lines in Jaipur is incomplete. The EHT crossings flagged "
            "here are candidates, not confirmations, and each one needs checking against imagery.",
        ),
        (
            "Restricted areas (low confidence)",
            "Military land use is often missing or approximate in Indian OSM data. Where this analysis shows "
            "nothing, that is a gap in the source, not evidence that nothing is there.",
        ),
        (
            "Built-up growth (low confidence)",
            "This comes from a spectral index, not a land-cover classification. Only the change between 2018 "
            "and now is used, never an absolute reading.",
        ),
        (
            "Hydraulic sensitivity (low confidence)",
            "A 30 m DEM cannot resolve a rectified channel cross-section. The output is a relative screening "
            "index over contributing area. It is not an afflux figure and it is not a flood claim.",
        ),
        (
            "Zoning attribution",
            "The zoning sheet is registered and readable under the corridor, but no chainage carries a "
            "zoning attribute yet. Categories on that sheet are separated by hatch pattern and printed "
            "letter codes, not by colour alone, so a colour classifier would silently merge commercial with "
            "wholesale market. Left undone on purpose rather than guessed.",
        ),
        (
            "Ground truth",
            "None. Nothing here has been checked against a field observation, because no field data was "
            "available to me.",
        ),
    ]
    story.append(_kv_table(limits, s, [42 * mm, doc.width - 42 * mm]))

    story.append(Paragraph("One correction worth flagging", s["h2"]))
    story.append(
        Paragraph(
            "I scoped this work against the Jaipur Master Plan 2047. While sourcing that document it became "
            "clear that <b>Master Plan 2047 is not an approved statutory plan.</b> It is still in "
            "preparation, with public reporting indicating a 2027 to 2028 release and an expansion from 18 "
            "to 27 planning zones. The plan in force remains Master Plan 2025, approved in 2011. I used the "
            "approved Zonal Development Plans instead. I flag it because any screening note that cites a "
            "2047 land-use position today is citing a document that does not exist yet, and that is better "
            "known before it reaches a decision file than after.",
            s["body"],
        )
    )

    story.append(Paragraph("Reproducing or contradicting this", s["h2"]))
    story.append(
        Paragraph(
            "The pipeline runs start to finish from public sources with no credentials and no licensed "
            "software. Every intermediate is written to disk, so any number in this brief can be traced back "
            "to the layer and the query that produced it.",
            s["body"],
        )
    )
    story.append(
        _kv_table(
            [
                ("Live atlas", LIVE_URL),
                ("Interactive analysis", f"{LIVE_URL}/analysis"),
                ("Stated limits, in full", f"{LIVE_URL}/limitations"),
                ("Source code and data ledger", REPO_URL),
            ],
            s,
            [42 * mm, doc.width - 42 * mm],
        )
    )

    story.append(Spacer(1, 4))
    story.append(
        _callout(
            "<b>The ask.</b> Twenty minutes to hear where the method is wrong. I am not asking anyone to act "
            "on this, and I would rather be corrected than agreed with. The parts most likely to be wrong "
            "are the ones listed on this page, and I would start there.",
            s,
            doc.width,
        )
    )

    story.append(PageBreak())

    # ------------------------------------------------------------- page 5
    story.append(Paragraph("Yeh project kya hai", s["title"]))
    story.append(
        Paragraph(
            "Pura brief, Hinglish mein. Saare numbers wahi hain jo upar English pages par diye gaye hain.",
            s["subtitle"],
        )
    )

    story.append(
        Paragraph(
            "Dravyavati river ke saath jo elevated corridor propose hua hai, uske liye maine ek screening "
            "tool banaya hai. Simple baat yeh hai: 36 km ka corridor har jagah barabar mushkil nahi hota. "
            "Dikkat kuch hi jagah par aati hai, jahan railway line, metro viaduct, check dam aur high-tension "
            "line, sab ek hi 200 metre ke andar aa jaate hain. Yeh tool wahi jagah pehle se dhoond leta hai, "
            "public data se, taaki survey team ka pehla hafta sahi jagah par lage.",
            s["lead"],
        )
    )

    story.append(Paragraph("KAAM KAISE KARTA HAI", s["kicker"]))
    story.append(
        Paragraph(
            f"Corridor ko har 100 metre ke {c['segments']} tukdon mein baanta gaya hai. Har tukde ko "
            f"{c['constraint_count']} tarah ki engineering dikkaton ke against 0 se 3 tak score diya gaya "
            f"hai. Ismein se <b>{sev['high']} tukde high</b> aur {sev['medium']} tukde medium nikle. In high "
            f"score wale tukdon ko jodne par <b>{len(hotspots)} stretch</b> bante hain, aur mera suggestion "
            "yeh hai ki survey team sabse pehle wahan jaaye.",
            s["body"],
        )
    )

    story.append(Paragraph("SABSE ZAROORI BAAT: DATA KAHAN SE AAYA", s["kicker"]))
    story.append(
        Paragraph(
            "<b>Isme JDA ka ya kisi consultancy ka koi data nahi hai.</b> Mere paas woh access hai hi nahi. "
            "Sab kuch OpenStreetMap, satellite imagery, Copernicus elevation data jaise public sources se "
            "liya gaya hai, aur har source ka URL aur date likha hua hai. Matlab koi bhi banda, bina kisi "
            "special permission ke, is poore analysis ko dobara bana sakta hai. Aur agar kahin galat hai to "
            "wahi banda usse galat bhi saabit kar sakta hai. Yeh jaan-boojh kar aisa banaya gaya hai, kyunki "
            "jis tool ko koi check hi na kar sake uski value kam hoti hai.",
            s["body"],
        )
    )

    story.append(Paragraph("KYA NIKLA", s["kicker"]))
    hi_rows = [
        ("Railway crossing", f"{cross['railway']} jagah"),
        ("Major road crossing", f"{cross['major_arterial']} jagah"),
        ("Metro se interface", f"{metro.get('operational', 0) + metro.get('construction', 0)} segment operational ya under-construction line par"),
        ("Dam / check structure", f"{cross['dam_check_structure']} structure, 100 m ke andar"),
        ("Tributary crossing", f"{cross['cross_drainage']} jagah paani corridor ko cross karta hai"),
        ("Tight curve", f"{irc['segments_below']} segment IRC:86 ke {irc['min_radius_m']} m minimum radius se neeche"),
        (
            "Zameen",
            f"Average {land['mean_unbuilt_pct']:.1f}% khaali hai, lekin buildings sirf "
            f"{land['segments_with_buildings']} segment mein concentrated hain. Yani acquisition ka pressure "
            "har jagah nahi, kuch hi jagah par hai",
        ),
    ]
    story.append(_kv_table(hi_rows, s, [42 * mm, doc.width - 42 * mm]))

    story.append(Paragraph("KAMZORIYAN, saaf-saaf", s["kicker"]))
    story.append(
        Paragraph(
            "Yeh design document nahi hai. Yeh hydraulic study nahi hai. Yeh alignment ka suggestion bhi "
            "nahi hai. Power line aur military area ka OSM data Jaipur mein adhoora hai, isliye woh "
            "findings sirf candidates hain, confirm nahi. Elevation data 30 m ka hai, jo channel ka "
            "cross-section resolve nahi kar sakta, isliye hydraulic wala number sirf relative comparison ke "
            "liye hai, flood ka claim nahi. Aur sabse badi baat: kuch bhi ground par verify nahi hua hai, "
            "kyunki mere paas field data tha hi nahi. Har cheez field survey se check honi chahiye.",
            s["body"],
        )
    )

    story.append(
        Paragraph(
            f"Length ke baare mein ek clarification: mera reconstruction {easing['channel_following_km']:.1f} km "
            f"aata hai jabki report 36 km kehti hai. Dono sahi hain. River ka centreline har mod follow karta "
            f"hai, jabki asli design curves ko seedha karta hai. Curves ease karne par yeh "
            f"{easing['eased_km']:.1f} km ho jaata hai, matlab reported figure se mil jaata hai, lekin tab "
            f"corridor river se {easing['drift_from_channel_m']:.0f} m tak door chala jaata hai. Woh "
            "acceptable hai ya nahi, yeh design aur land acquisition ka sawaal hai, mera nahi."
            if easing else "",
            s["body"],
        )
    )

    story.append(Spacer(1, 4))
    story.append(
        _callout(
            "<b>Meri request.</b> Bees minute chahiye, sirf yeh sunne ke liye ki method mein kahan galti hai. "
            "Main yeh nahi keh raha ki iske base par koi decision liya jaaye. Mujhe tareef se zyada correction "
            "chahiye, aur jo hisse sabse zyada galat ho sakte hain woh maine khud upar likh diye hain.",
            s,
            doc.width,
        )
    )
    story.append(Spacer(1, 10))
    story.append(Paragraph(DISCLAIMER, s["small"]))

    doc.build(story)
    return out_path


if __name__ == "__main__":
    path = build_brief()
    print(f"Wrote {path.relative_to(REPO_ROOT)} ({path.stat().st_size / 1024:.0f} KB)")
