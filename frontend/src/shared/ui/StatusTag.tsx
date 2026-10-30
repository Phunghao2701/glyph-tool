import type { ReactNode } from "react";
import type { StatusTone } from "../types/ui";
import { Badge } from "./primitives/badge";

type StatusTagProps = { children: ReactNode; tone?: StatusTone };
const variants = { good: "default", warn: "secondary", bad: "destructive", neutral: "outline" } as const;

export function StatusTag({ children, tone = "neutral" }: StatusTagProps) {
  const variant = variants[tone];
  const style = { good: "pill-green", warn: "pill-gold", bad: "pill-red", neutral: "pill-gray" }[tone];
  return <Badge variant={variant} className={`pill ${style}`}>{children}</Badge>;
}
