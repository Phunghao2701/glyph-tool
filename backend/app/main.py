from __future__ import annotations

import hashlib
import hmac
import json
import math
import os
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Literal

from fastapi import Body, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import AnyHttpUrl, BaseModel, Field, ValidationError
from starlette.background import BackgroundTask

from .backups import BackupError, backup_exports_to_google_drive, create_export_backup_zip
from .db import (
    DATA_ROOT, EXPORTS_ROOT, MAX_UPLOAD_BYTES, PROJECTS_ROOT, db, init_db,
    job_payload, json_load, now, project_payload, revision_payload,
)
from .export_dedup import find_export_by_identity
from .font_pipeline import analyze_font, export_filename, normalize_export_filename
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
    expose_headers=["Content-Disposition", "X-Backup-File-Count", "X-Backup-Collapsed-Versions", "X-Backup-AI-Assisted"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.on_event("shutdown")
def stop_workers() -> None:
    shutdown()


drive_backup_lock = Lock()
font_discovery_handoff_lock = Lock()


class ProjectCreate(BaseModel):
    name: str = Field(default="Font project", min_length=1, max_length=120)


class FontDiscoveryManifest(BaseModel):
    schema_version: Literal[1]
    source: str = Field(min_length=1, max_length=120)
    source_font_id: str | None = Field(default=None, max_length=240)
    discovery_record_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    family: str = Field(min_length=1, max_length=120)
    format: Literal["ttf", "otf"]
    source_url: AnyHttpUrl
    license_name: str | None = Field(default=None, max_length=160)
    license_url: str | None = Field(default=None, max_length=2048)
    license_status: str = Field(default="unknown", max_length=40)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    coverage: dict[str, Any]
    coverage_classification: dict[str, Any]
    selection_reason: str = Field(min_length=1, max_length=2000)
    candidate_reviewed_by_user: bool
    license_acknowledged_by_user: bool
    source_terms_acknowledged_by_user: bool
    created_at: datetime


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class VariantUpdate(BaseModel):
    label: str = Field(min_length=1, max_length=120)


class AnalysisUpdate(BaseModel):
    report: dict[str, Any]


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


class ReviewUpdate(BaseModel):
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


class RevisionUpdate(BaseModel):
    approved: bool


class ExportBody(BaseModel):
    variantId: str
    revisionId: str
    format: Literal["ttf", "otf"]
    name: str = Field(default="", max_length=120)


class ExportUpdate(BaseModel):
    filename: str = Field(min_length=1, max_length=200)


class DriveBackupBody(BaseModel):
    folderId: str = Field(min_length=10, max_length=200)


class JobCreate(BaseModel):
    projectId: str
    kind: Literal["analyze", "generate_initial", "build_revision", "refine_variant", "validate", "export"]
    revisionId: str | None = None
    variantId: str | None = None
    format: Literal["ttf", "otf"] | None = None
    name: str = Field(default="", max_length=120)
    message: str = Field(default="", max_length=8000)
    label: str | None = Field(default=None, min_length=1, max_length=120)


class JobUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=120)
    action: Literal["cancel"] | None = None


class SettingUpdate(BaseModel):
    value: Any


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


