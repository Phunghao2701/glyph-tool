import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type FormEvent, type ReactNode } from "react";
import {
  ApiError, approveRevision, connectOllamaCloud, createProject, createReview, createRevision, disconnectAiProvider,
  getAiProviderModels, getAiProviders, getEditorDocument, getExport, getJob, getProject, getRevision, listProjects,
  selectAiProvider, selectAiProviderModel, startAnalysis, startChatGptConnect, startExport, startValidation,
  startVariantRefinement, startVariants, uploadSource, type AiProviderId, type AiProviderModel, type AiProviderStatus, type AiProviders, type ExportArtifact,
  type Job, type Project, type Revision, type Variant
} from "./api";
import GlyphEditorFrame from "./GlyphEditorFrame";

type Navigate = (path: string, replace?: boolean) => void;
const Navigation = createContext<Navigate>(() => undefined);
const EditorFlushContext = createContext<(flush: (() => Promise<void>) | null) => void>(() => undefined);

function useNavigate(): Navigate { return useContext(Navigation); }
function useRegisterEditorFlush() { return useContext(EditorFlushContext); }

function AppLink({ to, children, className }: { to: string; children: ReactNode; className?: string }) {
  const navigate = useNavigate();
  return <a className={className} href={to} onClick={event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    navigate(to);
  }}>{children}</a>;
}

function AppShell({ children }: { children: ReactNode }) {
  const pathname = window.location.pathname;
  const hash = window.location.hash.slice(1);
  const isOverview = pathname === "/projects" && hash !== "projects" && hash !== "providers";
  const isProjects = hash === "projects" || (pathname.startsWith("/projects/") && pathname !== "/projects/new");
  return <div className="app-shell">
    <header className="topbar">
      <AppLink to="/projects" className="brand"><span className="brand-mark">V</span><span>Viet Font Studio<small>KHÔNG GIAN FONT CỤC BỘ</small></span></AppLink>
      <div className="topbar-actions"><span className="local-pill"><i /> Không gian cục bộ</span><span className="topbar-avatar" aria-label="Không gian cục bộ">VF</span></div>
    </header>
    <div className="workspace-layout">
      <aside className="sidebar">
        <div className="workspace-card"><span className="workspace-symbol">VF</span><span><b>Không gian font</b><small>Hệ thống một người dùng</small></span></div>
        <p className="sidebar-label">KHÔNG GIAN</p>
        <nav className="side-nav" aria-label="Điều hướng không gian">
          <AppLink to="/projects" className={"side-link " + (isOverview ? "active" : "")}><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.5"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.5"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.5"/></svg>Tổng quan</AppLink>
          <AppLink to="/projects#projects" className={"side-link " + (isProjects ? "active" : "")}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7.5h6l2 2h8v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z"/><path d="M4 7.5V5a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v2.5"/></svg>Dự án font</AppLink>
          <AppLink to="/projects#providers" className={"side-link " + (hash === "providers" ? "active" : "")}><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5v4M12 16.5v4M3.5 12h4M16.5 12h4"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="9"/></svg>Nhà cung cấp AI<span className="side-pending">Thiết lập</span></AppLink>
        </nav>
        <AppLink to="/projects/new" className="sidebar-create"><span>＋</span>Tạo dự án font</AppLink>
        <div className="sidebar-bottom"><span className="sidebar-status"><i />Xử lý font cục bộ</span><small>AI sẵn sàng khi bạn kết nối provider.</small></div>
      </aside>
      <main className="main">{children}</main>
    </div>
    <footer className="footer">Không gian font cục bộ · Quy trình VFK</footer>
  </div>;
}

function Button({ children, onClick, disabled, kind = "secondary", type = "button" }: {
  children: ReactNode; onClick?: () => void; disabled?: boolean; kind?: "primary" | "secondary" | "quiet" | "danger"; type?: "button" | "submit";
}) {
  return <button className={"button " + kind} type={type} onClick={onClick} disabled={disabled}>{children}</button>;
}
function ErrorBox({ error, retry }: { error: string; retry?: () => void }) {
  return <div className="error-box" role="alert"><span>{error}</span>{retry && <button onClick={retry}>Thử lại</button>}</div>;
}
function Loading({ label = "Đang tải…" }: { label?: string }) {
  return <div className="loading"><span className="spinner" />{label}</div>;
}
function StatusTag({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "good" | "warn" | "bad" }) {
  return <span className={"status-tag " + tone}><i />{children}</span>;
}
function getError(error: unknown): string {
  return error instanceof ApiError ? error.message : error instanceof Error ? error.message : "Có lỗi không xác định.";
}
function isDone(status: string) {
  return status === "succeeded" || status === "completed" || status === "failed" || status === "cancelled";
}

function JobWatch({ jobId, onDone }: { jobId: string; onDone?: (job: Job) => void }) {
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
  if (!job) return <Loading label="Đang kết nối tới job…" />;
  const progressPct = Math.max(0, Math.min(100, job.progressPct ?? 0));
  return <div className="job-card">
    <div className="job-head"><div><strong>{job.currentStep || job.kind}</strong><small>Job {job.id.slice(0, 8)}</small></div>
      <StatusTag tone={job.status === "failed" ? "bad" : isDone(job.status) ? "good" : "warn"}>{job.status}</StatusTag></div>
    <div className="progress"><span style={{ transform: "scaleX(" + (progressPct / 100) + ")" }} /></div>
    <div className="job-foot"><span>{job.currentStep || "Đang xử lý"}</span><b>{progressPct}%</b></div>
    {job.error && <ErrorBox error={job.error.message} />}
  </div>;
}

