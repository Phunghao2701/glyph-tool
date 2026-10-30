"""Đổi font TrueType (.ttf, glyf) sang CFF (.otf) để chạy được chuỗi build.sh (vnfont → addons → place_hoi → horn5 đều ghi CFF).
Giữ nguyên hmtx, cmap, GSUB / GPOS / GDEF, name, OS/2; bỏ glyf / loca / hinting (cvt, fpgm, prep, gasp).
Đường cong bậc 2 (qCurveTo) đổi chính xác sang bậc 3 — nét không đổi; đảo chiều contour theo chuẩn CFF.
Bản .ttf gốc vẫn dùng làm SRC_TTF cho otf2ttf.py ở cuối để trả về đúng định dạng và giữ hinting cho glyph không đổi.
usage: ttf2otf.py IN.ttf OUT.otf
build by @nhatmotion"""
import sys
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.reverseContourPen import ReverseContourPen
from fontTools.pens.recordingPen import DecomposingRecordingPen

IN, OUT = sys.argv[1], sys.argv[2]
f = TTFont(IN)
assert "glyf" in f, "không phải TrueType"
gs = f.getGlyphSet(); order = f.getGlyphOrder(); hm = f["hmtx"]
cs = {}
for g in order:
    pen = T2CharStringPen(hm[g][0], gs)   # nominalWidthX = 0 → width ghi thẳng
    rec = DecomposingRecordingPen(gs); gs[g].draw(rec)   # tách composite trước, nếu không thành phần sẽ không bị đảo chiều
    rec.replay(ReverseContourPen(pen))   # TrueType: viền ngoài cùng chiều kim đồng hồ → CFF: ngược chiều
    cs[g] = pen.getCharString()
nm = f["name"]
ps = nm.getDebugName(6) or "Font-Regular"
fb = FontBuilder(font=f); fb.isTTF = False
fb.setupCFF(ps, {"FullName": nm.getDebugName(4) or ps, "FamilyName": nm.getDebugName(1) or ps,
                 "Weight": nm.getDebugName(2) or "Regular", "version": "%.3f" % f["head"].fontRevision,
                 "Notice": (nm.getDebugName(0) or "")[:200], "ItalicAngle": f["post"].italicAngle,
                 "isFixedPitch": f["post"].isFixedPitch},
            cs, {})
for t in ("glyf", "loca", "cvt ", "fpgm", "prep", "gasp", "hdmx", "LTSH", "VDMX"):
    if t in f: del f[t]
m = newTable("maxp"); m.tableVersion = 0x00005000; m.numGlyphs = len(order); f["maxp"] = m
f["post"].formatType = 3.0
f.sfntVersion = "OTTO"
# kiểm: width CFF == hmtx
from fontTools.pens.basePen import NullPen
top = f["CFF "].cff.topDictIndex[0]; nom = getattr(top.Private, "nominalWidthX", 0)
for g in order:
    c = top.CharStrings[g]; c.draw(NullPen())
    assert abs(c.width - hm[g][0]) < 0.5, g
f.save(OUT)
print("ttf2otf: %d glyph → %s" % (len(order), OUT))
