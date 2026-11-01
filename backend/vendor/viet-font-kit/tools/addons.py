"""Bổ sung cho vnfont.py: thêm đ Đ (d/D + thanh ngang) và thu hẹp dấu ngã trên ĩ Ĩ cho nằm trong advance.
usage: addons.py IN.otf OUT.otf [addons.json]
addons.json: {"bar": 52, "d": [x0, y_giữa, x1], "D": [x0, y_giữa, x1]} — ĐO LẠI cho từng font (thanh ngang đ Đ ≈ độ dày nét ngang chữ E)."""
import sys, copy
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
import pathops

f = TTFont(sys.argv[1])
cff = f["CFF "].cff; top = cff.topDictIndex[0]; csi = top.CharStrings
NOM = getattr(top.Private, "nominalWidthX", 0)
hmtx = f["hmtx"]; cmap = f.getBestCmap()
gs = f.getGlyphSet()

def rec(n):
    r = RecordingPen(); gs[n].draw(r); return r.value

def contours(ops):
    out, cur = [], []
    for op, a in ops:
        cur.append((op, a))
        if op in ("closePath", "endPath"): out.append(cur); cur = []
    return out

def bounds(ops):
    b = BoundsPen(None)
    for op, a in ops: getattr(b, op)(*a)
    return b.bounds

def rect(x0, y0, x1, y1):
    return [("moveTo", ((x0, y0),)), ("lineTo", ((x1, y0),)), ("lineTo", ((x1, y1),)), ("lineTo", ((x0, y1),)), ("closePath", ())]

def put(name, ops, width, new):
    p = pathops.Path(); pen = p.getPen()
    for op, a in ops: getattr(pen, op)(*a)
    p = pathops.op(p, pathops.Path(), pathops.PathOp.UNION, fix_winding=True)
    r = RecordingPen(); p.draw(r)
    t2 = T2CharStringPen(width - NOM, None)
    for op, a in r.value: getattr(t2, op)(*a)
    cs = t2.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
    if new:
        csi.charStringsIndex.append(cs); csi.charStrings[name] = len(csi.charStringsIndex) - 1
    else:
        csi.charStringsIndex[csi.charStrings[name]] = cs
    hmtx.metrics[name] = (width, int(bounds(r.value)[0]))

# ---- đ Đ: thanh ngang dày 52 (gần nét ngang giữa của E), giữ advance của d / D ----
import json, os
AC = json.load(open(sys.argv[3])) if len(sys.argv) > 3 and os.path.exists(sys.argv[3]) else {}
if not AC: print("addons: chưa có addons.json — dùng số mẫu, PHẢI đo lại thanh đ Đ cho font này", file=sys.stderr)
BAR = AC.get("bar", 52); _d = AC.get("d", [220, 734, 480]); _D = AC.get("D", [10, 421, 300])
NEW = {0x0111: ("dcroat", "d", (_d[0], _d[1] - BAR / 2, _d[2], _d[1] + BAR / 2)),
       0x0110: ("Dcroat", "D", (_D[0], _D[1] - BAR / 2, _D[2], _D[1] + BAR / 2))}
order = list(f.getGlyphOrder())
_had = {name for cp, (name, *_r) in NEW.items() if cp in cmap}   # đ Đ có sẵn → không đụng
for cp, (name, base, r) in NEW.items():
    if cp in cmap: continue
    put(name, rec(base) + rect(*r), gs[base].width, True)
    order.append(name)
f.setGlyphOrder(order); top.charset = order; f["maxp"].numGlyphs = len(order)
for t in f["cmap"].tables:
    if t.isUnicode():
        for cp, (name, *_r) in NEW.items(): t.cmap.setdefault(cp, name)
gdef = f["GDEF"].table if "GDEF" in f else None
if gdef and gdef.GlyphClassDef:
    for name, *_r in NEW.values(): gdef.GlyphClassDef.classDefs[name] = 1

# kerning: đ Đ thừa hưởng cặp kern của d D
pairs = {name: base for name, base, _r in NEW.values() if name not in _had}
added_new = {n for n, *_r in NEW.values()} - set(_had)
gpos = f.get("GPOS")
lookups = gpos.table.LookupList.Lookup if added_new and gpos and gpos.table.LookupList else []
for lk in lookups:
    for st in lk.SubTable:
        if lk.LookupType == 9: st = st.ExtSubTable
        if getattr(st, "LookupType", lk.LookupType) != 2: continue   # chỉ PairPos (bỏ qua mark / mkmk / context)
        if st.Format == 1:
            for ps in st.PairSet:
                add = [copy.deepcopy(r) for r in ps.PairValueRecord if r.SecondGlyph in pairs.values()]
                for r in add:
                    r.SecondGlyph = [n for n, b in pairs.items() if b == r.SecondGlyph][0]
                ps.PairValueRecord += add
                ps.PairValueRecord.sort(key=lambda r: f.getGlyphID(r.SecondGlyph)); ps.PairValueCount = len(ps.PairValueRecord)
            items = list(zip(st.Coverage.glyphs, st.PairSet))
            for n, b in pairs.items():
                if b in st.Coverage.glyphs: items.append((n, copy.deepcopy(st.PairSet[st.Coverage.glyphs.index(b)])))
            items.sort(key=lambda p: f.getGlyphID(p[0]))
            st.Coverage.glyphs = [p[0] for p in items]; st.PairSet = [p[1] for p in items]; st.PairSetCount = len(items)
        elif st.Format == 2:
            for n, b in pairs.items():
                if b in st.Coverage.glyphs:
                    st.Coverage.glyphs.append(n)
                    c = st.ClassDef1.classDefs.get(b)
                    if c: st.ClassDef1.classDefs[n] = c
                c2 = st.ClassDef2.classDefs.get(b)
                if c2: st.ClassDef2.classDefs[n] = c2
            st.Coverage.glyphs.sort(key=f.getGlyphID)

# ---- ĩ Ĩ: dấu ngã rộng hơn chữ i → thu hẹp theo chiều ngang cho nằm trong advance ----
gs = f.getGlyphSet()
for cp in (0x0129, 0x0128):
    n = cmap.get(cp)
    if not n: continue
    w = gs[n].width
    cs = contours(rec(n))
    big = max(cs, key=lambda c: (bounds(c)[3] - bounds(c)[1]))
    top_y = bounds(big)[3]
    marks = [c for c in cs if bounds(c)[1] > top_y - 5]
    rest = [c for c in cs if c not in marks]
    mx0, _, mx1, _ = bounds([x for c in marks for x in c])
    room = w - 2 * 6
    if mx1 - mx0 <= room: continue
    s = room / (mx1 - mx0); cx = w / 2
    out = [x for c in rest for x in c]
    for c in marks:
        r = RecordingPen(); tp = TransformPen(r, (s, 0, 0, 1, cx - (mx0 + mx1) / 2 * s, 0))
        for op, a in c: getattr(tp, op)(*a)
        out += r.value
    put(n, out, w, False)
    print("tilde on %s: %.0f → %.0f wide (advance %d)" % (n, mx1 - mx0, room, w))

# kiểm tra width CFF == hmtx
from fontTools.pens.basePen import NullPen
for g in f.getGlyphOrder():
    c = csi[g]; c.draw(NullPen()); assert abs(c.width - hmtx[g][0]) < 0.5, g
f.save(sys.argv[2]); print("→", sys.argv[2])
