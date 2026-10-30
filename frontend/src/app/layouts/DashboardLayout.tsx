import { useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { AppLink } from "../providers/NavigationProvider";
import { Icon, LanguageSwitcher } from "../../shared/ui";
import { APP_PATHS } from "../../shared/constants/routes";
import { Button } from "../../shared/ui/primitives/button";

function getPageLabel(pathname: string, search: string, hash: string) {
  const [root, projectId, section] = pathname.split("/").filter(Boolean);
  const view = new URLSearchParams(search).get("view");
  if (root !== "projects" || !projectId) return "navigation.overview";
  if (projectId === "new") return "navigation.newProject";
  if (section === "validation") return "navigation.qa";
  if (section === "export") return "navigation.export";
  if (section === "variants") return "navigation.glyphStudio";
  if (hash === "providers" || view === "settings") return "navigation.aiSettings";
  if (hash === "projects" || view === "projects") return "navigation.projects";
  return "project.details";
}

export function DashboardLayout({ children, pathname, search = "", hash = "" }: {
  children: ReactNode;
  pathname: string;
  search?: string;
  hash?: string;
}) {
  const { t } = useTranslation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [root, projectId, section, variantId] = pathname.split("/").filter(Boolean);
  const hasProject = root === "projects" && projectId && projectId !== "new";
  const projectPath = hasProject ? `/projects/${projectId}` : "";
  const studioPath = projectPath && section === "variants" && variantId
    ? `${projectPath}/variants/${variantId}/editor`
    : "";
  const view = new URLSearchParams(search).get("view");
  const isOverview = (pathname === "/projects" || pathname === "/") && hash !== "projects" && hash !== "providers" && !["projects", "settings"].includes(view || "");
  const isProjects = hash === "projects" || view === "projects" || (!!hasProject && !["validation", "export", "variants"].includes(section || ""));
  const isStudio = section === "variants";
  const isValidation = section === "validation";
  const isExport = section === "export";
  const closeMobileMenu = () => setMobileMenuOpen(false);

  useEffect(() => {
    if (!mobileMenuOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === "Escape") closeMobileMenu(); };
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [mobileMenuOpen]);

  return <div className={`app-shell${mobileMenuOpen ? " menu-open" : ""}`}>
    <a className="skip-link" href="#main-content">{t("navigation.skip")}</a>
    <aside id="primary-sidebar" className="sidebar" aria-label={t("navigation.primary")}>
      <AppLink to={APP_PATHS.dashboard} className="brand" afterNavigate={closeMobileMenu} ariaLabel="VietFont Studio" title="VietFont Studio">
        <img className="brand-mark" src="/images/brand/vietfont-studio-mark.svg" alt="" />
        <span className="brand-copy"><strong>VietFont <span>Studio</span></strong><small>{t("navigation.brandTagline")}</small></span>
      </AppLink>
      <div className="workspace-picker"><span className="workspace-avatar">VF</span><span className="workspace-text"><strong>{t("navigation.workspaceName")}</strong><small>{t("navigation.personal")}</small></span><span className="picker-caret" aria-hidden="true">⌄</span></div>
      <nav aria-label={t("navigation.workspace")}>
        <div className="nav-group">
          <div className="nav-heading">{t("navigation.space")}</div>
          <AppLink to={APP_PATHS.dashboard} afterNavigate={closeMobileMenu} ariaCurrent={isOverview ? "page" : undefined} ariaLabel={t("navigation.overview")} title={t("navigation.overview")} className={`nav-link${isOverview ? " is-active" : ""}`}><Icon name="layout-dashboard" /><span>{t("navigation.overview")}</span></AppLink>
          <AppLink to={APP_PATHS.projects} afterNavigate={closeMobileMenu} ariaCurrent={isProjects ? "page" : undefined} ariaLabel={t("navigation.projects")} title={t("navigation.projects")} className={`nav-link${isProjects ? " is-active" : ""}`}><Icon name="folder-open" /><span>{t("navigation.projects")}</span></AppLink>
        </div>
        <div className="nav-group">
          <div className="nav-heading">{t("navigation.workflow")}</div>
          {studioPath ? <AppLink to={studioPath} afterNavigate={closeMobileMenu} ariaCurrent={isStudio ? "page" : undefined} ariaLabel={t("navigation.glyphStudio")} title={t("navigation.glyphStudio")} className={`nav-link${isStudio ? " is-active" : ""}`}><Icon name="pen-tool" /><span>{t("navigation.glyphStudio")}</span></AppLink> : <span className="nav-link" aria-disabled="true" title={t("navigation.glyphStudio")}><Icon name="pen-tool" /><span>{t("navigation.glyphStudio")}</span></span>}
          {projectPath ? <AppLink to={`${projectPath}/validation`} afterNavigate={closeMobileMenu} ariaCurrent={isValidation ? "page" : undefined} ariaLabel={t("navigation.qa")} title={t("navigation.qa")} className={`nav-link${isValidation ? " is-active" : ""}`}><Icon name="shield-check" /><span>{t("navigation.qa")}</span></AppLink> : <span className="nav-link" aria-disabled="true" title={t("navigation.qa")}><Icon name="shield-check" /><span>{t("navigation.qa")}</span></span>}
          {projectPath ? <AppLink to={`${projectPath}/export`} afterNavigate={closeMobileMenu} ariaCurrent={isExport ? "page" : undefined} ariaLabel={t("navigation.export")} title={t("navigation.export")} className={`nav-link${isExport ? " is-active" : ""}`}><Icon name="package" /><span>{t("navigation.export")}</span></AppLink> : <span className="nav-link" aria-disabled="true" title={t("navigation.export")}><Icon name="package" /><span>{t("navigation.export")}</span></span>}
        </div>
        <div className="nav-group">
          <div className="nav-heading">{t("navigation.system")}</div>
          <AppLink to={APP_PATHS.aiProviders} afterNavigate={closeMobileMenu} ariaCurrent={hash === "providers" || view === "settings" ? "page" : undefined} ariaLabel={t("navigation.aiSettings")} title={t("navigation.aiSettings")} className={`nav-link${hash === "providers" || view === "settings" ? " is-active" : ""}`}><Icon name="settings-2" /><span>{t("navigation.aiSettings")}</span></AppLink>
        </div>
      </nav>
      <div className="sidebar-spacer" />
      <AppLink to={APP_PATHS.newProject} afterNavigate={closeMobileMenu} ariaLabel={t("navigation.createProject")} title={t("navigation.createProject")} className="btn btn-primary sidebar-create"><Icon name="plus" /><span>{t("navigation.createProject")}</span></AppLink>
      <div className="sidebar-local"><span className="local-pulse" /><div><strong>{t("navigation.localEngine")}</strong><small>{t("navigation.localFiles")}</small></div></div>
      <small className="sidebar-version">VIETFONT STUDIO</small>
    </aside>
    <Button variant="ghost" className="mobile-shade p-0" type="button" aria-label={t("navigation.closeMenu")} onClick={closeMobileMenu} />
    <div className="main-column">
      <header className="topbar">
        <div className="topbar-left">
          <Button variant="ghost" className="menu-button icon-button p-0" type="button" aria-label={t("navigation.openMenu")} aria-controls="primary-sidebar" aria-expanded={mobileMenuOpen} onClick={() => setMobileMenuOpen(open => !open)}><Icon name="menu" /></Button>
          <div className="breadcrumb"><span>{t("navigation.workspaceCrumb")}</span><Icon name="chevron-right" /><strong>{t(getPageLabel(pathname, search, hash))}</strong></div>
        </div>
        <div className="topbar-right"><LanguageSwitcher /><span className="environment-tag"><i className="env-dot" />{t("navigation.local")}</span><span className="avatar-button" aria-label="Viet Font Studio">VF</span></div>
      </header>
      <main id="main-content" className="content">{children}</main>
    </div>
  </div>;
}

