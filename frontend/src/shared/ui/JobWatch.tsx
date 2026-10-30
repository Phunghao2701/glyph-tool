import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { getJob, type Job } from "../lib/api";
import { getError } from "../utils/errors";
import { StatusTag } from "./StatusTag";
import { ErrorBox, Loading } from "./Feedback";
import { Progress } from "./primitives/progress";

function isDone(status: string) {
  return status === "succeeded" || status === "completed" || status === "failed" || status === "cancelled";
}

export function JobWatch({ jobId, onDone }: { jobId: string; onDone?: (job: Job) => void }) {
  const { t } = useTranslation();
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState("");
  const done = useRef(onDone);
  done.current = onDone;

  useEffect(() => {
    let active = true;
    let timer = 0;
    let delayMs = 3_000;
    let previousProgress = "";
    const poll = async () => {
      try {
        const next = await getJob(jobId);
        if (!active) return;
        setError("");
        setJob(next);
        if (isDone(next.status)) { done.current?.(next); return; }
        const progress = `${next.status}:${next.progressPct ?? 0}:${next.currentStep ?? ""}`;
        delayMs = progress === previousProgress ? Math.min(delayMs * 2, 10_000) : 3_000;
        previousProgress = progress;
      } catch (e) {
        if (active) {
          setError(getError(e));
          delayMs = Math.min(delayMs * 2, 30_000);
        }
      }
      if (active) timer = window.setTimeout(poll, delayMs);
    };
    void poll();
    return () => { active = false; window.clearTimeout(timer); };
  }, [jobId]);

  if (error) return <ErrorBox error={error} />;
  if (!job) return <Loading label={t("job.connected")} />;
  const progressPct = Math.max(0, Math.min(100, job.progressPct ?? 0));
  return <div className="job-card">
    <div className="job-head"><div><strong>{job.currentStep || t("job.processing")}</strong><small>{t("job.id", { id: job.id.slice(0, 8) })}</small></div>
      <StatusTag tone={job.status === "failed" ? "bad" : isDone(job.status) ? "good" : "warn"}>{t(`common.status.${job.status}`, { defaultValue: job.status })}</StatusTag></div>
    <Progress className="progress" value={progressPct} aria-label={t("job.progress")} />
    <div className="job-foot"><span>{job.currentStep || t("job.processing")}</span><b>{progressPct}%</b></div>
    {job.error && <ErrorBox error={job.error.message} />}
  </div>;
}

