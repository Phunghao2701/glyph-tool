"""Export glyph outlines + composition recipes for the review page's vector editor.
usage: export_editor.py FONT RECIPES OUT.json"""
import sys, json, math
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
f = TTFont(sys.argv[1]); gs = f.getGlyphSet(); cmap = f.getBestCmap()
R = json.load(open(sys.argv[2]))
class P(BasePen):
    def __init__(s): super().__init__(gs); s.c = []; s.cur = None   # gs: chữ ghép (composite .ttf) tự tách
    def _moveTo(s, p): s.cur = [["M", [r(p)]]]
    def _lineTo(s, p): s.cur.append(["L", [r(p)]])
    def _curveToOne(s, a, b, c): s.cur.append(["C", [r(a), r(b), r(c)]])
    def _qCurveToOne(s, a, b): s.cur.append(["Q", [r(a), r(b)]])
    def _closePath(s): s.c.append(s.cur); s.cur = None
    _endPath = _closePath
def r(p): return [round(p[0], 1), round(p[1], 1)]
def _mid(a, b): return [round((a[0] + b[0]) / 2, 1), round((a[1] + b[1]) / 2, 1)]
def conv(js):  # recipe contour format -> editor format
    """Bàn vẽ chỉ hiểu Q một điểm điều khiển. Font .ttf ghi qCurveTo nhiều điểm (điểm trên đường ngầm ở giữa 2 điểm
    điều khiển) → tách thành từng đoạn Q; contour toàn điểm điều khiển (điểm cuối None) thì mở bằng M ở điểm giữa.
    Không tách = glyph vỡ (lòng chữ đặc, nét gãy) ở “Xem trong chữ” và khung vẽ (lỗi B, font .ttf)."""
    m = {"moveTo": "M", "lineTo": "L", "curveTo": "C"}
    out = []
    for c in js:
        cc = []
        for op, pts in c:
            if op in m: cc.append([m[op], pts]); continue
            if op != "qCurveTo": continue
            pts = list(pts)
            if pts[-1] is None:                                   # toàn điểm điều khiển
                offs = pts[:-1]; st = _mid(offs[-1], offs[0]); cc.append(["M", [st]])
                for i, q in enumerate(offs): cc.append(["Q", [q, _mid(q, offs[(i + 1) % len(offs)])]])
                continue
            offs, end = pts[:-1], pts[-1]
            for i, q in enumerate(offs):
                cc.append(["Q", [q, end if i == len(offs) - 1 else _mid(q, offs[i + 1])]])
        out.append(cc)
    return out
G = {}
for cp, n in sorted(cmap.items()):
    p = P(); gs[n].draw(p)
    G[n] = {"u": cp, "w": gs[n].width, "c": p.c}
os2 = f["OS/2"]
out = {"upm": f["head"].unitsPerEm, "xh": getattr(os2, "sxHeight", 0) or 500, "cap": getattr(os2, "sCapHeight", 0) or 700,
       "asc": os2.sTypoAscender, "desc": os2.sTypoDescender, "tildeW": R["tilde_w"],
       "lbAsc": f["hhea"].ascent, "lbDesc": f["hhea"].descent, "axis": R.get("axis", 0),
       "glyphs": G,
       "marks": {k: conv(v) for k, v in R["marks"].items()},
       "recipes": {n: {"u": v["u"], "w": v["w"], "s": conv(v["static"]), "m": v["marks"], **({"sax": [round(v["sax"][0], 2), round(v["sax"][1], 4)]} if v.get("sax") else {})} for n, v in R["glyphs"].items()}}
# ---- đồng bộ recipe với nét THẬT trong font (luật: ghép recipe phải ra đúng glyph) ----
# Sau vnfont còn place_hoi (dời dấu hỏi), horn5 (râu ghép vào thân, dời dấu thanh)… nên recipe của vnfont có thể lệch.
# Lệch thì dựng lại recipe từ glyph thật: contour trên đỉnh thân / dưới chân = dấu (gán vào dấu gần nhất của recipe, tính lại
# phép biến đổi theo khung bao), phần còn lại (kể cả râu đã ghép) = nét tĩnh. Vẫn lệch thì bỏ recipe, bàn vẽ hiện glyph thật.
def _bb(cs):
    xs = [p[0] for c in cs for _o, pts in c for p in pts]; ys = [p[1] for c in cs for _o, pts in c for p in pts]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None
def _tf(cs, t):
    return [[[o, [[t[0] * x + t[2] * y + t[4], t[1] * x + t[3] * y + t[5]] for x, y in pts]] for o, pts in c] for c in cs]
def _close(a, b, tol=1):
    return a is not None and b is not None and all(abs(x - y) <= tol for x, y in zip(a, b))
