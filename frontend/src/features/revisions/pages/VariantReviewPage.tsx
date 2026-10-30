import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { createReview, getProject, startVariantRefinement, type Project } from "../api/revisions.api";
import { AppLink, useNavigate } from "../../../app/providers/NavigationProvider";
import { Button, ErrorBox, JobWatch, Loading, StatusTag } from "../../../shared/ui";
import { getError } from "../../../shared/utils/errors";
import { useAiReadiness } from "../../ai-providers";
import { Textarea } from "../../../shared/ui/primitives/textarea";
import { AnimatePresence, motion } from "motion/react";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";

export function VariantReviewPage({ projectId, variantId }: { projectId: string; variantId: string }) {
  const { t } = useTranslation();
  const reduceMotion = usePrefersReducedMotion();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [message, setMessage] = useState("");
  const [sample, setSample] = useState("ẦẤẨẪẬ ẮẮ ỜỚỢ ơ ư đ Đ\\nNgười Việt dùng font đẹp, đúng dấu.");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [refineJobId, setRefineJobId] = useState("");
  const [refining, setRefining] = useState(false);
  const [error, setError] = useState("");
  const ai = useAiReadiness();
  const load = useCallback(() => getProject(projectId).then(setProject).catch(e => setError(getError(e))), [projectId]);
  useEffect(() => { void load(); }, [load]);
  if (!project) return error ? <section className="page"><ErrorBox error={error} retry={load} /></section> : <Loading />;
  const variant = project.variants.find(v => v.id === variantId);
  if (!variant) return <section className="page"><ErrorBox error={t("review.missingVariant")} /></section>;
  const revision = variant.currentRevision;
  const family = "vfk-preview-" + variant.id.replace(/[^a-zA-Z0-9]/g, "");
  const saveFeedback = async () => {
    if (!revision) return;
    setBusy(true); setError(""); setSaved(false);
    try {
      await createReview(variant.id, { revisionId: revision.id, message, glyphEditIds: [] });
      setSaved(true);
    } catch (e) { setError(getError(e)); }
    finally { setBusy(false); }
  };
  const runRefinement = async () => {
    if (!ai.ready) { setError(t("review.refineError")); return; }
    if (!revision || !message.trim()) return;
    setBusy(true); setError(""); setRefining(true);
    try {
      const job = await startVariantRefinement(variant.id, revision.id, message.trim());
      setRefineJobId(job.id);
    } catch (e) { setRefining(false); setError(getError(e)); }
    finally { setBusy(false); }
  };
  return <section className="page">
    <div className="crumb"><AppLink to={"/projects/" + projectId}>{project.name}</AppLink><span>/</span><b>VER {variant.label}</b></div>
    <div className="page-heading"><div><p className="eyebrow">{t("review.eyebrow")}</p><h1>VER {variant.label}</h1><p className="lede">{t("review.description")}</p></div>{revision && <StatusTag tone={revision.approved ? "good" : "neutral"}>{t(`common.status.${revision.status}`, { defaultValue: revision.status })}</StatusTag>}</div>
    {error && <ErrorBox error={error} />}
    {revision?.aiDesign && <section className="ai-design-summary" aria-label={t("review.aiProfile")}>
      <div><p className="eyebrow">{t("review.aiProfile")}</p><h2>{revision.aiDesign.sourceStyle || t("review.sourceStyle")}</h2></div>
      {revision.aiDesign.rationale && <p>{revision.aiDesign.rationale}</p>}
      {(revision.aiDesign.providerId || revision.aiDesign.modelId) && <small>{revision.aiDesign.providerId || "AI"}{revision.aiDesign.modelId ? " · " + revision.aiDesign.modelId : ""}</small>}
    </section>
    }
    {refineJobId && <JobWatch jobId={refineJobId} onDone={() => { setRefining(false); void load(); }} />}
    {revision?.previewUrl && <style>{'@font-face{font-family:"' + family + '";src:url("' + revision.previewUrl + '");font-display:swap}'}</style>}
    <div className="review-layout">
      <div className="panel preview-panel">
        <div className="panel-heading"><div><p className="eyebrow">{t("review.preview")}</p><h2>{t("review.compare")}</h2></div><Button kind="quiet" onClick={() => navigate("/projects/" + projectId + "/variants/" + variant.id + "/editor")}>{t("review.openEditor")}</Button></div>
        <Textarea className="sample-input" value={sample} onChange={e => setSample(e.target.value)} aria-label={t("review.sample")} />
        <div className="font-preview" style={{ fontFamily: revision?.previewUrl ? '"' + family + '", sans-serif' : "inherit" }}>{sample}</div>
      </div>
      <div className="panel form-stack">
        <p className="eyebrow">{t("review.feedback")}</p><h2>{t("review.feedbackTitle")}</h2>
        <label>Feedback<Textarea value={message} onChange={e => setMessage(e.target.value)} rows={5} placeholder={t("review.feedbackPlaceholder")} /></label>
        <Button kind="primary" onClick={() => void saveFeedback()} disabled={busy || !revision}>{busy ? t("review.saving") : t("review.saveFeedback")}</Button>
        <AnimatePresence initial={false} mode="wait">{saved && <motion.div key="saved" initial={reduceMotion ? false : { opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -3 }} transition={{ duration: reduceMotion ? 0 : 0.15 }}><StatusTag tone="good">{t("review.feedbackSaved")}</StatusTag></motion.div>}</AnimatePresence>
        {!ai.ready && <p className="provider-gate">{ai.loading ? t("review.checkingProvider") : t("review.refineNeedsProvider")} <AppLink to="/projects#providers">{t("review.openSettings")}</AppLink></p>}
        <Button kind="primary" onClick={() => void runRefinement()} disabled={busy || refining || !ai.ready || !revision || !message.trim()}>{refining ? t("review.refining") : !ai.ready ? t("review.needAi") : t("review.refine")}</Button>
        <Button onClick={() => navigate("/projects/" + projectId + "/variants/" + variant.id + "/editor")}>{t("review.openCanvas")}</Button>
        <Button kind="quiet" onClick={() => navigate("/projects/" + projectId + "/validation?variantId=" + variant.id)}>{t("review.validation")}</Button>
        <p className="fine-print">{t("review.savedProject")}</p>
      </div>
    </div>
  </section>;
}
