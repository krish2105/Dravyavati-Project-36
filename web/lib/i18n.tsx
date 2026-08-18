"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

/**
 * Bilingual UI, English default.
 *
 * Register follows how Rajasthan government engineering documents are
 * actually written: formal administrative Hindi, but standard technical
 * terms kept in their English form — कॉरिडोर, चेनेज, IRC:86, NDBI. Coining
 * Sanskritised equivalents for terms engineers only ever meet in English
 * would read as machine-translated to the audience this is for.
 */

export type Lang = "en" | "hi";

const DICT = {
  // chrome
  brand: ["Dravyavati Atlas", "द्रव्यवती एटलस"],
  screeningGrade: ["Screening-grade", "स्क्रीनिंग-स्तर"],
  navAtlas: ["Atlas", "एटलस"],
  navAnalysis: ["Analysis", "विश्लेषण"],
  navSegments: ["Segments", "सेगमेंट"],
  navMethod: ["Method", "पद्धति"],
  navSources: ["Sources", "स्रोत"],
  navLimits: ["Limits", "सीमाएँ"],

  // stat bar
  reconstructed: ["Reconstructed", "पुनर्निर्मित"],
  segments: ["Segments", "सेगमेंट"],
  constraints: ["Constraints", "अवरोध श्रेणियाँ"],
  robustHotspots: ["Robust hotspots", "स्थिर हॉटस्पॉट"],
  highSeverity: ["High severity", "उच्च गंभीरता"],
  mediumSeverity: ["Medium severity", "मध्यम गंभीरता"],
  lowSeverity: ["Low severity", "निम्न गंभीरता"],
  railCrossings: ["Rail crossings", "रेल क्रॉसिंग"],
  crossDrainage: ["Cross-drainage", "क्रॉस-ड्रेनेज"],
  belowIrc: ["Below IRC radius", "IRC त्रिज्या से कम"],
  loading: ["Loading…", "लोड हो रहा है…"],

  // map controls
  legend: ["Legend", "लेजेंड"],
  robustOnly: ["Robust hotspots only", "केवल स्थिर हॉटस्पॉट"],
  terrain3d: ["3D terrain", "3D भूभाग"],
  zoningSheet: ["Zoning sheet", "ज़ोनिंग शीट"],
  markers: ["Corridor markers", "कॉरिडोर चिह्न"],

  // legend panel
  compositeSeverity: ["Composite severity", "समग्र गंभीरता"],
  bandLow: ["Low — bottom 70% of segments", "निम्न — नीचे के 70% सेगमेंट"],
  bandMedium: ["Medium — 70th–90th percentile", "मध्यम — 70वें–90वें पर्सेंटाइल"],
  bandHigh: ["High — top 10% of segments", "उच्च — शीर्ष 10% सेगमेंट"],
  robustLegend: [
    "Robust hotspot (stable under ±35% reweighting)",
    "स्थिर हॉटस्पॉट (±35% भार-परिवर्तन पर अपरिवर्तित)",
  ],
  legendNote: [
    "Equal-weight composite across all {n} constraints. Click a segment on the map for its full breakdown.",
    "सभी {n} अवरोध श्रेणियों पर समान-भार समग्र स्कोर। पूरा विवरण देखने के लिए मानचित्र पर सेगमेंट क्लिक करें।",
  ],
  provenanceNote: [
    "See data/SOURCES.md for provenance and confidence per layer.",
    "प्रत्येक लेयर की स्रोत-श्रृंखला और विश्वसनीयता हेतु data/SOURCES.md देखें।",
  ],

  // disclaimer — the one string that must never soften in either language
  disclaimer: [
    "Screening-grade, not design-grade. Real pipeline output, every layer cited in data/SOURCES.md. Verify against field survey.",
    "यह स्क्रीनिंग-स्तर का आकलन है, डिज़ाइन-स्तर का नहीं। समस्त लेयर data/SOURCES.md में उद्धृत हैं। क्षेत्रीय सर्वेक्षण से सत्यापन आवश्यक है।",
  ],
  disclaimerShort: [
    "Screening-grade, not design-grade. All findings require verification against field survey.",
    "स्क्रीनिंग-स्तर, डिज़ाइन-स्तर नहीं। समस्त निष्कर्षों का क्षेत्रीय सर्वेक्षण से सत्यापन आवश्यक है।",
  ],

  // markers
  northTerminus: ["North terminus", "उत्तरी छोर"],
  southTerminus: ["South terminus", "दक्षिणी छोर"],
  flowDirection: ["Flow: north → south (downstream)", "प्रवाह: उत्तर → दक्षिण (अनुप्रवाह)"],
} as const;

export type Key = keyof typeof DICT;

const LangContext = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({
  lang: "en",
  setLang: () => {},
});

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    const saved = window.localStorage.getItem("atlas-lang");
    if (saved === "hi" || saved === "en") setLangState(saved);
  }, []);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    window.localStorage.setItem("atlas-lang", l);
    document.documentElement.lang = l;
  }, []);

  return <LangContext.Provider value={{ lang, setLang }}>{children}</LangContext.Provider>;
}

export function useLang() {
  return useContext(LangContext);
}

/** t("legendNote", { n: 13 }) */
export function useT() {
  const { lang } = useLang();
  return useCallback(
    (key: Key, vars?: Record<string, string | number>) => {
      let s: string = DICT[key][lang === "hi" ? 1 : 0];
      if (vars) for (const [k, v] of Object.entries(vars)) s = s.replace(`{${k}}`, String(v));
      return s;
    },
    [lang],
  );
}

export function LanguageToggle({ className = "" }: { className?: string }) {
  const { lang, setLang } = useLang();
  return (
    <div
      className={`flex shrink-0 items-center rounded-full border border-line p-0.5 ${className}`}
      role="group"
      aria-label="Language / भाषा"
    >
      {(["en", "hi"] as const).map((l) => (
        <button
          key={l}
          type="button"
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          className={`rounded-full px-2 py-0.5 text-[11px] transition-colors ${
            lang === l ? "bg-channel/20 font-medium text-channel-dim dark:text-channel" : "text-fog"
          }`}
        >
          {l === "en" ? "EN" : "हिं"}
        </button>
      ))}
    </div>
  );
}
