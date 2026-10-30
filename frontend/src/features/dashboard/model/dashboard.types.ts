import type { ReactNode } from "react";
import type { AiProviders } from "../../../shared/lib/api";

export type DashboardView = "overview" | "projects" | "settings";
export type DashboardPageProps = {
  navigate: (path: string) => void;
  view: DashboardView;
  renderProviderSection: (onSnapshot: (snapshot: AiProviders | null) => void) => ReactNode;
};

