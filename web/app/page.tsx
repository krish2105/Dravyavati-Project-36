import { SmoothScroll } from "@/components/landing/smooth-scroll";
import { Cursor } from "@/components/landing/cursor";
import { Nav } from "@/components/landing/nav";
import { Hero } from "@/components/landing/hero";
import { BentoFeatures } from "@/components/landing/bento-features";
import { SourcesFooter } from "@/components/landing/sources-footer";

export default function Home() {
  return (
    <SmoothScroll>
      <Cursor />
      <Nav />
      <main>
        <Hero />
        <BentoFeatures />
        <SourcesFooter />
      </main>
    </SmoothScroll>
  );
}
