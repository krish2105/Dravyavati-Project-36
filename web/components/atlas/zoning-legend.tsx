"use client";

import { useState } from "react";
import { useJson } from "@/lib/analytics";
import { useLang } from "@/lib/i18n";

type ZoningLegend = {
  sheet: string;
  source: string;
  why_not_classified: string;
  categories: { en: string; hi: string; symbology: string }[];
};

const COPY = {
  title: ["Zoning sheet legend", "ज़ोनिंग शीट लेजेंड"],
  intro: [
    "Land-use categories on the overlaid JDA sheet. Read them directly off the sheet — they are not machine-classified.",
    "अध्यारोपित JDA शीट पर भू-उपयोग श्रेणियाँ। इन्हें सीधे शीट से पढ़ें — ये मशीन द्वारा वर्गीकृत नहीं हैं।",
  ],
  why: ["Why not classified automatically", "स्वतः वर्गीकरण क्यों नहीं"],
  whyBody: [
    "Categories are separated by hatch pattern and embedded letter codes, not fill colour alone. Commercial and wholesale market share a cross-hatch; central park and stadium share a dot fill and differ only by the letters CP and S. A nearest-colour classifier would merge those pairs, so no chainage carries a zoning attribute.",
    "श्रेणियाँ केवल रंग से नहीं, बल्कि हैच पैटर्न और अंकित अक्षर-कोड से पृथक होती हैं। वाणिज्यिक और थोक बाज़ार दोनों क्रॉस-हैच हैं; सेंट्रल पार्क और स्टेडियम दोनों बिंदुयुक्त हैं और केवल CP तथा S अक्षरों से भिन्न हैं। निकटतम-रंग वर्गीकरण इन युग्मों को मिला देगा, इसलिए किसी भी चेनेज पर ज़ोनिंग विशेषता निर्दिष्ट नहीं की गई है।",
  ],
  showSheet: ["View legend as printed", "मूल लेजेंड देखें"],
  hideSheet: ["Hide printed legend", "मूल लेजेंड छिपाएँ"],
};

export function ZoningLegend() {
  const data = useJson<ZoningLegend>("/overlays/zdp_10_legend.json");
  const { lang } = useLang();
  const [showSheet, setShowSheet] = useState(false);
  const i = lang === "hi" ? 1 : 0;

  if (!data) return null;

  return (
    <div className="border-t border-line p-4 text-sm">
      <h2 className="font-display text-sm font-medium text-foreground">{COPY.title[i]}</h2>
      <p className="mt-1 text-[11px] leading-relaxed text-fog">{COPY.intro[i]}</p>

      <ul className="mt-3 space-y-1">
        {data.categories.map((c) => (
          <li key={c.en} className="text-xs leading-snug text-fog">
            <span className="text-foreground">{lang === "hi" ? c.hi : c.en}</span>
            <span className="text-fog/70"> · {c.symbology}</span>
          </li>
        ))}
      </ul>

      <button
        type="button"
        onClick={() => setShowSheet((v) => !v)}
        className="mt-3 w-full rounded-lg border border-line px-2 py-1.5 text-[11px] text-fog transition-colors hover:border-channel hover:text-foreground"
      >
        {showSheet ? COPY.hideSheet[i] : COPY.showSheet[i]}
      </button>

      {showSheet && (
        // The legend as printed, so a reviewer can match hatching by eye
        // rather than trusting our transcription of it.
        <img
          src="/overlays/zdp_10_legend.jpg"
          alt={COPY.title[i]}
          className="mt-2 w-full rounded-lg border border-line bg-white"
          loading="lazy"
        />
      )}

      <p className="mt-3 border-t border-line pt-2 text-[11px] leading-relaxed text-fog">
        <span className="text-foreground">{COPY.why[i]}.</span> {COPY.whyBody[i]}
      </p>
    </div>
  );
}
