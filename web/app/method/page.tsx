import { SiteHeader } from "@/components/site-header";
import { DocPage, Section, Rows, Confidence } from "@/components/doc";

export const metadata = { title: "Method — Dravyavati Corridor Constraint Atlas" };

const CONSTRAINTS: [string, React.ReactNode][] = [
  ["01 · Railway crossing", <>Alignment buffer ∩ OSM <code>railway=rail</code>, ±150 m. Scored 3 where it intersects, 0 otherwise. <Confidence level="high" /></>],
  ["02 · Metro interface", <>Status-aware against OSM <code>railway</code> in subway/light_rail (operational), <code>construction</code>, and <code>proposed</code>, ±200 m, with a wider ±350 m test for stations. Operational and under-construction score 3, proposed scores 2 — a line still on paper may move. <Confidence level="high" /> operational, <Confidence level="medium" /> proposed.</>],
  ["03 · Existing elevated structure", <>OSM <code>bridge=yes</code> or <code>layer&gt;0</code> within 100 m. <Confidence level="high" /></>],
  ["04 · Major arterial crossing", <>OSM <code>highway</code> in trunk/primary/secondary, ±50 m. <Confidence level="high" /></>],
  ["05 · Restricted / military area", <>OSM <code>landuse=military</code> within 200 m. Coverage of this tag in India is frequently absent or approximate, so a zero here means the source data is silent, not that nothing is there. <Confidence level="low" /></>],
  ["06 · Entry–exit feasibility", <>Distance to the nearest arterial × the unbuilt fraction of the corridor buffer, normalised to 0–3. Combines Session 4's distance term with Session 5's building coverage. <Confidence level="medium" /></>],
  ["07 · Curve severity", <>Radius of curvature per segment from a three-point circumscribed circle, compared against IRC:86-2018 Table 8.2. At a 60 km/h design speed with super-elevation limited to 4% (the code's own recommendation for urban sections with frequent intersections) the minimum radius is 150 m. Segments below it score 3. <Confidence level="high" /></>],
  ["08 · EHT line crossing", <>OSM <code>power=line</code> within 150 m. OSM's power coverage in Jaipur is incomplete, so these are candidates to check against imagery, not confirmed crossings. <Confidence level="low" /></>],
  ["09 · Dam / check structure", <>OSM <code>waterway</code> in dam/weir within 100 m. <Confidence level="medium" /></>],
  ["10 · Land availability", <>Share of a 60 m corridor buffer covered by building footprints, banded into 0–3. <Confidence level="high" /></>],
  ["11 · Habitation proximity", <>Building count within a 100 m buffer, banded 0–3, with WorldPop density carried alongside as a supporting column rather than folded silently into the score. <Confidence level="high" /></>],
  ["12 · Hydraulic sensitivity", <>D8 flow accumulation on Copernicus GLO-30, sampled at each segment midpoint, forced monotonic downstream (contributing area cannot shrink) and min–max normalised. A relative index only. <Confidence level="low" /></>],
  ["13 · Built-up growth since 2018", <>Mean change in NDBI = (SWIR16 − NIR)/(SWIR16 + NIR) between cloud-free 2018 and 2026 Sentinel-2 composites, inside a 100 m buffer. Only the difference is used; the absolute index is not trustworthy here because bare soil mimics built-up signal. <Confidence level="low" /></>],
];

export default function MethodPage() {
  return (
    <>
      <SiteHeader badge="Method" />
      <DocPage
        title="How each number is produced"
        lede="Every figure in this atlas comes from a stated operation on a cited public dataset. This page is the audit trail: what was computed, with which buffer, from which source, and how confident it is."
      >
        <Section title="1 · Alignment reconstruction">
          <p>
            OpenStreetMap carries the Dravyavati/Amanishah channel as <code>natural=water</code> polygons,
            not as a centreline. Those polygons are unioned in EPSG:32643 and reduced to a skeleton via a
            Voronoi medial axis; the skeleton is loaded as a graph and its longest path taken, which
            removes the branching artefacts a raw medial axis produces.
          </p>
          <p>
            The southern endpoint is where NH-148C actually crosses the channel — the intersection of two
            independently-mapped public features, preferred over the press-named landmark, which sits about
            6.4 km from the mapped channel. The northern endpoint is the mapped channel&apos;s own extent:
            no verified public coordinate exists for the &ldquo;Majar Dam&rdquo; named in press coverage, so
            none was invented.
          </p>
          <p>
            Simplification is set at 320 m — the lowest tolerance that keeps the line free of
            self-intersections. Higher tolerances shorten the result toward the reported ~36 km but flatten
            curvature until nearly every segment reads as straight, which fails the curvature check below.
          </p>
        </Section>

        <Section title="2 · Chainage">
          <p>
            The centreline is cut into 100 m segments keyed on <code>chainage_m</code>. That key is the join
            for every layer that follows: if an analysis cannot be expressed per-chainage, it does not enter
            the atlas.
          </p>
        </Section>

        <Section title="3 · The thirteen constraints">
          <Rows rows={CONSTRAINTS} />
        </Section>

        <Section title="4 · Composite and sensitivity">
          <p>
            The composite is a weighted mean of the thirteen scores, equal-weighted by default. Severity
            bands are percentile-based against the composite&apos;s own distribution — top 10% high, next
            20% medium — rather than fixed 0–3 cutoffs. That choice is forced by the data: most constraints
            are sparse and binary, so the composite tops out near 1.2 and fixed absolute thresholds would
            classify essentially everything as low.
          </p>
          <p>
            Every constraint weight is then perturbed ±35% across eight deterministic combinations, and only
            chainages whose severity band survives all of them are reported as robust. That threshold is
            sensitive: ±50% leaves zero robust segments, ±30% leaves 47. The tightness of that range is
            itself a finding — many segments sit close together in composite score.
          </p>
        </Section>

        <Section title="5 · The ML layer">
          <p>
            Four methods, all constrained by one rule: nothing predicts a quantity this repository has no
            ground truth for. There is no observed traffic count, no tendered cost, no gauged flood record
            here, so nothing outputs one.
          </p>
          <Rows
            rows={[
              ["Monte Carlo uncertainty", "5,000 runs perturbing weights and scores jointly. Each layer's perturbation scale comes from its own confidence tag, so a low-confidence layer moves a full point while a high-confidence one barely shifts. Yields a 90% interval per chainage."],
              ["DBSCAN clustering", "Groups robust hotspot segments into contiguous corridors along chainage (ε = 600 m), because decisions are made over stretches, not isolated 100 m cells."],
              ["Isolation Forest", "Flags chainages whose combination of constraints is unusual even where no single constraint is extreme — a segment mid-range on eight things at once is a real problem no per-constraint threshold catches."],
              ["Neural surrogate", "A 64/32 MLP fitted to reproduce the composite from the constraint vector, then permutation importance over 20 repeats. It explains this atlas's own index; it does not forecast anything."],
            ]}
          />
        </Section>

        <Section title="Projection discipline">
          <p>
            All spatial analysis runs in EPSG:32643 (UTM 43N); storage and serving are EPSG:4326.
            Conversions are explicit, and analysis functions are wrapped in a guard that raises if handed a
            frame in the wrong CRS. This is not theoretical hygiene — a buffer applied while still in
            degrees silently erased an entire layer during development, and the guard plus a unit check is
            what surfaced it.
          </p>
        </Section>
      </DocPage>
    </>
  );
}
