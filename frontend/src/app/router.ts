import { APP_PATHS } from "../shared/constants/routes";

export type DashboardView = "overview" | "projects" | "settings";

export type AppRoute =
  | { kind: "dashboard"; view: DashboardView; pathname: string; search: string; hash: string }
  | { kind: "new-project"; pathname: string; search: string; hash: string }
  | { kind: "project"; projectId: string; query: URLSearchParams; pathname: string; search: string; hash: string }
  | { kind: "variant-review"; projectId: string; variantId: string; pathname: string; search: string; hash: string }
  | { kind: "studio"; projectId: string; variantId: string; query: URLSearchParams; pathname: string; search: string; hash: string }
  | { kind: "validation"; projectId: string; pathname: string; search: string; hash: string }
  | { kind: "export"; projectId: string; pathname: string; search: string; hash: string }
  | { kind: "published-fonts"; pathname: string; search: string; hash: string };

export function resolveRoute(path: string): AppRoute {
  const url = new URL(path, window.location.origin);
  const parts = url.pathname.split("/").filter(Boolean).map(decodeURIComponent);
  const [root, projectId, section, resourceId, sub] = parts;
  const hash = decodeURIComponent(url.hash.slice(1));

  if (url.pathname === APP_PATHS.publishedFonts) {
    return { kind: "published-fonts", pathname: url.pathname, search: url.search, hash };
  }
  if (root !== "projects" || parts.length <= 1) {
    const view = hash === "providers" || url.searchParams.get("view") === "settings"
      ? "settings"
      : hash === "projects" || url.searchParams.get("view") === "projects"
        ? "projects"
        : "overview";
    return { kind: "dashboard", view, pathname: url.pathname, search: url.search, hash };
  }
  if (projectId === "new") return { kind: "new-project", pathname: url.pathname, search: url.search, hash };
  if (section === "validation") return { kind: "validation", projectId, pathname: url.pathname, search: url.search, hash };
  if (section === "export") return { kind: "export", projectId, pathname: url.pathname, search: url.search, hash };
  if (section === "variants" && sub === "editor" && resourceId) {
    return { kind: "studio", projectId, variantId: resourceId, query: url.searchParams, pathname: url.pathname, search: url.search, hash };
  }
  if (section === "variants" && resourceId) return { kind: "variant-review", projectId, variantId: resourceId, pathname: url.pathname, search: url.search, hash };
  return { kind: "project", projectId, query: url.searchParams, pathname: url.pathname, search: url.search, hash };
}

