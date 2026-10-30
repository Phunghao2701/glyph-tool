import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "./Button";
import { Alert, AlertDescription } from "./primitives/alert";
import { Spinner } from "./primitives/spinner";

export function ErrorBox({ error, retry }: { error: string; retry?: () => void }) {
  const { t } = useTranslation();
  return <Alert variant="destructive" className="notice danger flex items-center justify-between gap-3"><AlertDescription className="m-0 flex-1 text-current">{error}</AlertDescription>{retry && <Button type="button" kind="quiet" onClick={retry}>{t("common.retry")}</Button>}</Alert>;
}

export function Loading({ label }: { label?: string }) {
  const { t } = useTranslation();
  return <div className="loading" role="status"><Spinner aria-hidden="true" />{label || t("common.loading")}</div>;
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="empty"><p>{children}</p></div>;
}