def _variant_or_404(conn, variant_id: str):
    row = conn.execute("SELECT * FROM variants WHERE id=?", (variant_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Variant not found")
    return row


def _review_payload(row) -> dict[str, Any]:
    return {
        "id": row["id"], "variantId": row["variant_id"], "revisionId": row["revision_id"],
        "message": row["message"], "glyphEditIds": json_load(row["glyph_edit_ids_json"], []),
        "decision": row["decision"], "createdAt": row["created_at"],
    }


def _export_payload(row) -> dict[str, Any]:
    return {
        "id": row["id"], "projectId": row["project_id"], "variantId": row["variant_id"],
        "revisionId": row["revision_id"], "format": row["format"], "filename": row["filename"],
        "downloadUrl": f"/api/exports/{row['id']}/download", "createdAt": row["created_at"],
    }


def _remove_child(path: Path, root: Path) -> None:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if resolved_root in resolved_path.parents:
        shutil.rmtree(resolved_path, ignore_errors=True)


def _remove_file_child(path: Path, root: Path) -> None:
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if resolved_root in resolved_path.parents:
        resolved_path.unlink(missing_ok=True)


def _refresh_project_status(conn, project_id: str) -> None:
    project = conn.execute("SELECT source_path,analysis_json FROM projects WHERE id=?", (project_id,)).fetchone()
    if not project:
        return
    has_variants = conn.execute("SELECT 1 FROM variants WHERE project_id=? LIMIT 1", (project_id,)).fetchone()
    status = "review_required" if has_variants else (
        "analysis_ready" if project["analysis_json"] else "uploaded" if project["source_path"] else "draft"
    )
    conn.execute("UPDATE projects SET status=?,updated_at=? WHERE id=?", (status, now(), project_id))


def _require_no_active_project_job(conn, project_id: str) -> None:
    if conn.execute(
        "SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running','cancelling') LIMIT 1",
        (project_id,),
    ).fetchone():
        raise HTTPException(409, "Wait for active font jobs to finish before changing this resource.")


def _clean_export_rows(rows) -> None:
    for row in rows:
        _remove_child(Path(row["file_path"]).parent, EXPORTS_ROOT)


def _set_revision_approval(conn, variant_id: str, revision_id: str, approved: bool) -> dict[str, Any]:
    variant = conn.execute("SELECT * FROM variants WHERE id=?", (variant_id,)).fetchone()
    revision = _revision_or_404(conn, revision_id)
    if not variant or revision["variant_id"] != variant_id:
        raise HTTPException(404, "Variant or revision not found.")
    validation = json_load(revision["validation_json"], {})
    if approved and revision["status"] != "ready":
        raise HTTPException(409, detail={"code": "REVISION_NOT_READY", "message": "Build this exact revision before approval."})
    if approved and validation.get("status") != "passed":
        raise HTTPException(409, detail={"code": "VALIDATION_REQUIRED", "message": "This revision must pass validation before approval."})
    timestamp = now() if approved else None
    conn.execute("UPDATE revisions SET approved_at=?,updated_at=? WHERE id=?", (timestamp, now(), revision_id))
    return {"variantId": variant_id, "revisionId": revision_id, "approved": approved, "approvedAt": timestamp}


def _provider_result(callback):
    try:
        return callback()
    except ProviderError as exc:
        raise HTTPException(exc.status_code, detail={"code": exc.code, "message": str(exc)}) from exc


def _require_font_discovery_bearer(authorization: str | None) -> None:
    expected = os.environ.get("FONT_DISCOVERY_BEARER_TOKEN", "").strip()
    if not expected:
        raise HTTPException(503, "Font Discovery handoff is not configured on this server.")
    scheme, separator, supplied = (authorization or "").partition(" ")
    if not separator or scheme.lower() != "bearer" or not supplied.strip():
        raise HTTPException(401, "A Bearer token is required.", headers={"WWW-Authenticate": "Bearer"})
    if not hmac.compare_digest(supplied.strip().encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(401, "Invalid Bearer token.", headers={"WWW-Authenticate": "Bearer"})


def _validate_font_discovery_selection(manifest: FontDiscoveryManifest) -> None:
    if not manifest.candidate_reviewed_by_user:
        raise HTTPException(422, detail={"code": "CANDIDATE_REVIEW_REQUIRED", "message": "The candidate must be reviewed before handoff."})

    classification = manifest.coverage_classification
    confidence = classification.get("confidence")
    if not (
        classification.get("classification") == "missing"
        and classification.get("fonttools_classification") == "missing"
        and classification.get("ai_classification") == "missing"
        and isinstance(confidence, (int, float))
        and not isinstance(confidence, bool)
        and math.isfinite(float(confidence))
        and confidence >= 0.72
        and confidence <= 1.0
    ):
        raise HTTPException(422, detail={"code": "COVERAGE_CLASSIFICATION_REQUIRED", "message": "AI must confirm missing Vietnamese coverage with at least 72% confidence."})

    try:
        present_value = manifest.coverage["present"]
        required_value = manifest.coverage["required"]
        percent_value = manifest.coverage["percent"]
        if type(present_value) is not int or type(required_value) is not int:
            raise TypeError
        if isinstance(percent_value, bool) or not isinstance(percent_value, (int, float)):
            raise TypeError
        present = present_value
        required = required_value
        percent = float(percent_value)
    except (KeyError, TypeError, ValueError):
        raise HTTPException(422, detail={"code": "INVALID_COVERAGE_REPORT", "message": "Coverage counts are required in the handoff manifest."}) from None
    expected_percent = round(100 * present / required, 1) if required > 0 else 0.0
    if (
        required <= 0 or present < 0 or present >= required or not math.isfinite(percent)
        or percent >= 100 or abs(percent - expected_percent) > 0.1
    ):
        raise HTTPException(422, detail={"code": "INCOMPLETE_COVERAGE_REQUIRED", "message": "Handoff requires measured incomplete Vietnamese coverage."})

    if manifest.license_status != "verified" and not (
        manifest.license_acknowledged_by_user and manifest.source_terms_acknowledged_by_user
    ):
        raise HTTPException(422, detail={"code": "LICENSE_REVIEW_REQUIRED", "message": "Unknown license evidence requires user acknowledgement of the license and source terms."})


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _find_project_with_source_hash(conn, sha256: str) -> str | None:
    rows = conn.execute(
        "SELECT id,source_path FROM projects WHERE source_path IS NOT NULL ORDER BY created_at"
    ).fetchall()
    for row in rows:
        path = Path(row["source_path"])
        if path.is_file() and hmac.compare_digest(_sha256_file(path), sha256):
            return str(row["id"])
    return None


def _ensure_source_analysis_job(project_id: str) -> dict[str, Any] | None:
    with db() as conn:
        project = _project_or_404(conn, project_id)
        if project["analysis_json"]:
            return None
        active_job = conn.execute(
            "SELECT * FROM jobs WHERE project_id=? AND status IN ('queued','running','cancelling') ORDER BY created_at DESC LIMIT 1",
            (project_id,),
        ).fetchone()
        if active_job:
            return job_payload(active_job)
    try:
        return start_analysis(project_id)
    except HTTPException as exc:
        if exc.status_code != 409:
            raise
        with db() as conn:
            active_job = conn.execute(
                "SELECT * FROM jobs WHERE project_id=? AND status IN ('queued','running','cancelling') ORDER BY created_at DESC LIMIT 1",
                (project_id,),
            ).fetchone()
            if active_job:
                return job_payload(active_job)
        raise


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "storage": str(DATA_ROOT)}


@app.get("/api/providers")
def get_ai_providers() -> dict[str, Any]:
    return get_providers_payload()


@app.get("/api/providers/{provider_id}")
def get_ai_provider(provider_id: Literal["chatgpt", "ollama_cloud"]) -> dict[str, Any]:
    payload = get_providers_payload()
    provider = next((item for item in payload["providers"] if item["id"] == provider_id), None)
    if provider is None:
        raise HTTPException(404, "AI provider not found.")
    return provider


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


@app.get("/api/settings")
def list_settings() -> dict[str, Any]:
    with db() as conn:
        rows = conn.execute("SELECT key,value FROM app_settings ORDER BY key").fetchall()
        return {"items": [{"key": row["key"], "value": json_load(row["value"], row["value"])} for row in rows]}


@app.post("/api/settings", status_code=201)
def create_setting(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    key = str(body.get("key", ""))
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,120}", key):
        raise HTTPException(422, "Setting key must be 1–120 letters, numbers, dots, underscores, colons, or hyphens.")
    if "value" not in body:
        raise HTTPException(422, "Setting value is required.")
    value = json.dumps(body["value"], ensure_ascii=False)
    with db() as conn:
        if conn.execute("SELECT 1 FROM app_settings WHERE key=?", (key,)).fetchone():
            raise HTTPException(409, "Setting already exists; use PUT to replace it.")
        conn.execute("INSERT INTO app_settings(key,value) VALUES(?,?)", (key, value))
    return {"key": key, "value": body["value"]}


@app.get("/api/settings/{key}")
def get_setting(key: str) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT key,value FROM app_settings WHERE key=?", (key,)).fetchone()
    if not row:
        raise HTTPException(404, "Setting not found.")
    return {"key": row["key"], "value": json_load(row["value"], row["value"])}


@app.put("/api/settings/{key}")
def update_setting(key: str, body: SettingUpdate) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,120}", key):
        raise HTTPException(422, "Invalid setting key.")
    value = json.dumps(body.value, ensure_ascii=False)
    with db() as conn:
        conn.execute(
            "INSERT INTO app_settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
    return {"key": key, "value": body.value}


@app.delete("/api/settings/{key}", status_code=204)
def delete_setting(key: str) -> None:
    with db() as conn:
        if not conn.execute("SELECT 1 FROM app_settings WHERE key=?", (key,)).fetchone():
            raise HTTPException(404, "Setting not found.")
        conn.execute("DELETE FROM app_settings WHERE key=?", (key,))


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


@app.put("/api/projects/{project_id}")
def update_project(project_id: str, body: ProjectUpdate) -> dict[str, Any]:
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Project name cannot be empty.")
    with db() as conn:
        _project_or_404(conn, project_id)
        conn.execute("UPDATE projects SET name=?,updated_at=? WHERE id=?", (name, now(), project_id))
        return project_payload(conn, project_id) or {}


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: str) -> None:
    with db() as conn:
        _project_or_404(conn, project_id)
        _require_no_active_project_job(conn, project_id)
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    _remove_child(PROJECTS_ROOT / project_id, PROJECTS_ROOT)
    _remove_child(EXPORTS_ROOT / project_id, EXPORTS_ROOT)


@app.post("/api/projects/{project_id}/source", status_code=201)
@app.put("/api/projects/{project_id}/source", status_code=200)
async def upload_source(project_id: str, file: UploadFile = File(...)) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".ttf", ".otf"}:
        raise HTTPException(415, "Upload a .ttf or .otf font.")
    with db() as conn:
        project = _project_or_404(conn, project_id)
        _require_no_active_project_job(conn, project_id)
        if conn.execute("SELECT 1 FROM variants WHERE project_id=?", (project_id,)).fetchone():
            raise HTTPException(409, "Create a new project to process a different source font.")
        previous_source_path = Path(project["source_path"]) if project["source_path"] else None
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
    if previous_source_path:
        _remove_file_child(previous_source_path, PROJECTS_ROOT)
    return {"projectId": project_id, "filename": filename, "format": suffix[1:], "sizeBytes": size, "status": "uploaded"}


