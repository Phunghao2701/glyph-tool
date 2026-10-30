export type JobStatus = "queued" | "running" | "succeeded" | "completed" | "failed" | "cancelled";
export type JobKind = "analyze" | "generate_initial" | "build_revision" | "validate" | "export" | string;

export interface ApiErrorBody {
  code?: string;
  message: string;
  retryable?: boolean;
  blockers?: string[];
  currentVersion?: number | null;
}

export class ApiError extends Error {
  status: number;
  body?: ApiErrorBody;
  constructor(message: string, status: number, body?: ApiErrorBody) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export interface Job {
  id: string;
  kind: JobKind;
  status: JobStatus;
  progressPct: number;
  currentStep: string;
  error?: ApiErrorBody | null;
  resultId?: string | null;
  updatedAt?: string;
}

export interface SourceFont {
  filename: string;
  format: string;
  downloadUrl?: string;
  sizeBytes?: number;
}

export interface AnalysisReport {
  format?: string;
  family?: string;
  subfamily?: string;
  unitsPerEm?: number;
  glyphCount?: number;
  outlineType?: string;
  isItalic?: boolean;
  isMonospace?: boolean;
  hasMarkAnchors?: boolean;
  supportedForGeneration?: boolean;
  missingBaseGlyphs?: string[];
  diagnostics?: string[];
  coverage?: {
    requiredCount?: number;
    presentCount?: number;
    missing?: string[];
    percent?: number;
  };
  metrics?: Record<string, number>;
}

export interface ValidationCheck {
  id: string;
  status: "passed" | "failed" | "skipped" | "warning" | string;
  detail?: string;
}

export interface ValidationResult {
  status: "passed" | "failed" | "running" | string;
  checks?: ValidationCheck[];
}

export interface AiDesign {
  sourceStyle?: string | null;
  providerId?: string | null;
  modelId?: string | null;
  rationale?: string | null;
  parameters?: Record<string, number>;
}

export interface Revision {
  id: string;
  variantId: string;
  baseRevisionId?: string | null;
  kind: string;
  status: string;
  aiDesign?: AiDesign | null;
  fontFormat?: string | null;
  previewUrl?: string | null;
  validation?: ValidationResult | null;
  approved: boolean;
  approvedAt?: string | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface Variant {
  id: string;
  label: string;
  status: string;
  currentRevisionId?: string | null;
  currentRevision?: Revision | null;
  revisions: Revision[];
}

export interface Project {
  id: string;
  name: string;
  status: string;
  sourceFont?: SourceFont | null;
  analysis?: AnalysisReport | null;
  variants: Variant[];
  activeJobs: Job[];
  canExport?: boolean;
  exportBlockers?: string[];
  createdAt?: string;
  updatedAt?: string;
}

export type Point = [number, number];
export type PathOp = ["M" | "L" | "C" | "Q", Point[]];
export type Contour = PathOp[];
export interface BrushStroke { w: number; pts: Point[] }

export interface GlyphEdit {
  revisionId?: string;
  kind: "glyph" | "mark";
  id?: string;
  targetId?: string;
  key?: string;
  w: number;
  touched: boolean;
  note: string;
  contours: Contour[];
  strokes: BrushStroke[];
  layer?: [number, number, number, number, number, number] | null;
  version: number;
  updatedAt?: string;
}

export interface FvGlyph { u: number; w: number; c: Contour[] }
export interface FvRecipe {
  u: number;
  w: number;
  s: Contour[];
  m: Array<{ m: string; t: [number, number, number, number, number, number] }>;
  sax?: [number, number];
}
export interface FvDocument {
  upm: number;
  xh: number;
  cap: number;
  asc: number;
  desc: number;
  lbAsc?: number;
  lbDesc?: number;
  axis?: number;
  tildeW?: number;
  glyphs: Record<string, FvGlyph>;
  marks: Record<string, Contour[]>;
  recipes: Record<string, FvRecipe>;
  kern?: Record<string, Record<string, number>>;
}
export interface EditorDocument {
  revisionId: string;
  baseRevisionId?: string | null;
  document: { fv: FvDocument } | FvDocument;
  edits: GlyphEdit[];
}
export type AiProviderId = "chatgpt" | "ollama_cloud";
export type AiProviderState = "disconnected" | "connected" | "needs_reconnect" | "error";
export interface AiProviderStatus {
  id: AiProviderId;
  status: AiProviderState;
  accountLabel?: string | null;
  selectedModelId?: string | null;
  authMode: "chatgpt_plan_oauth" | "api_key";
  errorCode?: string | null;
}
export interface AiProviders {
  selectedProviderId: AiProviderId | null;
  providers: AiProviderStatus[];
}
export interface AiProviderModel { id: string; displayName: string }
export interface ExportArtifact {
  id: string;
  variantId: string;
  revisionId: string;
  format: string;
  filename: string;
  downloadUrl: string;
}

const API_ROOT = import.meta.env.VITE_API_BASE_URL || "/api";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const response = await fetch(API_ROOT + path, { ...init, headers, credentials: "same-origin" });
  const raw = await response.text();
  let payload: unknown = null;
  if (raw) {
    try { payload = JSON.parse(raw); } catch { payload = raw; }
  }
  if (!response.ok) {
    const value = payload && typeof payload === "object" ? payload as { detail?: unknown; error?: unknown; message?: string } : {};
    const detail = value.detail ?? value.error;
    const body = detail && typeof detail === "object" ? detail as ApiErrorBody :
      typeof detail === "string" ? { message: detail } :
      value.message ? { message: value.message } : undefined;
    throw new ApiError(body?.message || response.statusText || "Yêu cầu thất bại.", response.status, body);
  }
  return payload as T;
}

function unwrapItems<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  if (value && typeof value === "object") {
    const record = value as { items?: T[]; data?: { items?: T[] } };
    return record.items ?? record.data?.items ?? [];
  }
  return [];
}

