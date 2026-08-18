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

        <Section title="Zoning: registered, but not classified">
          <p>
            The approved Zonal Development Plan sheets print a labelled geographic graticule, so sheet 10
            has now been georeferenced from the sheet itself — graticule interval read off the printed
            labels, ticks measured in the neatline margin, affine fitted by least squares. Residuals are
            <strong> 0.75 m in longitude and 1.40 m in latitude</strong>, with 0.19% anisotropy. Against
            100 m chainage segments, registration error is not a material source of error.
          </p>
          <p>
            It covers chainage 9.1–20.0 km, a contiguous 110-segment run, which is itself a check: a bad
            fit would produce scattered or empty coverage. You can switch it on over the map.
          </p>
          <p>
            What is still <em>not</em> done is classifying the land-use colours into zoning categories, and
            reading the sheet&apos;s own legend settled why. The categories are separated by <strong>hatch
            pattern and embedded letter codes, not fill colour</strong>. Commercial (specialised market) and
            wholesale market are both pink cross-hatch. Central park and stadium are both dot-filled and
            differ only by the letters CP and S. A nearest-colour classifier would merge those pairs
            systematically, and it would do so silently.
          </p>
          <p>
            So no chainage carries a zoning attribute. Instead the registered sheet is published as an
            overlay with its full 18-category legend transcribed beside it in both languages, plus the
            legend as printed, so a reviewer decodes the hatching by eye rather than trusting a classifier
            nobody has validated. Doing this properly would need texture classification plus OCR of the
            embedded codes at scan resolution — a research task, not a quick pass.
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