@app.post("/api/integrations/font-discovery/handoffs", status_code=202)
async def receive_font_discovery_handoff(
    font: UploadFile = File(...),
    manifest: str = Form(...),
    authorization: str | None = Header(default=None),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
) -> JSONResponse:
    _require_font_discovery_bearer(authorization)
    if len(manifest.encode("utf-8")) > 64 * 1024:
        raise HTTPException(413, "Handoff manifest exceeds the 64 KiB limit.")
    try:
        handoff_manifest = FontDiscoveryManifest.model_validate_json(manifest)
    except ValidationError as exc:
        errors = [
            {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        raise HTTPException(422, detail={"code": "INVALID_HANDOFF_MANIFEST", "errors": errors}) from exc
    _validate_font_discovery_selection(handoff_manifest)

    if not re.fullmatch(r"[a-fA-F0-9]{64}", idempotency_key):
        raise HTTPException(422, detail={"code": "INVALID_IDEMPOTENCY_KEY", "message": "Idempotency-Key must be a SHA-256 hex digest."})

    supplied_name = (font.filename or "").replace("\\", "/")
    filename = Path(supplied_name).name.strip().replace("\x00", "")[:200]
    if not filename:
        filename = f"{handoff_manifest.family}.{handoff_manifest.format}"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".ttf", ".otf"} or suffix[1:] != handoff_manifest.format:
        raise HTTPException(415, "The multipart font extension must match the manifest format (TTF or OTF).")

    staging_dir = PROJECTS_ROOT / ".incoming"
    staging_dir.mkdir(parents=True, exist_ok=True)
    staged_path = staging_dir / f"{uuid.uuid4().hex}.uploading"
    final_path: Path | None = None
    committed = False
    size = 0
    header = b""
    digest = hashlib.sha256()
    try:
        with staged_path.open("wb") as output:
            while chunk := await font.read(1024 * 1024):
                if len(header) < 4:
                    header += chunk[: 4 - len(header)]
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, "Font file exceeds the 50 MiB limit.")
                digest.update(chunk)
                output.write(chunk)
        if size < 12:
            raise HTTPException(400, "Uploaded font is empty or invalid.")
        if handoff_manifest.format == "otf" and header != b"OTTO":
            raise HTTPException(415, "The manifest declares OTF but the font header is not CFF OpenType.")
        if handoff_manifest.format == "ttf" and header not in (b"\x00\x01\x00\x00", b"true"):
            raise HTTPException(415, "The manifest declares TTF but the font header is not TrueType.")
        received_sha256 = digest.hexdigest()
        if not hmac.compare_digest(received_sha256, handoff_manifest.sha256.casefold()):
            raise HTTPException(422, detail={"code": "SHA256_MISMATCH", "message": "Font bytes do not match the manifest SHA-256."})
        expected_idempotency_key = hashlib.sha256(
            f"{handoff_manifest.discovery_record_id}:{received_sha256}".encode()
        ).hexdigest()
        if not hmac.compare_digest(expected_idempotency_key, idempotency_key.casefold()):
            raise HTTPException(422, detail={"code": "IDEMPOTENCY_KEY_MISMATCH", "message": "Idempotency-Key does not match the discovery record and font hash."})

        handoff_id = ""
        project_id = ""
        duplicate = False
        with font_discovery_handoff_lock:
            with db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                existing_request = conn.execute(
                    "SELECT id,idempotency_key,discovery_record_id,sha256,project_id FROM font_discovery_handoffs "
                    "WHERE idempotency_key=? OR discovery_record_id=? LIMIT 1",
                    (idempotency_key.casefold(), handoff_manifest.discovery_record_id),
                ).fetchone()
                if existing_request:
                    if (
                        existing_request["idempotency_key"] != idempotency_key.casefold()
                        or existing_request["discovery_record_id"] != handoff_manifest.discovery_record_id
                        or not hmac.compare_digest(existing_request["sha256"], received_sha256)
                    ):
                        raise HTTPException(409, detail={"code": "IDEMPOTENCY_CONFLICT", "message": "This idempotency key or discovery record ID was already used for a different handoff."})
                    handoff_id = str(existing_request["id"])
                    project_id = str(existing_request["project_id"])
                    duplicate = True
                else:
                    existing_hash = conn.execute(
                        "SELECT id,project_id FROM font_discovery_handoffs WHERE sha256=? ORDER BY created_at LIMIT 1",
                        (received_sha256,),
                    ).fetchone()
                    if existing_hash:
                        project_id = str(existing_hash["project_id"])
                        duplicate = True
                    else:
                        project_id = _find_project_with_source_hash(conn, received_sha256) or ""
                        duplicate = bool(project_id)

                    handoff_id = uuid.uuid4().hex
                    if not duplicate:
                        project_id = uuid.uuid4().hex
                        timestamp = now()
                        target_dir = PROJECTS_ROOT / project_id / "source"
                        target_dir.mkdir(parents=True, exist_ok=True)
                        final_path = target_dir / f"{uuid.uuid4().hex}-{filename}"
                        staged_path.replace(final_path)
                        project_name = handoff_manifest.family.strip()[:120] or filename.rsplit(".", 1)[0][:120]
                        conn.execute(
                            "INSERT INTO projects(id,name,status,source_path,source_filename,source_format,created_at,updated_at) "
                            "VALUES(?,?,?,?,?,?,?,?)",
                            (project_id, project_name, "uploaded", str(final_path), filename,
                             handoff_manifest.format, timestamp, timestamp),
                        )

                    conn.execute(
                        "INSERT INTO font_discovery_handoffs(id,idempotency_key,discovery_record_id,sha256,project_id,manifest_json,status,created_at) "
                        "VALUES(?,?,?,?,?,?,?,?)",
                        (
                            handoff_id, idempotency_key.casefold(), handoff_manifest.discovery_record_id, received_sha256,
                            project_id, json.dumps(handoff_manifest.model_dump(mode="json"), ensure_ascii=False),
                            "duplicate" if duplicate else "accepted", now(),
                        ),
                    )
            committed = True
            analysis_job = _ensure_source_analysis_job(project_id)

        result = {
            "status": "duplicate" if duplicate else "accepted",
            "duplicate": duplicate,
            "handoffId": handoff_id,
            "idempotencyKey": idempotency_key.casefold(),
            "discoveryRecordId": handoff_manifest.discovery_record_id,
            "sha256": received_sha256,
            "projectId": project_id,
            "analysisJob": analysis_job,
        }
        return JSONResponse(status_code=200 if duplicate else 202, content=result)
    except HTTPException:
        if not committed and final_path:
            _remove_child(final_path.parent.parent, PROJECTS_ROOT)
        raise
    except Exception as exc:
        if not committed and final_path:
            _remove_child(final_path.parent.parent, PROJECTS_ROOT)
        raise HTTPException(500, "Unable to accept the font handoff.") from exc
    finally:
        staged_path.unlink(missing_ok=True)
        await font.close()


