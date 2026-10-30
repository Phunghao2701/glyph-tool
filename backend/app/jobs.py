from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
import shutil

from .ai_design import build_initial_style_profile, refine_variant_style
from .db import EXPORTS_ROOT, PROJECTS_ROOT, db, job_payload, json_load, now
from .font_pipeline import (
    analyze_font,
    apply_editor_edits,
    generate_initial_variants,
    validate_font,
    write_export,
)

log = logging.getLogger("viet-font-tool.jobs")
_POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="font-job")


class JobCancelled(Exception):
    pass


JOB_LABELS = {
    "analyze": "Analyze source font",
    "generate_initial": "Generate VER options",
    "refine_variant": "Refine VER option with AI",
    "build_revision": "Build glyph revision",
    "validate": "Validate font revision",
    "export": "Export font",
}


def _check_cancelled(job_id: str) -> None:
    with db() as conn:
        row = conn.execute("SELECT status,cancel_requested FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not row or row["cancel_requested"] or row["status"] in {"cancelling", "cancelled"}:
        raise JobCancelled()


def _finish_cancelled(job_id: str, project_id: str, revision_id: str | None) -> None:
    update_job(job_id, status="cancelled", current_step="Cancelled", error_json=None)
    with db() as conn:
        if revision_id:
            conn.execute(
                "UPDATE revisions SET status='draft',updated_at=? WHERE id=? AND status='building'",
                (now(), revision_id),
            )
        project = conn.execute("SELECT source_path,analysis_json FROM projects WHERE id=?", (project_id,)).fetchone()
        if project:
            has_variants = conn.execute("SELECT 1 FROM variants WHERE project_id=? LIMIT 1", (project_id,)).fetchone()
            fallback_status = "review_required" if has_variants else (
                "analysis_ready" if project["analysis_json"] else "uploaded" if project["source_path"] else "draft"
            )
            conn.execute(
                "UPDATE projects SET status=CASE WHEN status IN ('analyzing','generating') THEN ? ELSE status END,updated_at=? WHERE id=?",
                (fallback_status, now(), project_id),
            )


def update_job(job_id: str, **values: Any) -> None:
    allowed = {"status", "progress_pct", "current_step", "result_id", "error_json"}
    patch = {key: value for key, value in values.items() if key in allowed}
    if not patch:
        return
    patch["updated_at"] = now()
    sql = ", ".join(f"{key}=?" for key in patch)
    with db() as conn:
        if patch.get("status") == "cancelled":
            conn.execute(
                f"UPDATE jobs SET {sql} WHERE id=? AND status NOT IN ('succeeded','failed')",
                (*patch.values(), job_id),
            )
        else:
            conn.execute(
                f"UPDATE jobs SET {sql} WHERE id=? AND status NOT IN ('cancelled','succeeded','failed','cancelling') AND cancel_requested=0",
                (*patch.values(), job_id),
            )


def create_job(
    project_id: str,
    kind: str,
    payload: dict[str, Any],
    revision_id: str | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    job_id = uuid.uuid4().hex
    timestamp = now()
    safe_label = (label or JOB_LABELS.get(kind, kind.replace("_", " ").title())).strip()[:120]
    with db() as conn:
        conn.execute(
            "INSERT INTO jobs(id,project_id,revision_id,kind,status,progress_pct,current_step,payload_json,label,created_at,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (job_id, project_id, revision_id, kind, "queued", 0, "Queued", json.dumps(payload), safe_label, timestamp, timestamp),
        )
    _POOL.submit(_run_job, job_id)
    with db() as conn:
        return job_payload(conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())


def _run_job(job_id: str) -> None:
    with db() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return
        if row["status"] in {"cancelled", "cancelling"} or row["cancel_requested"]:
            conn.execute("UPDATE jobs SET status='cancelled',current_step='Cancelled',updated_at=? WHERE id=?", (now(), job_id))
            return
        job = dict(row)
    update_job(job_id, status="running", current_step="Starting", progress_pct=1)
    project_id = job["project_id"]
    revision_id = job["revision_id"]
    payload = json_load(job["payload_json"], {})

    def progress(percent: int, step: str) -> None:
        _check_cancelled(job_id)
        update_job(job_id, progress_pct=max(0, min(99, int(percent))), current_step=step)

    try:
        _check_cancelled(job_id)
        if job["kind"] == "analyze":
            with db() as conn:
                project = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            report = analyze_font(project["source_path"])
            _check_cancelled(job_id)
            with db() as conn:
                conn.execute(
                    "UPDATE projects SET analysis_json=?,status='analysis_ready',updated_at=? WHERE id=?",
                    (json.dumps(report), now(), project_id),
                )
            result_id = project_id

        elif job["kind"] == "generate_initial":
            with db() as conn:
                project = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            analysis = json_load(project["analysis_json"], {})
            provider_snapshot = payload.get("aiProvider") if isinstance(payload.get("aiProvider"), dict) else None
            selected_provider = (
                str(provider_snapshot.get("providerId")),
                str(provider_snapshot.get("modelId")),
                str(provider_snapshot.get("accountLabel") or ""),
            ) if provider_snapshot else None
            profile = build_initial_style_profile(analysis, selected_provider)
            if profile:
                progress(4, "AI analyzed font measurements and prepared VER design options")
            outputs = generate_initial_variants(
                project["source_path"], project_id,
                PROJECTS_ROOT / project_id / "jobs" / job_id, progress,
                style_profile=profile,
            )
            _check_cancelled(job_id)
            result_id = None
            with db() as conn:
                for output in outputs:
                    variant_id = uuid.uuid4().hex
                    revision_id_new = uuid.uuid4().hex
                    timestamp = now()
                    validation = output.get("validation", {})
                    revision_status = "ready" if validation.get("status") == "passed" else "validation_failed"
                    conn.execute(
                        "INSERT INTO variants(id,project_id,label,status,current_revision_id,created_at) VALUES(?,?,?,?,?,?)",
                        (variant_id, project_id, output["label"], "review_required", revision_id_new, timestamp),
                    )
                    conn.execute(
                        "INSERT INTO revisions(id,project_id,variant_id,parent_revision_id,kind,status,font_path,editor_document_path,parameters_json,validation_json,created_at,updated_at) "
                        "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            revision_id_new, project_id, variant_id, None, "initial",
                            revision_status, output["font_path"], output["editor_document_path"],
                            json.dumps(output.get("parameters", {})), json.dumps(validation), timestamp, timestamp,
                        ),
                    )
                    result_id = revision_id_new
                conn.execute("UPDATE projects SET status='review_required',updated_at=? WHERE id=?", (now(), project_id))

        elif job["kind"] == "refine_variant":
            with db() as conn:
                project = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
                variant = conn.execute(
                    "SELECT * FROM variants WHERE id=? AND project_id=?",
                    (payload["variantId"], project_id),
                ).fetchone()
                base = conn.execute("SELECT * FROM revisions WHERE id=?", (payload["baseRevisionId"],)).fetchone()
            if not project or not variant or not base:
                raise RuntimeError("The variant or revision for this refinement no longer exists.")
            base_parameters = json_load(base["parameters_json"], {})
            prior_profile = base_parameters.get("aiStyleProfile") if isinstance(base_parameters, dict) else None
            analysis = json_load(project["analysis_json"], {})
            label = str(variant["label"])[-1:]
            provider_snapshot = payload.get("aiProvider") if isinstance(payload.get("aiProvider"), dict) else None
            if not provider_snapshot:
                raise RuntimeError("The AI provider selection for this refinement is missing.")
            selected_provider = (
                str(provider_snapshot.get("providerId")),
                str(provider_snapshot.get("modelId")),
                str(provider_snapshot.get("accountLabel") or ""),
            )
            progress(8, "AI is applying the design feedback to this VER option")
            refined_profile = refine_variant_style(
                analysis, f"1{label}", prior_profile, str(payload.get("feedback") or ""), selected_provider,
            )
            outputs = generate_initial_variants(
                project["source_path"], project_id,
                PROJECTS_ROOT / project_id / "jobs" / job_id, progress,
                style_profile=refined_profile, variant_labels=[label],
            )
            _check_cancelled(job_id)
            if len(outputs) != 1:
                raise RuntimeError("The local font engine did not build the refined variant.")
            output = outputs[0]
            new_revision_id = uuid.uuid4().hex
            timestamp = now()
            validation = output.get("validation", {})
            revision_status = "ready" if validation.get("status") == "passed" else "validation_failed"
            parameters = output.get("parameters", {})
            parameters["refinementFeedback"] = str(payload.get("feedback") or "")[:8000]
            with db() as conn:
                conn.execute(
                    "INSERT INTO revisions(id,project_id,variant_id,parent_revision_id,kind,status,font_path,editor_document_path,parameters_json,validation_json,created_at,updated_at) "
                    "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        new_revision_id, project_id, variant["id"], base["id"], "ai-refinement",
                        revision_status, output["font_path"], output["editor_document_path"],
                        json.dumps(parameters, ensure_ascii=False), json.dumps(validation), timestamp, timestamp,
                    ),
                )
                conn.execute(
                    "UPDATE variants SET status='review_required',current_revision_id=? WHERE id=?",
                    (new_revision_id, variant["id"]),
                )
                conn.execute("UPDATE projects SET status='review_required',updated_at=? WHERE id=?", (now(), project_id))
            result_id = new_revision_id

        elif job["kind"] == "build_revision":
            with db() as conn:
                revision = conn.execute("SELECT * FROM revisions WHERE id=?", (revision_id,)).fetchone()
                parent = conn.execute("SELECT * FROM revisions WHERE id=?", (revision["parent_revision_id"],)).fetchone()
                edit_rows = conn.execute(
                    "SELECT kind,target_id,body_json FROM glyph_edits WHERE revision_id=? ORDER BY kind,target_id",
                    (revision_id,),
                ).fetchall()
            edits = [{"kind": r["kind"], "targetId": r["target_id"], **json_load(r["body_json"], {})} for r in edit_rows]
            result = apply_editor_edits(
                parent["font_path"], parent["editor_document_path"], edits,
                PROJECTS_ROOT / project_id / "jobs" / job_id, progress,
            )
            validation = validate_font(result["font_path"], progress)
            _check_cancelled(job_id)
            revision_status = "ready" if validation["status"] == "passed" else "validation_failed"
            with db() as conn:
                conn.execute(
                    "UPDATE revisions SET status=?,font_path=?,editor_document_path=?,validation_json=?,updated_at=? WHERE id=?",
                    (revision_status, result["font_path"], result["editor_document_path"], json.dumps(validation), now(), revision_id),
                )
                conn.execute(
                    "UPDATE variants SET status='review_required',current_revision_id=? WHERE id=?",
                    (revision_id, revision["variant_id"]),
                )
                conn.execute("UPDATE projects SET status='review_required',updated_at=? WHERE id=?", (now(), project_id))
            result_id = revision_id

        elif job["kind"] == "validate":
            with db() as conn:
                revision = conn.execute("SELECT * FROM revisions WHERE id=?", (revision_id,)).fetchone()
            report = validate_font(revision["font_path"], progress)
            _check_cancelled(job_id)
            with db() as conn:
                conn.execute(
                    "UPDATE revisions SET validation_json=?,status=?,updated_at=? WHERE id=?",
                    (json.dumps(report), "ready" if report["status"] == "passed" else "validation_failed", now(), revision_id),
                )
            result_id = revision_id

        elif job["kind"] == "export":
            with db() as conn:
                variant = conn.execute("SELECT * FROM variants WHERE id=? AND project_id=?", (payload["variantId"], project_id)).fetchone()
                revision = conn.execute("SELECT * FROM revisions WHERE id=?", (payload["revisionId"],)).fetchone()
            if not variant or not revision or revision["variant_id"] != variant["id"]:
                raise RuntimeError("The approved export revision or variant no longer exists.")
            validation = json_load(revision["validation_json"], {})
            if not revision["approved_at"] or revision["status"] != "ready" or validation.get("status") != "passed":
                raise RuntimeError("Export blocked because this exact revision is no longer approved and validated.")
            if Path(revision["font_path"]).suffix.lower().lstrip(".") != payload["format"]:
                raise RuntimeError("Export format no longer matches the selected revision.")
            export_id = uuid.uuid4().hex
            output_path, filename = write_export(
                revision["font_path"], EXPORTS_ROOT / project_id / export_id,
                payload["format"], payload.get("name", ""), revision["id"], variant["label"],
            )
            try:
                _check_cancelled(job_id)
            except JobCancelled:
                shutil.rmtree((EXPORTS_ROOT / project_id / export_id).resolve(), ignore_errors=True)
                raise
            with db() as conn:
                conn.execute(
                    "INSERT INTO exports(id,project_id,variant_id,revision_id,format,filename,file_path,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (export_id, project_id, variant["id"], revision["id"], payload["format"], filename, output_path, now()),
                )
                conn.execute("UPDATE projects SET status='exported',updated_at=? WHERE id=?", (now(), project_id))
            result_id = export_id
        else:
            raise RuntimeError(f"Unknown job type: {job['kind']}")

        _check_cancelled(job_id)
        update_job(job_id, status="succeeded", progress_pct=100, current_step="Complete", result_id=result_id)
        with db() as conn:
            final_status = conn.execute("SELECT status FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not final_status or final_status["status"] != "succeeded":
            raise JobCancelled()
    except JobCancelled:
        _finish_cancelled(job_id, project_id, revision_id)
    except Exception as exc:
        with db() as conn:
            current = conn.execute("SELECT status,cancel_requested FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not current or current["cancel_requested"] or current["status"] in {"cancelling", "cancelled"}:
            _finish_cancelled(job_id, project_id, revision_id)
            return
        log.exception("Job %s failed", job_id)
        update_job(
            job_id, status="failed", current_step="Failed",
            error_json=json.dumps({"code": type(exc).__name__, "message": str(exc)[:2000], "retryable": True}),
        )
        if revision_id:
            with db() as conn:
                conn.execute(
                    "UPDATE revisions SET status='failed',updated_at=? WHERE id=? AND status='building'",
                    (now(), revision_id),
                )
        with db() as conn:
            conn.execute("UPDATE projects SET status='needs_attention',updated_at=? WHERE id=?", (now(), project_id))


def shutdown() -> None:
    _POOL.shutdown(wait=False, cancel_futures=True)
