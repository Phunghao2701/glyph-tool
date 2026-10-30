from __future__ import annotations

import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Callable

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from .db import TOOLS_ROOT


class FontPipelineError(RuntimeError):
    pass


def export_filename(source_font: str | Path, name: str) -> str:
    """Return the same sanitized filename that write_export will create."""
    source = Path(source_font)
    actual_format = source.suffix.lower().lstrip(".")
    safe = "".join(c for c in (name or source.stem) if c.isalnum() or c in " -_").strip() or source.stem
    return f"{safe}.{actual_format}"


def normalize_export_filename(filename: str) -> str:
    """Normalize names for duplicate checks on case-insensitive local filesystems."""
    return unicodedata.normalize("NFKC", filename).strip().casefold()


Progress = Callable[[int, str], None]
# Keep this in sync with tools/kiemword.py: 67 lowercase Vietnamese letters.
VN_LOWER = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
VN_CHARS = VN_LOWER + VN_LOWER.upper()


def _run(script: str, *args: str | Path, cwd: Path | None = None, env: dict[str, str] | None = None, timeout: int = 900) -> str:
    path = TOOLS_ROOT / script
    if not path.is_file():
        raise FontPipelineError(f"Font-kit tool not found: {path}")
    proc_env = os.environ.copy()
    proc_env["KIT"] = str(TOOLS_ROOT)
    if env:
        proc_env.update(env)
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-I", str(path), *(str(x) for x in args)],
        cwd=str(cwd or TOOLS_ROOT),
        env=proc_env,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )
    output = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
    if result.returncode:
        raise FontPipelineError(f"{script} failed (exit {result.returncode}): {output[-5000:]}")
    return output.strip()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _glyph_bounds(font: TTFont, char: str) -> tuple[float, float, float, float] | None:
    cmap = font.getBestCmap()
    name = cmap.get(ord(char))
    if not name:
        return None
    pen = BoundsPen(font.getGlyphSet())
    font.getGlyphSet()[name].draw(pen)
    return pen.bounds


