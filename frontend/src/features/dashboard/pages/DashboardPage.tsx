import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { listProjects, type AiProviderId, type AiProviders, type Project } from "../api/dashboard.api";
import { DashboardHero } from "../components/DashboardHero";
import { DashboardMetrics } from "../components/DashboardMetrics";
import { DashboardProjects } from "../components/DashboardProjects";
import { DashboardTaskQueue } from "../components/DashboardTaskQueue";
import { WorkflowRoadmap } from "../components/WorkflowRoadmap";
import type { DashboardPageProps } from "../model/dashboard.types";
import { errorText, projectNeedsReview } from "../utils/dashboard.helpers";
import { ErrorBox } from "../../../shared/ui";

export function DashboardPage({ navigate, view, renderProviderSection }: DashboardPageProps) {
  const { t } = useTranslation();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [providerSnapshot, setProviderSnapshot] = useState<AiProviders | null>(null);
  const reload = useCallback(() => {
    setLoading(true); setError("");
    listProjects().then(setProjects).catch(e => setError(errorText(e))).finally(() => setLoading(false));
  }, []);
  useEffect(() => { reload(); }, [reload]);

  const selectedProvider = providerSnapshot?.providers.find(provider => provider.id === providerSnapshot.selectedProviderId);
  const connectedProvider = providerSnapshot?.providers.find(provider => provider.status === "connected");
  const aiReady = selectedProvider?.status === "connected" && !!selectedProvider.selectedModelId;
  const providerName = (id?: AiProviderId | null) => id === "chatgpt" ? "ChatGPT" : id === "ollama_cloud" ? "Ollama Cloud" : "AI provider";
  const selectedProviderName = aiReady ? providerName(selectedProvider?.id) : "";
  const pendingProjects = useMemo(() => projects.filter(projectNeedsReview), [projects]);
  const totalVariants = projects.reduce((sum, project) => sum + project.variants.length, 0);
  const reviewedProjects = projects.filter(project => project.variants.some(variant => !!variant.currentRevision?.approved)).length;
  const analyzedProjects = projects.filter(project => typeof project.analysis?.coverage?.percent === "number");
  const averageCoverage = analyzedProjects.length ? Math.round(analyzedProjects.reduce((sum, project) => sum + (project.analysis?.coverage?.percent || 0), 0) / analyzedProjects.length) : null;
  const hasVariants = projects.some(project => project.variants.length > 0);
  const hasReviewedVariant = projects.some(project => project.variants.some(variant => !!variant.currentRevision?.approved));
  const hasPassedValidation = projects.some(project => project.variants.some(variant => variant.currentRevision?.validation?.status === "passed"));
  const aiLabel = !providerSnapshot ? t("dashboard.checkingProvider") : aiReady ? t("dashboard.providerConnected", { provider: selectedProviderName }) : connectedProvider?.selectedModelId ? t("dashboard.providerConnectedNoModel", { provider: providerName(connectedProvider.id) }) : connectedProvider ? t("dashboard.providerNeedsModel", { provider: providerName(connectedProvider.id) }) : t("dashboard.providerRequired");
  const openProjectList = () => navigate("/projects?view=projects");
  const openProject = (projectId: string) => navigate("/projects/" + projectId);
  const isProjects = view === "projects";
  const isSettings = view === "settings";

  return <div className="dashboard-view">
    {isSettings ? <div className="page-head"><div><div className="eyebrow">{t("dashboard.settingsEyebrow")}</div><h1 className="page-title">{t("dashboard.settings")}</h1><p className="page-description">{t("dashboard.settingsDescription")}</p></div></div> : isProjects ? null : <DashboardHero onCreateProject={() => navigate("/projects/new")} onViewProjects={openProjectList} />}
    {error && <ErrorBox error={error} retry={reload} />}
    {!isSettings && !isProjects && <DashboardMetrics pendingProjectCount={pendingProjects.length} totalVariantCount={totalVariants} projectCount={projects.length} reviewedProjectCount={reviewedProjects} averageCoverage={averageCoverage} loading={loading} />}
    {!isSettings && !isProjects && <div className="dashboard-lower section-block">
      <DashboardTaskQueue projects={projects} onOpenProject={openProject} />
      <section><div className="section-heading"><div><div className="eyebrow">{t("dashboard.state")}</div><h2 className="section-title">{t("dashboard.workflow")}</h2><p className="section-subtitle">{t("dashboard.workflowDescription")}</p></div></div>
        <WorkflowRoadmap hasProjects={projects.length > 0} hasAnalysis={analyzedProjects.length > 0} hasVariants={hasVariants} hasReviewedVariant={hasReviewedVariant} hasPassedValidation={hasPassedValidation} aiReady={!!aiReady} providerName={selectedProviderName} />
      </section>
    </div>}
    {!isSettings && <DashboardProjects projects={projects} loading={loading} onCreateProject={() => navigate("/projects/new")} onOpenProject={openProject} onViewAll={openProjectList} mode={isProjects ? "all" : "recent"} />}
    <div className="provider-feature-slot" style={{ display: isSettings ? "block" : "none" }}>{renderProviderSection(setProviderSnapshot)}</div>
    <span className="visually-hidden" role="status">{aiLabel}</span>
    {isSettings && <p className="settings-provider-summary"><span className="env-dot" />{aiLabel}</p>}
  </div>;
}
