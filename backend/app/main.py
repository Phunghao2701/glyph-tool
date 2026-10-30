from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import Body, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .db import (
    DATA_ROOT, EXPORTS_ROOT, MAX_UPLOAD_BYTES, PROJECTS_ROOT, db, init_db,
    job_payload, json_load, now, project_payload, revision_payload,
)
from .font_pipeline import analyze_font
from .jobs import create_job, shutdown
from .providers import (
    ProviderError,
    connect_ollama_cloud,
    disconnect_provider,
    get_providers_payload,
    get_selected_provider_config,
    list_provider_models,
    select_model,
    select_provider,
    start_chatgpt_connect,
)

app = FastAPI(title="Việt hóa Font", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.on_event("shutdown")
def stop_workers() -> None:
    shutdown()


class ProjectCreate(BaseModel):
    name: str = Field(default="Font project", min_length=1, max_length=120)


class GenerateRequest(BaseModel):
    mode: Literal["generate_initial", "apply_manual_edits"] = "generate_initial"
    baseRevisionId: str | None = None
    variantId: str | None = None


class RevisionCreate(BaseModel):
    baseRevisionId: str
    kind: Literal["manual-edit"] = "manual-edit"


class GlyphEditBody(BaseModel):
    expectedVersion: int | None = None
    w: float = Field(default=0, ge=0, le=100000)
    touched: bool = True
    note: str = Field(default="", max_length=4000)
    contours: list[Any] = Field(default_factory=list, max_length=1000)
    strokes: list[Any] = Field(default_factory=list, max_length=1000)
    layer: list[float] | None = None


class ReviewBody(BaseModel):
    revisionId: str
    message: str = Field(default="", max_length=8000)
    glyphEditIds: list[dict[str, str]] = Field(default_factory=list, max_length=1000)


class OllamaConnectBody(BaseModel):
    apiKey: str = Field(min_length=8, max_length=4096)


class ProviderSelectionBody(BaseModel):
    providerId: Literal["chatgpt", "ollama_cloud"]


class ProviderModelBody(BaseModel):
    modelId: str = Field(min_length=1, max_length=200)


class RefineBody(BaseModel):
    revisionId: str
    message: str = Field(min_length=1, max_length=8000)


class RevisionRef(BaseModel):
    revisionId: str | None = None


class ApprovalBody(BaseModel):
    revisionId: str
    approved: bool = True


class ExportBody(BaseModel):
    variantId: str
    revisionId: str
    format: Literal["ttf", "otf"]
    name: str = Field(default="", max_length=120)


def _project_or_404(conn, project_id: str):
    row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Project not found")
    return row


def _revision_or_404(conn, revision_id: str):
    row = conn.execute("SELECT * FROM revisions WHERE id=?", (revision_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Revision not found")
    return row


def _provider_result(callback):
    try:
        return callback()
    except ProviderError as exc:
        raise HTTPException(exc.status_code, detail={"code": exc.code, "message": str(exc)}) from exc


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "storage": str(DATA_ROOT)}


@app.get("/api/providers")
def get_ai_providers() -> dict[str, Any]:
    return get_providers_payload()


@app.post("/api/providers/chatgpt/connect")
def connect_chatgpt(request: Request) -> dict[str, str]:
    return _provider_result(lambda: start_chatgpt_connect(request.headers.get("origin")))


@app.post("/api/providers/ollama_cloud/connect")
def connect_ollama(body: OllamaConnectBody) -> dict[str, Any]:
    return _provider_result(lambda: connect_ollama_cloud(body.apiKey))


@app.get("/api/providers/{provider_id}/models")
def get_provider_models(provider_id: Literal["chatgpt", "ollama_cloud"]) -> dict[str, Any]:
    return _provider_result(lambda: {"models": list_provider_models(provider_id)})


@app.put("/api/providers/{provider_id}/model")
def put_provider_model(provider_id: Literal["chatgpt", "ollama_cloud"], body: ProviderModelBody) -> dict[str, Any]:
    return _provider_result(lambda: select_model(provider_id, body.modelId))


@app.put("/api/providers/selection")
def put_provider_selection(body: ProviderSelectionBody) -> dict[str, Any]:
    return _provider_result(lambda: select_provider(body.providerId))


@app.delete("/api/providers/{provider_id}/connection")
def delete_provider_connection(provider_id: Literal["chatgpt", "ollama_cloud"]) -> dict[str, Any]:
    return _provider_result(lambda: disconnect_provider(provider_id))


@app.get("/api/projects")
def list_projects() -> dict[str, Any]:
    with db() as conn:
        ids = conn.execute("SELECT id FROM projects ORDER BY updated_at DESC").fetchall()
        return {"items": [project_payload(conn, row["id"]) for row in ids]}


@app.post("/api/projects", status_code=201)
def create_project(body: ProjectCreate) -> dict[str, Any]:
    project_id = uuid.uuid4().hex
    timestamp = now()
    with db() as conn:
        conn.execute(
            "INSERT INTO projects(id,name,status,created_at,updated_at) VALUES(?,?,?,?,?)",
            (project_id, body.name.strip() or "Font project", "draft", timestamp, timestamp),
        )
        return project_payload(conn, project_id) or {}


@app.get("/api/projects/{project_id}")
def get_project(project_id: str) -> dict[str, Any]:
    with db() as conn:
        result = project_payload(conn, project_id)
        if result is None:
            raise HTTPException(404, "Project not found")
        return result


@app.post("/api/projects/{project_id}/source", status_code=201)
async def upload_source(project_id: str, file: UploadFile = File(...)) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".ttf", ".otf"}:
        raise HTTPException(415, "Upload a .ttf or .otf font.")
    with db() as conn:
        _project_or_404(conn, project_id)
        if conn.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running')", (project_id,)).fetchone():
            raise HTTPException(409, "Wait for the active font job before replacing the source.")
        if conn.execute("SELECT 1 FROM variants WHERE project_id=?", (project_id,)).fetchone():
            raise HTTPException(409, "Create a new project to process a different source font.")
    target_dir = PROJECTS_ROOT / project_id / "source"
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(file.filename or f"source{suffix}").name
    target = target_dir / f"{uuid.uuid4().hex}-{filename}"
    temp = target.with_suffix(target.suffix + ".uploading")
    size = 0
    header = b""
    try:
        with temp.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                if not header:
                    header = chunk[:4]
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, "Font file exceeds the 50 MiB limit.")
                output.write(chunk)
        if size < 12:
            raise HTTPException(400, "Uploaded file is empty or invalid.")
        if suffix == ".otf" and header != b"OTTO":
            raise HTTPException(415, "The file extension is .otf but its header is not CFF OpenType.")
        if suffix == ".ttf" and header not in (b"\x00\x01\x00\x00", b"true"):
            raise HTTPException(415, "The file extension is .ttf but its header is not TrueType.")
        temp.replace(target)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    with db() as conn:
        conn.execute(
            "UPDATE projects SET source_path=?,source_filename=?,source_format=?,analysis_json=NULL,status='uploaded',updated_at=? WHERE id=?",
            (str(target), filename, suffix[1:], now(), project_id),
        )
    return {"projectId": project_id, "filename": filename, "format": suffix[1:], "sizeBytes": size, "status": "uploaded"}


