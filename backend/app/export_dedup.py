from __future__ import annotations

from pathlib import Path
from sqlite3 import Connection

from .font_pipeline import normalize_export_filename


def find_export_by_identity(
    conn: Connection,
    *,
    project_id: str,
    variant_id: str,
    revision_id: str,
    output_format: str,
    filename: str,
    require_file: bool = True,
    exclude_export_id: str | None = None,
):
    """Find the newest artifact with the same export identity."""
    candidates = conn.execute(
        "SELECT * FROM exports WHERE project_id=? AND variant_id=? AND revision_id=? AND lower(format)=lower(?) "
        "ORDER BY created_at DESC",
        (project_id, variant_id, revision_id, output_format),
    ).fetchall()
    expected = normalize_export_filename(filename)
    for row in candidates:
        if row["id"] == exclude_export_id or normalize_export_filename(row["filename"]) != expected:
            continue
        if not require_file or Path(row["file_path"]).is_file():
            return row
    return None
