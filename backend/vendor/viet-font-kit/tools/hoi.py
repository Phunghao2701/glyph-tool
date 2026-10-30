"""Dấu hỏi mới (vòng 3): từ dấu ? của font (bỏ chấm, cắt cuống) — bản A giữ đầu giọt của ?, bản B thay đầu bằng tai chữ g.
Xuất contours ở toạ độ local (đáy-giữa = 0,0) để đưa vào config "marks": {"hook":…, "hook_s":…} của vnfont.py.
usage: hoi.py SRC.otf OUT.json VARIANT(A|B) H XSTRETCH [CUT_Y] [ROT] [EAR_S]"""
import sys, json, math
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
import pathops
f = TTFont(sys.argv[1]); gs = f.getGlyphSet(); cm = f.getBestCmap()
var, H, XS = sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
CUT = float(sys.argv[6]) if len(sys.argv) > 6 else 260
ROT = float(sys.argv[7]) if len(sys.argv) > 7 else 150
ES = float(sys.argv[8]) if len(sys.argv) > 8 else 0.9
I_, U_, D_ = pathops.PathOp.INTERSECTION, pathops.PathOp.UNION, pathops.PathOp.DIFFERENCE
def P(n):
    p = pathops.Path(); gs[cm[ord(n)]].draw(p.getPen()); return p
def rect(x0, y0, x1, y1):
    p = pathops.Path(); pen = p.getPen(); pen.moveTo((x0, y0)); pen.lineTo((x0, y1)); pen.lineTo((x1, y1)); pen.lineTo((x1, y0)); pen.closePath(); return p
def op(a, b, k): return pathops.op(a, b, k, fix_winding=True)
def tf(p, t):
    o = pathops.Path(); p.draw(TransformPen(o.getPen(), t)); return o
q = op(P("?"), rect(-100, CUT, 1000, 2000), I_)              # bỏ chấm + phần cuống dưới
if var == "B":
    q = op(q, rect(-100, 795, float(__import__("os").environ.get("TX2", 0)), 2000), D_)
    q = op(q, rect(-100, 560, float(__import__("os").environ.get("TX", 120)), float(__import__("os").environ.get("TY", 775))), D_)               # bỏ đầu giọt của ?
    ear = op(P("g"), rect(355, float(__import__("os").environ.get("EARCUT", 600)), 600, 900), I_)          # bầu tai g
    x0, y0, x1, y1 = ear.bounds; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    a = math.radians(ROT); c, s = math.cos(a), math.sin(a)
    ear = tf(ear, (c * ES, s * ES, -s * ES, c * ES, -cx * c * ES + cy * s * ES + float(__import__("os").environ.get("EX", 75)), -cx * s * ES - cy * c * ES + float(__import__("os").environ.get("EY", 680))))
    q = op(q, ear, U_)
if var == "B":   # lấp khe nối giữa bầu tai g và vòm (đóng hình thái), rồi fit lại bezier
    import os
    sys.path.insert(0, os.environ.get("KIT", "."))
    import qhook, marks as MK
    r0 = RecordingPen(); q.draw(r0); cs0, cur = [], []
    for o_, a_ in r0.value:
        cur.append((o_, a_))
        if o_ == "closePath": cs0.append(cur); cur = []
    R = float(os.environ.get("CLOSE", 10))
    g = qhook.to_poly(cs0).buffer(R, join_style="round").buffer(-R, join_style="round")
    q = pathops.Path(); pen = q.getPen()
    for c in MK.poly_to_contours(g, simplify=0.4):
        for o_, a_ in c: getattr(pen, o_)(*a_)
x0, y0, x1, y1 = q.bounds; k = H / (y1 - y0)
q = tf(q, (k * XS, 0, 0, k, -(x0 + x1) / 2 * k * XS, -y0 * k))
BUF = float(__import__("os").environ.get("BUF", 0))
if BUF:   # bù nét khi thu nhỏ: nở đều mỗi bên BUF đơn vị, fit lại bezier
    import os
    sys.path.insert(0, os.environ.get("KIT", "."))
    import qhook, marks as MK
    r0 = RecordingPen(); q.draw(r0); cs0, cur = [], []
    for o_, a_ in r0.value:
        cur.append((o_, a_))
        if o_ == "closePath": cs0.append(cur); cur = []
    g = qhook.to_poly(cs0).buffer(BUF, join_style="round")
    q = pathops.Path(); pen = q.getPen()
    for c in MK.poly_to_contours(g, simplify=0.3):
        for o_, a_ in c: getattr(pen, o_)(*a_)
    x0, y0, x1, y1 = q.bounds
    q = tf(q, (1, 0, 0, 1, -(x0 + x1) / 2, -y0))
r = RecordingPen(); q.draw(r); cs, cur = [], []
for o_, a_ in r.value:
    cur.append([o_, [list(map(lambda v: round(v, 1), p)) for p in a_]])
    if o_ == "closePath": cs.append(cur); cur = []
json.dump(cs, open(sys.argv[2], "w"))
print(var, "bounds", [round(v) for v in q.bounds])
