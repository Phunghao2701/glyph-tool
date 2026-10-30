import { useTranslation } from "react-i18next";
import { AnimatePresence, motion } from "motion/react";
import type { Project } from "../../../shared/lib/api";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";
import { AppLink } from "../../../app/providers/NavigationProvider";
import { APP_PATHS } from "../../../shared/constants/routes";
import { Icon } from "../../../shared/ui/Icon";
import { Button } from "../../../shared/ui/primitives/button";

type DashboardTaskQueueProps = { projects: Project[]; onOpenProject: (projectId: string) => void };

function pendingVariants(project: Project) {
  return project.variants.filter(variant => !!variant.currentRevision && !variant.currentRevision.approved);
}

export function DashboardTaskQueue({ projects, onOpenProject }: DashboardTaskQueueProps) {
  const { t } = useTranslation();
  const reduceMotion = usePrefersReducedMotion();
  const pending = projects.filter(project => pendingVariants(project).length > 0);
  return (
    <section>
      <div className="section-heading"><div><div className="eyebrow">{t("dashboard.today")}</div><h2 className="task-queue-title">{t("dashboard.needReview")} <span className="pending-count">({pending.length})</span></h2><p className="section-subtitle">{t("dashboard.continueReview")}</p></div><AppLink className="btn btn-text" to={APP_PATHS.projects}>{t("dashboard.viewAll")} <Icon name="arrow-right" /></AppLink></div>
      <div className="card task-list"><AnimatePresence initial={false} mode="popLayout">{pending.length ? pending.map((project, index) => {
        const coverage = project.analysis?.coverage?.percent;
        const count = pendingVariants(project).length;
        return <motion.div key={project.id} className="task-motion-row" layout={!reduceMotion} initial={reduceMotion ? false : { opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -4 }} transition={{ duration: reduceMotion ? 0 : 0.16, ease: [0.22, 1, 0.36, 1] }}>
        <Button variant="ghost" className="task-item h-auto" type="button" onClick={() => onOpenProject(project.id)} aria-label={t("dashboard.reviewProject", { name: project.name })}>
          <span className={`font-thumb ${["olive", "", "sand"][index % 3]}`} aria-hidden="true">Aa</span>
          <span className="task-info"><span className="task-title">{project.name}</span><span className="task-sub">{project.sourceFont?.filename || t("dashboard.uploadedFont")} · {t("dashboard.statuses.pending")}</span><span className="task-meta"><span className="pill pill-gold">{t("dashboard.statuses.pending")}</span><span>{t("dashboard.variantsCount", { count })}</span>{typeof coverage === "number" && <span>{Math.round(coverage)}% coverage</span>}</span></span>
          <span className="task-arrow"><Icon name="chevron-right" size={16} /></span>
        </Button></motion.div>;
      }) : <motion.div key="empty" className="empty" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0 }} transition={{ duration: reduceMotion ? 0 : 0.16 }}><div className="empty-icon"><Icon name="check-circle-2" /></div><h3>{t("dashboard.noPending")}</h3><p>{t("dashboard.noPendingDescription")}</p></motion.div>}</AnimatePresence></div>
    </section>
  );
}