@app.get("/api/projects/{project_id}/source")
def download_source(project_id: str) -> FileResponse:
    with db() as conn:
        project = _project_or_404(conn, project_id)
    if not project["source_path"] or not Path(project["source_path"]).is_file():
        raise HTTPException(404, "Source font not found.")
    return FileResponse(project["source_path"], filename=project["source_filename"] or "source-font")


@app.post("/api/projects/{project_id}/analysis-jobs", status_code=202)
def start_analysis(project_id: str) -> dict[str, Any]:
    with db() as conn:
        project = _project_or_404(conn, project_id)
        if not project["source_path"]:
            raise HTTPException(409, "Upload a font before analysis.")
        active = conn.execute(
            "SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running')",
            (project_id,),
        ).fetchone()
        if active:
            raise HTTPException(409, "A font job is already running for this project.")
        conn.execute("UPDATE projects SET status='analyzing',updated_at=? WHERE id=?", (now(), project_id))
    return create_job(project_id, "analyze", {})


@app.post("/api/projects/{project_id}/variants", status_code=202)
def create_or_build_variants(project_id: str, body: GenerateRequest) -> dict[str, Any]:
    ai_provider = None
    if body.mode == "generate_initial":
        ai_provider = _provider_result(get_selected_provider_config)
        if ai_provider is None:
            raise HTTPException(
                409,
                detail={
                    "code": "AI_PROVIDER_REQUIRED",
                    "message": "Connect an AI provider and select a model before generating VER options. The VFK engine will apply and validate the AI-assisted design locally.",
                },
            )
    with db() as conn:
        project = _project_or_404(conn, project_id)
        if not project["source_path"]:
            raise HTTPException(409, "Upload a font before generation.")
        if conn.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running')", (project_id,)).fetchone():
            raise HTTPException(409, "A font job is already running for this project.")
        if body.mode == "generate_initial":
            if not project["analysis_json"]:
                raise HTTPException(409, "Analyze the font before generation.")
            report = json_load(project["analysis_json"], {})
            if not report.get("supportedForGeneration", False):
                raise HTTPException(422, "This font type is not supported by the local MVP engine.")
            if conn.execute("SELECT 1 FROM variants WHERE project_id=?", (project_id,)).fetchone():
                raise HTTPException(409, "Initial variants already exist.")
            if conn.execute("SELECT 1 FROM jobs WHERE project_id=? AND kind='generate_initial' AND status IN ('queued','running')", (project_id,)).fetchone():
                raise HTTPException(409, "Variant generation is already running.")
            conn.execute("UPDATE projects SET status='generating',updated_at=? WHERE id=?", (now(), project_id))
        else:
            if not body.baseRevisionId or not body.variantId:
                raise HTTPException(422, "baseRevisionId and variantId are required for manual edits.")
            revision = _revision_or_404(conn, body.baseRevisionId)
            if revision["variant_id"] != body.variantId or revision["status"] != "draft":
                raise HTTPException(409, "Manual-edit draft is missing or is not editable.")
            if conn.execute("SELECT 1 FROM jobs WHERE revision_id=? AND status IN ('queued','running')", (body.baseRevisionId,)).fetchone():
                raise HTTPException(409, "A job is already running for this revision.")
            conn.execute("UPDATE revisions SET status='building',updated_at=? WHERE id=?", (now(), body.baseRevisionId))
    if body.mode == "generate_initial":
        ai_snapshot = {
            "providerId": ai_provider[0], "modelId": ai_provider[1], "accountLabel": ai_provider[2],
        }
        return create_job(project_id, "generate_initial", {"aiProvider": ai_snapshot})
    return create_job(project_id, "build_revision", {}, revision_id=body.baseRevisionId)


