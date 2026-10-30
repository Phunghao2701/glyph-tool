import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { DashboardLayout } from "./layouts/DashboardLayout";
import { StudioLayout } from "./layouts/StudioLayout";
import { EditorFlushProvider } from "./providers/EditorFlushProvider";
import { NavigationProvider, type Navigate } from "./providers/NavigationProvider";
import { resolveRoute, type AppRoute } from "./router";
import { DashboardPage } from "../features/dashboard";
import { NewProjectPage } from "../features/font-import";
import { ProjectPage } from "../features/projects";
import { VariantReviewPage } from "../features/revisions";
import { EditorPage } from "../features/glyph-studio";
import { ValidationPage } from "../features/validation";
import { ExportPage } from "../features/font-export";
import { ProviderSettingsPage } from "../features/ai-providers";
import { PublishedFontsPage } from "../features/published-fonts";
import { getError } from "../shared/utils/errors";

function currentPath() {
  return window.location.pathname + window.location.search + window.location.hash;
}

function routeTransitionKey(route: AppRoute) {
  switch (route.kind) {
    case "dashboard": return "dashboard:" + route.view;
    case "new-project": return "new-project";
    case "project": return "project:" + route.projectId;
    case "variant-review": return "variant:" + route.projectId + ":" + route.variantId;
    case "studio": return "studio:" + route.projectId + ":" + route.variantId;
    case "validation": return "validation:" + route.projectId;
    case "export": return "export:" + route.projectId;
    case "published-fonts": return "published-fonts";
  }
}

export default function App() {
  const { t } = useTranslation();
  const [path, setPath] = useState(currentPath);
  const pathRef = useRef(path);
  const editorFlushRef = useRef<(() => Promise<void>) | null>(null);
  const registerEditorFlush = useCallback((flush: (() => Promise<void>) | null) => {
    editorFlushRef.current = flush;
  }, []);
  const navigate = useCallback<Navigate>((to, replace = false) => {
    void (async () => {
      try {
        await editorFlushRef.current?.();
      } catch (error) {
        window.alert(t("editor.unsavedNavigation") + getError(error));
        return;
      }
      if (replace) window.history.replaceState({}, "", to);
      else window.history.pushState({}, "", to);
      const next = currentPath();
      pathRef.current = next;
      setPath(next);
      if (!window.location.hash) window.scrollTo({ top: 0, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
    })();
  }, [t]);

  useEffect(() => {
    const onPop = () => {
      const next = currentPath();
      const flush = editorFlushRef.current;
      if (!flush) {
        pathRef.current = next;
        setPath(next);
        return;
      }
      void flush().then(() => {
        pathRef.current = next;
        setPath(next);
      }).catch(error => {
        window.history.pushState({}, "", pathRef.current);
        window.alert(t("editor.unsavedNavigation") + getError(error));
      });
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, [t]);

  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (!hash) return;
    const frame = window.requestAnimationFrame(() => {
      document.getElementById(decodeURIComponent(hash))?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start",
      });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [path]);

  const route = useMemo(() => resolveRoute(path), [path]);
  let page: ReactNode;
  switch (route.kind) {
    case "dashboard":
      page = <DashboardPage navigate={navigate} view={route.view} renderProviderSection={onSnapshot => <ProviderSettingsPage onSnapshot={onSnapshot} />} />;
      break;
    case "new-project":
      page = <NewProjectPage />;
      break;
    case "project":
      page = <ProjectPage projectId={route.projectId} query={route.query} />;
      break;
    case "variant-review":
      page = <VariantReviewPage projectId={route.projectId} variantId={route.variantId} />;
      break;
    case "studio":
      page = <StudioLayout><EditorPage projectId={route.projectId} variantId={route.variantId} query={route.query} /></StudioLayout>;
      break;
    case "validation":
      page = <ValidationPage projectId={route.projectId} />;
      break;
    case "export":
      page = <ExportPage projectId={route.projectId} />;
      break;
    case "published-fonts":
      page = <PublishedFontsPage />;
      break;
  }

  return <NavigationProvider navigate={navigate}>
    <EditorFlushProvider register={registerEditorFlush}>
      <DashboardLayout routeKey={routeTransitionKey(route)} pathname={route.pathname} search={route.search} hash={route.hash}>{page}</DashboardLayout>
    </EditorFlushProvider>
  </NavigationProvider>;
}

