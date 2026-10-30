import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { approveRevision, getProject, startValidation, type Project } from "../api/validation.api";
import { AppLink, useNavigate } from "../../../app/providers/NavigationProvider";
import { Button, ErrorBox, JobWatch, Loading, StatusTag } from "../../../shared/ui";
import { getError } from "../../../shared/utils/errors";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../../shared/ui/primitives/select";
import { Progress } from "../../../shared/ui/primitives/progress";

export function ValidationPage({ projectId }: { projectId: string }) {
  const { t } = useTranslation();
  const [project, setProject] = useState<Project | null>(null);
  const [selected, setSelected] = useState(new URLSearchParams(window.location.search).get("variantId") || "");
  const [jobId, setJobId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const load = useCallback(() => getProject(projectId).then(next => {
    setProject(next);
    setSelected(old => old || next.variants[0]?.id || "");
  }).catch(reason => setError(getError(reason))), [projectId]);
  useEffect(() => { void load(); }, [load]);
  if (!project) return error ? <section className="page"><ErrorBox error={error} retry={load} /></section> : <Loading />;

  const variant = project.variants.find(item => item.id === selected);
  const revision = variant?.currentRevision;
  const checks = revision?.validation?.checks || [];
  const missing = project.analysis?.coverage?.missing || [];
  const coverage = project.analysis?.coverage;
  const percent = typeof coverage?.percent === "number" ? Math.max(0, Math.min(100, Math.round(coverage.percent))) : null;
  const passed = revision?.validation?.status === "passed";
  const run = async () => {
    if (!variant || !revision) return;
    setBusy(true); setError("");
    try { const job = await startValidation(variant.id, revision.id); setJobId(job.id); }
    catch (reason) { setError(getError(reason)); }
    finally { setBusy(false); }
  };
  const approve = async () => {
    if (!variant || !revision) return;
    setBusy(true); setError("");
    try { await approveRevision(variant.id, revision.id); await load(); }
    catch (reason) { setError(getError(reason)); }
    finally { setBusy(false); }
  };

  return <section className="page validation-page">
    <div className="page-head"><div><div className="eyebrow">{t("validation.eyebrow")}</div><h1 className="page-title">{t("validation.title")}</h1><p className="page-description">{t("validation.description")}</p></div>
      <div className="page-actions"><StatusTag tone={passed ? "good" : revision?.validation ? "bad" : "warn"}>{revision?.validation?.status ? t(`common.status.${revision.validation.status}`, { defaultValue: revision.validation.status }) : t("validation.notRun")}</StatusTag><AppLink className="btn btn-light" to={`/projects/${projectId}/export${variant ? `?variantId=${variant.id}` : ""}`}>{t("validation.toExport")}</AppLink></div>
    </div>
    {error && <ErrorBox error={error} />}
    {jobId && <JobWatch jobId={jobId} onDone={load} />}
    <div className="qa-layout">
      <section className="card qa-card">
        <div className="section-heading"><div><div className="eyebrow">{t("validation.checklist")}</div><h2 className="section-title">{t("validation.state")}</h2></div>
          <label className="form-label">{t("validation.variant")}<Select value={selected || undefined} onValueChange={setSelected}><SelectTrigger className="form-input" aria-label={t("validation.variant")}><SelectValue placeholder={t("validation.variant")} /></SelectTrigger><SelectContent>{project.variants.map(item => <SelectItem key={item.id} value={item.id}>VER {item.label}</SelectItem>)}</SelectContent></Select></label>
        </div>
        <div className="qa-rows">
          {checks.length ? checks.map((check, index) => <div className="qa-row" key={check.id || index}><div><strong>{String(index + 1).padStart(2, "0")} · {check.id}</strong><small>{check.detail || t("validation.noCheckDetails")}</small></div><span className={`qa-value${check.status === "passed" ? "" : " wait"}`}>{t(`common.status.${check.status}`, { defaultValue: check.status })}</span></div>) :
            <div className="qa-row"><div><strong>{t("validation.revisionValidation")}</strong><small>{revision ? t("validation.noValidation", { id: revision.id.slice(0, 8) }) : t("validation.chooseRevision")}</small></div><span className="qa-value wait">{t("validation.notRun")}</span></div>}
        </div>
        <div className="btn-row" style={{ marginTop: 18 }}>
          <Button kind="primary" onClick={() => void run()} disabled={busy || !revision}>{busy ? t("validation.makeJob") : t("validation.run")}</Button>
          <Button kind="secondary" onClick={() => void approve()} disabled={busy || !revision || !passed || !!revision.approved}>{revision?.approved ? t("validation.approved") : t("validation.approve")}</Button>
          {revision && <Button kind="quiet" onClick={() => navigate(`/projects/${projectId}/export?variantId=${variant?.id}&revisionId=${revision.id}`)}>{t("validation.continueExport")}</Button>}
        </div>
      </section>
      <aside className="card qa-card">
        <div className="eyebrow">{t("validation.coverage")}</div>
        <div className="metric-num" style={{ fontSize: 42, marginTop: 8 }}>{percent === null ? "—" : `${percent}%`}</div>
        <Progress className="progress-track" style={{ margin: "13px 0 9px" }} value={percent ?? 0} aria-label={t("validation.coverage")} />
        <p>{typeof coverage?.requiredCount === "number" && typeof coverage.presentCount === "number" ? t("validation.missingMapping", { count: coverage.requiredCount - coverage.presentCount }) : t("validation.afterAnalysis")}</p>
        <div className="divider" /><h3>{t("validation.missingChars")}</h3>
        {missing.length ? <><div className="missing-list">{missing.slice(0, 36).join(" ")}</div>{missing.length > 36 && <p style={{ marginTop: 10 }}>{t("validation.otherMissing", { count: missing.length - 36 })}</p>}</> : <p style={{ marginTop: 8 }}>{coverage ? t("validation.noMissingCmap") : t("validation.noMissingData")}</p>}
      </aside>
    </div>
    <div className="notice" style={{ marginTop: 18 }}>{t("validation.coverageNote")}</div>
  </section>;
}