def analyze_font(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        font = TTFont(source, lazy=False, recalcBBoxes=False, recalcTimestamp=False)
        cmap = font.getBestCmap() or {}
    except Exception as exc:
        raise FontPipelineError(f"Could not parse font: {exc}") from exc
    missing = [ch for ch in VN_CHARS if ord(ch) not in cmap]
    names = font["name"]
    family = names.getDebugName(16) or names.getDebugName(1) or source.stem
    subfamily = names.getDebugName(17) or names.getDebugName(2) or "Regular"
    is_variable = "fvar" in font
    is_italic = bool(getattr(font["post"], "italicAngle", 0)) if "post" in font else False
    outline = "TrueType outlines" if "glyf" in font else "CFF outlines" if "CFF " in font else "unsupported outlines"
    feature_tags: list[str] = []
    if "GPOS" in font:
        table = font["GPOS"].table
        if table.FeatureList:
            feature_tags = sorted({r.FeatureTag for r in table.FeatureList.FeatureRecord})
    os2 = font["OS/2"] if "OS/2" in font else None
    upm = max(1, int(font["head"].unitsPerEm))
    sample_glyph_metrics: dict[str, dict[str, float]] = {}
    for char in "aenorsHOD":
        bounds = _glyph_bounds(font, char)
        if bounds:
            x0, y0, x1, y1 = bounds
            sample_glyph_metrics[char] = {
                "widthEm": round((x1 - x0) / upm, 4),
                "heightEm": round((y1 - y0) / upm, 4),
                "centerXEm": round(((x0 + x1) / 2) / upm, 4),
            }
    required_ascii = ["?", "d", "D", "E", "o", "O", "u", "U", "r", "i"]
    missing_bases = [char for char in required_ascii if ord(char) not in cmap]
    fmt = source.suffix.lower().lstrip(".")
    outline_matches = (fmt == "ttf" and "glyf" in font) or (fmt == "otf" and "CFF " in font)
    supported = outline_matches and not is_variable and not is_italic and not missing_bases
    diagnostics: list[str] = []
    if is_variable: diagnostics.append("Variable fonts are not included in the local MVP engine.")
    if is_italic: diagnostics.append("Italic fonts require the separate italic-font pipeline and are not supported by this MVP.")
    if not outline_matches: diagnostics.append("This MVP requires glyf outlines for TTF and CFF outlines for OTF.")
    if missing_bases: diagnostics.append('Required Latin base glyphs are missing: ' + ', '.join(missing_bases))
    return {
        "format": fmt,
        "family": family,
        "subfamily": subfamily,
        "unitsPerEm": upm,
        "glyphCount": len(font.getGlyphOrder()),
        "outlineType": outline,
        "isVariable": is_variable,
        "isItalic": is_italic,
        "isMonospace": bool(getattr(font["post"], "isFixedPitch", 0)) if "post" in font else False,
        "weightClass": int(getattr(os2, "usWeightClass", 400)) if os2 else 400,
        "italicAngle": float(getattr(font["post"], "italicAngle", 0)) if "post" in font else 0.0,
        "sampleGlyphMetrics": sample_glyph_metrics,
        "tables": sorted(font.keys()),
        "features": feature_tags,
        "hasMarkAnchors": "mark" in feature_tags or "mkmk" in feature_tags,
        "metrics": {
            "xHeight": getattr(os2, "sxHeight", 0) if os2 else 0,
            "capHeight": getattr(os2, "sCapHeight", 0) if os2 else 0,
            "typoAscender": getattr(os2, "sTypoAscender", 0) if os2 else 0,
            "typoDescender": getattr(os2, "sTypoDescender", 0) if os2 else 0,
            "winAscent": getattr(os2, "usWinAscent", 0) if os2 else 0,
            "winDescent": getattr(os2, "usWinDescent", 0) if os2 else 0,
        },
        "coverage": {
            "requiredCount": len(VN_CHARS),
            "presentCount": len(VN_CHARS) - len(missing),
            "missing": missing,
            "percent": round(100 * (len(VN_CHARS) - len(missing)) / max(1, len(VN_CHARS)), 1),
        },
        "missingBaseGlyphs": missing_bases,
        "supportedForGeneration": supported,
        "diagnostics": diagnostics,
    }


def _profile_configs(
    source_otf: Path,
    label: str,
    work: Path,
    font_format: str,
    style: dict[str, Any] | None = None,
) -> tuple[Path, Path, Path, Path]:
    font = TTFont(source_otf)
    upm = font["head"].unitsPerEm
    scale = upm / 1000.0
    stack_place = "top" if label == "B" else "right"
    style = style or {}

    def bounded(name: str, default: float, low: float, high: float) -> float:
        try:
            value = float(style.get(name, default))
        except (TypeError, ValueError):
            value = default
        return min(high, max(low, value))

    gap_scale = bounded("spacingScale", 1.0, 0.8, 1.2)
    cfg: dict[str, Any] = {
        "suffix": "VN",
        "dot": {"k": bounded("dotSquareness", 0.66, 0.55, 0.8)},
        "hook": {
            "style": "question", "h": round(240 * bounded("hookHeightScale", 1.0, 0.85, 1.15)),
            "xstretch": bounded("hookWidthScale", 1.1, 0.9, 1.3),
            "stack": bounded("stackScale", 0.82, 0.65, 1.0),
            "stack_w": bounded("stackWidthScale", 0.86, 0.7, 1.0), "stack_place": stack_place,
            "caps_flat": 0.9, "gap_right": 24, "gap": 40,
        },
        "horn": {"style": "arc"},
        "horn_kern": round(12 * bounded("hornKerningScale", 1.0, 0.5, 1.5)),
        "contain_marks": True,
        "caps_stack_flat": 1.0,
        "stack_gap_ag": round(20 * gap_scale),
    }
    cfg["hook"]["gap_right"] = round(24 * gap_scale)
    feature_tags: set[str] = set()
    if "GPOS" in font and font["GPOS"].table.FeatureList:
        feature_tags = {f.FeatureTag for f in font["GPOS"].table.FeatureList.FeatureRecord}
    if "mark" in feature_tags or "mkmk" in feature_tags:
        cfg["anchor_marks"] = {"stack_hook": "hook", "dot_gap": round(40 * scale), "dot_min": round(10 * scale)}
    config_path = work / "config.json"
    addons_path = work / "addons.json"
    hook_path = work / "hook_single.json"
    hoi_path = work / "hoi_place.json"
    _write_json(config_path, cfg)

    b_d = _glyph_bounds(font, "d")
    b_D = _glyph_bounds(font, "D")
    if b_d:
        x0, y0, x1, y1 = b_d
        d_bar = [round(x0 + (x1 - x0) * 0.08), round(y0 + (y1 - y0) * 0.90), round(x1 - (x1 - x0) * 0.08)]
    else:
        d_bar = [round(220 * scale), round(734 * scale), round(480 * scale)]
    if b_D:
        x0, y0, x1, y1 = b_D
        D_bar = [round(x0 + (x1 - x0) * 0.08), round(y0 + (y1 - y0) * 0.45), round(x1 - (x1 - x0) * 0.08)]
    else:
        D_bar = [round(10 * scale), round(421 * scale), round(300 * scale)]
    _write_json(addons_path, {"bar": round(52 * scale), "d": d_bar, "D": D_bar})
    _write_json(hoi_path, {
        "gap_lc": round(60 * scale), "gap_uc": round(50 * scale),
        "dx_lc": 0.04, "dx_uc": 0.03, "s_lc": 1.0, "s_uc": 0.94,
        "gap_src": True,
    })
    return config_path, addons_path, hook_path, hoi_path


def _horn_config(source_otf: Path, destination: Path, upm: int) -> Path:
    s = upm / 1000.0
    payload = {
        "src": str(source_otf),
        "max_overlap": round(9000 * s * s),
        "O": {}, "U": {}, "o": {}, "u": {},
        "all": {
            "reach": round(60 * s), "rise": round(80 * s),
            "thin": round(30 * s), "head": round(100 * s),
            "p": 2.15, "t0": 0.29, "dyO": 0, "dyU": 0,
        },
        "lc_ratio": 0.9, "lc_wratio": 1.0,
        "clear": round(10 * s), "tone_gap": round(28 * s),
        "tail_x": round(215 * s),
    }
    _write_json(destination, payload)
    return destination


def _run_ots(path: Path) -> dict[str, Any]:
    if importlib.util.find_spec("ots") is None:
        return {"id": "ots", "status": "skipped", "detail": "OpenType Sanitizer module is not installed."}
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-I", "-m", "ots", str(path)],
        capture_output=True, text=True, timeout=180, encoding="utf-8", errors="replace",
    )
    return {
        "id": "ots",
        "status": "passed" if result.returncode == 0 else "failed",
        "detail": ((result.stdout or "") + (result.stderr or ""))[-2000:],
    }