function App() {
  const [path, setPath] = useState(window.location.pathname + window.location.search + window.location.hash);
  const pathRef = useRef(path);
  const editorFlushRef = useRef<(() => Promise<void>) | null>(null);
  const registerEditorFlush = useCallback((flush: (() => Promise<void>) | null) => {
    editorFlushRef.current = flush;
  }, []);
  const navigate = useCallback<Navigate>((to, replace = false) => {
    void (async () => {
      try {
        await editorFlushRef.current?.();
      } catch (error) {
        window.alert("Bản vẽ chưa lưu được nên vẫn ở lại editor. " + getError(error));
        return;
      }
      if (replace) window.history.replaceState({}, "", to);
      else window.history.pushState({}, "", to);
      const next = window.location.pathname + window.location.search + window.location.hash;
      pathRef.current = next;
      setPath(next);
      if (!window.location.hash) window.scrollTo({ top: 0, behavior: "smooth" });
    })();
  }, []);
  useEffect(() => {
    const onPop = () => {
      const next = window.location.pathname + window.location.search + window.location.hash;
      const flush = editorFlushRef.current;
      if (!flush) {
        pathRef.current = next;
        setPath(next);
        return;
      }
      void flush().then(() => {
        pathRef.current = next;
        setPath(next);
      }).catch(error => {
        window.history.pushState({}, "", pathRef.current);
        window.alert("Bản vẽ chưa lưu được nên vẫn ở lại editor. " + getError(error));
      });
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);
  useEffect(() => {
    const hash = window.location.hash.slice(1);
    if (!hash) return;
    const frame = window.requestAnimationFrame(() => {
      document.getElementById(decodeURIComponent(hash))?.scrollIntoView({
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "start"
      });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [path]);
  const route = useMemo(() => {
    const url = new URL(path, window.location.origin);
    return { parts: url.pathname.split("/").filter(Boolean).map(decodeURIComponent), query: url.searchParams };
  }, [path]);
  const [root, projectId, section, resourceId, sub] = route.parts;
  let page: ReactNode;
  if (root !== "projects" || route.parts.length <= 1) page = <ProjectsPage />;
  else if (projectId === "new") page = <NewProjectPage />;
  else if (section === "validation") page = <ValidationPage projectId={projectId} />;
  else if (section === "export") page = <ExportPage projectId={projectId} />;
  else if (section === "variants" && sub === "editor") page = <EditorPage projectId={projectId} variantId={resourceId} query={route.query} />;
  else if (section === "variants" && resourceId) page = <VariantPage projectId={projectId} variantId={resourceId} />;
  else page = <ProjectPage projectId={projectId} query={route.query} />;
  return <Navigation.Provider value={navigate}><EditorFlushContext.Provider value={registerEditorFlush}><AppShell>{page}</AppShell></EditorFlushContext.Provider></Navigation.Provider>;
}

function ProjectsPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [providerSnapshot, setProviderSnapshot] = useState<AiProviders | null>(null);
  const reload = useCallback(() => {
    setLoading(true); setError("");
    listProjects().then(setProjects).catch(e => setError(getError(e))).finally(() => setLoading(false));
  }, []);
  useEffect(() => { reload(); }, [reload]);
  const analyzedCount = projects.filter(project => !!project.analysis).length;
  const variantCount = projects.reduce((count, project) => count + (project.variants?.length || 0), 0);
  const selectedProvider = providerSnapshot?.providers.find(provider => provider.id === providerSnapshot.selectedProviderId);
  const connectedProvider = providerSnapshot?.providers.find(provider => provider.status === "connected");
  const aiReady = selectedProvider?.status === "connected" && !!selectedProvider.selectedModelId;
  const providerName = (providerId?: AiProviderId | null) => providerId === "chatgpt" ? "ChatGPT theo gói" : providerId === "ollama_cloud" ? "Ollama Cloud" : "Provider AI";
  const selectedProviderLabel = aiReady ? providerName(selectedProvider?.id) : "";
  const aiNextStep = connectedProvider?.selectedModelId
    ? `Đã kết nối ${providerName(connectedProvider.id)} · bấm “Dùng provider này” bên dưới.`
    : connectedProvider
      ? `Đã kết nối ${providerName(connectedProvider.id)} · cần chọn model.`
      : "Cần kết nối provider AI và chọn model.";
  const aiWaitLabel = connectedProvider?.selectedModelId ? "Đã kết nối · chọn provider" : connectedProvider ? "Đã kết nối · chọn model" : "Cần kết nối AI";
  const aiStatusLabel = !providerSnapshot ? "Đang tải trạng thái AI" :
    aiReady ? selectedProviderLabel : selectedProvider?.status === "needs_reconnect" ? "Cần đăng nhập lại" :
    selectedProvider?.status === "connected" ? "Cần chọn model" : selectedProvider?.status === "error" ? "Kiểm tra kết nối AI" :
    connectedProvider?.selectedModelId ? `${providerName(connectedProvider.id)} đã kết nối · chưa chọn` :
    connectedProvider ? `${providerName(connectedProvider.id)} đã kết nối · cần chọn model` :
    selectedProvider ? "Provider chưa sẵn sàng" : "Cần kết nối provider AI";
  return <section className="page dashboard-page">
    <div className="dashboard-heading">
      <div><p className="eyebrow">KHÔNG GIAN FONT CỤC BỘ / TỔNG QUAN</p><h1>Xưởng Việt hóa font</h1><p className="lede">Phân tích font nguồn, tạo phương án chữ Việt, duyệt revision rồi xuất font đã kiểm định.</p></div>
      <Button kind="primary" onClick={() => navigate("/projects/new")}>＋ Tạo dự án font</Button>
    </div>
    {error && <ErrorBox error={error} retry={reload} />}
    <div className="dashboard-metrics">
      <div><span>Dự án font</span><b>{loading ? "—" : projects.length}</b><small>trong không gian này</small></div>
      <div><span>Đã phân tích</span><b>{loading ? "—" : analyzedCount}</b><small>font nguồn đã đọc</small></div>
      <div><span>Phương án</span><b>{loading ? "—" : variantCount}</b><small>phương án VER đã tạo</small></div>
      <div className="metric-state"><span>Hồ sơ phong cách AI</span><b>{aiStatusLabel}</b><small>{aiReady ? "AI + VFK sẵn sàng cho phân tích phong cách và VER" : aiNextStep}</small>
        {!aiReady && connectedProvider?.selectedModelId && <button type="button" className="metric-provider-link" onClick={() => document.getElementById("providers")?.scrollIntoView({ behavior: "smooth", block: "start" })}>Chọn provider đang kết nối ↓</button>}
      </div>
    </div>

    <section className="dashboard-section roadmap-section" aria-labelledby="workflow-title">
      <div className="section-title"><div><p className="eyebrow">QUY TRÌNH HỆ THỐNG</p><h2 id="workflow-title">Từ font nguồn đến file xuất</h2></div><StatusTag tone={aiReady ? "good" : "warn"}>{aiReady ? "AI đã sẵn sàng · " + selectedProviderLabel : aiStatusLabel}</StatusTag></div>
      <div className="workflow-roadmap">
        <article className="roadmap-step"><span className="step-number">01</span><div><small>TIẾP NHẬN</small><h3>Tiếp nhận và đọc font</h3><p>Lõi VFK đọc metadata, đo coverage glyph và áp dụng quy tắc cục bộ.</p><span className="step-state ready">VFK · luôn bật</span></div></article>
        <article className={"roadmap-step " + (!aiReady ? "pending" : "")}><span className="step-number">02</span><div><small>HỒ SƠ PHONG CÁCH AI</small><h3>Phân tích phong cách font</h3><p>AI đọc phong cách font nguồn để định hướng cách xử lý glyph và các phương án VER.</p><span className={"step-state " + (aiReady ? "ready" : "waiting")}>{aiReady ? "Sẵn sàng · " + selectedProviderLabel : aiWaitLabel}</span></div></article>
        <article className={"roadmap-step " + (!aiReady ? "pending" : "")}><span className="step-number">03</span><div><small>TẠO PHƯƠNG ÁN</small><h3>VER 1A / 1B / 1C</h3><p>{aiReady ? "AI tạo ba hướng thiết kế; lõi VFK áp dụng quy tắc và ánh xạ glyph cho từng phương án." : aiNextStep}</p><span className={"step-state " + (aiReady ? "ready" : "waiting")}>{aiReady ? "AI + lõi VFK" : aiWaitLabel}</span></div></article>
        <article className="roadmap-step"><span className="step-number">04</span><div><small>DUYỆT</small><h3>Xem trước phương án</h3><p>So sánh mẫu chữ Việt và góp ý trên revision.</p><span className="step-state neutral">Trong từng dự án</span></div></article>
        <article className={"roadmap-step " + (!aiReady ? "pending" : "")}><span className="step-number">05</span><div><small>TINH CHỈNH</small><h3>Góp ý AI và sửa glyph</h3><p>Gửi feedback để AI tinh chỉnh phương án; editor cục bộ luôn hỗ trợ sửa contour thủ công.</p><span className={"step-state " + (aiReady ? "ready" : "waiting")}>{aiReady ? "AI refinement + vector editor" : "AI refinement cần provider + model"}</span></div></article>
        <article className="roadmap-step"><span className="step-number">06</span><div><small>BÀN GIAO</small><h3>Kiểm định và xuất font</h3><p>Chạy kiểm tra cục bộ, duyệt đúng revision rồi xuất TTF/OTF.</p><span className="step-state neutral">Kiểm định cục bộ</span></div></article>
      </div>
      <p className="roadmap-note">{aiReady ? "Provider và model đã chọn sẽ tạo hồ sơ phong cách và hướng dẫn VER. Lõi VFK luôn áp dụng quy tắc, ánh xạ glyph, kiểm định và xuất font cục bộ." : `${aiNextStep} Lõi VFK luôn áp dụng quy tắc, ánh xạ glyph, kiểm định và xuất font.`}</p>
    </section>

    <section id="projects" className="dashboard-section" aria-labelledby="projects-title">
      <div className="section-title"><div><p className="eyebrow">DỰ ÁN CỦA BẠN</p><h2 id="projects-title">Dự án font</h2></div><span className="section-count">{loading ? "…" : projects.length + " dự án"}</span></div>
      {loading ? <Loading label="Đang tải dự án font…" /> : projects.length === 0 ? <div className="empty-state"><div className="empty-icon">Aa</div><h2>Bắt đầu từ một font Latin</h2><p>Tải TTF hoặc OTF lên để kiểm tra glyph tiếng Việt và bắt đầu dự án đầu tiên.</p><Button kind="primary" onClick={() => navigate("/projects/new")}>Tạo dự án đầu tiên</Button></div> :
        <div className="project-grid">{projects.map(project => <AppLink key={project.id} to={"/projects/" + project.id} className="project-card">
          <div className="project-card-top"><span className="font-glyph">Aa</span><StatusTag tone={project.status === "exported" ? "good" : "neutral"}>{project.status}</StatusTag></div>
          <h2>{project.name}</h2><p>{project.sourceFont?.filename || "Chưa có font nguồn"}</p>
          <div className="project-card-foot"><span>{project.variants?.length || 0} phương án</span><span>{project.updatedAt ? new Date(project.updatedAt).toLocaleDateString("vi-VN") : "Mới"} ↗</span></div>
        </AppLink>)}</div>}
    </section>

    <ProviderSelection onSnapshot={setProviderSnapshot} />
  </section>;
}

function providerStatusLabel(provider?: AiProviderStatus) {
  if (!provider) return "Chưa có trạng thái";
  if (provider.status === "connected") return "Đã kết nối";
  if (provider.status === "needs_reconnect") return "Cần đăng nhập lại";
  if (provider.status === "error") return "Cần kiểm tra";
  return "Chưa kết nối";
}
function providerStatusTone(provider?: AiProviderStatus): "neutral" | "good" | "warn" | "bad" {
  if (provider?.status === "connected") return "good";
  if (provider?.status === "error") return "bad";
  if (provider?.status === "needs_reconnect") return "warn";
  return "neutral";
}

function useAiReadiness() {
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

function ProviderSelection({ onSnapshot }: { onSnapshot: (snapshot: AiProviders | null) => void }) {
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
      if (message.ok) setNotice("ChatGPT đã kết nối. Đang tải trạng thái mới.");
      else setError("Đăng nhập ChatGPT chưa hoàn tất." + (message.errorCode ? " Mã: " + message.errorCode : ""));
      void reload();
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [reload]);

  const providers = snapshot?.providers || [];
  const chatgpt = providers.find(provider => provider.id === "chatgpt");
  const ollama = providers.find(provider => provider.id === "ollama_cloud");
  const connectChatGpt = async () => {
    setError(""); setNotice("");
    const authWindow = window.open("about:blank", "vfk-chatgpt-sign-in", "popup,width=520,height=720");
    if (!authWindow) { setError("Trình duyệt đã chặn cửa sổ đăng nhập. Cho phép popup rồi thử lại."); return; }
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
      setNotice("Hoàn tất đăng nhập trong cửa sổ ChatGPT vừa mở.");
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
      setNotice("Ollama Cloud đã kết nối.");
      await reload();
    } catch (e) { setError(getError(e)); }
    finally { setAction(""); }
  };
  const chooseProvider = async (providerId: AiProviderId) => {
    setError(""); setNotice(""); setAction("select:" + providerId);
    try { const next = await selectAiProvider(providerId); setSnapshot(next); onSnapshot(next); setNotice("Đã chọn provider cho quy trình AI."); }
    catch (e) { setError(getError(e)); }
    finally { setAction(""); }
  };
  const chooseModel = async (providerId: AiProviderId, modelId: string) => {
    setError(""); setNotice(""); setAction("model:" + providerId);
    try {
      await selectAiProviderModel(providerId, modelId);
      await reload();
      setNotice("Model đã được lưu.");
    } catch (e) { setError(getError(e)); }
    finally { setAction(""); }
  };
  const disconnect = async (providerId: AiProviderId) => {
    setError(""); setNotice(""); setAction("disconnect:" + providerId);
    try { await disconnectAiProvider(providerId); await reload(); setNotice("Provider đã ngắt kết nối."); }
    catch (e) { setError(getError(e)); }
    finally { setAction(""); }
  };
  const selectedId = snapshot?.selectedProviderId;
  const activeProvider = snapshot?.providers.find(provider => provider.id === selectedId);
  const selectedReady = activeProvider?.status === "connected" && !!activeProvider.selectedModelId;
  const firstConnected = snapshot?.providers.find(provider => provider.status === "connected");
  const firstConnectedName = firstConnected?.id === "chatgpt" ? "ChatGPT theo gói" : firstConnected?.id === "ollama_cloud" ? "Ollama Cloud" : "Provider AI";
  const providerSectionStatus = selectedReady ? "AI đã sẵn sàng" :
    activeProvider?.status === "connected" ? "Đã chọn · cần chọn model" :
    activeProvider?.status === "needs_reconnect" ? "Cần đăng nhập lại" :
    firstConnected?.selectedModelId ? "Đã kết nối · cần chọn provider" :
    firstConnected ? "Đã kết nối · cần chọn model" : "Cần kết nối provider";
  const renderProviderControls = (provider: AiProviderStatus | undefined, id: AiProviderId) => {
    const connected = provider?.status === "connected";
    const selected = selectedId === id;
    return <>
      {connected && <ProviderModelChooser provider={provider} onSelect={modelId => chooseModel(id, modelId)} />}
      {connected && <div className="provider-controls">
        <button type="button" className={"provider-action " + (selected ? "current" : "")} disabled={!!action || !provider?.selectedModelId || selected} onClick={() => void chooseProvider(id)}>
          {selected ? "Đang được chọn" : "Dùng provider này"}
        </button>
        <button type="button" className="provider-disconnect" disabled={!!action} onClick={() => void disconnect(id)}>Ngắt kết nối</button>
      </div>}
    </>;
  };
  return <section id="providers" className="dashboard-section provider-section" aria-labelledby="provider-title">
    <div className="section-title"><div><p className="eyebrow">KẾT NỐI AI</p><h2 id="provider-title">Chọn nhà cung cấp AI</h2></div>
      <StatusTag tone={selectedReady ? "good" : "warn"}>{providerSectionStatus}</StatusTag></div>
    <p className="provider-intro">VFK luôn áp dụng quy tắc, ánh xạ glyph, kiểm định và xuất font cục bộ. Phân tích phong cách AI, tạo VER và tinh chỉnh bằng AI cần provider đã kết nối cùng model đã chọn.</p>
    {!selectedReady && firstConnected?.selectedModelId && <p className="provider-notice" role="status">{firstConnectedName} và model {firstConnected.selectedModelId} đã kết nối. Chọn “Dùng provider này” để bật AI cho quy trình.</p>}
    <p className="provider-privacy">Nhà cung cấp cloud đã chọn nhận metadata font và số đo đã chuẩn hóa cùng feedback để đề xuất VER. File font, đường dẫn cục bộ và outline thô vẫn ở máy này.</p>
    {error && <ErrorBox error={error} retry={reload} />}{notice && <p className="provider-notice" role="status">{notice}</p>}
    {loading && !snapshot && <Loading label="Đang tải trạng thái provider…" />}
    <div className="vfk-core-note"><span className="core-note-mark">VF</span><div><small>LÕI CỤC BỘ · LUÔN BẬT</small><b>VFK system engine</b><p>Quy tắc, ánh xạ glyph, contour và kiểm định chạy tại máy; VFK phối hợp với provider AI đã chọn trong toàn bộ quy trình VER.</p></div><StatusTag tone="good">Luôn bật</StatusTag></div>
    <div className="provider-grid">
      <article className="provider-card">
        <div className="provider-card-head"><span className="provider-mark openai">AI</span><StatusTag tone={providerStatusTone(chatgpt)}>{providerStatusLabel(chatgpt)}</StatusTag></div>
        <p className="provider-kind">SIGN IN WITH CHATGPT · PLAN</p><h3>OpenAI / ChatGPT</h3>
        <p>{chatgpt?.accountLabel ? "Đăng nhập: " + chatgpt.accountLabel : "Đăng nhập ChatGPT để dùng quyền truy cập theo gói tài khoản."}</p>
        {chatgpt?.status === "connected" ? renderProviderControls(chatgpt, "chatgpt") :
          <button type="button" className="provider-action" disabled={!!action} onClick={() => void connectChatGpt()}>{action === "chatgpt" ? "Đang mở đăng nhập…" : "Sign in with ChatGPT"}</button>}
        {chatgpt?.errorCode && <small className="provider-error-code">Mã trạng thái: {chatgpt.errorCode}</small>}
      </article>
      <article className="provider-card">
        <div className="provider-card-head"><span className="provider-mark ollama">OL</span><StatusTag tone={providerStatusTone(ollama)}>{providerStatusLabel(ollama)}</StatusTag></div>
        <p className="provider-kind">OLLAMA CLOUD · API KEY</p><h3>Ollama Cloud</h3>
        <p>{ollama?.status === "connected" ? (ollama.accountLabel || "Đã lưu khóa ở backend.") : "Nhập API key để kết nối tài khoản Ollama Cloud."}</p>
        {ollama?.status === "connected" ? renderProviderControls(ollama, "ollama_cloud") :
          <form className="provider-key-form" onSubmit={connectOllama}>
            <input type="password" value={apiKey} onChange={event => setApiKey(event.target.value)} autoComplete="off" spellCheck={false} aria-label="Ollama Cloud API key" placeholder="Ollama Cloud API key" />
            <button type="submit" className="provider-action" disabled={!!action || !apiKey.trim()}>{action === "ollama_cloud" ? "Đang kiểm tra…" : "Kết nối bằng API key"}</button>
          </form>}
        {ollama?.errorCode && <small className="provider-error-code">Mã trạng thái: {ollama.errorCode}</small>}
      </article>
    </div>
    <p className="provider-footnote">ChatGPT dùng đăng nhập OAuth theo gói, không phải khóa API của OpenAI Platform. API key Ollama được gửi trực tiếp tới backend và xóa khỏi biểu mẫu sau khi gửi.</p>
  </section>;
}

function ProviderModelChooser({ provider, onSelect }: { provider: AiProviderStatus; onSelect: (modelId: string) => void }) {
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
    <summary>{provider.selectedModelId ? "Mô hình: " + provider.selectedModelId : "Chọn model"}</summary>
    {loading && <small>Đang tải mô hình…</small>}{error && <small className="model-error">{error}</small>}
    {!loading && loaded && models.length === 0 && <small>Provider chưa trả về model nào.</small>}
    {!loading && models.length > 0 && <select aria-label={"Chọn model cho " + provider.id} value={provider.selectedModelId || ""} onChange={event => { if (event.target.value) onSelect(event.target.value); }}>
      <option value="" disabled>Chọn mô hình…</option>{models.map(model => <option key={model.id} value={model.id}>{model.displayName}</option>)}
    </select>}
  </details>;
}

function NewProjectPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError("");
    if (!file) { setError("Chọn một file TTF hoặc OTF trước."); return; }
    if (!/\.(ttf|otf)$/i.test(file.name)) { setError("Chỉ nhận file .ttf hoặc .otf."); return; }
    setBusy(true);
    try {
      const project = await createProject(name.trim() || file.name.replace(/\.(ttf|otf)$/i, ""));
      await uploadSource(project.id, file);
      const job = await startAnalysis(project.id);
      navigate("/projects/" + project.id + "?job=" + encodeURIComponent(job.id));
    } catch (e) { setError(getError(e)); setBusy(false); }
  };
  return <section className="page narrow">
    <AppLink to="/projects" className="back-link">← Tất cả dự án</AppLink>
    <p className="eyebrow">NEW PROJECT / 01</p><h1>Tạo dự án font</h1><p className="lede">Tải font nguồn lên. Hệ thống lưu file cục bộ, đọc metadata và kiểm tra glyph tiếng Việt.</p>
    <form className="panel form-stack" onSubmit={submit}>
      <label>Tên dự án <input value={name} onChange={e => setName(e.target.value)} placeholder="Ví dụ: Instrument Serif Việt hóa" /></label>
      <label className="dropzone"><input type="file" accept=".ttf,.otf,font/ttf,font/otf" onChange={e => setFile(e.target.files?.[0] || null)} />
        <span className="drop-icon">↑</span><strong>{file ? file.name : "Chọn font TTF hoặc OTF"}</strong><small>{file ? (file.size / 1024 / 1024).toFixed(2) + " MB" : "Tối đa 50 MiB · fontTools pipeline"}</small>
      </label>
      {error && <ErrorBox error={error} />}
      <div className="button-row"><Button type="submit" kind="primary" disabled={busy}>{busy ? "Đang tải và phân tích…" : "Tạo dự án & phân tích"}</Button><AppLink to="/projects" className="button quiet">Hủy</AppLink></div>
      <p className="fine-print">Dự án chạy một người dùng trên máy này. File font được lưu trong workspace cục bộ.</p>
    </form>
  </section>;
}

function ProjectPage({ projectId, query }: { projectId: string; query: URLSearchParams }) {

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [jobId, setJobId] = useState(query.get("job") || "");
  const [busy, setBusy] = useState(false);
  const ai = useAiReadiness();
  const hasLoaded = useRef(false);
  const reload = useCallback(() => {
    if (!hasLoaded.current) setLoading(true);
    setError("");
    getProject(projectId).then(next => { hasLoaded.current = true; setProject(next); })
      .catch(e => setError(getError(e))).finally(() => setLoading(false));
  }, [projectId]);
  useEffect(() => { reload(); }, [reload]);
  const initialVariants = async () => {
    if (!ai.ready) { setError("Kết nối provider AI và chọn model trước khi tạo VER."); return; }
    setBusy(true); setError("");
    try { const job = await startVariants(projectId, { mode: "generate_initial" }); setJobId(job.id); }
    catch (e) { setError(getError(e)); }
    finally { setBusy(false); }
  };
  if (loading) return <Loading />;
  if (error && !project) return <section className="page"><ErrorBox error={error} retry={reload} /></section>;
  if (!project) return <section className="page"><ErrorBox error="Không tìm thấy dự án." /></section>;
  const analysis = project.analysis;
  const missing = analysis?.coverage?.missing || [];
  const unsupported = analysis?.supportedForGeneration === false;
  return <section className="page">
    <div className="crumb"><AppLink to="/projects">Dự án</AppLink><span>/</span><b>{project.name}</b></div>
    <div className="page-heading"><div><p className="eyebrow">PROJECT / {project.id.slice(0, 8)}</p><h1>{project.name}</h1><p className="lede">{project.sourceFont?.filename || "Chưa có font nguồn"}</p></div><StatusTag>{project.status}</StatusTag></div>
    {jobId && <JobWatch jobId={jobId} onDone={reload} />}
    {error && <ErrorBox error={error} retry={reload} />}
    {project.activeJobs.filter(job => job.id !== jobId).map(job => <JobWatch key={job.id} jobId={job.id} onDone={reload} />)}
    <div className="workflow-grid">
      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">01 / ANALYSIS</p><h2>Phân tích font</h2></div><StatusTag tone={analysis ? "good" : "warn"}>{analysis ? "hoàn tất" : project.sourceFont ? "chưa phân tích" : "chưa upload"}</StatusTag></div>
        {analysis ? <>
          <div className="metric-grid"><div><strong>{analysis.coverage?.presentCount ?? "—"}</strong><small>glyph Việt đã có</small></div><div><strong>{missing.length}</strong><small>glyph cần xử lý</small></div><div><strong>{analysis.unitsPerEm ?? "—"}</strong><small>units per em</small></div></div>
          <p className="mini-copy">{analysis.family || "Font"} · {analysis.subfamily || ""} · {analysis.outlineType || analysis.format}</p>
          {missing.length > 0 && <p className="mini-copy">Thiếu: {missing.slice(0, 24).join(" ")}{missing.length > 24 ? " …" : ""}</p>}
          {analysis.diagnostics?.map((note, i) => <p key={i} className="fine-print">{note}</p>)}
          {unsupported && <ErrorBox error="Font này hiện chưa được hỗ trợ bởi local MVP engine." />}
        </> : <div className="soft-empty">Metadata, coverage và chẩn đoán sẽ xuất hiện sau khi job phân tích hoàn tất.</div>}
      </section>
      <section className="panel">
        <div className="panel-heading"><div><p className="eyebrow">02 / TẠO PHƯƠNG ÁN</p><h2>Phương án</h2></div><span className="count">{project.variants.length}</span></div>
        {project.variants.length > 0 ? <div className="variant-list">{project.variants.map(v => <VariantRow key={v.id} variant={v} projectId={project.id} />)}</div> :
          <div className="soft-empty">Tạo VER 1A, 1B và 1C để so sánh cách đặt dấu.</div>}
        {analysis && <Button kind="primary" onClick={initialVariants} disabled={busy || !ai.ready || unsupported || project.variants.length > 0 || !!project.activeJobs.length}>
          {busy ? "Đang tạo job…" : !ai.ready ? "Cần provider AI + model" : project.variants.length ? "Phương án đã được tạo" : "Tạo VER 1A · 1B · 1C"}
        </Button>}
        {!ai.ready && <p className="provider-gate">{ai.loading ? "Đang kiểm tra provider AI…" : "Tạo VER cần provider AI đã kết nối và model được chọn."} <AppLink to="/projects#providers">Mở cài đặt AI →</AppLink></p>}
      </section>
    </div>
    <div className="panel-heading section-head"><div><p className="eyebrow">03 / QUALITY & BÀN GIAO</p><h2>Tiếp tục quy trình</h2></div></div>
    <div className="action-grid">
      <AppLink to={"/projects/" + project.id + "/validation"} className="action-card"><b>Validation</b><span>Kiểm tra coverage tiếng Việt, Word/Windows và sanitizer.</span><i>→</i></AppLink>
      <AppLink to={"/projects/" + project.id + "/export"} className="action-card"><b>Export</b><span>Chỉ xuất đúng revision đã duyệt và validation đạt.</span><i>→</i></AppLink>
    </div>
  </section>;
}

function VariantRow({ variant, projectId }: { variant: Variant; projectId: string }) {
  const revision = variant.currentRevision;
  const tone = revision?.validation?.status === "passed" && revision.approved ? "good" : "neutral";
  return <div className="variant-row"><div className="variant-label">{variant.label}</div><div className="variant-info"><b>{variant.status}</b><small>{revision?.kind || "chưa có revision"} · {revision?.fontFormat || "preview pending"}</small></div><StatusTag tone={tone}>{revision?.approved ? "đã duyệt" : revision?.validation?.status || "review"}</StatusTag><AppLink to={"/projects/" + projectId + "/variants/" + variant.id} className="tiny-link">Mở →</AppLink></div>;
}

function VariantPage({ projectId, variantId }: { projectId: string; variantId: string }) {
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [message, setMessage] = useState("");
  const [sample, setSample] = useState("ẦẤẨẪẬ ẮẮ ỜỚỢ ơ ư đ Đ\\nNgười Việt dùng font đẹp, đúng dấu.");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [refineJobId, setRefineJobId] = useState("");
  const [refining, setRefining] = useState(false);
  const [error, setError] = useState("");
  const ai = useAiReadiness();
  const load = useCallback(() => getProject(projectId).then(setProject).catch(e => setError(getError(e))), [projectId]);
  useEffect(() => { void load(); }, [load]);
  if (!project) return error ? <section className="page"><ErrorBox error={error} retry={load} /></section> : <Loading />;
  const variant = project.variants.find(v => v.id === variantId);
  if (!variant) return <section className="page"><ErrorBox error="Không tìm thấy phương án." /></section>;
  const revision = variant.currentRevision;
  const family = "vfk-preview-" + variant.id.replace(/[^a-zA-Z0-9]/g, "");
  const saveFeedback = async () => {
    if (!revision) return;
    setBusy(true); setError(""); setSaved(false);
    try {
      await createReview(variant.id, { revisionId: revision.id, message, glyphEditIds: [] });
      setSaved(true);
    } catch (e) { setError(getError(e)); }
    finally { setBusy(false); }
  };
  const runRefinement = async () => {
    if (!ai.ready) { setError("Kết nối provider AI và chọn model trước khi yêu cầu tinh chỉnh."); return; }
    if (!revision || !message.trim()) return;
    setBusy(true); setError(""); setRefining(true);
    try {
      const job = await startVariantRefinement(variant.id, revision.id, message.trim());
      setRefineJobId(job.id);
    } catch (e) { setRefining(false); setError(getError(e)); }
    finally { setBusy(false); }
  };
  return <section className="page">
    <div className="crumb"><AppLink to={"/projects/" + projectId}>{project.name}</AppLink><span>/</span><b>VER {variant.label}</b></div>
    <div className="page-heading"><div><p className="eyebrow">VARIANT / DUYỆT</p><h1>VER {variant.label}</h1><p className="lede">So sánh preview, lưu feedback hoặc mở bàn vẽ vector.</p></div>{revision && <StatusTag tone={revision.approved ? "good" : "neutral"}>{revision.status}</StatusTag>}</div>
    {error && <ErrorBox error={error} />}
    {revision?.aiDesign && <section className="ai-design-summary" aria-label="AI design profile">
      <div><p className="eyebrow">HỒ SƠ THIẾT KẾ AI</p><h2>{revision.aiDesign.sourceStyle || "Phong cách nguồn"}</h2></div>
      {revision.aiDesign.rationale && <p>{revision.aiDesign.rationale}</p>}
      {(revision.aiDesign.providerId || revision.aiDesign.modelId) && <small>{revision.aiDesign.providerId || "AI"}{revision.aiDesign.modelId ? " · " + revision.aiDesign.modelId : ""}</small>}
    </section>
    }
    {refineJobId && <JobWatch jobId={refineJobId} onDone={() => { setRefining(false); void load(); }} />}
    {revision?.previewUrl && <style>{'@font-face{font-family:"' + family + '";src:url("' + revision.previewUrl + '");font-display:swap}'}</style>}
    <div className="review-layout">
      <div className="panel preview-panel">
        <div className="panel-heading"><div><p className="eyebrow">LIVE PDUYỆT</p><h2>So mẫu tiếng Việt</h2></div><Button kind="quiet" onClick={() => navigate("/projects/" + projectId + "/variants/" + variant.id + "/editor")}>Mở editor ↗</Button></div>
        <textarea className="sample-input" value={sample} onChange={e => setSample(e.target.value)} aria-label="Nội dung mẫu" />
        <div className="font-preview" style={{ fontFamily: revision?.previewUrl ? '"' + family + '", sans-serif' : "inherit" }}>{sample}</div>
      </div>
      <div className="panel form-stack">
        <p className="eyebrow">DUYỆT / NOTES</p><h2>Ghi góp ý</h2>
        <label>Feedback<textarea value={message} onChange={e => setMessage(e.target.value)} rows={5} placeholder="Ví dụ: dấu hỏi chữ ẩ thấp hơn; giữ độ rộng hiện tại…" /></label>
        <Button kind="primary" onClick={() => void saveFeedback()} disabled={busy || !revision}>{busy ? "Đang lưu…" : "Lưu feedback"}</Button>
        {saved && <StatusTag tone="good">feedback đã lưu</StatusTag>}
        {!ai.ready && <p className="provider-gate">{ai.loading ? "Đang kiểm tra provider AI…" : "Tinh chỉnh AI cần provider đã kết nối và model được chọn."} <AppLink to="/projects#providers">Mở cài đặt AI →</AppLink></p>}
        <Button kind="primary" onClick={() => void runRefinement()} disabled={busy || refining || !ai.ready || !revision || !message.trim()}>{refining ? "Đang gửi yêu cầu tinh chỉnh…" : !ai.ready ? "Cần provider AI + model" : "Gửi feedback để AI tinh chỉnh"}</Button>
        <Button onClick={() => navigate("/projects/" + projectId + "/variants/" + variant.id + "/editor")}>Mở bàn vẽ vector</Button>
        <Button kind="quiet" onClick={() => navigate("/projects/" + projectId + "/validation?variantId=" + variant.id)}>Validation revision →</Button>
        <p className="fine-print">Feedback được lưu trong project. Vector edits nằm trên revision nháp riêng.</p>
      </div>
    </div>
  </section>;
}

function EditorPage({ projectId, variantId, query }: { projectId: string; variantId: string; query: URLSearchParams }) {
  const navigate = useNavigate();
  const registerEditorFlush = useRegisterEditorFlush();
  const [project, setProject] = useState<Project | null>(null);
  const [revision, setRevision] = useState<Revision | null>(null);
  const [doc, setDoc] = useState<Awaited<ReturnType<typeof getEditorDocument>> | null>(null);
  const [feedback, setFeedback] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saveState, setSaveState] = useState<"saved" | "saving" | "error">("saved");
  const flushRef = useRef<(() => Promise<void>) | null>(null);
  useEffect(() => {
    registerEditorFlush(() => flushRef.current ? flushRef.current() : Promise.resolve());
    return () => registerEditorFlush(null);
  }, [registerEditorFlush]);
  const load = useCallback(async () => {
    setError("");
    try {
      const p = await getProject(projectId);
      setProject(p);
      const v = p.variants.find(item => item.id === variantId);
      if (!v?.currentRevisionId) throw new Error("Phương án chưa có revision để mở editor.");
      const requested = query.get("revisionId");
      let current: Revision;
      if (requested) current = await getRevision(requested);
      else {
        current = await createRevision(v.id, v.currentRevisionId);
        const url = new URL(window.location.href);
        url.searchParams.set("revisionId", current.id);
        window.history.replaceState({}, "", url.toString());
      }
      setRevision(current);
      setDoc(await getEditorDocument(current.id));
    } catch (e) { setError(getError(e)); }
  }, [projectId, variantId, query]);
  useEffect(() => { void load(); }, [load]);
  const submitManualBuild = async () => {
    if (!revision) return;
    setBusy(true); setError("");
    try {
      await flushRef.current?.();
      const latestDoc = await getEditorDocument(revision.id);

      const edits = latestDoc.edits.filter(item => item.touched || item.note || item.strokes?.length).map(item => ({
        kind: item.kind, id: item.targetId || item.id || ""
      })).filter(item => item.id);
      await createReview(variantId, { revisionId: revision.id, message: feedback, glyphEditIds: edits });
      const job = await startVariants(projectId, {
        mode: "apply_manual_edits", baseRevisionId: revision.id, variantId
      });
      navigate("/projects/" + projectId + "?job=" + encodeURIComponent(job.id));
    } catch (e) { setError(getError(e)); }
    finally { setBusy(false); }
  };
  if (error && !project) return <section className="page"><ErrorBox error={error} retry={() => void load()} /></section>;
  if (!project || !revision || !doc) return error ? <section className="page"><ErrorBox error={error} retry={() => void load()} /></section> : <Loading label="Đang mở bàn vẽ và tải contours…" />;
  const variant = project.variants.find(item => item.id === variantId);
  return <section className="page editor-page">
    <div className="crumb"><AppLink to={"/projects/" + projectId}>{project.name}</AppLink><span>/</span><AppLink to={"/projects/" + projectId + "/variants/" + variantId}>VER {variant?.label || ""}</AppLink><span>/</span><b>Bàn vẽ vector</b></div>
    <div className="page-heading editor-heading"><div><p className="eyebrow">VECTOR WORKSPACE / DRAFT {revision.id.slice(0, 8)}</p><h1>Chỉnh sửa glyph</h1><p className="lede">Đường vector, dấu và nét cọ lưu trên revision nháp; bản gốc không bị ghi đè.</p></div><StatusTag tone={saveState === "error" ? "bad" : saveState === "saving" ? "warn" : "good"}>{saveState === "saving" ? "đang lưu" : saveState === "error" ? "lỗi lưu" : "đã lưu"}</StatusTag></div>
    {error && <ErrorBox error={error} />}
    <GlyphEditorFrame revisionId={revision.id} document={doc} onFlushReady={fn => { flushRef.current = fn; }} onSaveState={setSaveState} />
    <div className="panel form-stack editor-submit"><label>Feedback cho revision<textarea value={feedback} onChange={e => setFeedback(e.target.value)} rows={3} placeholder="Ghi chú thay đổi cho revision này…" /></label>
      <div className="button-row"><Button kind="primary" disabled={busy || saveState === "saving"} onClick={() => void submitManualBuild()}>{busy ? "Đang build…" : "Lưu bản vẽ & build revision"}</Button><Button kind="quiet" onClick={() => navigate("/projects/" + projectId + "/variants/" + variantId)}>Quay lại preview</Button></div>
      <p className="fine-print">Undo/redo thuộc phiên editor; contours và nét cọ tham chiếu được lưu theo glyph. Nét cọ không xuất vào outline font.</p>
    </div>
  </section>;
}