@app.delete("/api/projects/{project_id}/source", status_code=204)
def delete_source(project_id: str) -> None:
    with db() as conn:
        project = _project_or_404(conn, project_id)
        _require_no_active_project_job(conn, project_id)
        if conn.execute("SELECT 1 FROM variants WHERE project_id=? LIMIT 1", (project_id,)).fetchone():
            raise HTTPException(409, "Delete generated variants before removing this source font.")
        source_path = Path(project["source_path"]) if project["source_path"] else None
        conn.execute(
            "UPDATE projects SET source_path=NULL,source_filename=NULL,source_format=NULL,analysis_json=NULL,status='draft',updated_at=? WHERE id=?",
            (now(), project_id),
        )
    if source_path:
        _remove_file_child(source_path, PROJECTS_ROOT)


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
            "SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running','cancelling')",
            (project_id,),
        ).fetchone()
        if active:
            raise HTTPException(409, "A font job is already running for this project.")
        conn.execute("UPDATE projects SET status='analyzing',updated_at=? WHERE id=?", (now(), project_id))
    return create_job(project_id, "analyze", {})


@app.get("/api/projects/{project_id}/analysis")
def get_analysis(project_id: str) -> dict[str, Any]:
    with db() as conn:
        project = _project_or_404(conn, project_id)
        report = json_load(project["analysis_json"])
    if report is None:
        raise HTTPException(404, "Font analysis has not been created for this project.")
    return {"projectId": project_id, "report": report}