def _require_ots(path: Path, context: str) -> dict[str, Any]:
    result = _run_ots(path)
    if result["status"] == "failed":
        raise FontPipelineError(f"OpenType Sanitizer rejected {context}: {result.get('detail', '')}")
    return result


def validate_font(path: str | Path, progress: Progress | None = None) -> dict[str, Any]:
    target = Path(path)
    checks: list[dict[str, Any]] = []
    try:
        font = TTFont(target, lazy=False, recalcBBoxes=False, recalcTimestamp=False)
        cmap = font.getBestCmap() or {}
        missing = [ch for ch in VN_CHARS if ord(ch) not in cmap]
        present_count = len(VN_CHARS) - len(missing)
        coverage = {
            "requiredCount": len(VN_CHARS),
            "presentCount": present_count,
            "missing": missing,
            "percent": round(100 * present_count / max(1, len(VN_CHARS)), 1),
        }
        checks.append({
            "id": "font_parse", "status": "passed",
            "detail": f"Parsed {target.suffix[1:].upper()} with {len(font.getGlyphOrder())} glyphs.",
        })
        checks.append({
            "id": "vietnamese_coverage", "status": "passed" if not missing else "failed",
            "detail": f"{present_count}/{len(VN_CHARS)} required characters present." + (f" Missing: {''.join(missing)}" if missing else ""),
        })
    except Exception as exc:
        return {"status": "failed", "checks": [{"id": "font_parse", "status": "failed", "detail": str(exc)}]}
    if progress:
        progress(90, "Checking Word/Windows font requirements")
    result = subprocess.run(
        [sys.executable, "-X", "utf8", "-I", str(TOOLS_ROOT / "kiemword.py"), str(target)],
        cwd=str(TOOLS_ROOT), env={**os.environ, "KIT": str(TOOLS_ROOT)},
        capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace",
    )
    text = ((result.stdout or "") + (result.stderr or "")).strip()
    passed = result.returncode == 0 and "KIỂM WORD: ĐẠT" in text
    checks.append({"id": "kiemword", "status": "passed" if passed else "failed", "detail": text[-3000:]})
    ots = _run_ots(target)
    checks.append(ots)
    required = all(c["status"] in {"passed", "skipped"} for c in checks)
    return {"status": "passed" if required else "failed", "checks": checks, "coverage": coverage}


