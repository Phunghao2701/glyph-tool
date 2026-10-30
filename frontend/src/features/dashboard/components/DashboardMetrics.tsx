import { NumberTicker } from "../../../shared/ui/number-ticker";
import { useTranslation } from "react-i18next";

type DashboardMetricsProps = {
  pendingProjectCount: number;
  totalVariantCount: number;
  projectCount: number;
  reviewedProjectCount: number;
  averageCoverage: number | null;
  loading: boolean;
};

function MetricValue({ value, loading, suffix = "", locale }: { value: number | null; loading: boolean; suffix?: string; locale: string }) {
  if (loading || value === null) return <span>{loading ? "—" : "—"}</span>;
  return <><NumberTicker value={value} locale={locale} minimumIntegerDigits={suffix ? 1 : 2} />{suffix}</>;
}

export function DashboardMetrics({ pendingProjectCount, totalVariantCount, projectCount, reviewedProjectCount, averageCoverage, loading }: DashboardMetricsProps) {
  const { t, i18n } = useTranslation();
  const locale = i18n.resolvedLanguage === "en" ? "en-US" : "vi-VN";
  return (
    <div className="metrics-grid">
      <div className="card metric-card"><div className="metric-head">{t("dashboard.metrics.pending")}</div><div className="metric-num"><MetricValue value={pendingProjectCount} loading={loading} locale={locale} /></div><div className="metric-foot"><strong>{loading ? "—" : totalVariantCount}</strong> {t("dashboard.metrics.variants")}</div></div>
      <div className="card metric-card"><div className="metric-head">{t("dashboard.metrics.projects")}</div><div className="metric-num"><MetricValue value={projectCount} loading={loading} locale={locale} /></div><div className="metric-foot">{t("dashboard.metrics.projectsFoot")}</div></div>
      <div className="card metric-card"><div className="metric-head">{t("dashboard.metrics.chosen")}</div><div className="metric-num"><MetricValue value={reviewedProjectCount} loading={loading} locale={locale} /></div><div className="metric-foot">{t("dashboard.metrics.qaNext")}</div></div>
      <div className="card metric-card"><div className="metric-head">{t("dashboard.metrics.coverage")}</div><div className="metric-num"><MetricValue value={averageCoverage} loading={loading} suffix="%" locale={locale} /></div><div className="metric-foot">{t("dashboard.metrics.coverageFoot")}</div></div>
    </div>
  );
}
