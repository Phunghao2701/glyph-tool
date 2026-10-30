import { useRef } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import { Button, Icon, MagicCard } from "../../../shared/ui";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";
import { useTranslation } from "react-i18next";

gsap.registerPlugin(useGSAP);

type DashboardHeroProps = {
  onCreateProject: () => void;
  onViewProjects: () => void;
};

export function DashboardHero({ onCreateProject, onViewProjects }: DashboardHeroProps) {
  const { t } = useTranslation();
  const rootRef = useRef<HTMLElement>(null);
  const reduceMotion = usePrefersReducedMotion();

  useGSAP(() => {
    if (reduceMotion) return;
    const timeline = gsap.timeline({ defaults: { ease: "power3.out" } });
    timeline
      .fromTo("[data-gsap='hero-copy']", { autoAlpha: 0, y: 34 }, { autoAlpha: 1, y: 0, duration: 0.72, stagger: 0.12 })
      .fromTo("[data-gsap='hero-specimen']", { autoAlpha: 0, y: 44, rotate: -12, scale: 0.78 }, { autoAlpha: 1, y: 0, rotate: 0, scale: 1, duration: 0.85, stagger: 0.14, ease: "back.out(1.45)" }, 0.28);
  }, { scope: rootRef, dependencies: [reduceMotion], revertOnUpdate: true });

  return (
    <MagicCard className="dashboard-hero" gradientColor="rgba(81, 131, 94, .12)" gradientFrom="#7fa98d" gradientTo="#d2bd88" gradientSize={300}>
      <section ref={rootRef} className="dashboard-hero-layout" aria-labelledby="dashboard-hero-title">
        <div className="dashboard-hero-copy">
          <p className="dashboard-hero-eyebrow" data-gsap="hero-copy">VietFont Studio <span>/</span> {t("dashboard.local")}</p>
          <h1 id="dashboard-hero-title" data-gsap="hero-copy"><span>{t("dashboard.title")}</span><em>{t("dashboard.titleAccent")}</em></h1>
          <p className="dashboard-hero-description" data-gsap="hero-copy">{t("dashboard.description")}</p>
          <div className="dashboard-hero-actions" data-gsap="hero-copy">
            <Button kind="primary" type="button" onClick={onCreateProject}><Icon name="plus" />{t("dashboard.create")}</Button>
            <Button kind="secondary" type="button" onClick={onViewProjects}>{t("dashboard.viewProjects")}<Icon name="arrow-right" /></Button>
          </div>
        </div>
        <div className="dashboard-hero-specimens" aria-hidden="true">
          <div className="dashboard-hero-orbit" data-gsap="hero-specimen" />
          <div className="dashboard-hero-tile dashboard-hero-tile-accent" data-gsap="hero-specimen"><span>Ắ</span></div>
          <div className="dashboard-hero-tile dashboard-hero-tile-base" data-gsap="hero-specimen"><span>Ữ</span></div>
        </div>
      </section>
    </MagicCard>
  );
}
