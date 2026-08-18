"use client";

import { useT } from "@/lib/i18n";
import { useJson, type Analytics } from "@/lib/analytics";

export function LegendPanel() {
  const t = useT();
  const analytics = useJson<Analytics>("/data/analytics.json");
  // Read from the pipeline rather than a literal: this panel previously said
  // "all 12 constraints" while the pipeline had moved to 13.
  const n = analytics?.corridor.constraint_count ?? 13;

  const rows: [string, string][] = [
    [t("bandLow"), "bg-channel"],
    [t("bandMedium"), "bg-[#c98f4a]"],
    [t("bandHigh"), "bg-flag"],
  ];

  return (
    <div className="p-4 text-sm">
      <h2 className="font-display text-sm font-medium text-foreground">{t("compositeSeverity")}</h2>
      <ul className="mt-3 space-y-2">
        {rows.map(([label, swatch]) => (
          <li key={label} className="flex items-center gap-2 text-xs text-fog">
            <span className={`h-3 w-3 shrink-0 rounded-sm ${swatch}`} aria-hidden />
            {label}
          </li>
        ))}
      </ul>
      <div className="mt-3 flex items-center gap-2 text-xs text-fog">
        <span className="h-3 w-3 shrink-0 rounded-sm border-2 border-flag/60" aria-hidden />
        {t("robustLegend")}
      </div>
      <div className="mt-3 flex items-center gap-2 text-xs text-fog">
        <span className="h-3 w-3 shrink-0 rounded-full border-2 border-white bg-channel" aria-hidden />
        {t("northTerminus")} / {t("southTerminus")}
      </div>
      <p className="mt-1 text-[11px] text-fog">{t("flowDirection")}</p>
      <p className="mt-4 border-t border-line pt-3 text-[11px] leading-relaxed text-fog">
        {t("legendNote", { n })}
      </p>
      <p className="mt-2 text-[11px] leading-relaxed text-fog">{t("provenanceNote")}</p>
    </div>
  );
}
