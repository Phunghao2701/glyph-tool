import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "motion/react";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";
import { useSourceFontPreview } from "../../../shared/hooks/useSourceFontPreview";
import type { Project } from "../../../shared/lib/api";
import { getRevisionCoverage } from "../../../shared/utils/revisionCoverage";
import { Button, CrudActions, Icon, Input, Progress, StatusTag } from "../../../shared/ui";
import { Button as ShadcnButton } from "../../../shared/ui/primitives/button";

type DashboardProjectsProps = {
  projects: Project[];
  loading: boolean;
  onCreateProject: () => void;
  onOpenProject: (projectId: string) => void;
  mode?: "recent" | "all";
  onViewAll?: () => void;
  onRenameProject: (projectId: string, name: string) => Promise<void>;
  onDeleteProject: (projectId: string) => Promise<void>;
};

type Filter = "all" | "pending" | "reviewed";

function projectHasPendingReview(project: Project) {
  return project.variants.some(variant => !!variant.currentRevision && !variant.currentRevision.approved);
}
function projectIsReviewed(project: Project) {
  return project.variants.some(variant => !!variant.currentRevision?.approved);
}
function revisionTimestamp(value?: string) {
  const parsed = Date.parse(value || "");
  return Number.isFinite(parsed) ? parsed : 0;
}
function ProjectCard({ project, index, onOpen, onRename, onDelete }: { project: Project; index: number; onOpen: () => void; onRename: (name: string) => Promise<void>; onDelete: () => Promise<void> }) {
  const { t } = useTranslation();
  const previewRevision = project.variants
    .filter(variant => variant.currentRevision?.approved && variant.currentRevision.previewUrl)
    .sort((a, b) => Date.parse(b.currentRevision?.updatedAt || "") - Date.parse(a.currentRevision?.updatedAt || ""))[0]
    ?.currentRevision;
  const { previewRef, previewFontFamily } = useSourceFontPreview<HTMLDivElement>(project.id, project.sourceFont?.format, previewRevision ? {
    id: previewRevision.id,
    url: previewRevision.previewUrl,
    format: previewRevision.fontFormat,
  } : undefined);
  const latestRevisionEntry = project.variants
    .filter(variant => !!variant.currentRevision)
    .map(variant => ({ variant, revision: variant.currentRevision! }))
    .sort((a, b) => revisionTimestamp(b.revision.updatedAt || b.revision.createdAt) - revisionTimestamp(a.revision.updatedAt || a.revision.createdAt))[0];
  const revisionCoverage = getRevisionCoverage(latestRevisionEntry?.revision.validation);
  const percent = project.analysis?.coverage?.percent;
  const coverage = typeof percent === "number" && Number.isFinite(percent) ? Math.max(0, Math.min(100, Math.round(percent))) : null;
  const present = project.analysis?.coverage?.presentCount;
  const required = project.analysis?.coverage?.requiredCount;
  const revisionCoverageLabel = latestRevisionEntry
    ? t("dashboard.revisionCoverageForVariant", { label: latestRevisionEntry.variant.label })
    : t("dashboard.revisionCoverage");
  const status = projectIsReviewed(project)
    ? { label: t("dashboard.statuses.approved"), tone: "green" }
    : project.variants.length
      ? { label: t("dashboard.statuses.pending"), tone: "gold" }
      : { label: t("dashboard.statuses.create"), tone: "gray" };
  const tone = ["olive", "", "sand"][index % 3];
  return (
    <article className="card project-card">
      <ShadcnButton type="button" variant="ghost" className="project-card-open h-auto flex-col items-stretch justify-start" onClick={onOpen} aria-label={t("dashboard.openProject", { name: project.name })}>
      <div ref={previewRef} className={`project-card-sample ${tone}`} style={{ fontFamily: previewFontFamily }}><span>Ag Ắ</span><span className="sample-ghost" aria-hidden="true">Aa</span></div>
      <div className="project-card-body">
        <div className="project-card-title-row"><h3 className="project-card-title">{project.name}</h3><Icon name="arrow-up-right" size={15} /></div>
        <p className="project-card-meta">{project.sourceFont?.filename || t("common.noSourceFont")} · {t("dashboard.uploadedFont")}</p>
        <div className="project-card-coverage">
          <div className="project-card-coverage-item">
            <div className="project-card-coverage-labels"><span>{t("dashboard.sourceCoverage")}</span><strong>{coverage === null ? t("dashboard.statuses.notAnalyzed") : `${present ?? "—"}/${required ?? "—"} · ${coverage}%`}</strong></div>
            {coverage !== null && <Progress className="progress-track" value={coverage} aria-label={`${t("dashboard.sourceCoverage")} ${project.name}`} aria-valuetext={`${coverage}%`} />}
          </div>
          <div className="project-card-coverage-item">
            <div className="project-card-coverage-labels"><span>{revisionCoverageLabel}</span><strong>{revisionCoverage ? `${revisionCoverage.presentCount}/${revisionCoverage.requiredCount} · ${revisionCoverage.percent}%` : latestRevisionEntry ? t("dashboard.statuses.notValidated") : t("dashboard.statuses.noRevision")}</strong></div>
            {revisionCoverage && <Progress className="progress-track" value={revisionCoverage.percent} aria-label={`${revisionCoverageLabel} ${project.name}`} aria-valuetext={`${revisionCoverage.percent}%`} />}
          </div>
        </div>
        {status.tone !== "green" && <div className="project-card-bottom"><StatusTag tone={status.tone === "gold" ? "warn" : "neutral"}>{status.label}</StatusTag></div>}
      </div>
      </ShadcnButton>
      <CrudActions className="project-card-actions" name={project.name} onRename={onRename} onDelete={onDelete} disabled={project.activeJobs.length > 0} iconOnly />
    </article>
  );
}

export function DashboardProjects({ projects, loading, onCreateProject, onOpenProject, onViewAll, onRenameProject, onDeleteProject, mode = "recent" }: DashboardProjectsProps) {
  const { t, i18n } = useTranslation();
  const reduceMotion = usePrefersReducedMotion();
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
      {loading ? <div className="card empty" role="status"><span>{t("common.loadingProjects")}</span></div> : visibleProjects.length ? <div className="project-grid"><AnimatePresence initial={false} mode="popLayout">{visibleProjects.map((project, index) => <motion.div key={project.id} className="project-motion-item" layout={!reduceMotion} initial={reduceMotion ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -4, scale: 0.985 }} transition={{ duration: reduceMotion ? 0 : 0.18, delay: reduceMotion ? 0 : Math.min(index, 4) * 0.025, ease: [0.22, 1, 0.36, 1] }}><ProjectCard project={project} index={index} onOpen={() => onOpenProject(project.id)} onRename={name => onRenameProject(project.id, name)} onDelete={() => onDeleteProject(project.id)} /></motion.div>)}</AnimatePresence></div> : <div className="card empty"><div className="empty-icon"><Icon name={isAll ? "search" : "folder-open"} /></div><h3>{isAll && (query || filter !== "all") ? t("dashboard.noSearchResults") : t("dashboard.noProjects")}</h3><p>{isAll && (query || filter !== "all") ? t("dashboard.noSearchDescription") : t("dashboard.noProjectsDescription")}</p><Button kind="primary" type="button" onClick={onCreateProject}><Icon name="plus" />{t("navigation.createProject")}</Button></div>}
    </section>
  );
}