@app.post("/api/variants/{variant_id}/refine-jobs", status_code=202)
def start_ai_refinement(variant_id: str, body: RefineBody) -> dict[str, Any]:
    feedback = body.message.strip()
    if not feedback:
        raise HTTPException(422, "Enter design feedback before starting an AI refinement.")
    try:
        selected = get_selected_provider_config()
    except ProviderError as exc:
        raise HTTPException(exc.status_code, detail={"code": exc.code, "message": str(exc)}) from exc
    if selected is None:
        raise HTTPException(409, detail={"code": "PROVIDER_NOT_SELECTED", "message": "Select a connected AI provider before asking it to refine a VER option."})
    with db() as conn:
        variant = conn.execute("SELECT * FROM variants WHERE id=?", (variant_id,)).fetchone()
        revision = _revision_or_404(conn, body.revisionId)
        if not variant or revision["variant_id"] != variant_id:
            raise HTTPException(404, "Variant or revision not found.")
        if variant["current_revision_id"] != body.revisionId or revision["status"] != "ready" or not revision["font_path"]:
            raise HTTPException(409, "Refinement requires the current built revision of this variant.")
        project = _project_or_404(conn, variant["project_id"])
        if not project["analysis_json"]:
            raise HTTPException(409, "Analyze the source font before refining a variant.")
        if conn.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running')", (variant["project_id"],)).fetchone():
            raise HTTPException(409, "Wait for the active font job before starting an AI refinement.")
        conn.execute(
            "INSERT INTO reviews(id,variant_id,revision_id,message,glyph_edit_ids_json,decision,created_at) VALUES(?,?,?,?,?,?,?)",
            (uuid.uuid4().hex, variant_id, body.revisionId, feedback, "[]", "changes_requested", now()),
        )
        conn.execute("UPDATE projects SET status='generating',updated_at=? WHERE id=?", (now(), variant["project_id"]))
        project_id = variant["project_id"]
    return create_job(
        project_id,
        "refine_variant",
        {
            "variantId": variant_id, "baseRevisionId": body.revisionId, "feedback": feedback,
            "aiProvider": {"providerId": selected[0], "modelId": selected[1], "accountLabel": selected[2]},
        },
        revision_id=body.revisionId,
    )


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    with db() as conn:
        job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not job:
        raise HTTPException(404, "Job not found.")
    return job_payload(job)


