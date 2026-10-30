import type { ReactNode } from "react";

export function StudioLayout({ children }: { children: ReactNode }) {
  return <div className="studio-route" data-layout="studio">{children}</div>;
}