def generate_initial_variants(
    source_path: str | Path,
    project_id: str,
    job_root: Path,
    progress: Progress | None = None,
    style_profile: dict[str, Any] | None = None,
    variant_labels: list[str] | None = None,
) -> list[dict[str, Any]]:
    source = Path(source_path).resolve()
    source_format = source.suffix.lower().lstrip(".")
    if source_format not in {"ttf", "otf"}:
        raise FontPipelineError("Only .ttf and .otf fonts are supported.")
    labels = variant_labels or ["A", "B", "C"]
    if not labels or any(label not in {"A", "B", "C"} for label in labels):
        raise FontPipelineError("Variant selection must use A, B, or C.")
    style_by_label = {
        str(item.get("label", ""))[-1:]: item
        for item in (style_profile or {}).get("variants", [])
        if isinstance(item, dict)
    }
    font = TTFont(source)
    if "fvar" in font:
        raise FontPipelineError("Variable fonts are not supported in the local MVP.")
    job_root.mkdir(parents=True, exist_ok=True)
    src_otf = job_root / "source.otf"
    if source_format == "ttf":
        _run("ttf2otf.py", source, src_otf, cwd=job_root)
    else:
        shutil.copy2(source, src_otf)
    results: list[dict[str, Any]] = []
    for index, label in enumerate(labels):
        if progress:
            progress(5 + int(index * 28 / len(labels)), f"Building VER 1{label}")
        work = job_root / f"ver-1{label}"
        work.mkdir(parents=True, exist_ok=True)
        variant_style = style_by_label.get(label)
        cfg, addons, hook_single, hoi_place = _profile_configs(src_otf, label, work, source_format, variant_style)
        recipes_path = work / "recipes.json"
        if label == "C":
            cm = font.getBestCmap() or {}
            qname = cm.get(ord("?"))
            qb = _glyph_bounds(font, "?") if qname else None
            if qb:
                cut = qb[1] + (qb[3] - qb[1]) * 0.48
                height = max(1, (font["OS/2"].sxHeight or font["head"].unitsPerEm * 0.5) * 0.52)
                custom_hook = work / "hook-half.json"
                _run("hoi.py", src_otf, custom_hook, "A", round(height), "1.25", round(cut), cwd=work)
                config = json.loads(cfg.read_text(encoding="utf-8"))
                contours = json.loads(custom_hook.read_text(encoding="utf-8"))
                config["marks"] = {"hook": contours, "hook_s": contours}
                _write_json(cfg, config)
        a_font, b_font, c_font, final_otf = (work / f"{name}.otf" for name in ("A", "B", "C", "D"))
        _run("vnfont.py", src_otf, a_font, "--config", cfg, "--recipes", recipes_path, cwd=work)
        recipe_data = json.loads(recipes_path.read_text(encoding="utf-8"))
        hook_single.write_text(json.dumps(recipe_data.get("marks", {}).get("hook", []), ensure_ascii=False), encoding="utf-8")
        _run("addons.py", a_font, b_font, addons, cwd=work)
        _run("place_hoi.py", b_font, c_font, src_otf, hook_single, hoi_place, cwd=work)
        config = json.loads(cfg.read_text(encoding="utf-8"))
        if "anchor_marks" in config:
            config["marks"] = recipe_data.get("marks", config.get("marks", {}))
            _write_json(cfg, config)
            _run("anchor_marks.py", c_font, c_font, src_otf, cfg, cwd=work)
        horn_cfg = _horn_config(src_otf, work / "horn5.json", font["head"].unitsPerEm)
        _run("horn5.py", c_font, final_otf, horn_cfg, cwd=work)
        kerned_otf = work / "D-autokern.otf"
        _run("autokern_horn.py", final_otf, kerned_otf, round(50 * font["head"].unitsPerEm / 1000), cwd=work)
        kerned_otf.replace(final_otf)
        if "GSUB" in TTFont(final_otf):
            _run("sortfeat.py", final_otf, cwd=work)
        stamp_env = {"FAMILY": font["name"].getDebugName(1) or source.stem}
        _run("stamp.py", final_otf, "1.001", f"1{label}", cwd=work, env=stamp_env)
        _run("winfix.py", final_otf, cwd=work)
        word = _run("kiemword.py", final_otf, "--fix", cwd=work)
        if "KIỂM WORD: ĐẠT" not in word:
            raise FontPipelineError(f"Word validation did not pass for VER 1{label}: {word[-2000:]}")
        _require_ots(final_otf, f"VER 1{label} intermediate OTF")
        if source_format == "ttf":
            final_font = work / f"{source.stem}-Vietnamese.ttf"
            _run("otf2ttf.py", final_otf, source, src_otf, final_font, cwd=work)
            _run("winfix.py", final_font, cwd=work)
            word = _run("kiemword.py", final_font, "--fix", cwd=work)
            if "KIỂM WORD: ĐẠT" not in word:
                raise FontPipelineError(f"Word validation did not pass for VER 1{label}: {word[-2000:]}")
            _require_ots(final_font, f"VER 1{label} TTF")
        else:
            final_font = final_otf
        editor_path = work / "editor.json"
        _run("export_editor.py", final_font, recipes_path, editor_path, cwd=work)
        validation = validate_font(final_font, progress)
        results.append({
            "label": f"1{label}", "font_path": str(final_font),
            "editor_document_path": str(editor_path),
            "parameters": {
                "stackPlace": "top" if label == "B" else "right",
                "hookSource": "upper-half" if label == "C" else "font-question",
                "aiStyle": variant_style,
                "aiStyleProfile": style_profile,
            },
            "validation": validation,
        })
    return results


