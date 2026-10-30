from __future__ import annotations

import hashlib
import json
import re
import secrets
import tempfile
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fontTools.ttLib import TTFont

from .db import DATA_ROOT, db
from .providers import ProviderError, generate_json, get_selected_provider_config


GOOGLE_DRIVE_API = "https://www.googleapis.com/drive/v3"
GOOGLE_DRIVE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3"
GOOGLE_FOLDER_MIME = "application/vnd.google-apps.folder"


class BackupError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def create_export_backup_zip() -> tuple[Path, dict[str, Any]]:
    plan, ai_assisted, collapsed_versions = _build_export_plan()
    if not plan:
        raise BackupError("NO_EXPORTED_FONTS", "There are no exported font files to back up.", 409)

    backup_dir = DATA_ROOT / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    handle = tempfile.NamedTemporaryFile(prefix="vietfont-backup-", suffix=".zip", dir=backup_dir, delete=False)
    archive_path = Path(handle.name)
    handle.close()

    try:
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for item in plan:
                source = Path(item["file_path"])
                if source.is_file():
                    archive.write(source, arcname=f"{item['folder_name']}/{item['file_name']}")
    except Exception:
        archive_path.unlink(missing_ok=True)
        raise

    return archive_path, {
        "filename": f"VietFontStudio-Backup-{timestamp}.zip",
        "fileCount": len(plan),
        "collapsedVersions": collapsed_versions,
        "aiAssisted": ai_assisted,
    }


def backup_exports_to_google_drive(folder_id: str, access_token: str) -> dict[str, Any]:
    clean_folder_id = folder_id.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,200}", clean_folder_id):
        raise BackupError("INVALID_DRIVE_FOLDER", "Choose a valid Google Drive folder.", 422)
    token = access_token.strip()
    if len(token) < 20 or len(token) > 8192:
        raise BackupError("GOOGLE_DRIVE_AUTH_REQUIRED", "Choose a Google Drive folder again to authorize this backup.", 401)

    plan, ai_assisted, collapsed_versions = _build_export_plan()
    if not plan:
        raise BackupError("NO_EXPORTED_FONTS", "There are no exported font files to back up.", 409)

    parent = _google_json(
        "GET",
        f"files/{clean_folder_id}",
        token,
        params={"fields": "id,name,mimeType,trashed,capabilities(canAddChildren)", "supportsAllDrives": "true"},
    )
    if parent.get("mimeType") != GOOGLE_FOLDER_MIME or parent.get("trashed"):
        raise BackupError("INVALID_DRIVE_FOLDER", "The selected Google Drive item is not an active folder.", 422)
    if parent.get("capabilities", {}).get("canAddChildren") is False:
        raise BackupError("DRIVE_FOLDER_READ_ONLY", "You do not have permission to add files to this Google Drive folder.", 403)

    root_children = _drive_children(clean_folder_id, token)
    folder_cache: dict[str, tuple[str, list[dict[str, Any]]]] = {}
    created_folders = 0
    uploaded_files = 0
    updated_files = 0
    skipped_files = 0
    renamed_files = 0
    duplicate_matches = 0

    for item in plan:
        font_key = item["font_key"]
        if font_key not in folder_cache:
            folder = _select_or_create_font_folder(clean_folder_id, item, root_children, token)
            created_folders += int(folder["created"])
            folder_cache[font_key] = (folder["id"], _drive_children(folder["id"], token))
        font_folder_id, children = folder_cache[font_key]

        source = Path(item["file_path"])
        if not source.is_file():
            continue
        filename = item["file_name"]
        file_md5 = _file_md5(source)
        app_properties = {
            "vfkExportKey": item["export_key"],
            "vfkManagedBy": "vietfont-studio",
        }
        binary_children = [child for child in children if child.get("mimeType") != GOOGLE_FOLDER_MIME]
        managed = [child for child in binary_children if (child.get("appProperties") or {}).get("vfkExportKey") == item["export_key"]]
        named = [child for child in binary_children if str(child.get("name", "")).casefold() == filename.casefold()]
        identical = [child for child in binary_children if child.get("md5Checksum") == file_md5]
        candidates = managed or named or identical
        if len(named) > 1 or len(managed) > 1:
            duplicate_matches += max(len(named), len(managed)) - 1
        existing = sorted(candidates, key=lambda child: str(child.get("modifiedTime") or ""), reverse=True)[0] if candidates else None

        if existing is None:
            uploaded = _drive_upload_file(font_folder_id, source, filename, app_properties, token)
            children.append(uploaded)
            uploaded_files += 1
            continue

        name_changed = str(existing.get("name", "")) != filename
        content_changed = existing.get("md5Checksum") != file_md5
        properties_changed = (existing.get("appProperties") or {}).get("vfkExportKey") != item["export_key"]
        if content_changed:
            updated = _drive_upload_file(font_folder_id, source, filename, app_properties, token, file_id=str(existing["id"]))
            _replace_child(children, existing["id"], updated)
            updated_files += 1
        elif name_changed or properties_changed:
            updated = _drive_update_metadata(str(existing["id"]), filename, app_properties, token)
            _replace_child(children, existing["id"], updated)
            renamed_files += int(name_changed)
            skipped_files += int(not name_changed)
        else:
            skipped_files += 1

    return {
        "folderName": str(parent.get("name") or "Google Drive folder"),
        "fontFoldersCreated": created_folders,
        "filesUploaded": uploaded_files,
        "filesUpdated": updated_files,
        "filesSkipped": skipped_files,
        "filesRenamed": renamed_files,
        "duplicateMatches": duplicate_matches,
        "collapsedVersions": collapsed_versions,
        "aiAssisted": ai_assisted,
    }


