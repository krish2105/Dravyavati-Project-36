"use client";

import { useEffect, useState } from "react";

export type ProfilePoint = {
  chainage_m: number;
  composite: number;
  p05: number;
  p95: number;
  band: "low" | "medium" | "high";
  robust: boolean;
  anomaly: boolean;
};

export type HotspotCorridor = {
  id: number;
  start_m: number;
  end_m: number;
  segments: number;
  mean_composite: number;
  top_drivers: { label: string; mean_score: number }[];
};

export type Analytics = {
  corridor: { length_km: number; segments: number; constraint_count: number };
  severity: Record<string, number>;
  robust_hotspots: number;
  anomalies: number;
  uncertainty: { mean_ci_width: number | null };
  crossings: Record<string, number>;
  metro: Record<string, number>;
  irc86: { min_radius_m: number | null; segments_below: number };
  land: { mean_unbuilt_pct: number; buildings_within_100m: number; segments_with_buildings: number };
  cooccurrence: { labels: string[]; matrix: number[][] };
  hotspot_corridors: HotspotCorridor[];
  profile: ProfilePoint[];
};

export type FeatureImportance = {
  surrogate_r2: number;
  features: { label: string; importance: number; std: number }[];
};

export function useJson<T>(url: string): T | null {
  const [data, setData] = useState<T | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetch(url)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d) => !cancelled && setData(d))
      .catch(() => !cancelled && setData(null));
    return () => {
      cancelled = true;
    };
  }, [url]);
  return data;
}

export const BAND_COLOR: Record<string, string> = {
  low: "var(--channel)",
  medium: "#c98f4a",
  high: "var(--flag)",
};

export const km = (m: number) => `${(m / 1000).toFixed(1)} km`;