export async function listProjects(): Promise<Project[]> {
  return unwrapItems<Project>(await request<unknown>("/projects"));
}
export async function getProject(projectId: string): Promise<Project> {
  return request<Project>("/projects/" + encodeURIComponent(projectId));
}
export async function createProject(name: string): Promise<Project> {
  return request<Project>("/projects", { method: "POST", body: JSON.stringify({ name }) });
}
export async function uploadSource(projectId: string, file: File): Promise<SourceFont> {
  const form = new FormData();
  form.append("file", file);
  return request<SourceFont>("/projects/" + encodeURIComponent(projectId) + "/source", { method: "POST", body: form });
}
export async function startAnalysis(projectId: string): Promise<Job> {
  return request<Job>("/projects/" + encodeURIComponent(projectId) + "/analysis-jobs", { method: "POST", body: JSON.stringify({}) });
}
const inFlightJobs = new Map<string, Promise<Job>>();
export function getJob(jobId: string): Promise<Job> {
  const pending = inFlightJobs.get(jobId);
  if (pending) return pending;
  const requestPromise = request<Job>("/jobs/" + encodeURIComponent(jobId)).finally(() => {
    if (inFlightJobs.get(jobId) === requestPromise) inFlightJobs.delete(jobId);
  });
  inFlightJobs.set(jobId, requestPromise);
  return requestPromise;
}
export async function startVariants(projectId: string, input: {
  mode: "generate_initial" | "apply_manual_edits";
  baseRevisionId?: string;
  variantId?: string;
}): Promise<Job> {
  return request<Job>("/projects/" + encodeURIComponent(projectId) + "/variants", { method: "POST", body: JSON.stringify(input) });
}
export async function createRevision(variantId: string, baseRevisionId: string): Promise<Revision> {
  return request<Revision>("/variants/" + encodeURIComponent(variantId) + "/revisions", {
    method: "POST", body: JSON.stringify({ baseRevisionId, kind: "manual-edit" })
  });
}
export async function getRevision(revisionId: string): Promise<Revision> {
  return request<Revision>("/revisions/" + encodeURIComponent(revisionId));
}
export async function getEditorDocument(revisionId: string): Promise<EditorDocument> {
  return request<EditorDocument>("/revisions/" + encodeURIComponent(revisionId) + "/editor-document");
}
export async function saveGlyphEdit(revisionId: string, edit: {
  kind: "glyph" | "mark"; id: string; expectedVersion: number | null; w: number; touched: boolean;
  note: string; contours: Contour[]; strokes: BrushStroke[]; layer?: number[] | null;
}): Promise<GlyphEdit> {
  return request<GlyphEdit>("/revisions/" + encodeURIComponent(revisionId) + "/glyph-edits/" +
    encodeURIComponent(edit.kind) + "/" + encodeURIComponent(edit.id), { method: "PUT", body: JSON.stringify(edit) });
}
export async function createReview(variantId: string, input: {
  revisionId: string; message: string; glyphEditIds: Array<{ kind: "glyph" | "mark"; id: string }>;
}): Promise<{ id: string }> {
  return request<{ id: string }>("/variants/" + encodeURIComponent(variantId) + "/reviews", {
    method: "POST", body: JSON.stringify(input)
  });
}
export async function startVariantRefinement(variantId: string, revisionId: string, message: string): Promise<Job> {
  return request<Job>("/variants/" + encodeURIComponent(variantId) + "/refine-jobs", {
    method: "POST", body: JSON.stringify({ revisionId, message })
  });
}
export async function startValidation(variantId: string, revisionId: string): Promise<Job> {
  return request<Job>("/variants/" + encodeURIComponent(variantId) + "/validation-jobs", {
    method: "POST", body: JSON.stringify({ revisionId })
  });
}
export interface ApprovalResult {
  variantId: string;
  revisionId: string;
  approved: boolean;
  approvedAt?: string | null;
}
export async function approveRevision(variantId: string, revisionId: string): Promise<ApprovalResult> {
  return request<ApprovalResult>("/variants/" + encodeURIComponent(variantId) + "/approval", {
    method: "POST", body: JSON.stringify({ revisionId, approved: true })
  });
}
export async function startExport(projectId: string, input: {
  variantId: string; revisionId: string; format: "ttf" | "otf"; name: string;
}): Promise<Job> {
  return request<Job>("/projects/" + encodeURIComponent(projectId) + "/exports", {
    method: "POST", body: JSON.stringify(input)
  });
}
export async function getExport(exportId: string): Promise<ExportArtifact> {
  return request<ExportArtifact>("/exports/" + encodeURIComponent(exportId));
}