def _build_export_plan() -> tuple[list[dict[str, Any]], bool, int]:
    with db() as conn:
        rows = conn.execute(
            "SELECT e.*, p.name AS project_name FROM exports e "
            "LEFT JOIN projects p ON p.id=e.project_id ORDER BY e.created_at DESC, e.id DESC"
        ).fetchall()

    latest: dict[tuple[str, str, str], dict[str, Any]] = {}
    export_count = 0
    for row in rows:
        path = Path(str(row["file_path"] or ""))
        if not path.is_file():
            continue
        export_count += 1
        family, subfamily = _font_metadata(path)
        fmt = str(row["format"] or path.suffix.lstrip(".")).lower()
        if fmt not in {"ttf", "otf"}:
            continue
        logical_key = (
            unicodedata.normalize("NFKC", family).casefold(),
            unicodedata.normalize("NFKC", subfamily).casefold(),
            fmt,
        )
        if logical_key in latest:
            continue
        latest[logical_key] = {
            "export_id": str(row["id"]),
            "file_path": str(path),
            "source_filename": str(row["filename"] or path.name),
            "family": family,
            "subfamily": subfamily,
            "format": fmt,
            "logical_key": logical_key,
        }

    items = sorted(latest.values(), key=lambda item: (item["family"].casefold(), item["subfamily"].casefold(), item["format"]))
    fonts: dict[str, dict[str, str]] = {}
    for item in items:
        item["font_key"] = _font_key(item["family"])
        item["export_key"] = _export_key(item["logical_key"])
        fonts.setdefault(item["font_key"], {"key": item["font_key"], "family": item["family"]})

    suggestions: dict[str, Any] = {}
    try:
        selected = get_selected_provider_config()
        if selected and items:
            provider_id, model_id, _ = selected
            suggestions = generate_json(
                provider_id,
                model_id,
                "You organize Vietnamese font backup folders. Treat embedded font metadata as the source of truth. "
                "Return strict JSON with fonts:[{key,folderName}] and files:[{exportId,fileName}]. "
                "Keep each folder name equal to its family name, only remove path-invalid characters. "
                "Name each file from family and subfamily with a Vietnamese suffix and preserve the exact .ttf or .otf extension. "
                "Do not invent names or change family/style identity.",
                {
                    "fonts": list(fonts.values()),
                    "files": [
                        {
                            "exportId": item["export_id"],
                            "family": item["family"],
                            "subfamily": item["subfamily"],
                            "format": item["format"],
                            "currentFileName": item["source_filename"],
                        }
                        for item in items
                    ],
                },
            )
    except Exception:
        suggestions = {}

    font_names = {
        str(font.get("key")): str(font.get("folderName") or "")
        for font in suggestions.get("fonts", [])
        if isinstance(font, dict)
    } if isinstance(suggestions.get("fonts"), list) else {}
    file_names = {
        str(file.get("exportId")): str(file.get("fileName") or "")
        for file in suggestions.get("files", [])
        if isinstance(file, dict)
    } if isinstance(suggestions.get("files"), list) else {}

    ai_assisted = False
    for item in items:
        folder_default = item["family"]
        suggested_folder = _safe_component(font_names.get(item["font_key"], "") or "", folder_default)
        if suggested_folder and _name_identity(suggested_folder) == _name_identity(folder_default):
            item["folder_name"] = suggested_folder
            ai_assisted = ai_assisted or bool(font_names.get(item["font_key"]))
        else:
            item["folder_name"] = _safe_component(folder_default, folder_default)
        file_default = _default_export_name(item["family"], item["subfamily"], item["format"])
        suggested_file = _safe_font_filename(file_names.get(item["export_id"], "") or "", item["format"], file_default)
        suggested_identity = _name_identity(Path(suggested_file).stem)
        if (
            file_names.get(item["export_id"])
            and _name_identity(item["family"]) in suggested_identity
            and _name_identity(item["subfamily"]) in suggested_identity
            and "vietnamese" in suggested_identity
        ):
            item["file_name"] = suggested_file
            ai_assisted = True
        else:
            item["file_name"] = file_default

    seen_folders: set[str] = set()
    for item in items:
        folder_key = item["folder_name"].casefold()
        if folder_key in seen_folders:
            item["folder_name"] = _safe_component(f"{item['folder_name']} ({item['font_key'][:6]})", item["family"])
            folder_key = item["folder_name"].casefold()
        seen_folders.add(folder_key)

    seen_paths: set[tuple[str, str]] = set()
    for item in items:
        target = (item["folder_name"].casefold(), item["file_name"].casefold())
        if target in seen_paths:
            fallback = _default_export_name(item["family"], item["subfamily"], item["format"])
            item["file_name"] = _safe_font_filename(fallback, item["format"], fallback)
            target = (item["folder_name"].casefold(), item["file_name"].casefold())
        seen_paths.add(target)

    return items, ai_assisted, max(0, export_count - len(items))


