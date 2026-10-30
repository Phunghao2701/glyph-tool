"""Râu ơ ư Ơ Ư kiểu thanh đậm (vòng 4, theo mẫu didone): cổ mảnh mọc từ một điểm trên viền chữ, kết bằng bầu tròn
lấy từ đầu giọt chữ r của chính font. Luật ghép (feedback người dùng):
  * râu chỉ chạm chữ gốc ở MỘT điểm nối (vai o / đầu chân phải u / mút chân serif U), cắm vào sâu tối đa `embed`;
  * phần râu chồng lên chữ gốc ≤ `max_overlap` đơn vị² — không phủ lên serif, không tạo khối lạ ở chân râu;
  * chữ gốc giữ nguyên nét (body ∪ râu, không sửa body).
usage: horn5.py IN.otf OUT.otf horn5.json
cfg: {"o":{"rot":..,"flip":true,"s":..,"embed":..,"at":y_frac}, "O":…, "u":…, "U":…, "clear":10, "tone_gap":28}"""
import sys, os, json, math, unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
import pathops
sys.path.insert(0, os.environ.get("KIT", os.path.dirname(os.path.abspath(__file__))))
import qhook
from shapely.geometry import Point, box as sbox
from shapely.ops import nearest_points

f = TTFont(sys.argv[1]); CFG = json.load(open(sys.argv[3]))
SRC = TTFont(CFG.get("src", sys.argv[1]))
cff = f["CFF "].cff; top = cff.topDictIndex[0]; csi = top.CharStrings
NOM = getattr(top.Private, "nominalWidthX", 0)
hmtx = f["hmtx"]; cmap = f.getBestCmap(); gs = f.getGlyphSet(); sgs = SRC.getGlyphSet(); scm = SRC.getBestCmap()
U_, I_, D_ = pathops.PathOp.UNION, pathops.PathOp.INTERSECTION, pathops.PathOp.DIFFERENCE

def op(a, b, k): return pathops.op(a, b, k, fix_winding=True)
def path_of(gset, n):
    p = pathops.Path(); gset[n].draw(p.getPen()); return p
def rect(x0, y0, x1, y1):
    p = pathops.Path(); pen = p.getPen()
    pen.moveTo((x0, y0)); pen.lineTo((x0, y1)); pen.lineTo((x1, y1)); pen.lineTo((x1, y0)); pen.closePath(); return p
def tf(p, t):
    o = pathops.Path(); p.draw(TransformPen(o.getPen(), t)); return o
def poly(p):
    r = RecordingPen(); p.draw(r); cs, cur = [], []
    for o_, a_ in r.value:
        cur.append((o_, a_))
        if o_ == "closePath": cs.append(cur); cur = []
    return qhook.to_poly(cs)

# đầu giọt chữ r: cánh tay từ x=TAIL_X sang phải + bầu tròn; đuôi (điểm nối) = giữa lát cắt tại TAIL_X
TAIL_X = CFG.get("tail_x", 215)
R = path_of(sgs, scm[ord("r")])
PIECE = op(R, rect(TAIL_X, 380, 600, 700), I_)
_s = poly(PIECE).intersection(sbox(TAIL_X - .5, -999, TAIL_X + 2, 2000)).bounds
TAIL = (TAIL_X, (_s[1] + _s[3]) / 2)

def horn_piece(L):
    c = CFG[L]; th = math.radians(c["rot"]); s = c["s"]; fy = -1 if c.get("flip") else 1
    # quanh điểm đuôi: lật dọc (tuỳ chọn) → xoay → co giãn
    a, b = math.cos(th) * s, math.sin(th) * s
    m = (a, b, -b * fy, a * fy)        # [x' y'] = M·[x y] với M = R(th)·S·diag(1,fy)
    m = (a, b, -b * fy, a * fy)
    tx, ty = TAIL
    def T(dx, dy):
        return (m[0], m[1], m[2], m[3], dx - (m[0] * tx + m[2] * ty), dy - (m[1] * tx + m[3] * ty))
    return T, c