@app.get("/api/variants/{variant_id}/revisions")
def list_revisions(variant_id: str) -> dict[str, Any]:
    with db() as conn:
        if not conn.execute("SELECT 1 FROM variants WHERE id=?", (variant_id,)).fetchone():
            raise HTTPException(404, "Variant not found.")
        rows = conn.execute("SELECT * FROM revisions WHERE variant_id=? ORDER BY created_at", (variant_id,)).fetchall()
        return {"items": [revision_payload(row) for row in rows]}


@app.post("/api/variants/{variant_id}/revisions", status_code=201)
def create_revision(variant_id: str, body: RevisionCreate) -> dict[str, Any]:
    revision_id = uuid.uuid4().hex
    timestamp = now()
    with db() as conn:
        variant = conn.execute("SELECT * FROM variants WHERE id=?", (variant_id,)).fetchone()
        if not variant:
            raise HTTPException(404, "Variant not found.")
        base = _revision_or_404(conn, body.baseRevisionId)
        if base["variant_id"] != variant_id or not base["font_path"]:
            raise HTTPException(409, "Base revision does not belong to this variant.")
        if base["status"] != "ready" or json_load(base["validation_json"], {}).get("status") != "passed":
            raise HTTPException(409, "Only a ready, validated revision can be used as an editor base.")
        conn.execute(
            "INSERT INTO revisions(id,project_id,variant_id,parent_revision_id,kind,status,font_path,editor_document_path,parameters_json,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (revision_id, variant["project_id"], variant_id, base["id"], body.kind, "draft",
             base["font_path"], base["editor_document_path"], base["parameters_json"], timestamp, timestamp),
        )
        return revision_payload(conn.execute("SELECT * FROM revisions WHERE id=?", (revision_id,)).fetchone())


@app.get("/api/revisions/{revision_id}")
def get_revision(revision_id: str) -> dict[str, Any]:
    with db() as conn:
        return revision_payload(_revision_or_404(conn, revision_id))


@app.get("/api/revisions/{revision_id}/editor-document")
def get_editor_document(revision_id: str) -> dict[str, Any]:
    with db() as conn:
        revision = _revision_or_404(conn, revision_id)
        edits = conn.execute("SELECT * FROM glyph_edits WHERE revision_id=? ORDER BY kind,target_id", (revision_id,)).fetchall()
    path = Path(revision["editor_document_path"] or "")
    if not path.is_file():
        raise HTTPException(404, "Editor document not found.")
    document = json.loads(path.read_text(encoding="utf-8"))
    edit_items = [
        {"kind": row["kind"], "targetId": row["target_id"], **json_load(row["body_json"], {}), "version": row["version"]}
        for row in edits
    ]
    return {
        "revisionId": revision_id, "baseRevisionId": revision["parent_revision_id"],
        "fontFormat": Path(revision["font_path"]).suffix.lower().lstrip("."),
        "previewUrl": f"/api/revisions/{revision_id}/preview",
        "document": document, "edits": edit_items,
    }