function ValidationPage({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [selected, setSelected] = useState(new URLSearchParams(window.location.search).get("variantId") || "");
  const [jobId, setJobId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const load = useCallback(() => getProject(projectId).then(p => {
    setProject(p);
    setSelected(old => old || p.variants[0]?.id || "");
  }).catch(e => setError(getError(e))), [projectId]);
  useEffect(() => { void load(); }, [load]);
  if (!project) return error ? <section className="page"><ErrorBox error={error} retry={load} /></section> : <Loading />;
  const variant = project.variants.find(v => v.id === selected);
  const revision = variant?.currentRevision;
  const run = async () => {
    if (!variant || !revision) return;
    setBusy(true); setError("");
    try { const job = await startValidation(variant.id, revision.id); setJobId(job.id); }
    catch (e) { setError(getError(e)); } finally { setBusy(false); }
  };
  const approve = async () => {
    if (!variant || !revision) return;
    setBusy(true); setError("");
    try { await approveRevision(variant.id, revision.id); await load(); }
    catch (e) { setError(getError(e)); } finally { setBusy(false); }
  };
  const passed = revision?.validation?.status === "passed";
  return <section className="page">
    <div className="crumb"><AppLink to={"/projects/" + projectId}>{project.name}</AppLink><span>/</span><b>Validation</b></div>
    <div className="page-heading"><div><p className="eyebrow">QUALITY / 04</p><h1>Kiểm tra revision</h1><p className="lede">Kết quả gắn với revision cụ thể.</p></div></div>
    {error && <ErrorBox error={error} />}{jobId && <JobWatch jobId={jobId} onDone={load} />}
    <div className="panel form-stack"><label>Phương án<select value={selected} onChange={e => setSelected(e.target.value)}>{project.variants.map(v => <option key={v.id} value={v.id}>{v.label}</option>)}</select></label>
      <div className="panel-heading"><h2>{revision ? "Revision " + revision.id.slice(0, 8) : "Chưa có revision"}</h2>{revision && <StatusTag tone={passed ? "good" : "warn"}>{revision.validation?.status || "chưa kiểm tra"}</StatusTag>}</div>
      {revision?.validation?.checks?.length ? <div className="check-list">{revision.validation.checks.map((c,i)=><div className="check-row" key={c.id || i}><StatusTag tone={c.status==="passed"?"good":c.status==="failed"?"bad":"warn"}>{c.status}</StatusTag><div><b>{c.id}</b><small>{c.detail}</small></div></div>)}</div> : <div className="soft-empty">Chưa có kết quả QA cho revision này.</div>}
      <div className="button-row"><Button kind="primary" disabled={busy || !revision} onClick={() => void run()}>{busy ? "Đang tạo job…" : "Chạy validation"}</Button><Button disabled={busy || !revision || !passed || revision.approved} onClick={() => void approve()}>{revision?.approved ? "Revision đã duyệt" : "Duyệt revision"}</Button>{revision && <Button kind="quiet" onClick={() => navigate("/projects/" + projectId + "/export?variantId=" + variant?.id + "&revisionId=" + revision.id)}>Tới export →</Button>}</div>
    </div>
  </section>;
}

function ExportPage({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<Project | null>(null);
  const [variantId, setVariantId] = useState("");
  const [revisionId, setRevisionId] = useState("");

  const [name, setName] = useState("");
  const [jobId, setJobId] = useState("");
  const [artifact, setArtifact] = useState<ExportArtifact | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => getProject(projectId).then(p => {
    setProject(p);
    const params = new URLSearchParams(window.location.search);
    const wanted = params.get("variantId") || p.variants[0]?.id || "";
    const v = p.variants.find(item => item.id === wanted) || p.variants[0];
    setVariantId(v?.id || "");
    setRevisionId(params.get("revisionId") || v?.currentRevisionId || "");
    if (v?.currentRevision && !name) setName("VFK-" + p.name.replace(/\\s+/g, "-"));
  }).catch(e => setError(getError(e))), [projectId, name]);
  useEffect(() => { void load(); }, [load]);
  if (!project) return error ? <section className="page"><ErrorBox error={error} retry={load} /></section> : <Loading />;
  const variant = project.variants.find(v => v.id === variantId);
  const revision = variant?.revisions.find(r => r.id === revisionId);
  const rawFormat = revision?.fontFormat?.toLowerCase();
  const format: "ttf" | "otf" | null = rawFormat === "ttf" || rawFormat === "otf" ? rawFormat : null;
  const eligible = !!revision?.approved && revision.validation?.status === "passed" && revision.status === "ready" && !!format;
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!variant || !revision || !format) return;
    setBusy(true); setError(""); setArtifact(null);
    try { const job = await startExport(projectId, { variantId: variant.id, revisionId: revision.id, format, name }); setJobId(job.id); }
    catch (e) { setError(getError(e)); } finally { setBusy(false); }
  };
  const finished = async (job: Job) => {
    if (job.status === "succeeded" && job.resultId) {
      try { setArtifact(await getExport(job.resultId)); } catch (e) { setError(getError(e)); }
    }
    await load();
  };
  return <section className="page narrow">
    <div className="crumb"><AppLink to={"/projects/" + projectId}>{project.name}</AppLink><span>/</span><b>Export</b></div>
    <div className="page-heading"><div><p className="eyebrow">BUILD / 05</p><h1>Xuất font</h1><p className="lede">Chỉ revision đã duyệt và validation đạt mới được xuất.</p></div></div>
    {error && <ErrorBox error={error} />}{jobId && <JobWatch jobId={jobId} onDone={finished} />}
    {artifact && <div className="download-card"><StatusTag tone="good">file sẵn sàng</StatusTag><b>{artifact.filename}</b><a className="download-link" href={artifact.downloadUrl}>Tải {artifact.format.toUpperCase()} ↓</a></div>}
    <form className="panel form-stack" onSubmit={submit}>
      <label>Phương án<select value={variantId} onChange={e => { setVariantId(e.target.value); const v=project.variants.find(x=>x.id===e.target.value); setRevisionId(v?.currentRevisionId || ""); }}>{project.variants.map(v=><option key={v.id} value={v.id}>VER {v.label}</option>)}</select></label>
      <label>Revision<select value={revisionId} onChange={e=>setRevisionId(e.target.value)}>{(variant?.revisions || []).map(r=><option key={r.id} value={r.id}>{r.id.slice(0,8)} · {r.kind} · {r.status}</option>)}</select></label>
      <div className="gate-card"><StatusTag tone={eligible?"good":"warn"}>{eligible?"đủ điều kiện":"chưa đủ điều kiện"}</StatusTag><span>{eligible ? "Được duyệt · QA đạt · revision sẵn sàng" : "Cần approval và validation passed cho chính revision này."}</span></div>
      <label>Tên file<input value={name} onChange={e=>setName(e.target.value)} required /></label>
      <label>Định dạng<select value={format || ""} disabled><option value={format || ""}>{format ? format.toUpperCase() : "Chưa xác định"}</option></select><small className="field-hint">Định dạng lấy từ revision đã build.</small></label>
      <Button type="submit" kind="primary" disabled={busy || !eligible}>{busy?"Đang tạo export job…":"Build & export font"}</Button>
    </form>
  </section>;
}

export default App;
