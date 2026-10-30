from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("VFK_DATA_DIR", REPO_ROOT / ".data")).resolve()
PROJECTS_ROOT = DATA_ROOT / "projects"
EXPORTS_ROOT = DATA_ROOT / "exports"
DB_PATH = DATA_ROOT / "viet-font-tool.sqlite3"
KIT_ROOT = REPO_ROOT / "backend" / "vendor" / "viet-font-kit"
TOOLS_ROOT = KIT_ROOT / "tools"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_load(value: str | None, fallback: Any = None) -> Any:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


@contextmanager
def db():
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    PROJECTS_ROOT.mkdir(parents=True, exist_ok=True)
    EXPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL,
                source_path TEXT, source_filename TEXT, source_format TEXT,
                analysis_json TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS variants (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                label TEXT NOT NULL, status TEXT NOT NULL, current_revision_id TEXT, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS revisions (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
                parent_revision_id TEXT, kind TEXT NOT NULL, status TEXT NOT NULL,
                font_path TEXT, editor_document_path TEXT, parameters_json TEXT,
                validation_json TEXT, approved_at TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                revision_id TEXT, kind TEXT NOT NULL, status TEXT NOT NULL,
                progress_pct INTEGER NOT NULL DEFAULT 0, current_step TEXT NOT NULL DEFAULT '',
                payload_json TEXT NOT NULL DEFAULT '{}', result_id TEXT, error_json TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS glyph_edits (
                revision_id TEXT NOT NULL REFERENCES revisions(id) ON DELETE CASCADE,
                kind TEXT NOT NULL, target_id TEXT NOT NULL, body_json TEXT NOT NULL,
                version INTEGER NOT NULL, updated_at TEXT NOT NULL,
                PRIMARY KEY (revision_id, kind, target_id)
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY, variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
                revision_id TEXT NOT NULL REFERENCES revisions(id) ON DELETE CASCADE,
                message TEXT NOT NULL DEFAULT '', glyph_edit_ids_json TEXT NOT NULL DEFAULT '[]',
                decision TEXT NOT NULL DEFAULT 'changes_requested', created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS exports (
                id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                variant_id TEXT NOT NULL REFERENCES variants(id) ON DELETE CASCADE,
                revision_id TEXT NOT NULL REFERENCES revisions(id) ON DELETE CASCADE,
                format TEXT NOT NULL, filename TEXT NOT NULL, file_path TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY, value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ai_provider_connections (
                provider_id TEXT PRIMARY KEY, status TEXT NOT NULL, auth_mode TEXT NOT NULL,
                account_label TEXT, account_subject TEXT, client_id TEXT, scopes_json TEXT NOT NULL DEFAULT '[]',
                expires_at REAL, error_code TEXT, selected_model_id TEXT, updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_revisions_variant ON revisions(variant_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_edits_revision ON glyph_edits(revision_id);
            """
        )
        for row in conn.execute("SELECT id FROM jobs WHERE status IN ('queued','running')").fetchall():
            conn.execute(
                "UPDATE jobs SET status='failed',current_step='Interrupted by app restart',error_json=?,updated_at=? WHERE id=?",
                (json.dumps({"code": "APP_RESTARTED", "message": "The local worker stopped before this job finished.", "retryable": True}), now(), row["id"]),
            )


def job_payload(job: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": job["id"], "kind": job["kind"], "status": job["status"],
        "progressPct": job["progress_pct"], "currentStep": job["current_step"],
        "error": json_load(job["error_json"]), "resultId": job["result_id"],
        "updatedAt": job["updated_at"],
    }


def revision_payload(row: sqlite3.Row) -> dict[str, Any]:
    validation = json_load(row["validation_json"])
    parameters = json_load(row["parameters_json"], {})
    font_path = row["font_path"]
    revision_id = row["id"]
    ai_profile = parameters.get("aiStyleProfile") if isinstance(parameters, dict) else None
    ai_variant = parameters.get("aiStyle") if isinstance(parameters, dict) else None
    return {
        "id": revision_id, "variantId": row["variant_id"],
        "baseRevisionId": row["parent_revision_id"], "kind": row["kind"],
        "status": row["status"],
        "fontFormat": Path(font_path).suffix.lower().lstrip(".") if font_path else None,
        "aiDesign": {
            "sourceStyle": ai_profile.get("sourceStyle") if isinstance(ai_profile, dict) else None,
            "providerId": ai_profile.get("providerId") if isinstance(ai_profile, dict) else None,
            "modelId": ai_profile.get("modelId") if isinstance(ai_profile, dict) else None,
            "rationale": ai_variant.get("rationale") if isinstance(ai_variant, dict) else None,
            "parameters": {
                key: ai_variant.get(key) for key in (
                    "dotSquareness", "hookWidthScale", "hookHeightScale", "stackScale",
                    "stackWidthScale", "spacingScale", "hornKerningScale",
                ) if key in ai_variant
            } if isinstance(ai_variant, dict) else {},
        } if isinstance(ai_profile, dict) or isinstance(ai_variant, dict) else None,
        "previewUrl": f"/api/revisions/{revision_id}/preview" if font_path else None,
        "validation": validation, "approved": bool(row["approved_at"]),
        "approvedAt": row["approved_at"], "createdAt": row["created_at"], "updatedAt": row["updated_at"],
    }


def project_payload(conn: sqlite3.Connection, project_id: str) -> dict[str, Any] | None:
    p = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    if not p:
        return None
    variants_out = []
    variants = conn.execute("SELECT * FROM variants WHERE project_id=? ORDER BY created_at,label", (project_id,)).fetchall()
    for variant in variants:
        revisions = conn.execute("SELECT * FROM revisions WHERE variant_id=? ORDER BY created_at", (variant["id"],)).fetchall()
        current = next((r for r in revisions if r["id"] == variant["current_revision_id"]), None)
        variants_out.append({
            "id": variant["id"], "label": variant["label"], "status": variant["status"],
            "currentRevisionId": variant["current_revision_id"],
            "currentRevision": revision_payload(current) if current else None,
            "revisions": [revision_payload(r) for r in revisions],
        })
    jobs = conn.execute(
        "SELECT * FROM jobs WHERE project_id=? AND status IN ('queued','running') ORDER BY created_at",
        (project_id,),
    ).fetchall()
    analysis = json_load(p["analysis_json"])
    can_export = any(
        rev["approved"] and rev["status"] == "ready" and rev["validation"] and rev["validation"].get("status") == "passed"
        for variant in variants_out for rev in variant["revisions"]
    )
    blockers = [] if can_export else (
        ["Generate or import a variant first."] if not variants_out else ["Approve a revision after its validation passes."]
    )
    return {
        "id": p["id"], "name": p["name"], "status": p["status"],
        "sourceFont": {
            "filename": p["source_filename"], "format": p["source_format"],
            "downloadUrl": f"/api/projects/{p['id']}/source",
        } if p["source_path"] else None,
        "analysis": analysis, "variants": variants_out,
        "activeJobs": [job_payload(j) for j in jobs],
        "canExport": can_export, "exportBlockers": blockers,
        "createdAt": p["created_at"], "updatedAt": p["updated_at"],
    }
