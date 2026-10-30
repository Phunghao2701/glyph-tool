import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { getProject, type Project } from "../api/projects.api";
import { AppLink } from "../../../app/providers/NavigationProvider";
import { ErrorBox, Icon, JobWatch, Loading, StatusTag } from "../../../shared/ui";
import { getError } from "../../../shared/utils/errors";
import { useAiReadiness } from "../../ai-providers";
import { AnalysisSummary } from "../../font-analysis";
import { VariantGenerationPanel } from "../../variants";
import { Button } from "../../../shared/ui/Button";

function getProjectSteps(project: Project, labels: string[]) {
  const hasAnalysis = !!project.analysis;
  const hasVariants = project.variants.length > 0;
  const hasReview = project.variants.some(variant => !!variant.currentRevision?.approved);
  const hasPassedValidation = project.variants.some(variant => variant.currentRevision?.validation?.status === "passed");
  const done = [hasAnalysis, hasVariants, hasReview, hasPassedValidation];
  const current = done.findIndex(value => !value);
  return labels.map((label, index) => ({
    label,
    complete: done[index],
    current: current === index,
  }));
}

export function ProjectPage({ projectId, query }: { projectId: string; query: URLSearchParams }) {
  const { t, i18n } = useTranslation();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [jobId, setJobId] = useState(query.get("job") || "");
  const ai = useAiReadiness();
  const hasLoaded = useRef(false);
  const reload = useCallback(() => {
    if (!hasLoaded.current) setLoading(true);
    setError("");
    getProject(projectId)
      .then(next => { hasLoaded.current = true; setProject(next); })
      .catch(reason => setError(getError(reason)))
      .finally(() => setLoading(false));
  }, [projectId]);
  useEffect(() => { reload(); }, [reload]);

  if (loading) return <Loading />;
  if (error && !project) return <section className="page"><ErrorBox error={error} retry={reload} /></section>;
  if (!project) return <section className="page"><ErrorBox error={t("project.missing")} /></section>;

  const analysis = project.analysis;
  const coverage = analysis?.coverage;
  const presentCount = coverage?.presentCount;
  const requiredCount = coverage?.requiredCount;
  const coveragePercent = typeof coverage?.percent === "number" ? Math.round(coverage.percent) : null;
  const variantForStudio = project.variants.find(variant => variant.currentRevisionId || variant.currentRevision?.id);
  const steps = getProjectSteps(project, t("project.steps", { returnObjects: true }) as string[]);
  const createdLabel = project.createdAt ? new Date(project.createdAt).toLocaleDateString(i18n.resolvedLanguage === "en" ? "en-US" : "vi-VN") : t("project.created");

  return <section className="page project-detail-page">
    <AppLink to="/projects?view=projects" className="back-link"><Icon name="arrow-left" /> {t("project.back")}</AppLink>
    <div className="detail-head">
      <div className="detail-head-title">
        <span className="font-thumb olive" aria-hidden="true">Aa</span>
        <div><div className="eyebrow">{t("project.eyebrow")}</div><h1>{project.name}</h1><p>{project.sourceFont?.filename || t("common.noSourceFont")} · {createdLabel}</p></div>
      </div>
      <div className="page-actions">
        <StatusTag tone={project.status === "failed" ? "bad" : project.analysis ? "good" : "warn"}>{t(`common.status.${project.status}`, { defaultValue: project.status })}</StatusTag>
        {variantForStudio ? <AppLink className="btn btn-primary" to={`/projects/${project.id}/variants/${variantForStudio.id}/editor`}><Icon name="pen-tool" /> {t("project.openStudio")}</AppLink> : <Button type="button" kind="primary" disabled title={t("project.needVariants")}><Icon name="pen-tool" /> {t("project.openStudio")}</Button>}
      </div>
    </div>

    <div className="detail-kpis">
      <div className="card detail-kpi"><small>{t("project.coverage")}</small><strong>{presentCount ?? "—"} <span style={{ font: "400 15px var(--sans)", color: "#94a096" }}>/ {requiredCount ?? "—"}</span></strong></div>
      <div className="card detail-kpi"><small>{t("project.vietnameseRatio")}</small><strong>{coveragePercent === null ? "—" : `${coveragePercent}%`}</strong></div>
      <div className="card detail-kpi"><small>{t("project.variantCount")}</small><strong>{project.variants.length || t("project.notCreated")}</strong></div>
    </div>

    <div className="card steps-bar">{steps.map((step, index) => <div key={step.label} className={`step-block${step.complete ? " done" : step.current ? " current" : ""}`}>
      <span className="step-round">{step.complete ? <Icon name="check" size={14} /> : index + 1}</span>
      <span className="step-info"><strong>{step.label}</strong><small>{step.complete ? t("project.stepDone") : step.current ? t("project.stepCurrent") : t("project.stepTodo")}</small></span>
    </div>)}</div>

    {jobId && <JobWatch jobId={jobId} onDone={reload} />}
    {project.activeJobs.filter(job => job.id !== jobId).map(job => <JobWatch key={job.id} jobId={job.id} onDone={reload} />)}
    {error && <ErrorBox error={error} retry={reload} />}

    <VariantGenerationPanel project={project} aiReady={!!ai.ready} aiLoading={ai.loading} onJobStarted={setJobId} onError={setError} />

    <div className="project-summary">
      <article className="card">
        <div className="eyebrow">{t("project.eyebrow")}</div><h2 className="section-title" style={{ margin: "7px 0 14px" }}>{t("project.fontInfo")}</h2>
        <div className="field-row"><span>{t("export.fileName")}</span><b>{project.sourceFont?.filename || t("common.noSourceFont")}</b></div>
        <div className="field-row"><span>{t("project.format")}</span><b>{project.sourceFont?.format?.toUpperCase() || analysis?.format?.toUpperCase() || t("common.notAvailable")}</b></div>
        <div className="field-row"><span>{t("project.family")}</span><b>{analysis?.family || t("common.noAnalysis")}</b></div>
        <div className="field-row"><span>{t("project.units")}</span><b>{analysis?.unitsPerEm ?? "—"}</b></div>
        <div className="field-row"><span>{t("project.outline")}</span><b>{analysis?.outlineType || "—"}</b></div>
      </article>
      <AnalysisSummary analysis={analysis} hasSourceFont={!!project.sourceFont} />
    </div>

    <div className="card action-footer">
      <small>{t("project.continue")}</small>
      <div className="btn-row"><AppLink className="btn btn-light" to={`/projects/${project.id}/validation`}><Icon name="shield-check" /> {t("project.openQa")}</AppLink><AppLink className="btn btn-primary" to={`/projects/${project.id}/export`}><Icon name="package" /> {t("project.export")}</AppLink></div>
    </div>
  </section>;
}