def _apply_contours(font: TTFont, glyph_name: str, contours: list[Any], width: float) -> None:
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.qu2cuPen import Qu2CuPen
    import pathops

    def set_empty_glyph() -> None:
        hmtx = font["hmtx"]
        if "CFF " in font:
            cff = font["CFF "].cff
            top = cff.topDictIndex[0]
            nominal = getattr(top.Private, "nominalWidthX", 0)
            charstring = T2CharStringPen(float(width) - nominal, None).getCharString(
                private=top.Private, globalSubrs=cff.GlobalSubrs,
            )
            index = top.CharStrings.charStrings[glyph_name]
            top.CharStrings.charStringsIndex[index] = charstring
        else:
            glyf = font["glyf"]
            glyph = TTGlyphPen(None).glyph()
            glyph.recalcBounds(glyf)
            glyf[glyph_name] = glyph
        hmtx.metrics[glyph_name] = (int(round(width)), 0)

    path = pathops.Path()
    pen = path.getPen()
    for contour in contours:
        for op, points in contour:
            pts = [tuple(float(v) for v in p) for p in points]
            if op == "M": pen.moveTo(pts[0])
            elif op == "L": pen.lineTo(pts[0])
            elif op == "C": pen.curveTo(*pts)
            elif op == "Q": pen.qCurveTo(*pts)
        pen.closePath()
    if not any(verb != pathops.PathVerb.MOVE for verb in path.verbs):
        set_empty_glyph()
        return
    path = pathops.op(path, pathops.Path(), pathops.PathOp.UNION, fix_winding=True)
    rec = RecordingPen()
    path.draw(rec)
    hmtx = font["hmtx"]
    if "CFF " in font:
        cff = font["CFF "].cff
        top = cff.topDictIndex[0]
        nominal = getattr(top.Private, "nominalWidthX", 0)
        target = T2CharStringPen(float(width) - nominal, None)
        rec.replay(Qu2CuPen(target, max_err=1.0))
        charstring = target.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
        index = top.CharStrings.charStrings[glyph_name]
        top.CharStrings.charStringsIndex[index] = charstring
        bounds = path.bounds
        hmtx.metrics[glyph_name] = (int(round(width)), int(math.floor(bounds[0])))
    else:
        glyf = font["glyf"]
        target = TTGlyphPen(None)
        rec.replay(Cu2QuPen(target, max_err=1.0, reverse_direction=True))
        glyph = target.glyph()
        glyph.recalcBounds(glyf)
        glyf[glyph_name] = glyph
        hmtx.metrics[glyph_name] = (int(round(width)), int(getattr(glyph, "xMin", 0) or 0))


