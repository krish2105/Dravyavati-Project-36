"use client";

import { useEffect, useRef, useState } from "react";
import { MapLibreMap, NavigationControl, LngLatBounds } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const JAIPUR_CENTER: [number, number] = [75.7873, 26.9124];

const RIVER_SOURCE_ID = "dravyavati-river";
const RIVER_LAYER_ID = "dravyavati-river-line";

export function MapShell() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [status, setStatus] = useState<"loading" | "loaded" | "empty" | "error">("loading");

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new MapLibreMap({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "&copy; OpenStreetMap contributors",
          },
        },
        layers: [{ id: "osm", type: "raster", source: "osm" }],
      },
      center: JAIPUR_CENTER,
      zoom: 11,
      attributionControl: { compact: true },
    });
    mapRef.current = map;
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");

    // The container can be zero-sized at construction time (e.g. a flex layout
    // that hasn't settled yet, or the tab starting hidden) — MapLibre only reads
    // its size once, so recover by resizing whenever the container's box changes.
    const resizeObserver = new ResizeObserver(() => map.resize());
    resizeObserver.observe(containerRef.current);

    map.on("load", async () => {
      try {
        const res = await fetch("/data/dravyavati-river.geojson");
        if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
        const geojson = await res.json();

        if (!geojson.features?.length) {
          setStatus("empty");
          return;
        }

        map.addSource(RIVER_SOURCE_ID, { type: "geojson", data: geojson });
        map.addLayer({
          id: RIVER_LAYER_ID,
          type: "line",
          source: RIVER_SOURCE_ID,
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": "#2fa8a0",
            "line-width": 4,
            "line-opacity": 0.9,
          },
        });

        const bounds = new LngLatBounds();
        let hasCoords = false;
        for (const feature of geojson.features) {
          const geom = feature.geometry;
          const coordsList: number[][] =
            geom.type === "LineString"
              ? geom.coordinates
              : geom.type === "MultiLineString"
                ? geom.coordinates.flat()
                : [];
          for (const c of coordsList) {
            bounds.extend(c as [number, number]);
            hasCoords = true;
          }
        }
        if (hasCoords) map.fitBounds(bounds, { padding: 80, duration: 0 });
        setStatus("loaded");
      } catch {
        setStatus("error");
      }
    });

    return () => {
      resizeObserver.disconnect();
      try {
        map.remove();
      } finally {
        mapRef.current = null;
      }
    };
  }, []);

  return (
    <div className="relative h-full w-full">
      <div
        ref={containerRef}
        className="h-full w-full dark:[filter:invert(1)_hue-rotate(180deg)_brightness(0.95)_contrast(0.9)]"
      />
      {status === "loading" && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center bg-background/60 font-mono text-xs text-fog">
          Loading corridor geometry…
        </div>
      )}
      {(status === "empty" || status === "error") && (
        <div className="pointer-events-none absolute inset-x-0 bottom-24 flex justify-center px-4">
          <p className="rounded-lg border border-line bg-surface/95 px-4 py-2 font-mono text-xs text-fog shadow-lg">
            {status === "empty"
              ? "No river geometry found yet — run the OSM fetch to populate public/data/dravyavati-river.geojson."
              : "Could not load river geometry."}
          </p>
        </div>
      )}
    </div>
  );
}
