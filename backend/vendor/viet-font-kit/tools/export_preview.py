"""Dữ liệu khung gõ thử trong mục R: nét từng chữ (bỏ râu, bỏ dấu nặng) để trang tự ghép râu / dấu nặng theo thanh kéo.
usage: export_preview.py FONT.otf SRC.otf horn5_ui.json OUT.json   (KIT=… cho qhook)"""
import sys, os, json, unicodedata
sys.path.insert(0, os.environ.get("KIT", "."))
import qhook
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
FONT, SRC, UI, OUT = sys.argv[1:5]
f = TTFont(FONT); gs = f.getGlyphSet(); cm = f.getBestCmap()
s = TTFont(SRC); sgs = s.getGlyphSet(); scm = s.getBestCmap()
def contours(gset, n):
    r = RecordingPen(); gset[n].draw(r); cs, cur = [], []
    for o, a in r.value:
        cur.append((o, a))
        if o == "closePath": cs.append(cur); cur = []
    return cs
def d_of(cs):
    p = SVGPathPen(None)
    for c in cs:
        for o, a in c: getattr(p, o)(*a)
    return p.getCommands()
def bb(cs):
    b = BoundsPen(None)
    for c in cs:
        for o, a in c: getattr(b, o)(*a)
    return b.bounds
VN = "aăâbcdđeêghiklmnoôơpqrstuưvxyAĂÂBCDĐEÊGHIKLMNOÔƠPQRSTUƯVXYfjwzFJWZ0123456789.,;:!?'\"()-–—/&%·…“”‘’«»*+=#@"
chars = set(VN)
for cp in cm:
    ch = chr(cp); d = unicodedata.normalize("NFD", ch)
    if len(d) > 1 and d[0].lower() in "aeiouy" and all(m in "̛̣̀́̃̉̂̆" for m in d[1:]): chars.add(ch)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flatpoly import glyph_poly
from shapely.geometry import box as _box
B0, BS, NB = -320, 16, 103
def prof(ch):
    P = glyph_poly(f, ch); L, R = [], []
    for i in range(NB):
        y = B0 + i * BS; q = P.intersection(_box(-2000, y, 4000, y + BS)) if P is not None else None
        if q is None or q.is_empty: L.append(None); R.append(None)
        else: L.append(round(q.bounds[0])); R.append(round(q.bounds[2]))
    return L, R
G = {}
for ch in sorted(chars):
    if ord(ch) not in cm: continue
    d = unicodedata.normalize("NFD", ch); horn = "̛" in d; dot = "̣" in d
    src = unicodedata.normalize("NFC", d.replace("̛", "")) if horn else ch
    n = cm[ord(src)]; cs = contours(gs, n); e = {"w": gs[n].width}
    if dot:
        dc = [c for c in cs if bb([c])[3] < -20]; cs = [c for c in cs if bb([c])[3] >= -20]
        b = bb(dc); e["dot"] = round((b[0] + b[2]) / 2, 1)
    if horn:
        L = d[0]; e["h"] = L
        top = bb(contours(sgs, scm[ord(L)]))[3]
        mk = [c for c in cs if bb([c])[1] > top - 5]; cs = [c for c in cs if bb([c])[1] <= top - 5]
        if mk:
            e["m"] = d_of(mk); P = qhook.to_poly(mk)
            geoms = getattr(P, "geoms", [P]); pts = []
            for g in geoms: pts += list(g.exterior.coords)[::3]
            e["mp"] = [[round(x), round(y)] for x, y in pts]
    e["d"] = d_of(cs); G[ch] = e
    # profile ngang (dải 16 đv từ -320): mép trái của chữ hoàn chỉnh; mép phải của chữ trơn (cho kern sau râu)
    e["lp"] = prof(ch)[0]
    if horn: e["rp"] = prof(src)[1]
# dấu nặng = chấm chữ i của font (luật người dùng), đặt tâm 0,0
_ic = contours(sgs, scm[ord("i")]); _stem = max(_ic, key=lambda c: bb([c])[3] - bb([c])[1])
idot = [c for c in _ic if bb([c])[1] > bb([_stem])[3] - 5]; ib = bb(idot)   # chấm i = contour nằm trên đỉnh thân i (không dùng số cứng)
from fontTools.pens.transformPen import TransformPen
sp = SVGPathPen(None)
for c in idot:
    tp = TransformPen(sp, (1, 0, 0, 1, -(ib[0] + ib[2]) / 2, -(ib[1] + ib[3]) / 2))
    for o, a in c: getattr(tp, o)(*a)
ui = json.load(open(UI))
ui["G"] = G; ui["space"] = gs[cm[32]].width; ui["band"] = [B0, BS, NB]
ui["ndot"] = {"d": sp.getCommands(), "w": round(ib[2] - ib[0]), "h": round(ib[3] - ib[1])}
pb = BoundsPen(sgs); sgs[scm[ord(".")]].draw(pb); ui["period"] = [round(pb.bounds[2] - pb.bounds[0]), round(pb.bounds[3] - pb.bounds[1])]
json.dump(ui, open(OUT, "w"), separators=(",", ":"))
print("export_preview:", len(G), "chữ,", os.path.getsize(OUT) // 1024, "KB")
