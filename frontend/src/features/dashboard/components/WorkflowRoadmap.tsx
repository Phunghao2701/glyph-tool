import { Icon } from "../../../shared/ui/Icon";
import { useTranslation } from "react-i18next";

type WorkflowRoadmapProps = {
  hasProjects: boolean;
  hasAnalysis: boolean;
  hasVariants: boolean;
  hasReviewedVariant: boolean;
  hasPassedValidation: boolean;
  aiReady: boolean;
  providerName: string;
};

export function WorkflowRoadmap({ hasProjects, hasAnalysis, hasVariants, hasReviewedVariant, hasPassedValidation, aiReady, providerName }: WorkflowRoadmapProps) {
  const { t } = useTranslation();
  const stages = t("dashboard.stages", { returnObjects: true }) as string[];
  const workflow = [
    { label: stages[0], done: hasAnalysis, now: !hasAnalysis },
    { label: stages[1], done: hasVariants, now: hasAnalysis && !hasVariants && aiReady },
    { label: stages[2], done: hasReviewedVariant, now: hasVariants && !hasReviewedVariant },
    { label: stages[3], done: hasPassedValidation, now: hasReviewedVariant && !hasPassedValidation },
  ];
  return (
    <div className="card system-panel">
      <div className="system-top"><span className="system-title">{t("dashboard.pipeline")}</span><span className="pill pill-green">{t("dashboard.localBadge")}</span></div>
      <div className="system-row"><div className="system-row-icon"><Icon name="shield-check" /></div><div><strong>{t("dashboard.unicode")}</strong><small>{hasAnalysis ? t("dashboard.readMetadata") : t("dashboard.readCmap")}</small></div></div>
      <div className="system-divider" />
      <div className="workflow-mini">{workflow.map((stage, index) => <div className="workflow-stage-wrap" key={stage.label}>{index > 0 && <span className="workline" />}<div className={"workflow-stage " + (stage.done ? "done" : stage.now ? "now" : "")}><span className="stage-icon">{stage.done ? <Icon name="check" size={13} /> : `0${index + 1}`}</span>{stage.label}</div></div>)}</div>
      <div className="system-caption">{hasProjects ? aiReady ? t("dashboard.aiReady", { provider: providerName }) : t("dashboard.needProvider") : t("dashboard.firstProject")} {t("dashboard.localNote")}</div>
    </div>
  );
}