def _compose(rc):
    cs = list(rc["s"])
    for mi in rc["m"]: cs += _tf(out["marks"].get(mi["m"], []), mi["t"])
    return cs
fixed, dropped = [], []
for n, rc in list(out["recipes"].items()):
    real = G[n]["c"] if n in G else None
    if real is None: continue
    nh = sum(1 for mi in rc["m"] if mi["m"].startswith("horn") and out["marks"].get(mi["m"]))   # râu RỜI (người dùng 27/10): font gộp râu vào thân, bàn vẽ giữ râu là hình riêng → thêm 1 contour / râu
    if len(_compose(rc)) == len(real) + nh and _close(_bb(_compose(rc)), _bb(real)): continue
    sb = _bb(rc["s"]) or _bb(real); top, bot = sb[3], sb[1]
    up_, lo_, st_ = [], [], []
    for c in real:
        b = _bb([c])
        (up_ if b[1] >= top - 5 else lo_ if b[3] <= bot + 5 else st_).append(c)
    inst = [mi for mi in rc["m"] if mi["m"] != "horn" and out["marks"].get(mi["m"])]
    pred = {i: _bb(_tf(out["marks"][mi["m"]], mi["t"])) for i, mi in enumerate(inst)}
    groups = {i: [] for i in pred}
    for c in up_ + lo_:
        b = _bb([c]); cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        same = [i for i in pred if (pred[i][1] + pred[i][3]) / 2 > top - 5 if cy > top - 5] if cy > top - 5 else [i for i in pred if (pred[i][1] + pred[i][3]) / 2 < bot + 5]
        cand = same or list(pred)
        if not cand: st_.append(c); continue
        # gán theo DÁNG trước (cỡ khung gần nhau: dấu mũ ≠ dấu huyền), vị trí sau — dấu có thể đã dời hẳn chỗ (vd anchor font gốc)
        def _cost(i):
            lb_ = _bb(out["marks"][inst[i]["m"]])    # cỡ dấu GỐC (chưa co): dấu có thể đã đổi cỡ / chỗ (anchor font gốc)
            return (abs(math.log(max(1, b[2] - b[0]) / max(1, lb_[2] - lb_[0]))) + abs(math.log(max(1, b[3] - b[1]) / max(1, lb_[3] - lb_[1])))
                    + 0.0008 * (abs((pred[i][0] + pred[i][2]) / 2 - cx) + abs((pred[i][1] + pred[i][3]) / 2 - cy)))
        i = min(cand, key=_cost)
        groups[i].append(c)
    m2 = []
    for i, mi in enumerate(inst):
        if not groups[i]: continue
        lb, fb = _bb(out["marks"][mi["m"]]), _bb(groups[i])
        sx = (fb[2] - fb[0]) / max(1e-6, lb[2] - lb[0]); sy = (fb[3] - fb[1]) / max(1e-6, lb[3] - lb[1])
        m2.append({"m": mi["m"], "t": [round(sx, 4), 0, 0, round(sy, 4), round(fb[0] - lb[0] * sx, 2), round(fb[1] - lb[1] * sy, 2)]})
    nr = dict(rc, s=st_, m=m2, w=G[n]["w"])
    if len(_compose(nr)) == len(real) and _close(_bb(_compose(nr)), _bb(real)): out["recipes"][n] = nr; fixed.append(n)
    else: del out["recipes"][n]; dropped.append(n)
print("export_editor: recipe đồng bộ lại %d (%s) · bỏ %d %s" % (len(fixed), " ".join(chr(G[n]["u"]) for n in fixed[:40]), len(dropped), " ".join(chr(G[n]["u"]) for n in dropped)))
KERN = {}
if "GPOS" in f:
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            st = st.ExtSubTable if lk.LookupType == 9 else st
            effective_type = getattr(st, "LookupType", lk.LookupType)
            if effective_type != 2: continue
            if getattr(st, "Format", None) == 1 and hasattr(st, "PairSet"):
                for g, ps in zip(st.Coverage.glyphs, st.PairSet):
                    for r in ps.PairValueRecord:
                        v = getattr(r.Value1, "XAdvance", 0) or 0
                        if v: KERN.setdefault(g, {})[r.SecondGlyph] = v
            elif getattr(st, "Format", None) == 2:
                c1, c2 = st.ClassDef1.classDefs, st.ClassDef2.classDefs
                for g in st.Coverage.glyphs:
                    row = st.Class1Record[c1.get(g, 0)].Class2Record
                    for g2, k2 in c2.items():
                        v = getattr(row[k2].Value1, "XAdvance", 0) or 0
                        if v: KERN.setdefault(g, {})[g2] = v
out["kern"] = KERN
json.dump(out, open(sys.argv[3], "w"), separators=(",", ":"))
