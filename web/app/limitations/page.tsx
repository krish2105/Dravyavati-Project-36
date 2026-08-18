import { SiteHeader } from "@/components/site-header";
import { DocPage, Section, Rows } from "@/components/doc";

export const metadata = { title: "Limits — Dravyavati Corridor Constraint Atlas" };

export default function LimitationsPage() {
  return (
    <>
      <SiteHeader badge="Limits" />
      <DocPage
        title="What this gets wrong"
        lede="Published deliberately. A screening tool that only advertises its strengths is harder to check, and the parts most likely to be wrong are the parts most worth stating first."
      >
        <Section title="The alignment is 41.2 km against a reported ~36 km">
          <p>
            That gap is about 14%, and it is a property of the method rather than a bug. The reconstruction
            follows the medial axis of the mapped channel. A designed alignment would ease curves far harder
            than a medial axis can, and would bridge across meanders rather than tracing them.
          </p>
          <p>
            Simplification could be pushed until the length matched — at 500 m tolerance it reaches roughly
            39.5 km — but that flattens curvature to the point where almost every segment reads as straight,
            which contradicts the physical reality of a river-following route and fails this project&apos;s
            own curvature sanity check. Matching the headline number by degrading the geometry underneath it
            would be the wrong trade.
          </p>
          <p>
            <strong>Consequence:</strong> chainages here will not correspond one-to-one with a DPR&apos;s.
            Treat them as positions along a reconstruction, not as surveyed stations.
          </p>
        </Section>

        <Section title="Four layers carry low confidence, and they matter">
          <Rows
            rows={[
              ["Power lines", "OSM's power=line coverage in Jaipur is incomplete. Every EHT crossing flagged here is a candidate to verify against imagery — and, more importantly, absence of a flag is not evidence of absence on the ground."],
              ["Military / restricted areas", "landuse=military is frequently missing or approximate across India. This analysis shows no military interface along the corridor. That should be read as the source data being silent, not as a finding."],
              ["Built-up growth", "NDBI is a spectral proxy, not a land-cover classifier. Bare soil in this region can read as built-up. Only the 2018→2026 change is used, never the absolute value, which limits but does not eliminate the problem."],
              ["Hydraulic sensitivity", "GLO-30 at 30 m cannot resolve a rectified channel cross-section. The output is a relative index over contributing area. It is not an afflux figure, not a flood depth, and not a flood risk statement — and it should never be quoted as one."],
            ]}
          />
        </Section>

        <Section title="No zoning layer exists">
          <p>
            The approved Zonal Development Plan sheets were obtained from the JDA asset host. They were not
            converted into zoning polygons, and no chainage carries a land-use attribute.
          </p>
          <p>
            An earlier version of this page said the sheets carried no usable coordinate reference. That
            was wrong, and the correction is favourable: the sheets do print a labelled geographic
            graticule — a meridian tick reading 75°40&apos;30&quot;E on sheet 10 — and a graphic scale bar.
            They are georeferenceable to survey precision from the sheet alone, with no eyeballed control
            points needed.
          </p>
          <p>
            What remains is separating the ruled graticule from drawn watercourses, which are inked in a
            similar blue and defeat a simple colour threshold. That is contained work. It was not rushed to
            completion, because a transform fitted from mis-identified lines would assign wrong land use to
            real chainages while looking entirely plausible — and no zoning will be published here until a
            transform exists and its RMS residual is published beside it.
          </p>
        </Section>

        <Section title="Nothing here is validated against ground truth">
          <p>
            This is the most important limitation on the page. No field survey, no utility drawing, no land
            record and no traffic count entered this analysis, because none was available to it. The atlas
            detects what open data records — and open data systematically under-records buried utilities,
            land titles and encroachment status, which are precisely the things that decide an urban
            corridor.
          </p>
          <p>
            The uncertainty analysis quantifies how much the <em>scores</em> could move given the confidence
            of their sources. It cannot quantify what the sources never saw.
          </p>
        </Section>

        <Section title="What would settle each of these">
          <Rows
            rows={[
              ["Alignment", "The DPR's own surveyed centreline. Everything else re-chainages against it in an afternoon."],
              ["Power and utilities", "Utility drawings from the distribution licensee, or GPR survey. Satellite tower-shadow checks would confirm the EHT candidates at low cost."],
              ["Military interface", "A direct answer from the cantonment authority — the one question open data cannot substitute for."],
              ["Hydraulics", "Surveyed cross-sections. Until then this layer should be treated as a prompt for where to survey, nothing more."],
              ["Land and habitation", "Revenue records and current encroachment survey. Building footprints tell you what is standing, not who has a claim."],
            ]}
          />
        </Section>

        <Section title="How to argue with this">
          <p>
            Every figure traces to a stated operation on a cited dataset, and the pipeline runs end to end
            from public sources with no credentials. If a number here looks wrong, it can be traced to the
            layer and the query that produced it, and corrected at source. That is the property worth having
            in a screening tool — not being right, but being checkable.
          </p>
        </Section>
      </DocPage>
    </>
  );
}
