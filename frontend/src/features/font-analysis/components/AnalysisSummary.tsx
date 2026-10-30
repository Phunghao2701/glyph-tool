import type { AnalysisReport } from "../api/analysis.api";
import { useTranslation } from "react-i18next";

export function AnalysisSummary({ analysis, hasSourceFont }: { analysis?: AnalysisReport | null; hasSourceFont: boolean }) {
  const { t } = useTranslation();
  const missing = analysis?.coverage?.missing || [];
  const percent = typeof analysis?.coverage?.percent === "number" ? Math.max(0, Math.min(100, Math.round(analysis.coverage.percent))) : 0;
  return <article className="card analysis-summary-card">
    <div className="eyebrow">{t("analysis.eyebrow")}</div>
    <h2 className="section-title" style={{ margin: "7px 0 14px" }}>{t("analysis.title")}</h2>
    {analysis ? <>
      <div className="field-row"><span>{t("analysis.family")}</span><b>{analysis.family || t("common.notAvailable")}</b></div>
      <div className="field-row"><span>{t("analysis.style")}</span><b>{analysis.subfamily || t("common.notAvailable")}</b></div>
      <div className="field-row"><span>{t("analysis.outline")}</span><b>{analysis.outlineType || analysis.format || t("common.notAvailable")}</b></div>
      <div className="field-row"><span>{t("analysis.units")}</span><b>{analysis.unitsPerEm ?? "—"}</b></div>
      <div className="progress-labels" style={{ marginTop: 15 }}><span>{t("analysis.coverage")}</span><strong>{percent}%</strong></div>
      <div className="progress-track"><div className="progress-fill" style={{ width: `${percent}%` }} /></div>
      {missing.length > 0 && <><h3 style={{ margin: "18px 0 8px" }}>{t("analysis.missing")}</h3><div className="missing-list">{missing.slice(0, 36).join(" ")}</div>{missing.length > 36 && <small className="tiny-muted">{t("analysis.otherMissing", { count: missing.length - 36 })}</small>}</>}
      {analysis.diagnostics?.map((note, index) => <p className="mini-note" key={index}>{note}</p>)}
    </> : <p className="mini-note">{hasSourceFont ? t("analysis.waiting") : t("analysis.uploadPrompt")}</p>}
  </article>;
}

