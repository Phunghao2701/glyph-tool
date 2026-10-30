import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import type { Variant } from "../api/variants.api";
import { AppLink } from "../../../app/providers/NavigationProvider";

const palettes = ["", "olive", "sand"];

export function VariantCard({ variant, projectId, index }: { variant: Variant; projectId: string; index: number }) {
  const { t } = useTranslation();
  const revision = variant.currentRevision;
  const previewFamily = `vfk-variant-${variant.id.replace(/[^a-zA-Z0-9]/g, "")}`;
  const previewStyle: CSSProperties | undefined = revision?.previewUrl
    ? { fontFamily: `"${previewFamily}", var(--serif)` }
    : undefined;
  return <>
    {revision?.previewUrl && <style>{`@font-face{font-family:"${previewFamily}";src:url("${revision.previewUrl}");font-display:swap}`}</style>}
    <AppLink
      to={`/projects/${projectId}/variants/${variant.id}`}
      className={`variant-card${revision?.approved ? " selected" : ""}`}
      aria-label={t("variants.openVariant", { label: variant.label })}
    >
      <div className="variant-top"><div><div className="variant-name">VER {variant.label}</div><div className="variant-code">{revision?.status ? t(`common.status.${revision.status}`, { defaultValue: revision.status }) : t(`common.status.${variant.status}`, { defaultValue: variant.status })}</div></div><span className="variant-check" aria-hidden="true">✓</span></div>
      <div className={`variant-sample ${palettes[index % palettes.length]}`} style={previewStyle}>Ắ ỗ ự</div>
      <h3>{revision?.aiDesign?.sourceStyle || t("variants.openVariant", { label: variant.label })}</h3>
      <p>{revision?.aiDesign?.rationale || t("review.description")}</p>
    </AppLink>
  </>;
}

