import { useEffect, useRef, useState } from "react";
import { getSourceFontUrl } from "../lib/api";

type FontFallback = { id: string; url?: string | null; format?: string | null };

export function useSourceFontPreview<T extends HTMLElement>(projectId: string, format?: string | null, fallback?: FontFallback) {
  const previewRef = useRef<T>(null);
  const [isNearViewport, setIsNearViewport] = useState(false);
  const safeProjectId = projectId.replace(/[^a-z\d_-]/gi, "-");
  const fontFamily = `VietFontSource-${safeProjectId}`;
  const fallbackFamily = fallback?.url ? `VietFontRevision-${safeProjectId}-${fallback.id.replace(/[^a-z\d_-]/gi, "-")}` : "";
  const fallbackUrl = fallback?.url;
  const fallbackFormat = fallback?.format;

  useEffect(() => {
    if (!format || isNearViewport || !previewRef.current) return;
    if (typeof IntersectionObserver === "undefined") {
      setIsNearViewport(true);
      return;
    }

    const observer = new IntersectionObserver(([entry]) => {
      if (entry?.isIntersecting) {
        setIsNearViewport(true);
        observer.disconnect();
      }
    }, { rootMargin: "160px 0px" });
    observer.observe(previewRef.current);
    return () => observer.disconnect();
  }, [format, isNearViewport, projectId]);

  useEffect(() => {
    if (!format || !isNearViewport) return;

    const style = document.createElement("style");
    const cssFormat = format.toLowerCase() === "otf" ? "opentype" : "truetype";
    const rules = [`@font-face { font-family: "${fontFamily}"; src: url("${getSourceFontUrl(projectId)}") format("${cssFormat}"); font-style: normal; font-weight: 400; font-display: swap; }`];
    if (fallbackUrl && fallbackFormat) {
      const fallbackCssFormat = fallbackFormat.toLowerCase() === "otf" ? "opentype" : "truetype";
      rules.push(`@font-face { font-family: "${fallbackFamily}"; src: url("${fallbackUrl}") format("${fallbackCssFormat}"); font-style: normal; font-weight: 400; font-display: swap; }`);
    }
    style.textContent = rules.join("\n");
    document.head.appendChild(style);
    return () => style.remove();
  }, [fallbackFamily, fallbackFormat, fallbackUrl, fontFamily, format, isNearViewport, projectId]);

  return {
    previewRef,
    previewFontFamily: format && isNearViewport
      ? [`"${fontFamily}"`, fallbackFamily ? `"${fallbackFamily}"` : "", "var(--serif)"].filter(Boolean).join(", ")
      : undefined,
  };
}