@app.put("/api/revisions/{revision_id}/glyph-edits/{kind}/{target_id}")
def save_glyph_edit(revision_id: str, kind: Literal["glyph", "mark"], target_id: str, body: GlyphEditBody) -> dict[str, Any]:
    if body.layer is not None and len(body.layer) != 6:
        raise HTTPException(422, "layer must contain six affine values.")
    with db() as conn:
        revision = _revision_or_404(conn, revision_id)
        if revision["status"] != "draft":
            raise HTTPException(409, "Only draft revisions can be edited.")
        doc_path = Path(revision["editor_document_path"] or "")
        document = json.loads(doc_path.read_text(encoding="utf-8")) if doc_path.is_file() else {}
        fv = document.get("fv", document)
        targets = fv.get("glyphs", {}) if kind == "glyph" else fv.get("marks", {})
        if target_id not in targets and not (kind == "glyph" and target_id in fv.get("recipes", {})):
            raise HTTPException(404, "Glyph or mark does not exist in this editor document.")
        old = conn.execute(
            "SELECT version FROM glyph_edits WHERE revision_id=? AND kind=? AND target_id=?",
            (revision_id, kind, target_id),
        ).fetchone()
        current = old["version"] if old else None
        if body.expectedVersion != current:
            raise HTTPException(409, detail={"code": "EDIT_VERSION_CONFLICT", "message": "The edit changed since it was loaded.", "currentVersion": current})
        version = (current or 0) + 1
        snapshot = {
            "w": body.w, "touched": body.touched, "note": body.note,
            "contours": body.contours, "strokes": body.strokes,
            "layer": body.layer, "updatedAt": now(),
        }
        conn.execute(
            "INSERT INTO glyph_edits(revision_id,kind,target_id,body_json,version,updated_at) VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(revision_id,kind,target_id) DO UPDATE SET body_json=excluded.body_json,version=excluded.version,updated_at=excluded.updated_at",
            (revision_id, kind, target_id, json.dumps(snapshot), version, snapshot["updatedAt"]),
        )
        conn.execute("UPDATE revisions SET updated_at=? WHERE id=?", (now(), revision_id))
    return {"revisionId": revision_id, "kind": kind, "id": target_id, **snapshot, "version": version}


@app.delete("/api/revisions/{revision_id}/glyph-edits/{kind}/{target_id}", status_code=204)
def delete_glyph_edit(revision_id: str, kind: Literal["glyph", "mark"], target_id: str) -> None:
    with db() as conn:
        revision = _revision_or_404(conn, revision_id)
        if revision["status"] != "draft":
            raise HTTPException(409, "Only draft revisions can be edited.")
        conn.execute("DELETE FROM glyph_edits WHERE revision_id=? AND kind=? AND target_id=?", (revision_id, kind, target_id))


@app.post("/api/variants/{variant_id}/reviews", status_code=201)
def create_review(variant_id: str, body: ReviewBody) -> dict[str, Any]:
    review_id = uuid.uuid4().hex
    with db() as conn:
        variant = conn.execute("SELECT * FROM variants WHERE id=?", (variant_id,)).fetchone()
        revision = _revision_or_404(conn, body.revisionId)
        if not variant or revision["variant_id"] != variant_id:
            raise HTTPException(404, "Variant or revision not found.")
        conn.execute(
            "INSERT INTO reviews(id,variant_id,revision_id,message,glyph_edit_ids_json,decision,created_at) VALUES(?,?,?,?,?,?,?)",
            (review_id, variant_id, body.revisionId, body.message, json.dumps(body.glyphEditIds), "changes_requested", now()),
        )
    return {"id": review_id, "variantId": variant_id, "revisionId": body.revisionId, "message": body.message, "glyphEditIds": body.glyphEditIds, "decision": "changes_requested"}


@app.post("/api/variants/{variant_id}/validation-jobs", status_code=202)
def start_validation(variant_id: str, body: RevisionRef | None = Body(default=None)) -> dict[str, Any]:
    with db() as conn:
        variant = conn.execute("SELECT * FROM variants WHERE id=?", (variant_id,)).fetchone()
        if not variant:
            raise HTTPException(404, "Variant not found.")
        revision_id = body.revisionId if body and body.revisionId else variant["current_revision_id"]
        revision = _revision_or_404(conn, revision_id)
        if revision["variant_id"] != variant_id or not revision["font_path"]:
            raise HTTPException(409, "Revision does not have a built font.")
        if revision["status"] not in {"ready", "validation_failed"}:
            raise HTTPException(409, "Only a built revision can be validated.")
        if conn.execute("SELECT 1 FROM jobs WHERE revision_id=? AND status IN ('queued','running')", (revision_id,)).fetchone():
            raise HTTPException(409, "A job is already running for this revision.")
        project_id = variant["project_id"]
    return create_job(project_id, "validate", {}, revision_id=revision_id)


