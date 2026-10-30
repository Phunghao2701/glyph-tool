import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { createRevision, createReview, getEditorDocument, getProject, getRevision, startVariants, type Project, type Revision } from "../api/glyph-studio.api";
import { AppLink, useNavigate } from "../../../app/providers/NavigationProvider";
import { useRegisterEditorFlush } from "../../../app/providers/EditorFlushProvider";
import { Button, ErrorBox, Icon, Loading, StatusTag } from "../../../shared/ui";
import { getError } from "../../../shared/utils/errors";
import GlyphEditorFrame from "../components/GlyphEditorFrame";
import { Textarea } from "../../../shared/ui/primitives/textarea";
import { AnimatePresence, motion } from "motion/react";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";

export function EditorPage({ projectId, variantId, query }: { projectId: string; variantId: string; query: URLSearchParams }) {
  const { t } = useTranslation();
  const reduceMotion = usePrefersReducedMotion();
  const navigate = useNavigate();
  const registerEditorFlush = useRegisterEditorFlush();
  const [project, setProject] = useState<Project | null>(null);
  const [revision, setRevision] = useState<Revision | null>(null);
  const [doc, setDoc] = useState<Awaited<ReturnType<typeof getEditorDocument>> | null>(null);
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saveState, setSaveState] = useState<"saved" | "saving" | "error">("saved");
  const flushRef = useRef<(() => Promise<void>) | null>(null);
  useEffect(() => {
    registerEditorFlush(() => flushRef.current ? flushRef.current() : Promise.resolve());
    return () => registerEditorFlush(null);
  }, [registerEditorFlush]);
  const load = useCallback(async () => {
    setError("");
    try {
      const p = await getProject(projectId);
      setProject(p);
      const v = p.variants.find(item => item.id === variantId);
      if (!v?.currentRevisionId) throw new Error(t("editor.noRevision"));
      const requested = query.get("revisionId");
      let current: Revision;
      if (requested) current = await getRevision(requested);
      else {
        current = await createRevision(v.id, v.currentRevisionId);
        const url = new URL(window.location.href);
        url.searchParams.set("revisionId", current.id);
        window.history.replaceState({}, "", url.toString());
      }
      setRevision(current);
      setDoc(await getEditorDocument(current.id));
    } catch (e) { setError(getError(e)); }
  }, [projectId, variantId, query, t]);
  useEffect(() => { void load(); }, [load]);
  const submitManualBuild = async () => {
    if (!revision) return;
    setBusy(true); setError("");
    try {
      await flushRef.current?.();
      const latestDoc = await getEditorDocument(revision.id);

      const edits = latestDoc.edits.filter(item => item.touched || item.note || item.strokes?.length).map(item => ({
        kind: item.kind, id: item.targetId || item.id || ""
      })).filter(item => item.id);
      await createReview(variantId, { revisionId: revision.id, message: feedback, glyphEditIds: edits });
      const job = await startVariants(projectId, {
        mode: "apply_manual_edits", baseRevisionId: revision.id, variantId
      });
      navigate("/projects/" + projectId + "?job=" + encodeURIComponent(job.id));
    } catch (e) { setError(getError(e)); }
    finally { setBusy(false); }
  };
  if (error && !project) return <section className="page"><ErrorBox error={error} retry={() => void load()} /></section>;
  if (!project || !revision || !doc) return error ? <section className="page"><ErrorBox error={error} retry={() => void load()} /></section> : <Loading label={t("common.openingEditor")} />;
  const variant = project.variants.find(item => item.id === variantId);
  return <section className="page editor-page">
    <div className="studio-head">
      <div>
        <AppLink to={`/projects/${projectId}`} className="back-link"><Icon name="arrow-left" /> {project.name} / {t("editor.back")}</AppLink>
        <div className="eyebrow">{t("editor.eyebrow")}</div>
        <h1 className="page-title">Glyph Studio <span className="studio-variant-label">· VER {variant?.label || ""}</span></h1>
        <p className="page-description">{t("editor.description")}</p>
      </div>
      <div className="page-actions"><AnimatePresence initial={false} mode="wait">{saveState !== "saved" && <motion.div key={saveState} initial={reduceMotion ? false : { opacity: 0, y: 3 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -3 }} transition={{ duration: reduceMotion ? 0 : 0.13 }}><StatusTag tone={saveState === "error" ? "bad" : "warn"}>{saveState === "saving" ? t("editor.saving") : t("editor.saveError")}</StatusTag></motion.div>}</AnimatePresence></div>
    </div>
    {error && <ErrorBox error={error} />}
    <div className="studio-shell studio-shell-full"><section className="card studio-center"><GlyphEditorFrame revisionId={revision.id} document={doc} onFlushReady={fn => { flushRef.current = fn; }} onSaveState={setSaveState} /></section></div>
    <div className="card qa-card form-stack editor-submit">
      <div className="eyebrow">{t("editor.revisionBuild")}</div>
      <label className="form-label">{t("editor.feedback")}<Textarea className="form-input" value={feedback} onChange={e => setFeedback(e.target.value)} rows={3} placeholder={t("editor.feedbackPlaceholder")} /></label>
      <div className="page-actions"><Button kind="primary" disabled={busy || saveState === "saving"} onClick={() => void submitManualBuild()}>{busy ? t("editor.building") : t("editor.saveBuild")}</Button><Button kind="quiet" onClick={() => navigate(`/projects/${projectId}/variants/${variantId}`)}>{t("editor.backPreview")}</Button></div>
      <p className="fine-print">{t("editor.footnote")}</p>
    </div>
  </section>;
}
