export type JobStatus = "queued" | "running" | "cancelling" | "succeeded" | "completed" | "failed" | "cancelled";
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
  projectId?: string;
  revisionId?: string | null;
  kind: JobKind;
  label?: string;
  status: JobStatus;
  progressPct: number;
  currentStep: string;
  payload?: Record<string, unknown>;
  error?: ApiErrorBody | null;
  resultId?: string | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface Review {
  id: string;
  variantId: string;
  revisionId: string;
  message: string;
  glyphEditIds: Array<{ kind: "glyph" | "mark"; id: string }>;
  decision: string;
  createdAt?: string;
}

export interface AppSetting { key: string; value: unknown }

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
  coverage?: {
    requiredCount?: number;
    presentCount?: number;
    missing?: string[];
    percent?: number;
  };
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
  projectId?: string;
  variantId: string;
  revisionId: string;
  format: string;
  filename: string;
  downloadUrl: string;
  createdAt?: string;
}

const API_ROOT = import.meta.env.VITE_API_BASE_URL || "/api";

export function getSourceFontUrl(projectId: string): string {
  return API_ROOT + "/projects/" + encodeURIComponent(projectId) + "/source";
}

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
export async function updateProject(projectId: string, name: string): Promise<Project> {
  return request<Project>("/projects/" + encodeURIComponent(projectId), { method: "PUT", body: JSON.stringify({ name }) });
}
export async function deleteProject(projectId: string): Promise<void> {
  return request<void>("/projects/" + encodeURIComponent(projectId), { method: "DELETE" });
}
export async function uploadSource(projectId: string, file: File): Promise<SourceFont> {
  const form = new FormData();
  form.append("file", file);
  return request<SourceFont>("/projects/" + encodeURIComponent(projectId) + "/source", { method: "POST", body: form });
}
export async function replaceSource(projectId: string, file: File): Promise<SourceFont> {
  const form = new FormData();
  form.append("file", file);
  return request<SourceFont>("/projects/" + encodeURIComponent(projectId) + "/source", { method: "PUT", body: form });
}
export async function deleteSource(projectId: string): Promise<void> {
  return request<void>("/projects/" + encodeURIComponent(projectId) + "/source", { method: "DELETE" });
}
export async function getAnalysis(projectId: string): Promise<{ projectId: string; report: AnalysisReport }> {
  return request<{ projectId: string; report: AnalysisReport }>("/projects/" + encodeURIComponent(projectId) + "/analysis");
}
export async function updateAnalysis(projectId: string, report: AnalysisReport): Promise<{ projectId: string; report: AnalysisReport }> {
  return request<{ projectId: string; report: AnalysisReport }>("/projects/" + encodeURIComponent(projectId) + "/analysis", {
    method: "PUT", body: JSON.stringify({ report }),
  });
}
export async function deleteAnalysis(projectId: string): Promise<void> {
  return request<void>("/projects/" + encodeURIComponent(projectId) + "/analysis", { method: "DELETE" });
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
export async function listJobs(projectId?: string): Promise<Job[]> {
  const query = projectId ? "?project_id=" + encodeURIComponent(projectId) : "";
  return unwrapItems<Job>(await request<unknown>("/jobs" + query));
}
export async function createJob(input: {
  projectId: string; kind: "analyze" | "generate_initial" | "build_revision" | "refine_variant" | "validate" | "export";
  revisionId?: string; variantId?: string; format?: "ttf" | "otf"; name?: string; message?: string; label?: string;
}): Promise<Job> {
  return request<Job>("/jobs", { method: "POST", body: JSON.stringify(input) });
}
export async function updateJob(jobId: string, input: { label?: string; action?: "cancel" }): Promise<Job> {
  return request<Job>("/jobs/" + encodeURIComponent(jobId), { method: "PATCH", body: JSON.stringify(input) });
}
export async function retryJob(jobId: string): Promise<Job> {
  return request<Job>("/jobs/" + encodeURIComponent(jobId) + "/retry", { method: "POST", body: JSON.stringify({}) });
}
export async function deleteJob(jobId: string): Promise<{ deleted: boolean; id?: string; job?: Job }> {
  return request<{ deleted: boolean; id?: string; job?: Job }>("/jobs/" + encodeURIComponent(jobId), { method: "DELETE" });
}
export async function startVariants(projectId: string, input: {
  mode: "generate_initial" | "apply_manual_edits";
  baseRevisionId?: string;
  variantId?: string;
}): Promise<Job> {
  return request<Job>("/projects/" + encodeURIComponent(projectId) + "/variants", { method: "POST", body: JSON.stringify(input) });
}
export async function getVariant(variantId: string): Promise<Variant> {
  return request<Variant>("/variants/" + encodeURIComponent(variantId));
}
export async function updateVariant(variantId: string, label: string): Promise<Variant> {
  return request<Variant>("/variants/" + encodeURIComponent(variantId), { method: "PUT", body: JSON.stringify({ label }) });
}
export async function deleteVariant(variantId: string): Promise<void> {
  return request<void>("/variants/" + encodeURIComponent(variantId), { method: "DELETE" });
}
export async function listVariants(projectId: string): Promise<Variant[]> {
  return unwrapItems<Variant>(await request<unknown>("/projects/" + encodeURIComponent(projectId) + "/variants"));
}
export async function createRevision(variantId: string, baseRevisionId: string): Promise<Revision> {
  return request<Revision>("/variants/" + encodeURIComponent(variantId) + "/revisions", {
    method: "POST", body: JSON.stringify({ baseRevisionId, kind: "manual-edit" })
  });
}
export async function getRevision(revisionId: string): Promise<Revision> {
  return request<Revision>("/revisions/" + encodeURIComponent(revisionId));
}
export async function updateRevision(revisionId: string, approved: boolean): Promise<Revision> {
  return request<Revision>("/revisions/" + encodeURIComponent(revisionId), { method: "PUT", body: JSON.stringify({ approved }) });
}
export async function deleteRevision(revisionId: string): Promise<void> {
  return request<void>("/revisions/" + encodeURIComponent(revisionId), { method: "DELETE" });
}
export async function listRevisions(variantId: string): Promise<Revision[]> {
  return unwrapItems<Revision>(await request<unknown>("/variants/" + encodeURIComponent(variantId) + "/revisions"));
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
export async function createGlyphEdit(revisionId: string, edit: {
  kind: "glyph" | "mark"; id: string; w: number; touched: boolean; note: string;
  contours: Contour[]; strokes: BrushStroke[]; layer?: number[] | null;
}): Promise<GlyphEdit> {
  return request<GlyphEdit>("/revisions/" + encodeURIComponent(revisionId) + "/glyph-edits/" + encodeURIComponent(edit.kind) + "/" + encodeURIComponent(edit.id), {
    method: "POST", body: JSON.stringify(edit),
  });
}
export async function getGlyphEdit(revisionId: string, kind: "glyph" | "mark", id: string): Promise<GlyphEdit> {
  return request<GlyphEdit>("/revisions/" + encodeURIComponent(revisionId) + "/glyph-edits/" + encodeURIComponent(kind) + "/" + encodeURIComponent(id));
}
export async function listGlyphEdits(revisionId: string): Promise<GlyphEdit[]> {
  return unwrapItems<GlyphEdit>(await request<unknown>("/revisions/" + encodeURIComponent(revisionId) + "/glyph-edits"));
}
export async function deleteGlyphEdit(revisionId: string, kind: "glyph" | "mark", id: string): Promise<void> {
  return request<void>("/revisions/" + encodeURIComponent(revisionId) + "/glyph-edits/" + encodeURIComponent(kind) + "/" + encodeURIComponent(id), { method: "DELETE" });
}
export async function createReview(variantId: string, input: {
  revisionId: string; message: string; glyphEditIds: Array<{ kind: "glyph" | "mark"; id: string }>;
}): Promise<{ id: string }> {
  return request<{ id: string }>("/variants/" + encodeURIComponent(variantId) + "/reviews", {
    method: "POST", body: JSON.stringify(input)
  });
}
export async function listReviews(variantId: string): Promise<Review[]> {
  return unwrapItems<Review>(await request<unknown>("/variants/" + encodeURIComponent(variantId) + "/reviews"));
}
export async function getReview(reviewId: string): Promise<Review> {
  return request<Review>("/reviews/" + encodeURIComponent(reviewId));
}
export async function updateReview(reviewId: string, input: { message: string; glyphEditIds: Review["glyphEditIds"] }): Promise<Review> {
  return request<Review>("/reviews/" + encodeURIComponent(reviewId), { method: "PUT", body: JSON.stringify(input) });
}
export async function deleteReview(reviewId: string): Promise<void> {
  return request<void>("/reviews/" + encodeURIComponent(reviewId), { method: "DELETE" });
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
export async function listExports(projectId?: string): Promise<ExportArtifact[]> {
  const query = projectId ? "?project_id=" + encodeURIComponent(projectId) : "";
  return unwrapItems<ExportArtifact>(await request<unknown>("/exports" + query));
}
export async function updateExport(exportId: string, filename: string): Promise<ExportArtifact> {
  return request<ExportArtifact>("/exports/" + encodeURIComponent(exportId), { method: "PUT", body: JSON.stringify({ filename }) });
}
export async function deleteExport(exportId: string): Promise<void> {
  return request<void>("/exports/" + encodeURIComponent(exportId), { method: "DELETE" });
}

export async function listSettings(): Promise<AppSetting[]> {
  return unwrapItems<AppSetting>(await request<unknown>("/settings"));
}
export async function createSetting(key: string, value: unknown): Promise<AppSetting> {
  return request<AppSetting>("/settings", { method: "POST", body: JSON.stringify({ key, value }) });
}
export async function getSetting(key: string): Promise<AppSetting> {
  return request<AppSetting>("/settings/" + encodeURIComponent(key));
}
export async function updateSetting(key: string, value: unknown): Promise<AppSetting> {
  return request<AppSetting>("/settings/" + encodeURIComponent(key), { method: "PUT", body: JSON.stringify({ value }) });
}
export async function deleteSetting(key: string): Promise<void> {
  return request<void>("/settings/" + encodeURIComponent(key), { method: "DELETE" });
}

let inFlightProviders: Promise<AiProviders> | null = null;
export function getAiProviders(): Promise<AiProviders> {
  if (inFlightProviders) return inFlightProviders;
  const pending = request<AiProviders>("/providers");
  const tracked = pending.finally(() => { if (inFlightProviders === tracked) inFlightProviders = null; });
  inFlightProviders = tracked;
  return tracked;
}

export async function getAiProvider(providerId: AiProviderId): Promise<AiProviderStatus> {
  return request<AiProviderStatus>("/providers/" + encodeURIComponent(providerId));
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