def outer_right(p, y):
    shape = poly(p)
    if shape.is_empty:
        raise ValueError("Cannot find an attachment point on an empty glyph outline.")
    bounds = shape.bounds
    if not all(math.isfinite(value) for value in bounds):
        raise ValueError("Cannot find an attachment point on a glyph with invalid bounds.")

    section = shape.intersection(sbox(-999, y - .5, 3000, y + .5))
    if not section.is_empty and math.isfinite(section.bounds[2]):
        return section.bounds[2]

    # Some fonts have a lowercase o shorter than u. If the requested scanline
    # misses the outline, anchor to the nearest point on its boundary instead
    # of passing NaN coordinates into the horn geometry.
    edge = nearest_points(Point(bounds[2] + 1, y), shape.boundary)[1]
    if not math.isfinite(edge.x):
        raise ValueError("Cannot find a finite attachment point on the glyph outline.")
    return edge.x

def attach_point(L, body):
    """điểm nối trên viền chữ GỐC (không dấu)"""
    c = CFG[L]; B = body.bounds
    if L in "oO":                       # vai phải: viền ngoài ở độ cao at·h
        y = c.get("ty", B[1] + (B[3] - B[1]) * c.get("at", 0.86)); return (outer_right(body, y), y)
    # u U: mút phải của đỉnh chân phải (u: góc trên phải thân; U: mút serif)
    y = c.get("ty", B[3] - c.get("down", 4)); return (outer_right(body, y), y)

def put(name, path, width):
    r = RecordingPen(); path.draw(r)
    t2 = T2CharStringPen(width - NOM, None)
    for o_, a in r.value: getattr(t2, o_)(*a)
    csi.charStringsIndex[csi.charStrings[name]] = t2.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
    hmtx.metrics[name] = (width, int(math.floor(path.bounds[0])))

def split_marks(n, base_top):
    r = RecordingPen(); gs[n].draw(r); cs, cur = [], []
    for o_, a in r.value:
        cur.append((o_, a))
        if o_ == "closePath": cs.append(cur); cur = []
    body = pathops.Path(); marks = pathops.Path()
    for c in cs:
        p = pathops.Path(); pen = p.getPen()
        for o_, a in c: getattr(pen, o_)(*a)
        tgt = marks if p.bounds[1] > base_top - 5 else body
        pen = tgt.getPen()
        for o_, a in c: getattr(pen, o_)(*a)
    return body, marks

def kp(L):
    return CFG["all"] if "all" in CFG else CFG["uc" if L.isupper() else "lc"]

def ox(body, y):
    return outer_right(body, y)

def horn_pts(L, body):
    """râu VER 1 (kệ: cổ chạy ngang từ đỉnh chân phải rồi dựng lên) + thanh đậm (vòng 7):
    cổ mảnh `thin` tới t0, rồi dày dần (mũ p) thành đầu giọt `head` như tai chữ g.
    Gốc (0,0) = góc trên phải chân / vai. U u: đỉnh chân phải. O o: CÙNG độ cao gốc với U u (+ dyO)
    → đỉnh râu Ơ = Ư, cổ không phải kéo dài."""
    import marks as MK
    # vòng 9: MỘT bộ thông số chung ("all"); chữ thường = chữ hoa × lc_ratio (cả dáng lẫn độ dày)
    up = L.isupper(); k = kp(L); s = 1.0 if up else CFG.get("lc_ratio", 0.9)
    ref = path_of(sgs, scm[ord("U" if up else "u")]); top = ref.bounds[3]
    # dyU: gốc râu Ư lên / xuống trên mép phải thân U (thanh "gốc râu Ư"); gốc Ơ theo cùng độ cao gốc Ư (+ dyO riêng)
    y0 = top + k.get("dyU", 0) * s + (k.get("dyO", 0) if L in "oO" else 0)
    if L in "uU": x0 = ox(body, y0 - 60)
    else: x0 = ox(body, y0 - 50 * s) - 8
    R, H = k["reach"], k["rise"]
    pts = MK.bez((-70, -50), (6, -56), (R + 2, -16), (R, H), 60)
    pts = [(x0 + x * s, y0 + y * s) for x, y in pts]
    n = len(pts) - 1; t0 = k.get("t0", 0.3); ws = []
    for i in range(n + 1):
        t = i / n; u = max(0.0, (t - t0) / (1 - t0))
        ws.append((k["thin"] + (k["head"] - k["thin"]) * u ** k["p"]) * (1.0 if up else CFG.get("lc_wratio", s)))   # độ dày chữ thường: hệ số riêng (mặc định = tỉ lệ dáng)
    return pts, ws, (x0, y0)

