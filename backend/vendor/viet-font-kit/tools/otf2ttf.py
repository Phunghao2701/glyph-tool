"""Trả font đã Việt hoá (CFF .otf) về TrueType (.ttf) khi font gốc là .ttf.
- Glyph KHÔNG đổi so với bản đổi thẳng (ttf2otf của font gốc) → dùng lại nguyên glyph glyf gốc (giữ hinting / composite).
- Glyph mới hoặc đã sửa → đổi bậc 3 → bậc 2 (cu2qu, sai số ≤ 1 đơn vị), đảo chiều contour theo chuẩn TrueType.
- Giữ cvt / fpgm / prep / gasp của font gốc; post format 2 (giữ tên glyph).
usage: otf2ttf.py VN.otf SRC.ttf BASE.otf OUT.ttf
       BASE.otf = kết quả ttf2otf.py SRC.ttf (để biết glyph nào không đổi)
build by @nhatmotion"""
import sys
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen

VN, SRC, BASE, OUT = sys.argv[1:5]
f = TTFont(VN); src = TTFont(SRC); base = TTFont(BASE)
order = f.getGlyphOrder(); gs = f.getGlyphSet(); bgs = base.getGlyphSet()
sglyf = src["glyf"]; hm = f["hmtx"]; shm = src["hmtx"]

def rec(gset, g):
    r = RecordingPen(); gset[g].draw(r)
    return [(o, tuple(tuple(round(v, 2) for v in p) for p in a)) for o, a in r.value]

glyf = newTable("glyf"); glyf.glyphs = {}; glyf.glyphOrder = order
kept = conv = 0
for g in order:
    same = (g in sglyf.glyphs and g in bgs and hm[g] == shm[g] and rec(gs, g) == rec(bgs, g))
    if same:
        glyf.glyphs[g] = sglyf[g]; kept += 1
    else:
        tp = TTGlyphPen(None)
        gs[g].draw(Cu2QuPen(tp, max_err=1.0, reverse_direction=True))
        glyf.glyphs[g] = tp.glyph(); conv += 1
f["glyf"] = glyf
f["loca"] = newTable("loca")
for t in ("cvt ", "fpgm", "prep", "gasp"):
    if t in src: f[t] = src[t]
mx = newTable("maxp"); mx.__dict__.update(src["maxp"].__dict__); f["maxp"] = mx
f["post"].formatType = 2.0; f["post"].extraNames = []; f["post"].mapping = {}
f["post"].glyphOrder = order
del f["CFF "]
f["head"].glyphDataFormat = 0
f.sfntVersion = "\x00\x01\x00\x00"
f.setGlyphOrder(order)
# lsb = xMin theo chuẩn TrueType (glyph mới chưa có khung bao → tính trước khi recalc maxp)
for g in order:
    gl = glyf[g]
    if gl.numberOfContours != 0:
        gl.recalcBounds(glyf)
        hm.metrics[g] = (hm[g][0], gl.xMin)
mx.numGlyphs = len(order); mx.recalc(f)
f.save(OUT)
# kiểm lại: số contour / khung bao của glyph đổi phải sát bản CFF
chk = TTFont(OUT); cg = chk.getGlyphSet()
from fontTools.pens.boundsPen import BoundsPen
bad = []
for g in order:
    a = BoundsPen(gs); gs[g].draw(a); b = BoundsPen(cg); cg[g].draw(b)
    if (a.bounds is None) != (b.bounds is None) or (a.bounds and max(abs(x - y) for x, y in zip(a.bounds, b.bounds)) > 2): bad.append(g)
print("otf2ttf: giữ nguyên %d glyph gốc (có hinting), đổi %d glyph; lệch khung > 2: %d %s → %s" % (kept, conv, len(bad), bad[:5], OUT))
