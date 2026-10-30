import { createContext, useContext, type ReactNode } from "react";

export type Navigate = (path: string, replace?: boolean) => void;
const NavigationContext = createContext<Navigate | null>(null);

export function NavigationProvider({ navigate, children }: { navigate: Navigate; children: ReactNode }) {
  return <NavigationContext.Provider value={navigate}>{children}</NavigationContext.Provider>;
}

export function useNavigate(): Navigate {
  const navigate = useContext(NavigationContext);
  if (!navigate) throw new Error("useNavigate must be used inside NavigationProvider.");
  return navigate;
}

export function AppLink({ to, children, className, afterNavigate, ariaCurrent, ariaLabel, title }: {
  to: string;
  children: ReactNode;
  className?: string;
  afterNavigate?: () => void;
  ariaCurrent?: "page";
  ariaLabel?: string;
  title?: string;
}) {
  const navigate = useNavigate();
  return <a className={className} href={to} aria-current={ariaCurrent} aria-label={ariaLabel} title={title} onClick={event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    navigate(to);
    afterNavigate?.();
  }}>{children}</a>;
}