def stroke_horn(L, body):
    import marks as MK
    pts, ws, (x0, y0) = horn_pts(L, body)
    sh = MK.vstroke(pts, ws)
    # cắt gốc râu trong lòng nét chữ: không để phần gốc lòi vào lòng chữ U / O (luật ghép một điểm)
    sh = sh.intersection(sbox(x0 - kp(L).get("clip", 36), -999, 3000, 3000))
    out = pathops.Path(); pen = out.getPen()
    for cont in MK.poly_to_contours(sh, simplify=0.3):
        for o_, a_ in cont: getattr(pen, o_)(*a_)
    return out

HORNS = {}
for L in "oOuU":
    body = path_of(sgs, scm[ord(L)])
    hp = stroke_horn(L, body); px, py = horn_pts(L, body)[2]
    if hp is None:
        T, c = horn_piece(L); e = c.get("embed", 14)
        hp = tf(tf(PIECE, T(px, py)), (1, 0, 0, 1, -e * 0.7, -e * 0.7))
    inter = op(hp, body, I_)
    ov = poly(inter).area if inter.bounds[2] > inter.bounds[0] else 0
    # phần râu nhô ra khỏi đỉnh chữ gốc ngay tại gốc (không được tạo cục lạ trên serif / vai)
    HORNS[L] = (hp, body.bounds[3])
    print("%s: nối tại (%d, %d), chồng lên chữ gốc %d đv², râu x %d-%d y %d-%d" % ((L, px, py, ov) + tuple(hp.bounds)))
    if ov > CFG.get("max_overlap", 2500): print("   ! chồng quá nhiều — chỉnh gốc râu")

done = []
for cp, name in sorted(cmap.items()):
    d = unicodedata.normalize("NFD", chr(cp))
    if "̛" not in d or cp == 0x031B: continue
    L = d[0]
    plain = cmap[ord(unicodedata.normalize("NFC", d.replace("̛", "")))]
    hp, base_top = HORNS[L]
    body, marks = split_marks(plain, base_top)
    w0 = gs[plain].width
    from fontTools.pens.boundsPen import BoundsPen
    _bp = BoundsPen(None); hp.draw(_bp)
    w = int(math.ceil(max(w0, _bp.bounds[2] + CFG.get("clear", 10))))
    sh = up = 0
    if marks.bounds[2] > marks.bounds[0]:
        need = CFG.get("tone_gap", 28)
        while poly(tf(marks, (1, 0, 0, 1, -sh, 0))).distance(poly(hp)) < need and sh < CFG.get("max_shift", 40): sh += 4
        marks = tf(marks, (1, 0, 0, 1, -sh, 0))
        while poly(marks).distance(poly(hp)) < need and up < 200:
            marks = tf(marks, (1, 0, 0, 1, 0, 4)); up += 4
    put(name, op(op(body, hp, U_), marks, U_), w)
    done.append("%s %d→%d%s%s" % (chr(cp), w0, w, " ←%d" % sh if sh else "", " ↑%d" % up if up else ""))
if 0x031B in cmap:
    ow = sgs[scm[ord("o")]].width
    put(cmap[0x031B], tf(HORNS["o"][0], (1, 0, 0, 1, -ow, 0)), 0)
f.save(sys.argv[2])
print("horn2:", " · ".join(done))
