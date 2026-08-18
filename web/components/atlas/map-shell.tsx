"use client";

import { useEffect, useRef, useState } from "react";
import { MapLibreMap, NavigationControl, LngLatBounds, Popup, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

// Turbopack emits maplibre's worker without its `maplibre-gl-shared.mjs`
// sibling, so the worker dies on first import: the map mounts and raster
// tiles draw, but every GeoJSON source hangs at isSourceLoaded=false and no
// vector feature ever renders. Serve both files ourselves instead — see
// scripts/copy-maplibre-worker.mjs.
setWorkerUrl("/maplibre/maplibre-gl-worker.mjs");

const JAIPUR_CENTER: [number, number] = [75.7873, 26.9124];

const RISK_SOURCE_ID = "chainage-risk";
const RISK_LAYER_ID = "chainage-risk-line";
const HOTSPOT_LAYER_ID = "chainage-risk-hotspot-outline";

const CONSTRAINT_LABELS: Record<string, string> = {
  railway_crossing: "Railway crossing",
  metro_interface: "Metro interface",
  existing_elevated_structure: "Existing elevated structure",
  major_arterial_crossing: "Major arterial crossing",
  restricted_military_area: "Restricted / military area",
  entry_exit_feasibility: "Entry–exit feasibility",
  curve_severity: "Curve severity",
  eht_line_crossing: "EHT line crossing",
  dam_check_structure: "Dam / check structure",
  land_availability: "Land availability",
  habitation_proximity: "Habitation proximity",
  hydraulic_sensitivity: "Hydraulic sensitivity",
};

function popupHtml(props: Record<string, unknown>): string {
  const rows = Object.entries(CONSTRAINT_LABELS)
    .map(([key, label]) => {
      const score = props[`${key}_score`] ?? (key === "hydraulic_sensitivity" ? props.hydraulic_sensitivity_index : undefined);
      const confidence = props[`${key}_confidence`];
      if (score === undefined || score === null) return "";
      const value = typeof score === "number" && key === "hydraulic_sensitivity" ? (score * 3).toFixed(1) : score;
      return `<tr><td style="padding-right:8px;color:var(--fog)">${label}</td><td style="text-align:right">${value}</td><td style="padding-left:8px;font-size:10px;color:var(--fog);text-transform:uppercase">${confidence ?? ""}</td></tr>`;
    })
    .join("");

  return `
    <div style="font-family:var(--font-sans, sans-serif); min-width:220px">
      <div style="font-family:var(--font-mono, monospace); font-size:11px; color:var(--fog)">chainage ${props.chainage_m}m</div>
      <div style="font-weight:600; margin:2px 0 6px">Composite ${Number(props.composite_score).toFixed(2)} — ${props.severity_band}${props.robust_hotspot ? " · robust hotspot" : ""}</div>
      <table style="font-size:12px; width:100%; border-collapse:collapse">${rows}</table>
    </div>
  `;
}

export function MapShell({
  showRobustOnly = false,
  terrain3d = false,
}: {
  showRobustOnly?: boolean;
  terrain3d?: boolean;
}) {
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
          // Public terrarium-encoded DEM, no auth. Used only for the 3D
          // view; MapLibre renders terrain natively, so this avoids pulling
          // in a whole second rendering library for one feature.
          terrainDem: {
            type: "raster-dem",
            tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
            tileSize: 256,
            encoding: "terrarium",
            maxzoom: 13,
            attribution: "Elevation: Mapzen / AWS Terrain Tiles",
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

    const resizeObserver = new ResizeObserver(() => map.resize());
    resizeObserver.observe(containerRef.current);

    map.on("load", async () => {
      try {
        const res = await fetch("/data/chainage_risk.geojson");
        if (!res.ok) throw new Error(`fetch failed: ${res.status}`);
        const geojson = await res.json();

        if (!geojson.features?.length) {
          setStatus("empty");
          return;
        }

        map.addSource(RISK_SOURCE_ID, { type: "geojson", data: geojson });

        map.addLayer({
          id: RISK_LAYER_ID,
          type: "line",
          source: RISK_SOURCE_ID,
          layout: { "line-join": "round", "line-cap": "round" },
          paint: {
            "line-color": [
              "match",
              ["get", "severity_band"],
              "high",
              "#e8a23d",
              "medium",
              "#c98f4a",
              /* low */ "#2fa8a0",
            ],
            "line-width": ["match", ["get", "severity_band"], "high", 6, "medium", 4.5, 3],
            "line-opacity": 0.9,
          },
        });

        map.addLayer({
          id: HOTSPOT_LAYER_ID,
          type: "line",
          source: RISK_SOURCE_ID,
          layout: { "line-join": "round", "line-cap": "round" },
          filter: ["==", ["get", "robust_hotspot"], true],
          paint: {
            "line-color": "#e8a23d",
            "line-width": 10,
            "line-opacity": 0.35,
            "line-blur": 2,
          },
        });
        map.moveLayer(HOTSPOT_LAYER_ID, RISK_LAYER_ID);

        const popup = new Popup({ closeButton: true, maxWidth: "300px" });
        map.on("click", RISK_LAYER_ID, (e) => {
          const feature = e.features?.[0];
          if (!feature) return;
          popup.setLngLat(e.lngLat).setHTML(popupHtml(feature.properties as Record<string, unknown>)).addTo(map);
        });
        map.on("mouseenter", RISK_LAYER_ID, () => (map.getCanvas().style.cursor = "pointer"));
        map.on("mouseleave", RISK_LAYER_ID, () => (map.getCanvas().style.cursor = ""));

        const bounds = new LngLatBounds();
        let hasCoords = false;
        for (const feature of geojson.features) {
          const coords: number[][] = feature.geometry.coordinates;
          for (const c of coords) {
            bounds.extend(c as [number, number]);
            hasCoords = true;
          }
        }
        if (hasCoords) map.fitBounds(bounds, { padding: 80, duration: 0 });

        // 'load' only means the *style* is ready — the GeoJSON source still
        // tiles/processes asynchronously. Wait for 'idle' so the "loading"
        // overlay doesn't disappear before there's actually anything to see.
        map.once("idle", () => setStatus("loaded"));
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

  useEffect(() => {
    const map = mapRef.current;
    if (!map || status !== "loaded") return;
    // Exaggeration is deliberately mild: this terrain is ~30 m data over
    // gently sloping ground, and a dramatic vertical stretch would imply
    // relief the source cannot actually resolve.
    if (terrain3d) {
      map.setTerrain({ source: "terrainDem", exaggeration: 1.4 });
      map.easeTo({ pitch: 62, bearing: -18, duration: 900 });
    } else {
      map.setTerrain(null);
      map.easeTo({ pitch: 0, bearing: 0, duration: 700 });
    }
  }, [terrain3d, status]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || status !== "loaded") return;
    const filter = showRobustOnly ? ["==", ["get", "robust_hotspot"], true] : null;
    if (map.getLayer(RISK_LAYER_ID)) map.setFilter(RISK_LAYER_ID, filter as never);
  }, [showRobustOnly, status]);

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
              ? "No scored corridor data yet — run the Python pipeline (src/scoring/composite.py) and src/export/web.py."
              : "Could not load corridor data."}
          </p>
        </div>
      )}
    </div>
  );
}
