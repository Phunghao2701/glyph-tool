import { Icon } from "../../../shared/ui/Icon";
import { useTranslation } from "react-i18next";
import { motion } from "motion/react";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";

type WorkflowRoadmapProps = {
  hasAnalysis: boolean;
  hasVariants: boolean;
  hasReviewedVariant: boolean;
  hasPassedValidation: boolean;
  aiReady: boolean;
};

export function WorkflowRoadmap({ hasAnalysis, hasVariants, hasReviewedVariant, hasPassedValidation, aiReady }: WorkflowRoadmapProps) {
  const { t } = useTranslation();
  const reduceMotion = usePrefersReducedMotion();
  const stages = t("dashboard.stages", { returnObjects: true }) as string[];
  const workflow = [
    { label: stages[0], done: hasAnalysis, now: !hasAnalysis },
    { label: stages[1], done: hasVariants, now: hasAnalysis && !hasVariants && aiReady },
    { label: stages[2], done: hasReviewedVariant, now: hasVariants && !hasReviewedVariant },
    { label: stages[3], done: hasPassedValidation, now: hasReviewedVariant && !hasPassedValidation },
  ];
  return (
    <div className="card system-panel">
      <div className="system-top"><span className="system-title">{t("dashboard.pipeline")}</span></div>
      <div className="system-row"><div className="system-row-icon"><Icon name="shield-check" /></div><div><strong>{t("dashboard.unicode")}</strong><small>{hasAnalysis ? t("dashboard.readMetadata") : t("dashboard.readCmap")}</small></div></div>
      <div className="system-divider" />
      <div className="workflow-mini">{workflow.map((stage, index) => <motion.div className="workflow-stage-wrap" key={stage.label} initial={false} animate={{ opacity: stage.done || stage.now ? 1 : 0.72, y: reduceMotion ? 0 : stage.now ? -2 : 0 }} transition={{ duration: reduceMotion ? 0 : 0.18, ease: [0.22, 1, 0.36, 1] }}>
        <div className={"workflow-stage " + (stage.done ? "done" : stage.now ? "now" : "")}><span className="stage-icon">{`0${index + 1}`}</span>{stage.label}</div>
        {index < workflow.length - 1 && <span className="workline" aria-hidden="true" />}
      </motion.div>)}</div>
    </div>
  );
}
