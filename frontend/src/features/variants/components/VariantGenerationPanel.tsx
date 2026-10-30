import { useState } from "react";
import { useTranslation } from "react-i18next";
import { startVariants, type Project } from "../api/variants.api";
import { VariantCard } from "./VariantCard";
import { AppLink } from "../../../app/providers/NavigationProvider";
import { APP_PATHS } from "../../../shared/constants/routes";
import { Button } from "../../../shared/ui";
import { getError } from "../../../shared/utils/errors";
import { AnimatePresence, motion } from "motion/react";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";

export function VariantGenerationPanel({
  project,
  aiReady,
  aiLoading,
  onJobStarted,
  onError,
}: {
  project: Project;
  aiReady: boolean;
  aiLoading: boolean;
  onJobStarted: (jobId: string) => void;
  onError: (message: string) => void;
}) {
  const { t } = useTranslation();
  const reduceMotion = usePrefersReducedMotion();
  const [busy, setBusy] = useState(false);
  const unsupported = project.analysis?.supportedForGeneration === false;
  const canGenerate = !!project.analysis && aiReady && !unsupported && !project.variants.length && !project.activeJobs.length;
  const createVariants = async () => {
    if (!aiReady) { onError(t("variants.requireProvider")); return; }
    setBusy(true);
    onError("");
    try {
      const job = await startVariants(project.id, { mode: "generate_initial" });
      onJobStarted(job.id);
    } catch (error) {
      onError(getError(error));
    } finally {
      setBusy(false);
    }
  };

  return <section className="section-block">
    <div className="section-heading"><div><div className="eyebrow">{t("variants.eyebrow")}</div><h2 className="section-title">{t("variants.title")}</h2><p className="section-subtitle">{t("variants.description")}</p></div>
      {project.analysis && <Button kind="primary" onClick={() => void createVariants()} disabled={busy || !canGenerate}>
        {busy ? t("variants.creating") : project.variants.length ? t("variants.created") : !aiReady ? t("variants.connect") : t("variants.create")}
      </Button>}
    </div>
    <AnimatePresence initial={false} mode="wait">
        {project.variants.length ? <motion.div key="variants" className="variant-grid" initial={reduceMotion ? false : { opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -4 }} transition={{ duration: reduceMotion ? 0 : 0.16, ease: [0.22, 1, 0.36, 1] }}>{project.variants.map((variant, index) => <VariantCard key={variant.id} variant={variant} projectId={project.id} index={index} />)}</motion.div> :
      <motion.div key="empty" className="card empty" initial={reduceMotion ? false : { opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -3 }} transition={{ duration: reduceMotion ? 0 : 0.14, ease: [0.22, 1, 0.36, 1] }}><div className="empty-icon">✳</div><h3>{t("variants.emptyTitle")}</h3><p>{unsupported ? t("variants.unsupported") : t("variants.connectPrompt")}</p>
        {project.analysis && !aiReady && <AppLink className="btn btn-light" to={APP_PATHS.aiProviders}>{t("variants.openSettings")}</AppLink>}
      </motion.div>}
    </AnimatePresence>
    {!aiReady && project.analysis && <p className="provider-gate">{aiLoading ? t("variants.checking") : t("variants.requireProvider")} <AppLink to={APP_PATHS.aiProviders}>{t("variants.openSettings")}</AppLink></p>}
    {project.activeJobs.length > 0 && <p className="tiny-muted">{t("variants.finishJob")}</p>}
  </section>;
}