def apply_editor_edits(
    base_font_path: str | Path,
    base_document_path: str | Path,
    edits: list[dict[str, Any]],
    job_root: Path,
    progress: Progress | None = None,
) -> dict[str, str]:
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.transformPen import TransformPen
    import pathops

    job_root.mkdir(parents=True, exist_ok=True)
    font = TTFont(base_font_path)
    doc = json.loads(Path(base_document_path).read_text(encoding="utf-8"))
    fv = doc.get("fv", doc)
    marks = dict(fv.get("marks", {}))
    glyph_edits: dict[str, dict[str, Any]] = {}
    mark_edits: dict[str, dict[str, Any]] = {}
    for edit in edits:
        if not edit.get("touched"):
            continue
        target_id = edit["targetId"]
        if edit["kind"] == "mark":
            mark_edits[target_id] = edit
        else:
            glyph_edits[target_id] = edit
    for mark_id, edit in mark_edits.items():
        marks[mark_id] = edit.get("contours", [])
    def transform(contours: list[Any], t: list[float]) -> list[Any]:
        a, b, c, d, e, f = t
        out = []
        for contour in contours:
            next_contour = []
            for op, points in contour:
                next_contour.append([op, [[a*x+c*y+e, b*x+d*y+f] for x, y in points]])
            out.append(next_contour)
        return out
    updated_glyphs: dict[str, list[Any]] = {}
    for glyph_name, recipe in fv.get("recipes", {}).items():
        if glyph_name in glyph_edits:
            continue
        if not any(part.get("m") in mark_edits for part in recipe.get("m", [])):
            continue
        contours = list(recipe.get("s", []))
        for part in recipe.get("m", []):
            source_mark = marks.get(part.get("m"), [])
            contours.extend(transform(source_mark, part.get("t", [1,0,0,1,0,0])))
        updated_glyphs[glyph_name] = contours
    for glyph_name, edit in glyph_edits.items():
        contours = edit.get("contours", [])
        updated_glyphs[glyph_name] = contours
    order = list(font.getGlyphOrder())
    widths = {name: font["hmtx"][name][0] for name in order if name in font["hmtx"].metrics}
    for i, (name, contours) in enumerate(updated_glyphs.items()):
        if name not in order:
            continue
        _apply_contours(font, name, contours, glyph_edits.get(name, {}).get("w", widths.get(name, 500)))
        if progress and i % 12 == 0:
            progress(35 + int(35 * i / max(1, len(updated_glyphs))), f"Applying vector edits ({i+1}/{len(updated_glyphs)})")
    font_path = job_root / f"revision{Path(base_font_path).suffix.lower()}"
    font.save(font_path)
    editor_doc = json.loads(json.dumps(doc))
    editor_fv = editor_doc.get("fv", editor_doc)
    editor_fv["marks"] = marks
    for name, contours in updated_glyphs.items():
        glyph_data = editor_fv.get("glyphs", {}).get(name)
        width = glyph_edits.get(name, {}).get("w", (glyph_data or {}).get("w", 500))
        if glyph_data is not None:
            glyph_data["c"] = contours
            glyph_data["w"] = width
        if name in glyph_edits and name in editor_fv.get("recipes", {}):
            recipe = editor_fv["recipes"][name]
            recipe["s"] = contours
            recipe["m"] = []
            recipe["w"] = width
    editor_path = job_root / "editor.json"
    editor_path.write_text(json.dumps(editor_doc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    _run("winfix.py", font_path, cwd=job_root)
    word = _run("kiemword.py", font_path, "--fix", cwd=job_root)
    if progress:
        progress(85, "Rechecking the edited font")
    if "KIỂM WORD: ĐẠT" not in word:
        raise FontPipelineError(f"Word validation failed after vector edits: {word[-2000:]}")
    return {"font_path": str(font_path), "editor_document_path": str(editor_path)}


def write_export(
    source_font: str | Path,
    export_dir: Path,
    output_format: str,
    name: str,
    revision_id: str,
    label: str,
) -> tuple[str, str]:
    source = Path(source_font)
    actual_format = source.suffix.lower().lstrip(".")
    if actual_format != output_format:
        raise FontPipelineError(f"This revision was built as {actual_format.upper()}; export that format.")
    export_dir.mkdir(parents=True, exist_ok=True)
    target = export_dir / export_filename(source, name)
    shutil.copy2(source, target)
    family = name.strip()
    if family:
        version = "1.001"
        _run("stamp.py", target, version, label, cwd=export_dir, env={"FAMILY": family})
    check = validate_font(target)
    if check["status"] != "passed":
        raise FontPipelineError("Exported font failed validation; the file was retained in local storage but not published.")
    return str(target), target.name
