/**
 * Copy MapLibre's worker bundle into public/ so it can be served as a static asset.
 *
 * Why this exists: Turbopack rewrites maplibre-gl's internal
 * `new URL('maplibre-gl-worker.mjs', import.meta.url)` into a hashed asset but
 * does NOT emit the worker's `maplibre-gl-shared.mjs` sibling next to it. The
 * worker then throws on its first import and dies silently — the map mounts,
 * raster basemap tiles still render (they don't need the worker), but every
 * GeoJSON/vector source stays stuck at isSourceLoaded=false and nothing draws.
 *
 * See https://github.com/maplibre/maplibre-gl-js/issues/7105 and
 * https://github.com/vercel/next.js/issues/86495
 *
 * Both files must land in the SAME directory because the worker imports the
 * shared module by relative path.
 */

import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const distDir = join(here, "..", "node_modules", "maplibre-gl", "dist");
const outDir = join(here, "..", "public", "maplibre");

mkdirSync(outDir, { recursive: true });

for (const file of ["maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"]) {
  copyFileSync(join(distDir, file), join(outDir, file));
  console.log(`copied ${file} -> public/maplibre/`);
}
