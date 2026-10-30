"""Đóng số phiên bản (Windows/Adobe cache theo version) + tên font mặc định + watermark VFK (Việt Font Kit).
usage: stamp.py FONT VERSION [NHÃN]   (vd 1.004 · vòng 3 nhiều bản: stamp.py F 1.003 3A → “Version 1.003 3A”)

Tên font mặc định: "VFK - <tên font gốc>" (biến PREFIX, mặc định "VFK - "; PREFIX="" giữ tên đang có;
  FAMILY="Tên khác" = tên người dùng đặt ở ô “Tên font xuất” trên trang duyệt, PostScript tự bỏ dấu):
  - name 1 / 16 (family): "VFK - Ten Font"
  - name 4 (full): family (+ kiểu nếu không phải Regular)
  - name 6 (PostScript, không dấu cách): "VFK-TenFont" (+ "-Bold"…)
  Tên gốc lấy từ family hiện tại, bỏ hậu tố " VN" (vnfont.py) và tiền tố cũ nếu có.
Watermark (mặc định "VFK", đổi bằng biến MARK, MARK="" để tắt):
  - name 5 (phiên bản, Windows hiện ở Properties → Details): "Version 1.004; VFK"
  - name 10 (mô tả, macOS Font Book / FontForge hiện): "Việt hoá bằng VFK · Vietnamese localization by VFK (Việt Font Kit)"
Không đụng bản quyền / tác giả gốc (name 0, 8, 9, 13, 14)."""
import sys, os, re
from fontTools.ttLib import TTFont
p, v = sys.argv[1], sys.argv[2]
label = sys.argv[3] if len(sys.argv) > 3 else ""   # vd "5B" → name 5 "Version 1.005 5B" (ver nhánh cùng số)
MARK = os.environ.get("MARK", "VFK").strip()
PREFIX = os.environ.get("PREFIX", "VFK - ")
f = TTFont(p); f["head"].fontRevision = float(v)
nm = f["name"]

# ---- tên mặc định: VFK - <tên gốc> ----
if PREFIX:
    sty = nm.getDebugName(17) or nm.getDebugName(2) or "Regular"
    fam0 = nm.getDebugName(16) or nm.getDebugName(1) or "Font"
    for old in (PREFIX, "VFK - ", "VFK-"):
        if fam0.startswith(old): fam0 = fam0[len(old):]
    fam0 = re.sub(r"\s+VN$", "", fam0).strip()
    fam = os.environ.get("FAMILY", "").strip() or PREFIX + fam0   # FAMILY: tên người dùng đặt ở ô “Tên font xuất” (db <DOC>/out/name)
    full = fam + ("" if sty == "Regular" else " " + sty)
    import unicodedata
    _a = lambda t: unicodedata.normalize("NFD", t.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode()
    ps = re.sub(r"[^A-Za-z0-9-]", "", re.sub(r"\s+-\s+", "-", _a(fam)))   # vd "VFK - Ten Font" → VFK-TenFont
    if sty != "Regular": ps += "-" + re.sub(r"[^A-Za-z0-9]", "", sty)
    ps = ps[:63]
    for rec in list(nm.names):
        if rec.nameID in (1, 16): nm.setName(fam, rec.nameID, rec.platformID, rec.platEncID, rec.langID)
        elif rec.nameID == 4: nm.setName(full, 4, rec.platformID, rec.platEncID, rec.langID)
        elif rec.nameID == 6: nm.setName(ps, 6, rec.platformID, rec.platEncID, rec.langID)
    if "CFF " in f:
        cff = f["CFF "].cff; td = cff.topDictIndex[0]
        cff.fontNames = [ps]; td.FullName = full; td.FamilyName = fam

ps = nm.getDebugName(6) or ""
ver = "Version " + v + (" " + label if label else "")
for n in nm.names:
    s = n.toUnicode()
    if n.nameID == 5: n.string = ver + ("; " + MARK if MARK else "")
    elif n.nameID == 3:
        parts = s.split(";")
        if parts and parts[0].startswith("Version"): parts[0] = ver
        else: parts = [ver] + parts
        if len(parts) > 2 and ps: parts[2] = ps          # unique ID mang tên PostScript mới → Windows không nhầm với font gốc
        elif ps: parts.append(ps)
        n.string = ";".join(parts)
if MARK:
    nm.removeNames(nameID=10)
    nm.setName("Việt hoá bằng " + MARK + " · Vietnamese localization by " + MARK + " (Việt Font Kit)", 10, 3, 1, 0x409)
    if any(n.platformID == 1 for n in nm.names): nm.setName("Vietnamese localization by " + MARK + " (Viet Font Kit)", 10, 1, 0, 0)
if "CFF " in f:
    td = f["CFF "].cff.topDictIndex[0]
    if hasattr(td, "version"): td.version = v
f.save(p); print(p, "→", v, "·", nm.getDebugName(1), "·", nm.getDebugName(6), ("· watermark " + MARK) if MARK else "")