let inFlightProviders: Promise<AiProviders> | null = null;
export function getAiProviders(): Promise<AiProviders> {
  if (inFlightProviders) return inFlightProviders;
  const pending = request<AiProviders>("/providers");
  const tracked = pending.finally(() => { if (inFlightProviders === tracked) inFlightProviders = null; });
  inFlightProviders = tracked;
  return tracked;
}

export async function startChatGptConnect(): Promise<{ authorizationUrl: string }> {
  return request<{ authorizationUrl: string }>("/providers/chatgpt/connect", { method: "POST", body: JSON.stringify({}) });
}
export async function connectOllamaCloud(apiKey: string): Promise<AiProviderStatus> {
  return request<AiProviderStatus>("/providers/ollama_cloud/connect", {
    method: "POST", body: JSON.stringify({ apiKey })
  });
}
export async function getAiProviderModels(providerId: AiProviderId): Promise<AiProviderModel[]> {
  const response = await request<{ models: AiProviderModel[] }>("/providers/" + encodeURIComponent(providerId) + "/models");
  return response.models || [];
}
export async function selectAiProviderModel(providerId: AiProviderId, modelId: string): Promise<AiProviderStatus> {
  return request<AiProviderStatus>("/providers/" + encodeURIComponent(providerId) + "/model", {
    method: "PUT", body: JSON.stringify({ modelId })
  });
}
export async function selectAiProvider(providerId: AiProviderId): Promise<AiProviders> {
  return request<AiProviders>("/providers/selection", { method: "PUT", body: JSON.stringify({ providerId }) });
}
export async function disconnectAiProvider(providerId: AiProviderId): Promise<AiProviderStatus> {
  return request<AiProviderStatus>("/providers/" + encodeURIComponent(providerId) + "/connection", { method: "DELETE" });
}