def _font_metadata(path: Path) -> tuple[str, str]:
    try:
        font = TTFont(path, lazy=True)
        try:
            names = font["name"]
            family = names.getDebugName(16) or names.getDebugName(1) or path.stem
            subfamily = names.getDebugName(17) or names.getDebugName(2) or "Regular"
            return _safe_text(family, 120), _safe_text(subfamily, 80)
        finally:
            font.close()
    except Exception:
        return _safe_text(path.stem, 120), "Regular"


def _drive_request(method: str, url: str, token: str, *, params: dict[str, str] | None = None, payload: dict[str, Any] | None = None, content: bytes | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request_headers = {"Authorization": f"Bearer {token}"}
    if headers:
        request_headers.update(headers)
    try:
        response = httpx.request(method, url, headers=request_headers, params=params, json=payload, content=content, timeout=180)
    except httpx.HTTPError as exc:
        raise BackupError("GOOGLE_DRIVE_UNAVAILABLE", "Could not reach Google Drive. Check the network and try again.", 502) from exc
    try:
        result = response.json()
    except ValueError:
        result = {}
    if response.is_error:
        if response.status_code == 401:
            raise BackupError("GOOGLE_DRIVE_AUTH_EXPIRED", "Google Drive access expired. Select the destination folder again.", 401)
        if response.status_code == 403:
            raise BackupError("GOOGLE_DRIVE_PERMISSION_DENIED", "Google Drive denied access to the selected folder.", 403)
        if response.status_code == 404:
            raise BackupError("GOOGLE_DRIVE_FOLDER_NOT_FOUND", "The selected Google Drive folder was not found.", 404)
        if response.status_code == 429:
            raise BackupError("GOOGLE_DRIVE_RATE_LIMIT", "Google Drive is temporarily limiting requests. Retry in a moment.", 429)
        message = "Google Drive could not complete this backup. Check the selected folder and try again."
        if "storageQuotaExceeded" in response.text:
            raise BackupError("GOOGLE_DRIVE_QUOTA_EXCEEDED", "The connected Google Drive account does not have enough storage space.", 507)
        raise BackupError("GOOGLE_DRIVE_REQUEST_FAILED", message, 502 if response.status_code >= 500 else response.status_code)
    return result if isinstance(result, dict) else {}


def _google_json(method: str, path: str, token: str, *, params: dict[str, str] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return _drive_request(method, f"{GOOGLE_DRIVE_API}/{path}", token, params=params, payload=payload)


def _drive_children(parent_id: str, token: str) -> list[dict[str, Any]]:
    children: list[dict[str, Any]] = []
    page_token = ""
    while True:
        params = {
            "q": f"'{_escape_query(parent_id)}' in parents and trashed = false",
            "fields": "nextPageToken,files(id,name,mimeType,md5Checksum,modifiedTime,appProperties)",
            "pageSize": "1000",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if page_token:
            params["pageToken"] = page_token
        response = _google_json("GET", "files", token, params=params)
        children.extend(child for child in response.get("files", []) if isinstance(child, dict))
        page_token = str(response.get("nextPageToken") or "")
        if not page_token:
            return children


def _select_or_create_font_folder(parent_id: str, item: dict[str, Any], children: list[dict[str, Any]], token: str) -> dict[str, Any]:
    key = item["font_key"]
    name = item["folder_name"]
    folders = [child for child in children if child.get("mimeType") == GOOGLE_FOLDER_MIME]
    managed = [child for child in folders if (child.get("appProperties") or {}).get("vfkFontKey") == key]
    named = [child for child in folders if str(child.get("name", "")).casefold() == name.casefold()]
    existing = managed or named
    if existing:
        folder = sorted(existing, key=lambda child: str(child.get("modifiedTime") or ""), reverse=True)[0]
        properties = dict(folder.get("appProperties") or {})
        properties.update({"vfkFontKey": key, "vfkManagedBy": "vietfont-studio"})
        if folder.get("name") != name or properties != (folder.get("appProperties") or {}):
            folder = _google_json(
                "PATCH", f"files/{folder['id']}", token,
                params={"fields": "id,name,mimeType,modifiedTime,appProperties", "supportsAllDrives": "true"},
                payload={"name": name, "appProperties": properties},
            )
            _replace_child(children, folder["id"], folder)
        return {"id": str(folder["id"]), "created": False}

    folder = _google_json(
        "POST", "files", token,
        params={"fields": "id,name,mimeType,modifiedTime,appProperties", "supportsAllDrives": "true"},
        payload={
            "name": name,
            "mimeType": GOOGLE_FOLDER_MIME,
            "parents": [parent_id],
            "appProperties": {"vfkFontKey": key, "vfkManagedBy": "vietfont-studio"},
        },
    )
    children.append(folder)
    return {"id": str(folder["id"]), "created": True}


def _drive_upload_file(folder_id: str, source: Path, filename: str, app_properties: dict[str, str], token: str, *, file_id: str | None = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {"name": filename, "appProperties": app_properties}
    if not file_id:
        metadata["parents"] = [folder_id]
    boundary = "vfk_" + secrets.token_hex(16)
    metadata_bytes = json.dumps(metadata, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    body = (
        f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()
        + metadata_bytes
        + f"\r\n--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n".encode()
        + source.read_bytes()
        + f"\r\n--{boundary}--".encode()
    )
    endpoint = f"files/{file_id}" if file_id else "files"
    method = "PATCH" if file_id else "POST"
    return _drive_request(
        method,
        f"{GOOGLE_DRIVE_UPLOAD_API}/{endpoint}",
        token,
        params={"uploadType": "multipart", "fields": "id,name,mimeType,md5Checksum,modifiedTime,appProperties", "supportsAllDrives": "true"},
        content=body,
        headers={"Content-Type": f"multipart/related; boundary={boundary}"},
    )


def _drive_update_metadata(file_id: str, filename: str, app_properties: dict[str, str], token: str) -> dict[str, Any]:
    return _google_json(
        "PATCH", f"files/{file_id}", token,
        params={"fields": "id,name,mimeType,md5Checksum,modifiedTime,appProperties", "supportsAllDrives": "true"},
        payload={"name": filename, "appProperties": app_properties},
    )


def _replace_child(children: list[dict[str, Any]], file_id: Any, updated: dict[str, Any]) -> None:
    for index, child in enumerate(children):
        if child.get("id") == file_id:
            children[index] = updated
            return


def _default_export_name(family: str, subfamily: str, fmt: str) -> str:
    family_token = re.sub(r"\s+", "", family)
    style_token = re.sub(r"\s+", "", subfamily)
    stem = _safe_component(f"{family_token}-{style_token}-Vietnamese", "Vietnamese-font")
    return f"{stem}.{fmt}"


def _safe_component(value: str, fallback: str) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", text)
    text = re.sub(r"\s+", " ", text).strip(" .")[:120].rstrip(" .")
    return text or re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", fallback).strip(" .") or "VietFont"


def _safe_font_filename(value: str, fmt: str, fallback: str) -> str:
    extension = "." + fmt
    name = _safe_component(value, fallback)
    suffix = Path(name).suffix.lower()
    if suffix:
        name = name[:-len(suffix)]
    return _safe_component(name, Path(fallback).stem)[:150].rstrip(" .") + extension


def _safe_text(value: str, limit: int) -> str:
    return unicodedata.normalize("NFC", str(value)).strip()[:limit] or "Font"


def _name_identity(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value)).casefold()
    return "".join(char for char in normalized if char.isalnum())


def _font_key(family: str) -> str:
    normalized = unicodedata.normalize("NFKC", family).casefold().strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:32]


def _export_key(logical_key: tuple[str, str, str]) -> str:
    return hashlib.sha256("\x00".join(logical_key).encode("utf-8")).hexdigest()[:32]


def _file_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _escape_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")
