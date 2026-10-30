import { useCallback, useEffect, useState } from "react";
import { getAiProviders, type AiProviders } from "../api/ai-providers.api";
import { getError } from "../../../shared/utils/errors";

export function useAiReadiness() {
  const [snapshot, setSnapshot] = useState<AiProviders | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const reload = useCallback(async () => {
    setLoading(true);
    try { setSnapshot(await getAiProviders()); setError(""); }
    catch (e) { setSnapshot(null); setError(getError(e)); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void reload(); }, [reload]);
  const selected = snapshot?.providers.find(provider => provider.id === snapshot.selectedProviderId);
  return { ready: selected?.status === "connected" && !!selected.selectedModelId, loading, error, reload };
}
