import { useState } from "react";
import { useTranslation } from "react-i18next";
import { startVariants, type Project } from "../api/variants.api";
import { VariantCard } from "./VariantCard";
import { AppLink } from "../../../app/providers/NavigationProvider";
import { APP_PATHS } from "../../../shared/constants/routes";
import { Button } from "../../../shared/ui";
import { getError } from "../../../shared/utils/errors";

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
    {project.variants.length ? <div className="variant-grid">{project.variants.map((variant, index) => <VariantCard key={variant.id} variant={variant} projectId={project.id} index={index} />)}</div> :
      <div className="card empty"><div className="empty-icon">✳</div><h3>{t("variants.emptyTitle")}</h3><p>{unsupported ? t("variants.unsupported") : t("variants.connectPrompt")}</p>
        {project.analysis && !aiReady && <AppLink className="btn btn-light" to={APP_PATHS.aiProviders}>{t("variants.openSettings")}</AppLink>}
      </div>}
    {!aiReady && project.analysis && <p className="provider-gate">{aiLoading ? t("variants.checking") : t("variants.requireProvider")} <AppLink to={APP_PATHS.aiProviders}>{t("variants.openSettings")}</AppLink></p>}
    {project.activeJobs.length > 0 && <p className="tiny-muted">{t("variants.finishJob")}</p>}
  </section>;
}