@app.put("/api/projects/{project_id}/analysis")
def update_analysis(project_id: str, body: AnalysisUpdate) -> dict[str, Any]:
    with db() as conn:
        _project_or_404(conn, project_id)
        _require_no_active_project_job(conn, project_id)
        conn.execute("UPDATE projects SET analysis_json=?,updated_at=? WHERE id=?", (json.dumps(body.report), now(), project_id))
    return {"projectId": project_id, "report": body.report}


@app.delete("/api/projects/{project_id}/analysis", status_code=204)
def delete_analysis(project_id: str) -> None:
    with db() as conn:
        project = _project_or_404(conn, project_id)
        _require_no_active_project_job(conn, project_id)
        next_status = "uploaded" if project["source_path"] else "draft"
        conn.execute("UPDATE projects SET analysis_json=NULL,status=?,updated_at=? WHERE id=?", (next_status, now(), project_id))


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
                    "message": "Connect an AI provider and select a model before generating VER options. The font engine will apply and validate the AI-assisted design locally.",
                },
            )
    with db() as conn:
        project = _project_or_404(conn, project_id)
        if not project["source_path"]:
            raise HTTPException(409, "Upload a font before generation.")
        if conn.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running','cancelling')", (project_id,)).fetchone():
            raise HTTPException(409, "A font job is already running for this project.")
        if body.mode == "generate_initial":
            if not project["analysis_json"]:
                raise HTTPException(409, "Analyze the font before generation.")
            report = json_load(project["analysis_json"], {})
            if not report.get("supportedForGeneration", False):
                raise HTTPException(422, "This font type is not supported by the local MVP engine.")
            if conn.execute("SELECT 1 FROM variants WHERE project_id=?", (project_id,)).fetchone():
                raise HTTPException(409, "Initial variants already exist.")
            if conn.execute("SELECT 1 FROM jobs WHERE project_id=? AND kind='generate_initial' AND status IN ('queued','running','cancelling')", (project_id,)).fetchone():
                raise HTTPException(409, "Variant generation is already running.")
            conn.execute("UPDATE projects SET status='generating',updated_at=? WHERE id=?", (now(), project_id))
        else:
            if not body.baseRevisionId or not body.variantId:
                raise HTTPException(422, "baseRevisionId and variantId are required for manual edits.")
            revision = _revision_or_404(conn, body.baseRevisionId)
            variant = _variant_or_404(conn, body.variantId)
            if variant["project_id"] != project_id or revision["variant_id"] != body.variantId or revision["status"] != "draft":
                raise HTTPException(409, "Manual-edit draft is missing or is not editable.")
            if conn.execute("SELECT 1 FROM jobs WHERE revision_id=? AND status IN ('queued','running','cancelling')", (body.baseRevisionId,)).fetchone():
                raise HTTPException(409, "A job is already running for this revision.")
            conn.execute("UPDATE revisions SET status='building',updated_at=? WHERE id=?", (now(), body.baseRevisionId))
    if body.mode == "generate_initial":
        ai_snapshot = {
            "providerId": ai_provider[0], "modelId": ai_provider[1], "accountLabel": ai_provider[2],
        }
        return create_job(project_id, "generate_initial", {"aiProvider": ai_snapshot})
    return create_job(project_id, "build_revision", {}, revision_id=body.baseRevisionId)


@app.get("/api/variants/{variant_id}")
def get_variant(variant_id: str) -> dict[str, Any]:
    with db() as conn:
        variant = _variant_or_404(conn, variant_id)
        project = project_payload(conn, variant["project_id"])
        return next(item for item in project["variants"] if item["id"] == variant_id)


@app.get("/api/projects/{project_id}/variants")
def list_project_variants(project_id: str) -> dict[str, Any]:
    with db() as conn:
        project = project_payload(conn, project_id)
        if project is None:
            raise HTTPException(404, "Project not found.")
        return {"items": project["variants"]}


@app.put("/api/variants/{variant_id}")
def update_variant(variant_id: str, body: VariantUpdate) -> dict[str, Any]:
    label = body.label.strip()
    if not label:
        raise HTTPException(422, "Variant label cannot be empty.")
    with db() as conn:
        variant = _variant_or_404(conn, variant_id)
        _require_no_active_project_job(conn, variant["project_id"])
        conn.execute("UPDATE variants SET label=? WHERE id=?", (label, variant_id))
        project = project_payload(conn, variant["project_id"])
        return next(item for item in project["variants"] if item["id"] == variant_id)


@app.delete("/api/variants/{variant_id}", status_code=204)
def delete_variant(variant_id: str) -> None:
    with db() as conn:
        variant = _variant_or_404(conn, variant_id)
        project_id = variant["project_id"]
        _require_no_active_project_job(conn, project_id)
        exports = conn.execute("SELECT * FROM exports WHERE variant_id=?", (variant_id,)).fetchall()
        conn.execute("DELETE FROM exports WHERE variant_id=?", (variant_id,))
        conn.execute("DELETE FROM variants WHERE id=?", (variant_id,))
        _refresh_project_status(conn, project_id)
    _clean_export_rows(exports)


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
        if conn.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running','cancelling')", (variant["project_id"],)).fetchone():
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