@app.post("/api/variants/{variant_id}/approval")
def approve_revision(variant_id: str, body: ApprovalBody) -> dict[str, Any]:
    with db() as conn:
        variant = conn.execute("SELECT * FROM variants WHERE id=?", (variant_id,)).fetchone()
        revision = _revision_or_404(conn, body.revisionId)
        if not variant or revision["variant_id"] != variant_id:
            raise HTTPException(404, "Variant or revision not found.")
        validation = json_load(revision["validation_json"], {})
        if body.approved and revision["status"] != "ready":
            raise HTTPException(409, detail={"code": "REVISION_NOT_READY", "message": "Build this exact revision before approval."})
        if body.approved and validation.get("status") != "passed":
            raise HTTPException(409, detail={"code": "VALIDATION_REQUIRED", "message": "This revision must pass validation before approval."})
        timestamp = now() if body.approved else None
        conn.execute("UPDATE revisions SET approved_at=?,updated_at=? WHERE id=?", (timestamp, now(), body.revisionId))
    return {"variantId": variant_id, "revisionId": body.revisionId, "approved": body.approved, "approvedAt": timestamp}


@app.post("/api/projects/{project_id}/exports", status_code=202)
def start_export(project_id: str, body: ExportBody) -> dict[str, Any]:
    with db() as conn:
        _project_or_404(conn, project_id)
        variant = conn.execute("SELECT * FROM variants WHERE id=? AND project_id=?", (body.variantId, project_id)).fetchone()
        revision = _revision_or_404(conn, body.revisionId)
        if not variant or revision["variant_id"] != body.variantId:
            raise HTTPException(404, "Variant or revision not found.")
        validation = json_load(revision["validation_json"], {})
        blockers = []
        if not revision["approved_at"]:
            blockers.append("Revision has not been approved.")
        if validation.get("status") != "passed":
            blockers.append("Validation has not passed.")
        if revision["status"] != "ready":
            blockers.append("Revision is not ready.")
        if blockers:
            raise HTTPException(409, detail={"code": "EXPORT_BLOCKED", "blockers": blockers})
        if Path(revision["font_path"]).suffix.lower().lstrip(".") != body.format:
            raise HTTPException(422, "Export format must match the built font format.")
    return create_job(
        project_id, "export",
        {"variantId": body.variantId, "revisionId": body.revisionId, "format": body.format, "name": body.name},
        revision_id=body.revisionId,
    )


@app.get("/api/revisions/{revision_id}/preview")
def preview_revision(revision_id: str) -> FileResponse:
    with db() as conn:
        revision = _revision_or_404(conn, revision_id)
    path = Path(revision["font_path"] or "")
    if not path.is_file():
        raise HTTPException(404, "Preview font not found.")
    media = "font/otf" if path.suffix.lower() == ".otf" else "font/ttf"
    return FileResponse(path, media_type=media, filename=path.name)


@app.get("/api/exports/{export_id}")
def get_export(export_id: str) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT * FROM exports WHERE id=?", (export_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Export not found.")
    return {
        "id": row["id"], "variantId": row["variant_id"], "revisionId": row["revision_id"],
        "format": row["format"], "filename": row["filename"],
        "downloadUrl": f"/api/exports/{export_id}/download", "createdAt": row["created_at"],
    }


@app.get("/api/exports/{export_id}/download")
def download_export(export_id: str) -> FileResponse:
    with db() as conn:
        row = conn.execute("SELECT * FROM exports WHERE id=?", (export_id,)).fetchone()
    if not row or not Path(row["file_path"]).is_file():
        raise HTTPException(404, "Export not found.")
    return FileResponse(row["file_path"], filename=row["filename"], media_type="application/octet-stream")


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
