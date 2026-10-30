import type { ValidationResult } from "../lib/api";

export interface RevisionCoverage {
  requiredCount: number;
  presentCount: number;
  missing: string[];
  percent: number;
}

export function getRevisionCoverage(validation?: ValidationResult | null): RevisionCoverage | null {
  const coverage = validation?.coverage;
  if (typeof coverage?.requiredCount === "number" && typeof coverage.presentCount === "number") {
    const requiredCount = Math.max(0, coverage.requiredCount);
    const presentCount = Math.max(0, Math.min(requiredCount, coverage.presentCount));
    return {
      requiredCount,
      presentCount,
      missing: coverage.missing || [],
      percent: typeof coverage.percent === "number"
        ? Math.max(0, Math.min(100, Math.round(coverage.percent)))
        : Math.round(100 * presentCount / Math.max(1, requiredCount)),
    };
  }

  // Older saved QA reports only contain the human-readable coverage check.
  const detail = validation?.checks?.find(check => check.id === "vietnamese_coverage")?.detail;
  const match = detail?.match(/^(\d+)\/(\d+) required characters present\.(?:\s*Missing:\s*([\s\S]*))?$/i);
  if (!match) return null;

  const presentCount = Number(match[1]);
  const requiredCount = Number(match[2]);
  return {
    requiredCount,
    presentCount,
    missing: match[3] ? Array.from(match[3].trim()) : [],
    percent: Math.round(100 * presentCount / Math.max(1, requiredCount)),
  };
}
