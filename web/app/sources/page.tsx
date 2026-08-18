import { SiteHeader } from "@/components/site-header";
import { DocPage, Section, Confidence } from "@/components/doc";

export const metadata = { title: "Sources — Dravyavati Corridor Constraint Atlas" };

type Source = {
  layer: string;
  provider: string;
  href: string;
  accessed: string;
  licence: string;
  confidence?: "high" | "medium" | "low";
  feeds: string;
  note?: string;
};

const SOURCES: Source[] = [
  {
    layer: "River channel geometry",
    provider: "OpenStreetMap via Overpass",
    href: "https://www.openstreetmap.org/",
    accessed: "2026-08-18",
    licence: "ODbL",
    confidence: "high",
    feeds: "Alignment reconstruction, cross-drainage channel exclusion",
    note: "21 natural=water ways named Dravyavati or Amanishah.",
  },
  {
    layer: "NH-148C / Ring Road",
    provider: "OpenStreetMap via Overpass",
    href: "https://www.openstreetmap.org/",
    accessed: "2026-08-18",
    licence: "ODbL",
    confidence: "high",
    feeds: "Southern corridor endpoint",
  },
  {
    layer: "Rail, bridges, arterials, military, power, dams",
    provider: "OpenStreetMap via Overpass",
    href: "https://www.openstreetmap.org/",
    accessed: "2026-08-19",
    licence: "ODbL",
    feeds: "Constraints 01, 03, 04, 05, 08, 09",
    note: "Power and military coverage in Jaipur is incomplete — both carry low confidence by design.",
  },
  {
    layer: "Metro network, phases and stations",
    provider: "OpenStreetMap via Overpass",
    href: "https://www.openstreetmap.org/",
    accessed: "2026-08-19",
    licence: "ODbL",
    confidence: "high",
    feeds: "Constraint 02",
    note: "Pink Line operational, Orange Line under construction, plus proposed segments.",
  },
  {
    layer: "Building footprints",
    provider: "OpenStreetMap via Overpass",
    href: "https://www.openstreetmap.org/",
    accessed: "2026-08-19",
    licence: "ODbL",
    confidence: "high",
    feeds: "Constraints 06, 10, 11",
    note: "Substituted for Google Open Buildings v3, whose public mirrors run 13–14 GB per S2 cell; a bbox-filtered remote read did not complete.",
  },
  {
    layer: "Copernicus DEM GLO-30",
    provider: "AWS Open Data",
    href: "https://registry.opendata.aws/copernicus-dem/",
    accessed: "2026-08-19",
    licence: "Copernicus terms",
    confidence: "low",
    feeds: "Constraint 12, cross-drainage candidates",
    note: "30 m cannot resolve a rectified channel cross-section.",
  },
  {
    layer: "Sentinel-2 L2A (2018 and 2026)",
    provider: "Earth Search STAC on AWS (Element 84)",
    href: "https://element84.com/earth-search/",
    accessed: "2026-08-19",
    licence: "Copernicus terms",
    confidence: "low",
    feeds: "Constraint 13",
    note: "No authentication required — chosen over Copernicus Data Space precisely because CDSE needs an account.",
  },
  {
    layer: "Population density 2020",
    provider: "WorldPop",
    href: "https://hub.worldpop.org/geodata/summary?id=41746",
    accessed: "2026-08-19",
    licence: "CC-BY 4.0",
    confidence: "medium",
    feeds: "Constraint 11 supporting column",
    note: "National 1 km product; the 100 m product is tiled sub-nationally without a stable direct URL.",
  },
  {
    layer: "Rainfall normals 2010–2020",
    provider: "Open-Meteo ERA5 archive",
    href: "https://open-meteo.com/",
    accessed: "2026-08-19",
    licence: "CC-BY 4.0",
    feeds: "Context only — not scored",
    note: "620.7 mm annual, 555.4 mm Jun–Sep (89.5%).",
  },
  {
    layer: "IRC:86-2018 Table 8.2",
    provider: "Indian Roads Congress",
    href: "https://law.resource.org/pub/in/bis/irc/irc.gov.in.086.2018.pdf",
    accessed: "2026-08-19",
    licence: "Published standard",
    confidence: "high",
    feeds: "Constraint 07",
    note: "Transcribed from the published table, not recalled from memory.",
  },
  {
    layer: "Zonal Development Plans (approved)",
    provider: "Jaipur Development Authority",
    href: "https://jda.rajasthan.gov.in/content/raj/udh/jda---jaipur/en/town-planning/zonal-development-plan.html",
    accessed: "2026-08-19",
    licence: "Government of Rajasthan",
    feeds: "Not yet attached to any chainage",
    note: "Downloaded but not georeferenced — see Limits.",
  },
  {
    layer: "Project endpoints and length",
    provider: "Press coverage (First India, ThePrint, The DeepState)",
    href: "https://theprint.in/india/rajasthan-govt-exploring-elevated-corridor-along-dravyavati-river-in-jaipur/2878789/",
    accessed: "2026-08-18",
    licence: "Editorial",
    confidence: "medium",
    feeds: "Alignment scoping",
  },
];

export default function SourcesPage() {
  return (
    <>
      <SiteHeader badge="Provenance" />
      <DocPage
        title="Every layer, and where it came from"
        lede="The rule this project runs on: if a layer cannot be traced to a public URL with an access date, the layer does not exist. This is that ledger, rendered — the same content as data/SOURCES.md in the repository."
      >
        <div className="space-y-3">
          {SOURCES.map((s) => (
            <article key={s.layer} className="rounded-xl border border-line bg-surface p-4">
              <div className="flex flex-wrap items-start justify-between gap-x-3 gap-y-1">
                <h3 className="text-sm font-medium text-foreground">{s.layer}</h3>
                {s.confidence && <Confidence level={s.confidence} />}
              </div>
              <p className="mt-1 text-xs text-fog">
                {s.provider} ·{" "}
                <a
                  href={s.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline decoration-line underline-offset-2 hover:text-foreground"
                >
                  source
                </a>{" "}
                · accessed {s.accessed} · {s.licence}
              </p>
              <p className="mt-2 text-xs text-fog">
                <span className="text-foreground">Feeds:</span> {s.feeds}
              </p>
              {s.note && <p className="mt-1 text-xs leading-relaxed text-fog">{s.note}</p>}
            </article>
          ))}
        </div>

        <Section title="A correction to this project's own scoping">
          <p>
            The brief this work was built from named the <strong>Jaipur Master Plan 2047</strong> as a
            land-use source. In the course of sourcing it, it became clear that Master Plan 2047 is not an
            approved statutory plan — it is in preparation, with public reporting indicating a 2027–28
            release and an expansion from 18 to 27 planning zones. The plan currently in force remains
            Master Plan 2025, approved in 2011.
          </p>
          <p>
            This is recorded rather than quietly dropped, because any screening work citing a 2047 land-use
            position today is citing a document that does not yet exist.
          </p>
        </Section>

        <Section title="The stranger test">
          <p>
            Before anything ships: could someone with no access to anything private rebuild this file from
            the URLs above alone? Where the answer is no, the layer is removed rather than shipped with a
            gap in its provenance.
          </p>
        </Section>
      </DocPage>
    </>
  );
}