@app.get("/api/projects/{project_id}/jobs")
def list_project_jobs(project_id: str) -> dict[str, Any]:
    with db() as conn:
        _project_or_404(conn, project_id)
        rows = conn.execute("SELECT * FROM jobs WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        return {"items": [job_payload(row) for row in rows]}


@app.get("/api/jobs")
def list_jobs(project_id: str | None = Query(default=None)) -> dict[str, Any]:
    with db() as conn:
        if project_id is not None:
            _project_or_404(conn, project_id)
            rows = conn.execute("SELECT * FROM jobs WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
        return {"items": [job_payload(row) for row in rows]}


@app.patch("/api/jobs/{job_id}")
@app.put("/api/jobs/{job_id}")
def update_job_resource(job_id: str, body: JobUpdate) -> dict[str, Any]:
    if body.label is None and body.action is None:
        raise HTTPException(422, "Provide a job label or a supported action.")
    with db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Job not found.")
        if body.label is not None:
            label = body.label.strip()
            if not label:
                raise HTTPException(422, "Job label cannot be empty.")
            conn.execute("UPDATE jobs SET label=?,updated_at=? WHERE id=?", (label, now(), job_id))
        if body.action == "cancel":
            if row["status"] not in {"queued", "running", "cancelling"}:
                raise HTTPException(409, "Only active jobs can be cancelled.")
            next_status = "cancelled" if row["status"] == "queued" else "cancelling"
            conn.execute(
                "UPDATE jobs SET status=?,cancel_requested=1,current_step=?,updated_at=? WHERE id=?",
                (next_status, "Cancelled" if next_status == "cancelled" else "Cancelling", now(), job_id),
            )
            if next_status == "cancelled":
                _refresh_project_status(conn, row["project_id"])
        updated = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return job_payload(updated)


@app.post("/api/jobs/{job_id}/retry", status_code=202)
def retry_job(job_id: str) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Job not found.")
        if row["status"] not in {"failed", "cancelled"}:
            raise HTTPException(409, "Only failed or cancelled jobs can be retried.")
        if conn.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running','cancelling')", (row["project_id"],)).fetchone():
            raise HTTPException(409, "Another font job is active for this project.")
        project_id, revision_id, kind = row["project_id"], row["revision_id"], row["kind"]
        payload = json_load(row["payload_json"], {})
        retry_label = f"{row['label']} (retry)"[:120]
        if kind == "generate_initial" and conn.execute("SELECT 1 FROM variants WHERE project_id=? LIMIT 1", (project_id,)).fetchone():
            raise HTTPException(409, "Initial VER options already exist; create a new project to retry generation.")
        if kind in {"analyze", "generate_initial", "refine_variant"}:
            conn.execute("UPDATE projects SET status=?,updated_at=? WHERE id=?", ("analyzing" if kind == "analyze" else "generating", now(), project_id))
    return create_job(project_id, kind, payload, revision_id, retry_label)


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Job not found.")
        if row["status"] in {"queued", "running", "cancelling"}:
            next_status = "cancelled" if row["status"] == "queued" else "cancelling"
            conn.execute(
                "UPDATE jobs SET status=?,cancel_requested=1,current_step=?,updated_at=? WHERE id=?",
                (next_status, "Cancelled" if next_status == "cancelled" else "Cancelling", now(), job_id),
            )
            if next_status == "cancelled":
                _refresh_project_status(conn, row["project_id"])
            return {"deleted": False, "job": job_payload(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())}
        conn.execute("DELETE FROM jobs WHERE id=?", (job_id,))
        return {"deleted": True, "id": job_id}


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


@app.put("/api/revisions/{revision_id}")
def update_revision(revision_id: str, body: RevisionUpdate) -> dict[str, Any]:
    with db() as conn:
        revision = _revision_or_404(conn, revision_id)
        result = _set_revision_approval(conn, revision["variant_id"], revision_id, body.approved)
        return {**revision_payload(_revision_or_404(conn, revision_id)), **result}


@app.delete("/api/revisions/{revision_id}", status_code=204)
def delete_revision(revision_id: str) -> None:
    with db() as conn:
        revision = _revision_or_404(conn, revision_id)
        project_id, variant_id = revision["project_id"], revision["variant_id"]
        if conn.execute(
            "SELECT 1 FROM jobs WHERE revision_id=? AND status IN ('queued','running','cancelling') LIMIT 1",
            (revision_id,),
        ).fetchone():
            raise HTTPException(409, "Wait for the active revision job to finish before deleting this revision.")
        if conn.execute("SELECT 1 FROM revisions WHERE parent_revision_id=? LIMIT 1", (revision_id,)).fetchone():
            raise HTTPException(409, "Delete descendant revisions before deleting this revision.")
        exports = conn.execute("SELECT * FROM exports WHERE revision_id=?", (revision_id,)).fetchall()
        conn.execute("DELETE FROM exports WHERE revision_id=?", (revision_id,))
        variant = conn.execute("SELECT current_revision_id FROM variants WHERE id=?", (variant_id,)).fetchone()
        conn.execute("DELETE FROM revisions WHERE id=?", (revision_id,))
        if variant and variant["current_revision_id"] == revision_id:
            fallback = revision["parent_revision_id"]
            if not fallback or not conn.execute("SELECT 1 FROM revisions WHERE id=?", (fallback,)).fetchone():
                latest = conn.execute("SELECT id FROM revisions WHERE variant_id=? ORDER BY created_at DESC LIMIT 1", (variant_id,)).fetchone()
                fallback = latest["id"] if latest else None
            conn.execute("UPDATE variants SET current_revision_id=? WHERE id=?", (fallback, variant_id))
        _refresh_project_status(conn, project_id)
    _clean_export_rows(exports)


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


@app.get("/api/revisions/{revision_id}/glyph-edits/{kind}/{target_id}")
def get_glyph_edit(revision_id: str, kind: Literal["glyph", "mark"], target_id: str) -> dict[str, Any]:
    with db() as conn:
        _revision_or_404(conn, revision_id)
        row = conn.execute(
            "SELECT * FROM glyph_edits WHERE revision_id=? AND kind=? AND target_id=?",
            (revision_id, kind, target_id),
        ).fetchone()
    if not row:
        raise HTTPException(404, "Glyph edit not found.")
    return {
        "revisionId": revision_id, "kind": kind, "id": target_id,
        **json_load(row["body_json"], {}), "version": row["version"], "updatedAt": row["updated_at"],
    }


@app.get("/api/revisions/{revision_id}/glyph-edits")
def list_glyph_edits(revision_id: str) -> dict[str, Any]:
    with db() as conn:
        _revision_or_404(conn, revision_id)
        rows = conn.execute(
            "SELECT * FROM glyph_edits WHERE revision_id=? ORDER BY kind,target_id", (revision_id,),
        ).fetchall()
    return {"items": [
        {
            "revisionId": revision_id, "kind": row["kind"], "id": row["target_id"],
            **json_load(row["body_json"], {}), "version": row["version"], "updatedAt": row["updated_at"],
        }
        for row in rows
    ]}


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


@app.post("/api/revisions/{revision_id}/glyph-edits/{kind}/{target_id}", status_code=201)
def create_glyph_edit(revision_id: str, kind: Literal["glyph", "mark"], target_id: str, body: GlyphEditBody) -> dict[str, Any]:
    if body.expectedVersion is not None:
        raise HTTPException(422, "A new glyph edit must not include expectedVersion.")
    with db() as conn:
        existing = conn.execute(
            "SELECT 1 FROM glyph_edits WHERE revision_id=? AND kind=? AND target_id=?",
            (revision_id, kind, target_id),
        ).fetchone()
        if existing:
            raise HTTPException(409, "Glyph edit already exists; use PUT to update it.")
    return save_glyph_edit(revision_id, kind, target_id, body)


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
    with db() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE id=?", (review_id,)).fetchone()
        return _review_payload(row)


@app.get("/api/variants/{variant_id}/reviews")
def list_reviews(variant_id: str) -> dict[str, Any]:
    with db() as conn:
        _variant_or_404(conn, variant_id)
        rows = conn.execute("SELECT * FROM reviews WHERE variant_id=? ORDER BY created_at DESC", (variant_id,)).fetchall()
        return {"items": [_review_payload(row) for row in rows]}


@app.get("/api/reviews/{review_id}")
def get_review(review_id: str) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE id=?", (review_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Review not found.")
    return _review_payload(row)


@app.put("/api/reviews/{review_id}")
def update_review(review_id: str, body: ReviewUpdate) -> dict[str, Any]:
    with db() as conn:
        row = conn.execute("SELECT * FROM reviews WHERE id=?", (review_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Review not found.")
        revision = _revision_or_404(conn, row["revision_id"])
        if revision["variant_id"] != row["variant_id"]:
            raise HTTPException(409, "Review revision no longer belongs to its variant.")
        conn.execute(
            "UPDATE reviews SET message=?,glyph_edit_ids_json=? WHERE id=?",
            (body.message, json.dumps(body.glyphEditIds), review_id),
        )
        return _review_payload(conn.execute("SELECT * FROM reviews WHERE id=?", (review_id,)).fetchone())


@app.delete("/api/reviews/{review_id}", status_code=204)
def delete_review(review_id: str) -> None:
    with db() as conn:
        if not conn.execute("SELECT 1 FROM reviews WHERE id=?", (review_id,)).fetchone():
            raise HTTPException(404, "Review not found.")
        conn.execute("DELETE FROM reviews WHERE id=?", (review_id,))


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
        if conn.execute("SELECT 1 FROM jobs WHERE revision_id=? AND status IN ('queued','running','cancelling')", (revision_id,)).fetchone():
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
        expected_filename = export_filename(revision["font_path"], body.name)
        existing = find_export_by_identity(
            conn,
            project_id=project_id,
            variant_id=body.variantId,
            revision_id=body.revisionId,
            output_format=body.format,
            filename=expected_filename,
        )
        if existing:
            previous_job = conn.execute(
                "SELECT * FROM jobs WHERE kind='export' AND status='succeeded' AND result_id=? ORDER BY updated_at DESC LIMIT 1",
                (existing["id"],),
            ).fetchone()
            if previous_job:
                return job_payload(previous_job)
        active_jobs = conn.execute(
            "SELECT * FROM jobs WHERE project_id=? AND revision_id=? AND kind='export' "
            "AND status IN ('queued','running') ORDER BY created_at DESC",
            (project_id, body.revisionId),
        ).fetchall()
        for active_job in active_jobs:
            active_payload = json_load(active_job["payload_json"], {})
            active_filename = export_filename(revision["font_path"], active_payload.get("name", ""))
            if (
                active_payload.get("variantId") == body.variantId
                and str(active_payload.get("format", "")).lower() == body.format.lower()
                and normalize_export_filename(active_filename) == normalize_export_filename(expected_filename)
            ):
                return job_payload(active_job)
    return create_job(
        project_id, "export",
        {"variantId": body.variantId, "revisionId": body.revisionId, "format": body.format, "name": body.name},
        revision_id=body.revisionId,
    )


@app.get("/api/projects/{project_id}/exports")
def list_project_exports(project_id: str) -> dict[str, Any]:
    with db() as conn:
        _project_or_404(conn, project_id)
        rows = conn.execute("SELECT * FROM exports WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        return {"items": [_export_payload(row) for row in rows]}


@app.get("/api/exports")
def list_exports(project_id: str | None = Query(default=None)) -> dict[str, Any]:
    with db() as conn:
        if project_id:
            _project_or_404(conn, project_id)
            rows = conn.execute("SELECT * FROM exports WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM exports ORDER BY created_at DESC").fetchall()
        return {"items": [_export_payload(row) for row in rows]}


@app.post("/api/jobs", status_code=202)
def create_job_resource(body: JobCreate) -> dict[str, Any]:
    if body.kind == "analyze":
        job = start_analysis(body.projectId)
    elif body.kind == "generate_initial":
        job = create_or_build_variants(body.projectId, GenerateRequest(mode="generate_initial"))
    elif body.kind == "build_revision":
        if not body.variantId or not body.revisionId:
            raise HTTPException(422, "variantId and revisionId are required for a build_revision job.")
        job = create_or_build_variants(
            body.projectId,
            GenerateRequest(mode="apply_manual_edits", baseRevisionId=body.revisionId, variantId=body.variantId),
        )
    elif body.kind == "refine_variant":
        if not body.variantId or not body.revisionId:
            raise HTTPException(422, "variantId and revisionId are required for a refine_variant job.")
        job = start_ai_refinement(body.variantId, RefineBody(revisionId=body.revisionId, message=body.message))
    elif body.kind == "validate":
        if not body.variantId:
            raise HTTPException(422, "variantId is required for a validate job.")
        job = start_validation(body.variantId, RevisionRef(revisionId=body.revisionId))
    else:
        if not body.variantId or not body.revisionId or not body.format:
            raise HTTPException(422, "variantId, revisionId, and format are required for an export job.")
        job = start_export(
            body.projectId,
            ExportBody(variantId=body.variantId, revisionId=body.revisionId, format=body.format, name=body.name),
        )
    if body.label:
        label = body.label.strip()
        if not label:
            raise HTTPException(422, "Job label cannot be empty.")
        with db() as conn:
            conn.execute("UPDATE jobs SET label=?,updated_at=? WHERE id=?", (label, now(), job["id"]))
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job["id"],)).fetchone()
            return job_payload(row)
    return job


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
    return _export_payload(row)


@app.put("/api/exports/{export_id}")
def update_export(export_id: str, body: ExportUpdate) -> dict[str, Any]:
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", body.filename).strip(" .")
    with db() as conn:
        row = conn.execute("SELECT * FROM exports WHERE id=?", (export_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Export not found.")
        if not filename:
            raise HTTPException(422, "Export filename cannot be empty.")
        suffix = Path(filename).suffix.lower().lstrip(".")
        if suffix and suffix != row["format"]:
            raise HTTPException(422, "Export filename extension must match the generated format.")
        if not suffix:
            filename = f"{filename}.{row['format']}"
        duplicate = None
        if normalize_export_filename(filename) != normalize_export_filename(row["filename"]):
            duplicate = find_export_by_identity(
                conn,
                project_id=row["project_id"],
                variant_id=row["variant_id"],
                revision_id=row["revision_id"],
                output_format=row["format"],
                filename=filename,
                require_file=False,
                exclude_export_id=export_id,
            )
        if duplicate:
            raise HTTPException(
                409,
                detail={
                    "code": "EXPORT_ALREADY_EXISTS",
                    "message": "An export with the same revision, format, and filename already exists.",
                    "exportId": duplicate["id"],
                },
            )
        conn.execute("UPDATE exports SET filename=? WHERE id=?", (filename, export_id))
        return _export_payload(conn.execute("SELECT * FROM exports WHERE id=?", (export_id,)).fetchone())


@app.delete("/api/exports/{export_id}", status_code=204)
def delete_export(export_id: str) -> None:
    with db() as conn:
        row = conn.execute("SELECT * FROM exports WHERE id=?", (export_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Export not found.")
        if conn.execute(
            "SELECT 1 FROM jobs WHERE result_id=? AND status IN ('queued','running','cancelling') LIMIT 1",
            (export_id,),
        ).fetchone():
            raise HTTPException(409, "Wait for the export job to finish before deleting this file.")
        conn.execute("DELETE FROM exports WHERE id=?", (export_id,))
    _remove_file_child(Path(row["file_path"]), EXPORTS_ROOT)
    _remove_child(Path(row["file_path"]).parent, EXPORTS_ROOT)


@app.get("/api/exports/{export_id}/download")
def download_export(export_id: str) -> FileResponse:
    with db() as conn:
        row = conn.execute("SELECT * FROM exports WHERE id=?", (export_id,)).fetchone()
    if not row or not Path(row["file_path"]).is_file():
        raise HTTPException(404, "Export not found.")
    return FileResponse(row["file_path"], filename=row["filename"], media_type="application/octet-stream")


@app.post("/api/backups/download")
def download_exports_backup() -> FileResponse:
    try:
        archive_path, result = create_export_backup_zip()
    except BackupError as exc:
        raise HTTPException(exc.status_code, detail={"code": exc.code, "message": str(exc)}) from exc
    return FileResponse(
        archive_path,
        filename=result["filename"],
        media_type="application/zip",
        headers={
            "X-Backup-File-Count": str(result["fileCount"]),
            "X-Backup-Collapsed-Versions": str(result["collapsedVersions"]),
            "X-Backup-AI-Assisted": "true" if result["aiAssisted"] else "false",
        },
        background=BackgroundTask(_remove_backup_file, archive_path),
    )


@app.post("/api/backups/google-drive")
def upload_exports_backup_to_drive(body: DriveBackupBody, request: Request) -> dict[str, Any]:
    authorization = request.headers.get("authorization", "")
    scheme, _, access_token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not access_token.strip():
        raise HTTPException(401, detail={"code": "GOOGLE_DRIVE_AUTH_REQUIRED", "message": "Select the destination folder again to authorize this backup."})
    try:
        with drive_backup_lock:
            return backup_exports_to_google_drive(body.folderId, access_token)
    except BackupError as exc:
        raise HTTPException(exc.status_code, detail={"code": exc.code, "message": str(exc)}) from exc


def _remove_backup_file(path: Path) -> None:
    path.unlink(missing_ok=True)


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    @app.get("/{frontend_path:path}", include_in_schema=False)
    def frontend_route(frontend_path: str) -> FileResponse:
        if frontend_path == "api" or frontend_path.startswith("api/"):
            raise HTTPException(404, "API route not found.")
        target = (FRONTEND_DIST / frontend_path).resolve()
        if FRONTEND_DIST.resolve() not in target.parents and target != FRONTEND_DIST.resolve():
            raise HTTPException(404, "File not found.")
        if target.is_file():
            return FileResponse(target)
        index = FRONTEND_DIST / "index.html"
        if index.is_file():
            return FileResponse(index, media_type="text/html")
        raise HTTPException(404, "Frontend build not found.")

    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
