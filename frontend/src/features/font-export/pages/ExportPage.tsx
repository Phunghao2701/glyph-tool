import { useCallback, useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { getExport, getProject, startExport, type ExportArtifact, type Job, type Project } from "../api/font-export.api";
import { AppLink } from "../../../app/providers/NavigationProvider";
import { Button, ErrorBox, Icon, JobWatch, Loading, StatusTag } from "../../../shared/ui";
import { getError } from "../../../shared/utils/errors";
import { Input } from "../../../shared/ui/primitives/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../../shared/ui/primitives/select";
import { AnimatePresence, motion } from "motion/react";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";
import "../export.css";

export function ExportPage({ projectId }: { projectId: string }) {
  const { t } = useTranslation();
  const reduceMotion = usePrefersReducedMotion();
  const [project, setProject] = useState<Project | null>(null);
  const [variantId, setVariantId] = useState("");
  const [revisionId, setRevisionId] = useState("");
  const [name, setName] = useState("");
  const [jobId, setJobId] = useState("");
  const [artifact, setArtifact] = useState<ExportArtifact | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => getProject(projectId).then(next => {
    setProject(next);
    const params = new URLSearchParams(window.location.search);
    const wanted = params.get("variantId") || next.variants[0]?.id || "";
    const variant = next.variants.find(item => item.id === wanted) || next.variants[0];
    setVariantId(variant?.id || "");
    setRevisionId(params.get("revisionId") || variant?.currentRevisionId || "");
    if (variant?.currentRevision && !name) setName(next.name.replace(/\s+/g, "-") + "-Vietnamese");
  }).catch(reason => setError(getError(reason))), [projectId, name]);
  useEffect(() => { void load(); }, [load]);

  if (!project) return error ? <section className="page"><ErrorBox error={error} retry={load} /></section> : <Loading />;
  const variant = project.variants.find(item => item.id === variantId);
  const revision = variant?.revisions.find(item => item.id === revisionId) || variant?.currentRevision;
  const rawFormat = revision?.fontFormat?.toLowerCase();
  const format: "ttf" | "otf" | null = rawFormat === "ttf" || rawFormat === "otf" ? rawFormat : null;
  const eligible = !!revision?.approved && revision.validation?.status === "passed" && revision.status === "ready" && !!format;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!variant || !revision || !format) return;
    setBusy(true); setError(""); setArtifact(null);
    try {
      const job = await startExport(projectId, { variantId: variant.id, revisionId: revision.id, format, name });
      setJobId(job.id);
    } catch (reason) { setError(getError(reason)); }
    finally { setBusy(false); }
  };
  const finished = async (job: Job) => {
    if (job.status === "succeeded" && job.resultId) {
      try { setArtifact(await getExport(job.resultId)); }
      catch (reason) { setError(getError(reason)); }
    }
    await load();
  };
  const stepStates = [true, !!variant?.currentRevision, !!revision?.approved, eligible];
  const readinessSteps = t("export.readinessSteps", { returnObjects: true }) as string[];

  return <section className="page export-page">
    <div className="page-head"><div><div className="eyebrow">{t("export.eyebrow")}</div><h1 className="page-title">{t("export.title")}</h1><p className="page-description">{t("export.description")}</p></div><AppLink className="btn btn-light" to={`/projects/${projectId}/validation${variant ? `?variantId=${variant.id}` : ""}`}>{t("export.backQa")}</AppLink></div>
    {error && <ErrorBox error={error} />}
    {jobId && <JobWatch jobId={jobId} onDone={finished} />}
    <div className="export-layout">
      <section className="card qa-card">
        <div className="eyebrow">{t("export.currentProject")}</div>
        <div className="export-file"><div className="export-file-icon"><Icon name="type" /></div><div><strong>{project.name}</strong><small>{project.sourceFont?.filename || t("common.noSourceFont")} · {variant ? `VER ${variant.label}` : t("export.noVariant")}</small></div></div>
        <AnimatePresence initial={false}>
          {artifact && <motion.div className="export-option" key={artifact.id} initial={reduceMotion ? false : { opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -3 }} transition={{ duration: reduceMotion ? 0 : 0.16, ease: [0.22, 1, 0.36, 1] }}><Icon name="file-check" /><div><strong>{artifact.filename}</strong><p>{t("export.built")}</p></div><a className="btn btn-primary btn-sm" href={artifact.downloadUrl}><Icon name="arrow-down" /> {t("export.download", { format: artifact.format.toUpperCase() })}</a></motion.div>}
        </AnimatePresence>
        <h2 className="section-title" style={{ margin: "20px 0 13px" }}>{t("export.handoff")}</h2>
        <div className="export-option"><Icon name="file-type" /><div><strong>{t("export.ttf")}</strong><p>{format === "ttf" ? t("export.revisionTtf") : t("export.onlyTtf")}</p></div><StatusTag tone={format === "ttf" ? "good" : "neutral"}>{format === "ttf" ? t("export.selected") : t("export.byRevision")}</StatusTag></div>
        <div className="export-option"><Icon name="file-type" /><div><strong>{t("export.otf")}</strong><p>{format === "otf" ? t("export.revisionTtf") : t("export.revisionOtf")}</p></div><StatusTag tone={format === "otf" ? "good" : "neutral"}>{format === "otf" ? t("export.selected") : t("export.byRevision")}</StatusTag></div>
        <form className="export-form" onSubmit={submit}>
          <label className="form-label">{t("export.variant")}<Select value={variantId || undefined} onValueChange={nextId => { setVariantId(nextId); const next = project.variants.find(item => item.id === nextId); setRevisionId(next?.currentRevisionId || ""); }}><SelectTrigger className="form-input" aria-label={t("export.variant")}><SelectValue placeholder={t("export.variant")} /></SelectTrigger><SelectContent>{project.variants.map(item => <SelectItem key={item.id} value={item.id}>VER {item.label}</SelectItem>)}</SelectContent></Select></label>
          <label className="form-label">{t("export.revision")}<Select value={revision?.id || undefined} onValueChange={setRevisionId}><SelectTrigger className="form-input" aria-label={t("export.revision")}><SelectValue placeholder={t("export.revision")} /></SelectTrigger><SelectContent>{(variant?.revisions || []).map(item => <SelectItem key={item.id} value={item.id}>{item.id.slice(0, 8)}{"\u00b7"}{item.kind}{"\u00b7"}{item.status}</SelectItem>)}</SelectContent></Select></label>
          <label className="form-label">{t("export.fileName")}<Input className="form-input" value={name} onChange={event => setName(event.target.value)} required /></label>
          <div className="export-eligibility"><StatusTag tone={eligible ? "good" : "warn"}>{eligible ? t("export.eligible") : t("export.ineligible")}</StatusTag><span>{eligible ? t("export.readySummary") : t("export.requirements")}</span></div>
          <div className="export-submit-row"><Button type="submit" kind="primary" disabled={busy || !eligible}>{busy ? t("export.creating") : t("export.build")}</Button></div>
        </form>
      </section>
      <aside className="card qa-card">
        <div className="eyebrow">{t("export.readiness")}</div><h2 className="section-title" style={{ margin: "9px 0 15px" }}>{t("export.before")}</h2>
        <div className="export-readiness-list">{readinessSteps.map((label, index) => <div className="export-readiness-item" key={label}>
          <div className={`workflow-stage${stepStates[index] ? " done" : index === stepStates.findIndex(value => !value) ? " now" : ""}`}><span className="stage-icon">{index + 1}</span>{label}</div>
          {index < readinessSteps.length - 1 && <span className="export-readiness-connector" aria-hidden="true" />}
        </div>)}</div>
        <div className="divider" />
        <div className="notice">{t("export.exportNote")}</div>
      </aside>
    </div>
  </section>;
}

