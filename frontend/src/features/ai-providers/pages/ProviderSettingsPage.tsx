import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import {
  connectOllamaCloud, disconnectAiProvider, getAiProviders, selectAiProvider, selectAiProviderModel, startChatGptConnect,
  type AiProviderId, type AiProviderStatus, type AiProviders,
} from "../api/ai-providers.api";
import { ErrorBox, Loading, StatusTag } from "../../../shared/ui";
import { getError } from "../../../shared/utils/errors";
import { ProviderModelChooser } from "../components/ProviderModelChooser";
import { Button } from "../../../shared/ui/Button";
import { Input } from "../../../shared/ui/primitives/input";
import { AnimatePresence, motion } from "motion/react";
import { usePrefersReducedMotion } from "../../../shared/hooks/usePrefersReducedMotion";

function providerStatusTone(provider?: AiProviderStatus): "neutral" | "good" | "warn" | "bad" {
  if (provider?.status === "connected") return "good";
  if (provider?.status === "error") return "bad";
  if (provider?.status === "needs_reconnect") return "warn";
  return "neutral";
}

export function ProviderSettingsPage({ onSnapshot }: { onSnapshot: (snapshot: AiProviders | null) => void }) {
  const { t } = useTranslation();
  const reduceMotion = usePrefersReducedMotion();
  const providerStatusLabel = (provider?: AiProviderStatus) => !provider ? t("providers.noStatus") : t(`providers.${provider.status === "connected" ? "connected" : provider.status === "needs_reconnect" ? "reconnect" : provider.status === "error" ? "check" : "disconnected"}`);
  const [snapshot, setSnapshot] = useState<Awaited<ReturnType<typeof getAiProviders>> | null>(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const popup = useRef<Window | null>(null);
  const callbackOrigin = useRef<string | null>(null);
  const expectedOAuthState = useRef<string | null>(null);
  const reload = useCallback(async () => {
    setLoading(true);
    try { const next = await getAiProviders(); setSnapshot(next); onSnapshot(next); setError(""); }
    catch (e) { onSnapshot(null); setError(getError(e)); }
    finally { setLoading(false); }
  }, [onSnapshot]);
  useEffect(() => { void reload(); }, [reload]);
  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      const source = popup.current;
      if (!source || event.source !== source || event.origin !== callbackOrigin.current) return;
      const message = event.data as { type?: string; providerId?: string; ok?: boolean; errorCode?: string; state?: string } | null;
      if (!message || message.type !== "vfk:provider-auth-complete" || message.providerId !== "chatgpt" || message.state !== expectedOAuthState.current) return;
      popup.current = null;
      callbackOrigin.current = null;
      expectedOAuthState.current = null;
      source.close();
      if (message.ok) setNotice(t("providers.connectedChatgpt"));
      else setError(t("providers.loginIncomplete") + (message.errorCode ? " " + t("providers.statusCode", { code: message.errorCode }) : ""));
      void reload();
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [reload, t]);

  const providers = snapshot?.providers || [];
  const chatgpt = providers.find(provider => provider.id === "chatgpt");
  const ollama = providers.find(provider => provider.id === "ollama_cloud");
  const connectChatGpt = async () => {
    setError(""); setNotice("");
    const authWindow = window.open("about:blank", "vfk-chatgpt-sign-in", "popup,width=520,height=720");
    if (!authWindow) { setError(t("providers.popupBlocked")); return; }
    popup.current = authWindow;
    setAction("chatgpt");
    try {
      const result = await startChatGptConnect();
      const redirectUri = new URL(result.authorizationUrl).searchParams.get("redirect_uri");
      if (!redirectUri) throw new Error("ChatGPT loopback callback is missing from the authorization request.");
      const callbackUrl = new URL(redirectUri);
      const expectedState = new URL(result.authorizationUrl).searchParams.get("state");
      if (!expectedState) throw new Error("OAuth state is missing from the authorization request.");
      expectedOAuthState.current = expectedState;
      if (callbackUrl.protocol !== "http:" || callbackUrl.hostname !== "127.0.0.1") throw new Error("Unexpected ChatGPT callback origin.");
      callbackOrigin.current = callbackUrl.origin;
      authWindow.location.href = result.authorizationUrl;
      result.authorizationUrl = "";
      setNotice(t("providers.finishLogin"));
    } catch (e) {
      authWindow.close(); popup.current = null; callbackOrigin.current = null; expectedOAuthState.current = null; setError(getError(e));
    } finally { setAction(""); }
  };
  const connectOllama = async (event: FormEvent) => {
    event.preventDefault();
    const secret = apiKey;
    if (!secret.trim()) return;
    setApiKey("");
    setError(""); setNotice(""); setAction("ollama_cloud");
    try {
      await connectOllamaCloud(secret);
      await reload();
    } catch (e) { setError(getError(e)); }
    finally { setAction(""); }
  };
  const chooseProvider = async (providerId: AiProviderId) => {
    setError(""); setNotice(""); setAction("select:" + providerId);
    try { const next = await selectAiProvider(providerId); setSnapshot(next); onSnapshot(next); setNotice(t("providers.selectedForWorkflow")); }
    catch (e) { setError(getError(e)); }
    finally { setAction(""); }
  };
  const chooseModel = async (providerId: AiProviderId, modelId: string) => {
    setError(""); setNotice(""); setAction("model:" + providerId);
    try {
      await selectAiProviderModel(providerId, modelId);
      await reload();
      setNotice(t("providers.modelSaved"));
    } catch (e) { setError(getError(e)); }
    finally { setAction(""); }
  };
  const disconnect = async (providerId: AiProviderId) => {
    setError(""); setNotice(""); setAction("disconnect:" + providerId);
    try { await disconnectAiProvider(providerId); await reload(); setNotice(t("providers.disconnectedNotice")); }
    catch (e) { setError(getError(e)); }
    finally { setAction(""); }
  };
  const selectedId = snapshot?.selectedProviderId;
  const activeProvider = snapshot?.providers.find(provider => provider.id === selectedId);
  const selectedReady = activeProvider?.status === "connected" && !!activeProvider.selectedModelId;
  const firstConnected = snapshot?.providers.find(provider => provider.status === "connected");
  const firstConnectedName = firstConnected?.id === "chatgpt" ? "ChatGPT" : firstConnected?.id === "ollama_cloud" ? "Ollama Cloud" : "AI provider";
  const providerSectionStatus = selectedReady ? t("providers.ready") :
    activeProvider?.status === "connected" ? t("providers.selectedNeedsModel") :
    activeProvider?.status === "needs_reconnect" ? t("providers.reconnect") :
    firstConnected?.selectedModelId ? t("providers.connectedChooseProvider") :
    firstConnected ? t("providers.connectedChooseModel") : t("providers.connectRequired");
  const renderProviderControls = (provider: AiProviderStatus | undefined, id: AiProviderId) => {
    const connected = provider?.status === "connected";
    const selected = selectedId === id;
    return <>
      {connected && <ProviderModelChooser provider={provider} onSelect={modelId => chooseModel(id, modelId)} />}
      {connected && <div className="provider-controls">
        <Button type="button" kind="primary" className={"provider-action " + (selected ? "current" : "")} disabled={!!action || !provider?.selectedModelId || selected} onClick={() => void chooseProvider(id)}>
          {selected ? t("providers.providerSelected") : t("providers.useProvider")}
        </Button>
        <Button type="button" kind="danger" className="provider-disconnect" disabled={!!action} onClick={() => void disconnect(id)}>{t("providers.disconnect")}</Button>
      </div>}
    </>;
  };
  return <section id="providers" className="dashboard-section provider-section" aria-labelledby="provider-title">
    <div className="section-title"><div><p className="eyebrow">{t("providers.titleEyebrow")}</p><h2 id="provider-title">{t("providers.title")}</h2></div>
      <StatusTag tone={selectedReady ? "good" : "warn"}>{providerSectionStatus}</StatusTag></div>
    <p className="provider-intro">{t("providers.intro")}</p>
    {!selectedReady && firstConnected?.selectedModelId && <p className="provider-notice" role="status">{t("providers.selectedNotice", { provider: firstConnectedName, model: firstConnected.selectedModelId })}</p>}
    {error && <ErrorBox error={error} retry={reload} />}<AnimatePresence initial={false} mode="wait">{notice && <motion.p key={notice} className="provider-notice" role="status" initial={reduceMotion ? false : { opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} exit={reduceMotion ? { opacity: 1 } : { opacity: 0, y: -3 }} transition={{ duration: reduceMotion ? 0 : 0.16 }}>{notice}</motion.p>}</AnimatePresence>
    {loading && !snapshot && <Loading label={t("providers.loading")} />}
    <div className="provider-grid">
      <article className="ai-provider-card">
        <div className="ai-provider-card-head"><span className="provider-mark openai">AI</span><StatusTag tone={providerStatusTone(chatgpt)}>{providerStatusLabel(chatgpt)}</StatusTag></div>
        <p className="provider-kind">{t("providers.openaiKind")}</p><h3>{t("providers.openai")}</h3>
        <p>{chatgpt?.accountLabel ? t("providers.loginAs", { account: chatgpt.accountLabel }) : t("providers.chatgptIntro")}</p>
        {chatgpt?.status === "connected" ? renderProviderControls(chatgpt, "chatgpt") :
          <Button type="button" kind="primary" className="provider-action" disabled={!!action} onClick={() => void connectChatGpt()}>{action === "chatgpt" ? t("providers.openingLogin") : t("providers.signIn")}</Button>}
        {chatgpt?.errorCode && <small className="provider-error-code">{t("providers.statusCode", { code: chatgpt.errorCode })}</small>}
      </article>
      <article className="ai-provider-card">
        <div className="ai-provider-card-head"><span className="provider-mark ollama">OL</span><StatusTag tone={providerStatusTone(ollama)}>{providerStatusLabel(ollama)}</StatusTag></div>
        <p className="provider-kind">{t("providers.ollamaKind")}</p><h3>{t("providers.ollama")}</h3>
        <p>{ollama?.status === "connected" ? (ollama.accountLabel || t("providers.savedKey")) : t("providers.ollamaIntro")}</p>
        {ollama?.status === "connected" ? renderProviderControls(ollama, "ollama_cloud") :
          <form className="provider-key-form" onSubmit={connectOllama}>
            <Input type="password" className="form-input" value={apiKey} onChange={event => setApiKey(event.target.value)} autoComplete="off" spellCheck={false} aria-label={t("providers.apiKey")} placeholder={t("providers.apiKey")} />
            <Button type="submit" kind="primary" className="provider-action" disabled={!!action || !apiKey.trim()}>{action === "ollama_cloud" ? t("providers.checking") : t("providers.connectWithKey")}</Button>
          </form>}
        {ollama?.errorCode && <small className="provider-error-code">{t("providers.statusCode", { code: ollama.errorCode })}</small>}
      </article>
    </div>
  </section>;
}
