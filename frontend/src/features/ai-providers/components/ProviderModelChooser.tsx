import { useState } from "react";
import { useTranslation } from "react-i18next";
import { getAiProviderModels, type AiProviderModel, type AiProviderStatus } from "../api/ai-providers.api";
import { getError } from "../../../shared/utils/errors";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../../shared/ui/primitives/select";

export function ProviderModelChooser({ provider, onSelect }: { provider: AiProviderStatus; onSelect: (modelId: string) => void }) {
  const { t } = useTranslation();
  const [models, setModels] = useState<AiProviderModel[]>([]);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const loadModels = async () => {
    if (loaded || loading) return;
    setLoading(true); setError("");
    try { setModels(await getAiProviderModels(provider.id)); setLoaded(true); }
    catch (e) { setError(getError(e)); }
    finally { setLoading(false); }
  };
  return <details className="provider-models" onToggle={event => { if (event.currentTarget.open) void loadModels(); }}>
    <summary>{provider.selectedModelId ? t("providers.model", { model: provider.selectedModelId }) : t("providers.chooseModel")}</summary>
    {loading && <small>{t("providers.loadModels")}</small>}{error && <small className="model-error">{error}</small>}
    {!loading && loaded && models.length === 0 && <small>{t("providers.noModels")}</small>}
    {!loading && models.length > 0 && <Select value={provider.selectedModelId || undefined} onValueChange={onSelect}>
      <SelectTrigger className="form-input" aria-label={t("providers.modelFor", { provider: provider.id })}><SelectValue placeholder={t("providers.chooseModelOption")} /></SelectTrigger>
      <SelectContent>{models.map(model => <SelectItem key={model.id} value={model.id}>{model.displayName}</SelectItem>)}</SelectContent>
    </Select>}
  </details>;
}
