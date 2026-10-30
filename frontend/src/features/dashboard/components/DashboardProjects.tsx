import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Project } from "../../../shared/lib/api";
import { Button, Icon, Input, Progress, StatusTag } from "../../../shared/ui";
import { Button as ShadcnButton } from "../../../shared/ui/primitives/button";

type DashboardProjectsProps = {
  projects: Project[];
  loading: boolean;
  onCreateProject: () => void;
  onOpenProject: (projectId: string) => void;
  mode?: "recent" | "all";
  onViewAll?: () => void;
};

type Filter = "all" | "pending" | "reviewed";

function projectHasPendingReview(project: Project) {
  return project.variants.some(variant => !!variant.currentRevision && !variant.currentRevision.approved);
}
function projectIsReviewed(project: Project) {
  return project.variants.some(variant => !!variant.currentRevision?.approved);
}
function ProjectCard({ project, index, onOpen }: { project: Project; index: number; onOpen: () => void }) {
  const { t } = useTranslation();
  const percent = project.analysis?.coverage?.percent;
  const coverage = typeof percent === "number" && Number.isFinite(percent) ? Math.max(0, Math.min(100, Math.round(percent))) : null;
  const present = project.analysis?.coverage?.presentCount;
  const required = project.analysis?.coverage?.requiredCount;
  const status = projectIsReviewed(project)
    ? { label: t("dashboard.statuses.approved"), tone: "green" }
    : project.variants.length
      ? { label: t("dashboard.statuses.pending"), tone: "gold" }
      : { label: t("dashboard.statuses.create"), tone: "gray" };
  const tone = ["olive", "", "sand"][index % 3];
  return (
    <ShadcnButton type="button" variant="ghost" className="card project-card h-auto flex-col items-stretch justify-start" onClick={onOpen} aria-label={t("dashboard.openProject", { name: project.name })}>
      <div className={`project-card-sample ${tone}`}><span>Ag Ắ</span><span className="sample-ghost" aria-hidden="true">Aa</span></div>
      <div className="project-card-body">
        <div className="project-card-title-row"><h3 className="project-card-title">{project.name}</h3><Icon name="arrow-up-right" size={15} /></div>
        <p className="project-card-meta">{project.sourceFont?.filename || t("common.noSourceFont")} · {t("dashboard.uploadedFont")}</p>
        <div className="progress-labels"><span>{t("dashboard.coverageLabel")}</span><strong>{coverage === null ? t("dashboard.statuses.notAnalyzed") : `${present ?? "—"}/${required ?? "—"} · ${coverage}%`}</strong></div>
        <Progress className="progress-track" value={coverage ?? 0} aria-label={`${t("dashboard.coverageLabel")} ${project.name}`} aria-valuetext={coverage === null ? t("dashboard.statuses.notAnalyzed") : `${coverage}%`} />
        <div className="project-card-bottom"><StatusTag tone={status.tone === "green" ? "good" : status.tone === "gold" ? "warn" : "neutral"}>{status.label}</StatusTag><span className="tiny-muted">{t("dashboard.variantsCount", { count: project.variants.length })}</span></div>
      </div>
    </ShadcnButton>
  );
}

export function DashboardProjects({ projects, loading, onCreateProject, onOpenProject, onViewAll, mode = "recent" }: DashboardProjectsProps) {
  const { t, i18n } = useTranslation();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const visibleProjects = useMemo(() => {
    const locale = i18n.resolvedLanguage === "en" ? "en-US" : "vi-VN";
    const normalized = query.trim().toLocaleLowerCase(locale);
    let result = projects.filter(project => !normalized || `${project.name} ${project.sourceFont?.filename || ""}`.toLocaleLowerCase(locale).includes(normalized));
    if (filter === "pending") result = result.filter(projectHasPendingReview);
    if (filter === "reviewed") result = result.filter(projectIsReviewed);
    return mode === "recent" ? result.slice(0, 4) : result;
  }, [filter, i18n.resolvedLanguage, mode, projects, query]);
  const isAll = mode === "all";
  return (
    <section className={isAll ? "projects-page" : "section-block projects-recent"}>
      <div className="section-heading">
        <div><div className="eyebrow">{isAll ? t("dashboard.allEyebrow") : t("dashboard.library")}</div><h2 className="section-title">{isAll ? t("dashboard.projectList") : t("dashboard.recent")}</h2><p className="section-subtitle">{isAll ? t("dashboard.organize") : t("dashboard.recentCount", { count: projects.length })}</p></div>
        {isAll ? <Button kind="primary" type="button" onClick={onCreateProject}><Icon name="plus" />{t("dashboard.createShort")}</Button> : <Button kind="quiet" type="button" onClick={onViewAll}>{t("dashboard.manage")} <Icon name="arrow-right" /></Button>}
      </div>
      {isAll && <div className="card project-toolbar"><label className="field-search"><Icon name="search" /><Input id="project-search" type="search" className="form-input" placeholder={t("dashboard.search")} value={query} onChange={event => setQuery(event.target.value)} aria-label={t("dashboard.searchLabel")} /></label><div className="filter-chips">{(["all", "pending", "reviewed"] as const).map(value => <ShadcnButton key={value} type="button" variant={filter === value ? "secondary" : "ghost"} className={`chip ${filter === value ? "is-selected" : ""}`} aria-pressed={filter === value} onClick={() => setFilter(value)}>{t(`dashboard.filters.${value}`)}</ShadcnButton>)}</div></div>}
      {loading ? <div className="card empty" role="status"><span>{t("common.loadingProjects")}</span></div> : visibleProjects.length ? <div className="project-grid">{visibleProjects.map((project, index) => <ProjectCard key={project.id} project={project} index={index} onOpen={() => onOpenProject(project.id)} />)}</div> : <div className="card empty"><div className="empty-icon"><Icon name={isAll ? "search" : "folder-open"} /></div><h3>{isAll && (query || filter !== "all") ? t("dashboard.noSearchResults") : t("dashboard.noProjects")}</h3><p>{isAll && (query || filter !== "all") ? t("dashboard.noSearchDescription") : t("dashboard.noProjectsDescription")}</p><Button kind="primary" type="button" onClick={onCreateProject}><Icon name="plus" />{t("navigation.createProject")}</Button></div>}
    </section>
  );
}
