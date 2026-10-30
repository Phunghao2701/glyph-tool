"""Áp thông số CHỈNH ĐỒNG LOẠT (tab Chỉnh dấu · Đồng loạt, db <DOC>/batch/p) vào font .ttf — cùng công thức với trang:
  mỗi dấu loại k: dời (dx, dy) + co giãn sc % quanh tâm đáy dấu (dấu nặng: tâm đỉnh); chữ hoa thêm uy; dấu thanh chồng thêm (sx, sy)
  và đi theo dấu mũ / trăng bên dưới; “mọi dấu” (all): dy + sc cho mọi dấu trên.
Tách thân / dấu bằng export_batch.split (cùng cách trang dùng). Chữ được sửa ghi lại thành glyph thường (bỏ dạng ghép).
Chạy winfix.py sau đó (dấu cao hơn → win phải nâng).
usage: batch_apply.py FONT.ttf PARAMS.json OUT.ttf      PARAMS = {"p": {...}} (bản ghi db) hoặc thẳng {...}
build by @nhatmotion"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_batch import split, VN
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen

src, prm, out = sys.argv[1:4]
P = json.load(open(prm)); P = P.get("p", P)
Z = dict(dx=0, dy=0, sc=100, uy=0, sx=0, sy=0)
def g(k): d = dict(Z); d.update(P.get(k) or {}); return d
A = g("all")
def shift(m, uc, cap):
    p = g(m["k"]); above = m["k"] != "dot"
    dx = p["dx"] + (p["sx"] + cap[0] if m["st"] else 0)
    dy = p["dy"] + (p["uy"] if uc else 0) + (p["sy"] + cap[1] if m["st"] else 0) + (A["dy"] if above else 0)
    sc = p["sc"] / 100.0 * (A["sc"] / 100.0 if above else 1)
    return dx, dy, sc

f = TTFont(src); glyf = f["glyf"]; hmtx = f["hmtx"]; changed = []
for ch in VN:
    r = split(f, ch)
    if not r or not r["marks"]: continue
    cap = (0, 0)
    for m in r["marks"]:
        if m["k"] in ("circ", "breve"): s = shift(m, r["uc"], (0, 0)); cap = (s[0], s[1])
    moves = []
    for m in r["marks"]:
        dx, dy, sc = shift(m, r["uc"], cap)
        if abs(dx) < 0.5 and abs(dy) < 0.5 and abs(sc - 1) < 1e-3: moves.append((m, None)); continue
        b = m["bb"]; ax = (b[0] + b[2]) / 2; ay = b[3] if m["k"] == "dot" else b[1]
        moves.append((m, (sc, 0, 0, sc, ax + dx - sc * ax, ay + dy - sc * ay)))
    if all(t is None for _, t in moves): continue
    pen = TTGlyphPen(None)
    def draw(cs, pn):
        for c, _ in cs:
            for op, a in c:
                if op == "moveTo": pn.moveTo(a[0])
                elif op == "lineTo": pn.lineTo(a[0])
                elif op == "qCurveTo": pn.qCurveTo(*a)
                elif op == "curveTo": pn.curveTo(*a)
                elif op == "closePath": pn.closePath()
                elif op == "endPath": pn.endPath()
    draw(r["body"], pen)
    for m, t in moves: draw(m["cs"], TransformPen(pen, t) if t else pen)
    gl = pen.glyph(); gl.recalcBounds(glyf); glyf[r["name"]] = gl
    hmtx[r["name"]] = (hmtx[r["name"]][0], getattr(gl, "xMin", 0) or 0)
    changed.append(ch)
f.save(out)
print("batch_apply: sửa %d chữ → %s" % (len(changed), out))
print("  " + "".join(changed))
