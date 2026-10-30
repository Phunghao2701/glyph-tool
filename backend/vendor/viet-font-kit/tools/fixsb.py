"""Sửa khoảng chừa (side bearing) của vài glyph sau khi dựng — vd dấu phẩy dính chữ tròn (o có RSB âm, phẩy có LSB âm).
usage: fixsb.py FONT "comma:12,semicolon:12"   → đặt LSB = số đã cho (đơn vị font), giữ RSB, độ rộng tăng tương ứng.
Chỉ chỉnh glyph được nêu; in độ rộng trước/sau. Font CFF: ghi width - nominalWidthX như vnfont."""
import sys
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
p, spec = sys.argv[1], sys.argv[2]
f = TTFont(p); gs = f.getGlyphSet()
top = f["CFF "].cff.topDictIndex[0] if "CFF " in f else None
for item in spec.split(","):
    name, lsb = item.split(":"); lsb = float(lsb)
    b = BoundsPen(gs); gs[name].draw(b); x0 = b.bounds[0]; w = gs[name].width
    dx = lsb - x0; nw = int(round(w + dx))
    if top is not None:
        pen = T2CharStringPen(nw - getattr(top.Private, "nominalWidthX", 0), None)
        gs[name].draw(TransformPen(pen, (1, 0, 0, 1, dx, 0)))
        cs = pen.getCharString(private=top.Private, globalSubrs=top.GlobalSubrs)
        top.CharStrings[name] = cs
    else:
        sys.exit("chỉ hỗ trợ CFF (.otf) ở bản này")
    f["hmtx"][name] = (nw, int(round(lsb)))
    print(name, "LSB %d → %d, width %d → %d" % (x0, lsb, w, nw))
f.save(p)
