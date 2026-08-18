"""JDA statutory planning documents — Zonal Development Plans.

Important correction to this project's original premise. The build pack
named "Jaipur Master Plan 2047" as the land-use source. As of August 2026
that document **is not approved and does not exist as a statutory plan** —
it is in preparation, with public reporting pointing at a 2027-28 release
and an expansion from 18 to 27 planning zones. The plan currently in force
is Master Plan 2025, approved in 2011.

What *is* approved and downloadable is the set of Zonal Development Plans
(ZDPs), which are the operative statutory land-use documents for each
planning zone. Those are fetched here.

Access note: `jda.rajasthan.gov.in` returns HTTP 403 to automated requests
regardless of user agent, but the asset host `jdaservice.rajasthan.gov.in`
serves the high-resolution ZDP sheets normally. That is the route used.

Georeferencing status: the ZDP sheets are ~10,800 x 15,000 px scans with no
embedded coordinate system and no printed graticule that survives at usable
resolution. Turning them into zoning polygons needs hand-picked ground
control points and colour classification per legend category. That work is
NOT done here, and no zoning attribute is attached to any chainage, because
a mis-registered zoning layer would silently assign wrong land use to real
chainages — the exact failure mode CLAUDE.md invariant 1 and 2 exist to
prevent. The sheets are downloaded and recorded so the step can be done
deliberately later.
"""

from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
ZDP_DIR = REPO_ROOT / "data" / "raw" / "jda_zdp"

ASSET_HOST = "https://jdaservice.rajasthan.gov.in/pdf/ZoneDevelopmentPlan"
LISTING_PAGE = (
    "https://jda.rajasthan.gov.in/content/raj/udh/jda---jaipur/en/"
    "town-planning/zonal-development-plan.html"
)

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

# The corridor runs roughly north-south through the centre and south of the
# city. These are the zones whose sheets were pulled; which of them the
# corridor actually intersects cannot be stated until the sheets are
# georeferenced, so no claim is made about that here.
DOWNLOADED_ZONES = ["10", "11A", "12", "13"]

# Real, citable planning context. Every figure here is quoted from published
# reporting, not derived by this pipeline, and none of it is scored.
PLANNING_CONTEXT = {
    "master_plan_2047_status": (
        "In preparation, not approved. Public reporting indicates a 2027-28 release and an "
        "expansion from 18 to 27 planning zones. The statutory plan currently in force is "
        "Master Plan 2025, approved 2011."
    ),
    "current_plan_area_sq_km": "approximately 2,940-3,000",
    "proposed_2047_area_sq_km": "approximately 6,000",
    "population_projection_2047": "10 to 12.5 million",
    "planning_zones_current": 18,
    "planning_zones_proposed": 27,
}


def fetch_zdp_sheets(zones: list[str] | None = None, force: bool = False) -> list[Path]:
    """Download high-resolution ZDP sheets from the JDA asset host."""
    ZDP_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for zone in zones or DOWNLOADED_ZONES:
        path = ZDP_DIR / f"Final_ZDP_{zone}.jpg"
        if path.exists() and not force:
            out.append(path)
            continue
        resp = requests.get(
            f"{ASSET_HOST}/Final_ZDP_{zone}.jpg",
            headers={"User-Agent": BROWSER_UA},
            timeout=180,
        )
        resp.raise_for_status()
        path.write_bytes(resp.content)
        out.append(path)
    return out


if __name__ == "__main__":
    print("Master Plan 2047 status:", PLANNING_CONTEXT["master_plan_2047_status"])
    for path in fetch_zdp_sheets():
        print(f"  {path.name}  {path.stat().st_size / 1e6:.0f} MB")
    print("\nZoning attributes are deliberately NOT attached to any chainage — see module docstring.")
