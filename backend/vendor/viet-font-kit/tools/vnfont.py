#!/usr/bin/env python3
"""vnfont — add the full Vietnamese alphabet to an OTF (CFF) or TTF (glyf) font.

usage:
  python3 -I vnfont.py SRC.otf OUT.otf [--config cfg.json] [--recipes recipes.json]

What it does
  * finds a body + top anchor for a e i o u y / A E I O U Y from the font's own precomposed letters
    (â, ê, ô, û, î, ÿ …) so the new letters share the original bodies and mark heights
  * reuses available source mark outlines and draws a fallback breve when absent
  * generates the marks a Latin font usually lacks: hook above (hỏi), dot below (nặng), horn (ơ ư)
    with stroke weight measured from the font's tilde, unless the config supplies custom outlines
  * stacks marks Vietnamese-style (sắc/huyền/hỏi to the right of the circumflex, ngã on top)
  * copies kerning from the base letter, keeps the base advance width (also for ơ ư)
  * renames the family (default suffix " VN"), raises winAscent/winDescent to stop clipping.
    USE_TYPO_METRICS (fsSelection bit 7) is CLEARED whenever the typo ascender / descender is lower than the ink:
    with the bit set Word (Windows) takes its line box from typo, not win, and CUTS stacked tones on capitals
    (Ấ Ễ Ố → Â Ê Ô — user report 27/10, `serif.regular.condensed.contrast.ttf` VN). Before 27/10 this script SET the bit — a kit bug.
  * optional --recipes: writes how every new glyph was composed (for the review page's live editor)

config keys (all optional):
  suffix        "VN"
  dot           {"k":0.66, "lc":120, "uc":128, "gap":40}      k: 0.5523 circle … 0.80 squarish
  hook          {"s":1.0, "w":null}  w defaults to the tilde weight
  horn          {"style":"arc"|"comma", "w":null, "angle":-28}
  marks         {"hook": contours, "hook_s": contours, "horn": contours, "dot": contours}
                custom mark outlines in mark-local units (as saved by the review page)
  glyphs        {"uni1EA3": {"w":…, "contours":…}}  whole-glyph overrides
  rebuild       ["U+00C0"]  existing letters to rebuild from parts (e.g. a wrong mark in the source)
  caps_stack_flat  0.86  vertical scale of Â Ă's circumflex / breve under a stacked tone (1.0 = keep the source mark as drawn)
  stack_gap_ag  min gap between circumflex and a right-stacked acute / grave (raise when ề ấ look cramped)
"""
import sys, os, math, json, argparse, unicodedata, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib.tables import otTables as ot
import pathops
import marks as MK

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--config"); ap.add_argument("--recipes")
A = ap.parse_args()
CFG = json.load(open(A.config)) if A.config else {}

f = TTFont(A.src)
IS_CFF = "CFF " in f
gs = f.getGlyphSet()
cmap = f.getBestCmap()
UPM = f["head"].unitsPerEm
K = UPM / 1000.0

# ---------------- outline helpers ----------------
def replay(ops, pen):
    for op, a in ops:
        getattr(pen, op)(*a)

def split_contours(ops):
    cs, cur = [], []
    for op, a in ops:
        cur.append((op, a))
        if op in ("closePath", "endPath"):
            cs.append(cur); cur = []
    if cur: cs.append(cur)
    return cs

def contours_of(name):
    r = RecordingPen(); gs[name].draw(r)
    # normalise TrueType qCurveTo into cubic for uniform handling
    from fontTools.pens.basePen import BasePen
    class Cub(BasePen):
        def __init__(s): super().__init__(None); s.v = []
        def _moveTo(s, p): s.v.append(("moveTo", (p,)))
        def _lineTo(s, p): s.v.append(("lineTo", (p,)))
        def _curveToOne(s, a, b, c): s.v.append(("curveTo", (a, b, c)))
        def _closePath(s): s.v.append(("closePath", ()))
        def _endPath(s): s.v.append(("closePath", ()))
    p = Cub(); replay(r.value, p)
    return split_contours(p.v)

def bounds(cs):
    bp = BoundsPen(None)
    for c in cs: replay(c, bp)
    return bp.bounds

def area(c):
    ap_ = AreaPen(); replay(c, ap_); return ap_.value

def transform(cs, t):
    out = []
    for cont in cs:
        r = RecordingPen(); replay(cont, TransformPen(r, t)); out.append(r.value)
    return out

def place_t(cs, cx, ybot, sx=1.0, sy=None, ref=None):
    """Affine that scales mark cs and puts its bbox bottom-centre at (cx, ybot).
    ref: bounds to use instead of cs's own (keeps a user-drawn mark exactly where it was drawn)."""
    sy = sx if sy is None else sy
    x0, y0, x1, y1 = ref or bounds(cs)
    return (sx, 0, 0, sy, cx - (x0 + x1) / 2 * sx, ybot - y0 * sy)

def union(cs):
    p = pathops.Path(); pen = p.getPen()
    for c in cs: replay(c, pen)
    p = pathops.op(p, pathops.Path(), pathops.PathOp.UNION, fix_winding=True)
    r = RecordingPen(); p.draw(r)
    return split_contours(r.value)

def split_body(name):
    cs = contours_of(name)
    big = max(cs, key=lambda c: abs(area(c)))
    top = bounds([big])[3]
    body = [c for c in cs if bounds([c])[1] < top - 5 * K]
    mk = [c for c in cs if bounds([c])[1] >= top - 5 * K]
    return body, mk

def gname(ch):
    return cmap.get(ord(ch))

def to_json_contours(cs):
    return [[[op, [list(map(lambda v: round(v, 1), p)) for p in a]] for op, a in c] for c in cs]

def from_json_contours(js):
    return [[(op, tuple(tuple(p) for p in a)) for op, a in c] for c in js]

# ---------------- measurements ----------------
def stroke_weight(cs):
    """median stroke thickness via distance transform on the skeleton"""
    import numpy as np
    from matplotlib.path import Path
    from scipy import ndimage
    from skimage.morphology import skeletonize
    v, c = [], []
    for cont in cs:
        for op, a in cont:
            if op == "moveTo": v.append(a[0]); c.append(Path.MOVETO)
            elif op == "lineTo": v.append(a[0]); c.append(Path.LINETO)
            elif op == "curveTo": v += list(a); c += [Path.CURVE4] * 3
            elif op == "closePath": v.append((0, 0)); c.append(Path.CLOSEPOLY)
    p = Path(v, c); e = p.get_extents()
    xs = np.arange(e.x0 - 4, e.x1 + 4, 1.0); ys = np.arange(e.y0 - 4, e.y1 + 4, 1.0)
    X, Y = np.meshgrid(xs, ys)
    m = p.contains_points(np.c_[X.ravel(), Y.ravel()]).reshape(X.shape)
    d = ndimage.distance_transform_edt(m)
    return float(np.median(d[skeletonize(m)] * 2))

# ---------------- source marks ----------------
def need(name, fallback_char):
    if name in gs: return contours_of(name)
    g = gname(fallback_char)
    if g: return split_body(g)[1]
    sys.exit("font has no %s mark" % name)

SRCMARK = {
    "acute": need("acute", "á"), "grave": need("grave", "à"), "tilde": need("tilde", "ã"),
    "circ": need("circumflex", "â"), "breve": need("breve", "ă") if ("breve" in gs or gname("ă")) else None,
}
TILDE_W = stroke_weight(SRCMARK["tilde"])
if SRCMARK["breve"] is None:
    # Some fonts have neither a standalone breve nor the precomposed ă glyph.
    # Draw a shallow bowl using the font's circumflex dimensions and tilde stroke
    # weight so Vietnamese breve forms can still be composed.
    _cx0, _cy0, _cx1, _cy1 = bounds(SRCMARK["circ"])
    _bw = max((_cx1 - _cx0) * 0.88, TILDE_W * 3)
    _bh = max((_cy1 - _cy0) * 0.65, TILDE_W * 2.2)
    _bs = min(max(TILDE_W, _bw * 0.06), _bh * 0.45, _bw * 0.16)
    SRCMARK["breve"] = [[
        ("moveTo", ((0, _bh),)),
        ("curveTo", ((_bw * 0.24, -_bh / 3), (_bw * 0.76, -_bh / 3), (_bw, _bh))),
        ("lineTo", ((_bw - _bs, _bh - _bs),)),
        ("curveTo", ((_bw * 0.76 - _bs, -_bh / 3 + _bs),
                     (_bw * 0.24 + _bs, -_bh / 3 + _bs), (_bs, _bh - _bs))),
        ("closePath", ()),
    ]]
    print("vnfont: source breve missing; generated a fallback from circumflex size and tilde weight", file=sys.stderr)

# ---------------- generated marks (local coords) ----------------
hc = CFG.get("hook", {})
HW = hc.get("w") or round(TILDE_W)
HS = hc.get("s", 1.0)
MARK_AXIS = {}   # mark key -> x offset of its visual axis (tail of hỏi) from its bbox centre, local units
if hc.get("style") == "skeleton" and gname("?"):
    # dấu hỏi = NÉT MÓC lấy khung xương từ dấu "?" của font (không phải "?" thu nhỏ) — quy tắc Ryan 25/10
    import qhook
    _q = contours_of(gname("?"))
    _H = hc.get("h", 240) * K; _W = (hc.get("w") or round(TILDE_W * 0.87)) * K
    _X = hc.get("xstretch", 1.1); _T = hc.get("trim", 0.0)
    _g1, _a1 = qhook.hook_from_skeleton(_q, _H, _W, 0.85, 0.95, _X, _T)
    _ss = hc.get("stack", 0.8)                       # dấu kép nhỏ hơn 15–25 %
    _g2, _a2 = qhook.hook_from_skeleton(_q, _H * _ss, _W * hc.get("stack_w", 0.92), 0.85, 0.95, _X, _T)   # nét giảm ít hơn cỡ → không bị nhạt
    GEN = {"hook": MK.poly_to_contours(_g1), "hook_s": MK.poly_to_contours(_g2)}
    MARK_AXIS = {"hook": _a1, "hook_s": _a2}
elif hc.get("style") == "question" and gname("?"):
    # dấu hỏi lấy từ dấu chấm hỏi của chính font (bỏ chấm, thu nhỏ, bù độ dày nét)
    import qhook
    _q = contours_of(gname("?"))
    _H = hc.get("h", 240) * K; _W = (hc.get("w") or round(TILDE_W * 0.9)) * K; _X = hc.get("xstretch", 1.1)
    GEN = {"hook": MK.poly_to_contours(qhook.hook_from_question(_q, _H, _W, _X)),
           "hook_s": MK.poly_to_contours(qhook.hook_from_question(_q, _H * hc.get("stack", 0.82), _W * 0.86, _X))}
else:
    # hook_v5 (dấu hỏi bản 1.003). "tweak": chỉnh nhẹ giữ dáng — lx/ly đầu nét trái, bx/top vòm, neck chỗ nối thân;
    # "ws" tỉ lệ nét đầu; "stack" cỡ dấu kép (mặc định 0.83), "stack_w" nét dấu kép (mặc định 0.84).
    _tw = hc.get("tweak", {}); _ws = hc.get("ws", 0.63)
    _ss = hc.get("stack", 0.83); _sw = hc.get("stack_w", 0.84)
    GEN = {
        "hook": MK.hook_v5(s=HS * K, w=HW * K, w_start=HW * _ws * K, w_tail=HW * 0.92 * K, **_tw),
        "hook_s": MK.hook_v5(s=_ss * HS * K, w=HW * _sw * K, w_start=HW * min(_ws, 0.5 * _sw / 0.84) * K, w_tail=HW * 0.74 * _sw / 0.84 * K, **_tw),
    }
    if hc.get("tail_axis"):   # trục = thân đuôi dấu hỏi (x=6 trước khi scale), tính lệch so với tâm bbox
        for _k, _sc in (("hook", HS * K), ("hook_s", _ss * HS * K)):
            _b = bounds(GEN[_k]); MARK_AXIS[_k] = 6 * _sc - (_b[0] + _b[2]) / 2
dc = CFG.get("dot", {})
DOT_K = dc.get("k", 0.66)
def dot_shape(d, k=DOT_K):
    r = d / 2; h = r * k
    return [[("moveTo", ((r, 0),)), ("curveTo", ((r, -h), (h, -r), (0, -r))), ("curveTo", ((-h, -r), (-r, -h), (-r, 0))),
             ("curveTo", ((-r, h), (-h, r), (0, r))), ("curveTo", ((h, r), (r, h), (r, 0))), ("closePath", ())]]
GEN["dot"] = dot_shape(dc.get("lc", 120) * K)          # local: lowercase size, uppercase via scale
DOT_UC_SCALE = dc.get("uc", 128) / dc.get("lc", 120)
hn = CFG.get("horn", {})
HORN_STYLE = hn.get("style", "arc")
HNW = hn.get("w") or TILDE_W
if HORN_STYLE == "comma" and "comma" in gs:
    COMMA = contours_of("comma")
    pts = [a[-1] for c in COMMA for op, a in c if op != "closePath"]
    tx, ty = min(pts, key=lambda p: p[1])
    ang = math.radians(hn.get("angle", -28)); ca, sa = math.cos(ang), math.sin(ang)
    m = transform(COMMA, (1, 0, 0, 1, -tx, -ty))
    GEN["horn"] = transform(m, (ca, sa, -sa, ca, -34 * K, -34 * K))
elif HORN_STYLE == "shelf":
    GEN["horn"] = MK.poly_to_contours(MK.horn_shelf(K, w0=HNW * 1.11, wm=HNW * 1.07, w1=HNW * 1.38,
                                                    reach=hn.get("reach", 72), rise=hn.get("rise", 60)))
else:
    GEN["horn"] = MK.poly_to_contours(MK.horn_arc(0, 0, K, w0=HNW * 1.2, wm=HNW * 1.05, w1=HNW * 1.3))

# custom marks from the review page override generated ones; generated bounds stay the reference
CUSTOM = {k: from_json_contours(v) for k, v in CFG.get("marks", {}).items()}
REF = {k: bounds(v) for k, v in GEN.items()}
def mark(k):
    if k in CUSTOM: return CUSTOM[k], REF.get(k) or bounds(CUSTOM[k])
    if k in GEN: return GEN[k], REF[k]
    return SRCMARK[k], bounds(SRCMARK[k])

# ---------------- bases ----------------
BASES = {"a": "â", "e": "ê", "o": "ô", "u": "û", "i": "î", "y": "ÿ",
         "A": "Â", "E": "Ê", "O": "Ô", "U": "Û", "I": "Î", "Y": "Ÿ"}
def shape_axis(cs, lo=0.30, hi=0.97):
    """trục hình dáng của thân chữ: tâm các lát cắt ngang (mép mực trái + phải)/2 trong khoảng [lo, hi]
    chiều cao, khớp đường thẳng x = a + b·y. Nghiêng được theo dáng chữ (giới hạn ±8°)."""
    import qhook, shapely
    poly = qhook.to_poly(cs).convex_hull
    if poly.is_empty:
        box = bounds(cs)
        return ((box[0] + box[2]) / 2, 0.0) if box else (0.0, 0.0)
    x0, y0, x1, y1 = poly.bounds   # bao lồi: tay chữ E/F không làm lệch trục
    ys, xs = [], []
    for k in range(24):
        y = y0 + (y1 - y0) * (lo + (hi - lo) * k / 23)
        seg = poly.intersection(shapely.geometry.box(x0 - 999, y - .5, x1 + 999, y + .5))
        if seg.is_empty: continue
        b = seg.bounds; ys.append(y); xs.append((b[0] + b[2]) / 2)
    import numpy as np
    if len(ys) < 3: return ((x0 + x1) / 2, 0.0)
    b, a = np.polyfit(ys, xs, 1)
    lim = math.tan(math.radians(8)); b = max(-lim, min(lim, b))
    a = float(np.mean(xs) - b * np.mean(ys))
    return (a, float(b))

info = {}
for L, pc in BASES.items():
    g = gname(pc)
    if g:
        body, mk = split_body(g)
        mx0, my0, mx1, my1 = bounds(mk)
        ax, ay, width = (mx0 + mx1) / 2, my0, gs[g].width
    else:  # fall back to the bare letter, anchor above its bbox
        g = gname(L); body = contours_of(g); width = gs[g].width
        x0, y0, x1, y1 = bounds(body)
        ax, ay = (x0 + x1) / 2, y1 + 30 * K
    bx0, by0, bx1, by1 = bounds([max(body, key=lambda c: abs(area(c)))])
    _sax = shape_axis(body)
    if CFG.get("anchor") == "shape": ax = _sax[0] + _sax[1] * ay       # dấu trên đặt theo trục hình dáng
    info[L] = dict(sax=_sax, body=body, width=width, ax=ax, ay=ay, bx=(bx0 + bx1) / 2, bb=(bx0, by0, bx1, by1),
                   caps=L.isupper(), src=g)

HORN_OF = {}
def outer_x_at(cs, y):
    """right-most x of the outline at height y"""
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    rings = []
    for c in cs:
        pts, cur = [], None
        for op, a in c:
            if op in ("moveTo", "lineTo"): cur = a[0]; pts.append(cur)
            elif op == "curveTo":
                p0 = cur
                for k in range(1, 9):
                    t = k / 8; u = 1 - t
                    pts.append((u**3*p0[0] + 3*u*u*t*a[0][0] + 3*u*t*t*a[1][0] + t**3*a[2][0], u**3*p0[1] + 3*u*u*t*a[0][1] + 3*u*t*t*a[1][1] + t**3*a[2][1]))
                cur = a[2]
        if len(pts) > 2: rings.append(Polygon(pts).buffer(0))
    g = unary_union(rings).intersection(box(-1e5, y - 0.5, 1e5, y + 0.5))
    return g.bounds[2]
# ---------------- text axis (trục chữ) ----------------
def detect_slant():
    """degrees the stems lean (positive = leans right). post.italicAngle wins when set; otherwise measured
    from the left edge of I / l stems at 20% and 80% of their height."""
    ia = float(f["post"].italicAngle or 0)
    if abs(ia) > 0.2: return -ia, "post.italicAngle"
    import qhook
    for ch in "Il|":
        g = gname(ch)
        if not g: continue
        poly = qhook.to_poly(contours_of(g))
        x0, y0, x1, y1 = poly.bounds
        def left_at(y):
            seg = poly.intersection(__import__("shapely").geometry.box(x0 - 999, y - .5, x1 + 999, y + .5))
            return seg.bounds[0] if not seg.is_empty else None
        ya, yb = y0 + (y1 - y0) * 0.2, y0 + (y1 - y0) * 0.8
        la, lb = left_at(ya), left_at(yb)
        if la is not None and lb is not None:
            return math.degrees(math.atan2(lb - la, yb - ya)), "stem " + ch
    return 0.0, "none"
SLANT, SLANT_SRC = detect_slant()
if CFG.get("axis") is not None: SLANT, SLANT_SRC = float(CFG["axis"]), "config"
TAN = math.tan(math.radians(SLANT)) if abs(SLANT) > 1.0 else 0.0
# font đứng (không nghiêng) → trục từng chữ là đường THẲNG ĐỨNG (luật Ryan 25/10: chữ không nghiêng thì không vẽ trục chéo;
# không chắc font có nghiêng không thì hỏi lại). Chỉ font nghiêng mới để trục nghiêng theo dáng ("axis_slant": true để ép).
if not TAN and not CFG.get("axis_slant"):
    for _L, _i in info.items():
        _a, _b = _i["sax"]; _y0, _y1 = _i["bb"][1], _i["bb"][3]
        _i["sax"] = (_a + _b * (_y0 + (_y1 - _y0) * 0.635), 0.0)
        if CFG.get("anchor") == "shape": _i["ax"] = _i["sax"][0]
if TAN:   # generated marks are drawn upright: lean them with the font
    for _k in ("hook", "hook_s", "dot", "horn"):
        if _k in GEN: GEN[_k] = transform(GEN[_k], (1, 0, TAN, 1, 0, 0))
    REF.update({_k: bounds(_v) for _k, _v in GEN.items()})
def axis_dx(y_from, y_to):
    """horizontal shift that keeps a mark on the slanted axis when it moves from y_from to y_to"""
    return (y_to - y_from) * TAN

BASE_SB = {}
for _L in BASES:
    _g = gname(_L); _b = bounds([max(contours_of(_g), key=lambda c: abs(area(c)))]); BASE_SB[_L] = (_b[0], gs[_g].width - _b[2])
CONTAIN = CFG.get("contain_marks", False)

if os.environ.get("VN_AXIS_DEBUG"):
    for _L, _i in info.items():
        _a, _b = _i["sax"]; print("axis %s: circumflex-centre %.0f  shape-axis@top %.0f  slope %.1f°" % (_L, _i["ax"], _a + _b * _i["ay"], math.degrees(math.atan(_b))))
DX = {"acute": 34 * K, "grave": -30 * K, "tilde": 0, "hook": 6 * K}

def compose(L, base_mark=None, tone=None, dot=False, horn=False):
    """-> (contours, width, parts)  parts = static contours + mark instances, for the live editor"""
    i = info[L]
    static = [list(c) for c in i["body"]]
    width = i["width"]; ax = i["ax"]
    inst = []                                   # (mark key, affine)
    if L in "iI" and dot and not tone:
        g = gname(L); static = contours_of(g); width = gs[g].width
    if horn:
        x0, y0, x1, y1 = i["bb"]
        if HORN_STYLE == "shelf":
            s = 0.9 if L.islower() else 1.0
            if L in "oO":   # shoulder: outer edge at the height where the neck runs
                yc = y1 - (y1 - y0) * hn.get("o_drop", 0.16)
                xs = outer_x_at(i["body"], yc)
                xa, ya = xs - 8 * K, yc + 50 * K * s
            else:           # stem: top-right corner
                xa, ya = outer_x_at(i["body"], y1 - 60 * K), y1
        elif L in "oO": xa, ya = x1 - (x1 - x0) * 0.10, y1 - (y1 - y0) * 0.22
        else: xa, ya = x1 - 26 * K, y1 - 34 * K
        if HORN_STYLE != "shelf": s = 0.92 if L.islower() else 1.05
        inst.append(("horn", (s, 0, 0, s, xa, ya)))
    if base_mark:
        bm = "circ" if base_mark == "circ" else "breve"
        # dấu mũ / trăng chữ hoa khi chồng: dẹt lại 0.86 (mặc định). "caps_stack_flat": 1.0 = giữ nguyên dấu gốc (luật src-marks: tôn trọng dấu font gốc)
        sy = CFG.get("caps_stack_flat", 0.86) if (i["caps"] and tone) else 1.0
        cs_, ref = mark(bm)
        t = place_t(cs_, ax, i["ay"], 1.0, sy, ref)
        inst.append((bm, t))
        bx0, by0, bx1, by1 = bounds(transform(cs_, t))
        if tone:
            key = "hook_s" if tone == "hook" else tone
            mc, mref = mark(key)
            s = 1.0 if tone == "hook" else (0.74 if tone == "tilde" else 0.78)
            # System workflow patch: stack_place="top" means all tones sit above the
            # circumflex/breve, matching the kit's VER 1B and quick_vn behavior.
            STACK_TOP = (base_mark in ("circ", "breve") and hc.get("stack_place") == "top"
                         and tone in ("acute", "grave", "hook"))
            if STACK_TOP:
                import qhook
                sy2 = hc.get("caps_flat", 0.86) if i["caps"] and tone == "hook" else 1.0
                dx = {"acute": 8, "grave": -8, "hook": 0}[tone] * K
                if tone == "hook": dx -= MARK_AXIS.get(key, 0)
                gap_top = CFG.get("stack_gap_top", max(22, round(TILDE_W * 0.95))) * K
                t2 = place_t(mc, (bx0 + bx1) / 2 + dx, by1 + gap_top, s, sy2, mref)
                base_poly = qhook.to_poly(transform(cs_, t))
                need = gap_top
                for _ in range(60):
                    if qhook.to_poly(transform(mc, t2)).distance(base_poly) >= need: break
                    t2 = (t2[0], t2[1], t2[2], t2[3], t2[4], t2[5] + 4 * K)
            elif base_mark == "circ" and tone in ("acute", "grave", "hook"):
                w = (mref[2] - mref[0]) * s
                t2 = place_t(mc, bx1 - 18 * K + w / 2, by0 + (by1 - by0) * (0.30 if tone == "hook" else 0.42), s, None, mref)
                if CONTAIN:   # keep the right-side tone inside the advance (Word/Excel/Canva don't kern)
                    right = i["bb"][2] + BASE_SB[L][1]
                    over = bounds(transform(mc, t2))[2] - right
                    if over > 0: t2 = (t2[0], t2[1], t2[2], t2[3], t2[4] - over, t2[5])
                _gr = (hc.get("gap_right") if tone == "hook" and hc.get("stack_place") == "right"
                       else CFG.get("stack_gap_ag") if tone in ("acute", "grave") else None)
                if _gr is not None:
                    # dấu thanh bên phải dấu mũ (hỏi VER 5B, sắc / huyền mọi bản có "stack_gap_ag"): nâng dần tới khi cách ^ đủ khe — không dính
                    import qhook
                    _cp = qhook.to_poly(transform(cs_, t)); _need = _gr * K
                    for _ in range(60):
                        if qhook.to_poly(transform(mc, t2)).distance(_cp) >= _need: break
                        t2 = (t2[0], t2[1], t2[2], t2[3], t2[4], t2[5] + 4 * K)
                    # còn dư khe (chữ rộng như Ồ) thì hạ xuống cho khe bằng các chữ khác — khe đều (lỗi A20), không thấp hơn 30 % cao dấu mũ
                    _ymin = by0 + (by1 - by0) * 0.30
                    for _ in range(80):
                        t3 = (t2[0], t2[1], t2[2], t2[3], t2[4], t2[5] - 2 * K)
                        if bounds(transform(mc, t3))[1] < _ymin or qhook.to_poly(transform(mc, t3)).distance(_cp) < _need: break
                        t2 = t3
            else:
                dxs = {"acute": 16, "grave": -14, "hook": 4, "tilde": 0}[tone] * K
                if tone == "hook" and MARK_AXIS: dxs = -MARK_AXIS.get(key, 0)
                gap = (hc.get("gap", 30) if tone == "hook" and MARK_AXIS else 20) * K
                t2 = place_t(mc, ax + dxs, by1 + gap, s, (hc.get("caps_flat", 0.86) if (i["caps"] and tone == "hook" and MARK_AXIS) else None), mref)
            inst.append((key, t2))
    elif tone:
        mc, mref = mark(tone)
        dy = -4 * K if tone == "tilde" else (2 * K if tone == "hook" else 0)
        sc = 0.95 if tone == "tilde" else 1.0
        if tone == "hook" and i["caps"]: sc = hc.get("caps_scale", 1.0)
        dxh = DX[tone]; syh = None
        if tone == "hook" and MARK_AXIS:
            dxh = -MARK_AXIS["hook"] * sc                    # đuôi dấu hỏi nằm trên trục chữ
            if horn: dxh -= hc.get("horn_shift", 30) * K     # ở ử: né sang trái nhường chỗ cho móc
            if i["caps"]: syh = sc * hc.get("caps_flat", 0.86)   # chữ hoa: dẹt lại
        inst.append((tone, place_t(mc, ax + dxh, i["ay"] + dy, sc, syh, mref)))
    if dot:
        mc, mref = mark("dot")
        s = DOT_UC_SCALE if i["caps"] else 1.0
        d = (mref[3] - mref[1]) * s
        cx = i["bx"] + (100 * K if L == "y" else 0) + axis_dx((i["bb"][1] + i["bb"][3]) / 2, -40 * K - d / 2)
        inst.append(("dot", place_t(mc, cx, -40 * K - d, s, None, mref)))
    cs = list(static)
    horn_cs = []
    for k, t in inst:
        part = transform(mark(k)[0], t)
        if k == "horn": horn_cs = part
        else: cs += part
    if horn_cs:
        cs = [c for c in union(static + horn_cs) if abs(area(c)) > 15000 * K * K] + cs[len(static):]
    parts = {"static": to_json_contours(static), "marks": [{"m": k, "t": [round(v, 4) for v in t]} for k, t in inst]}
    HORN_OF[(L, base_mark, tone, dot)] = horn_cs
    return cs, width, parts

# ---------------- inventory ----------------
TONES = [(None, False), ("grave", False), ("acute", False), ("hook", False), ("tilde", False), (None, True)]
VOW = {"a": ("a", None, False), "ă": ("a", "breve", False), "â": ("a", "circ", False),
       "e": ("e", None, False), "ê": ("e", "circ", False), "i": ("i", None, False),
       "o": ("o", None, False), "ô": ("o", "circ", False), "ơ": ("o", None, True),
       "u": ("u", None, False), "ư": ("u", None, True), "y": ("y", None, False)}
COMB = {"grave": "̀", "acute": "́", "hook": "̉", "tilde": "̃"}
jobs = []
for bch, (L, bm, horn) in VOW.items():
    for up in (False, True):
        for tone, dot in TONES:
            s = (bch.upper() if up else bch) + (COMB[tone] if tone else "") + ("̣" if dot else "")
            ch = unicodedata.normalize("NFC", s)
            if len(ch) == 1:
                jobs.append((ch, L.upper() if up else L, bm, tone, dot, horn))
REBUILD = {int(x.replace("U+", ""), 16) for x in CFG.get("rebuild", [])}
OVR = CFG.get("glyphs", {})

# ---------------- write ----------------
order = list(f.getGlyphOrder())
hmtx = f["hmtx"]
added, recipes, replaced = {}, {}, {}
HORN_GLYPHS = {}
BODYBB = {}
if IS_CFF:
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    cff = f["CFF "].cff; top = cff.topDictIndex[0]; csi = top.CharStrings
    def put(name, cs, width, new):
        # CFF stores advance as a delta from nominalWidthX — GDI/Word read this, HarfBuzz reads hmtx
        pen = T2CharStringPen(width - getattr(top.Private, 'nominalWidthX', 0), None)
        for c in cs: replay(c, pen)
        chs = pen.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
        if new:
            csi.charStringsIndex.append(chs); csi.charStrings[name] = len(csi.charStringsIndex) - 1
        else:
            csi.charStringsIndex[csi.charStrings[name]] = chs
else:
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.pens.cu2quPen import Cu2QuPen
    glyf = f["glyf"]
    def put(name, cs, width, new):
        tp = TTGlyphPen(None); pen = Cu2QuPen(tp, max_err=1.0 * K, reverse_direction=True)
        for c in cs: replay(c, pen)
        glyf[name] = tp.glyph()

for ch, L, bm, tone, dot, horn in jobs:
    cp = ord(ch)
    exists = cp in cmap
    if exists and cp not in REBUILD: continue
    name = cmap[cp] if exists else "uni%04X" % cp
    cs, width, parts = compose(L, bm, tone, dot, horn)
    if name in OVR:
        cs = from_json_contours(OVR[name]["contours"]); width = OVR[name].get("w", width)
    put(name, cs, width, not exists)
    if not exists: order.append(name)
    hmtx.metrics[name] = (width, int(math.floor(bounds(cs)[0])))
    recipes[name] = dict(u=cp, ch=ch, w=width, base=info[L]["src"], sax=list(info[L]["sax"]), **parts)
    if horn: HORN_GLYPHS[name] = (HORN_OF[(L, bm, tone, dot)], width)
    BODYBB[name] = bounds([max(contours_of(gname(L)), key=lambda c: abs(area(c)))]) if (L in "iI" and dot and not tone) else info[L]["bb"]
    if exists: replaced[cp] = name
    else: added[cp] = (name, L, horn)

f.setGlyphOrder(order)
if IS_CFF: top.charset = order
f["maxp"].numGlyphs = len(order)
if not IS_CFF: f["maxp"].recalc(f)
for t in f["cmap"].tables:
    if t.isUnicode():
        for cp, (name, *_r) in added.items():
            t.cmap[cp] = name
if "GDEF" in f and f["GDEF"].table.GlyphClassDef:
    for name, *_r in added.values(): f["GDEF"].table.GlyphClassDef.classDefs[name] = 1

# ---------------- spacing: accented letters get the side bearings of their plain letter ----------------
# Many Latin fonts draw à á â … with slightly different bodies/advances than a. In Vietnamese almost every
# vowel carries a mark, so those differences show up as uneven spacing. Shift each accented letter so its
# body has exactly the plain letter's left/right side bearings (marks move with it; horn may overhang).
SPACING = CFG.get("match_base_spacing", True)
spacing_fixed = []
if SPACING:
    gs = f.getGlyphSet()
    def big_bb(cs): return bounds([max(cs, key=lambda c: abs(area(c)))])
    base_sb = {}
    for L in BASES:
        g = gname(L); x0, _, x1, _ = big_bb(contours_of(g)); base_sb[L] = (x0, gs[g].width - x1)
    allmap = dict(cmap); allmap.update({cp: v[0] for cp, v in added.items()})
    for cp, n in sorted(allmap.items()):
        dch = unicodedata.normalize("NFD", chr(cp))
        if len(dch) < 2 or dch[0] not in BASES: continue
        L = dch[0]
        cs = contours_of(n)
        bb = BODYBB.get(n) or big_bb(split_body(n)[0])
        lsb, rsb = base_sb[L]
        dx = lsb - bb[0]; w = int(round(bb[2] - bb[0] + lsb + rsb))
        if abs(dx) < 0.5 and w == hmtx[n][0]: continue
        cs2 = transform(cs, (1, 0, 0, 1, dx, 0))
        put(n, cs2, w, False); hmtx.metrics[n] = (w, int(math.floor(bounds(cs2)[0])))
        if n in recipes:
            r = recipes[n]; r["w"] = w
            r["static"] = to_json_contours(transform(from_json_contours(r["static"]), (1, 0, 0, 1, dx, 0)))
            for m in r["marks"]: m["t"][4] = round(m["t"][4] + dx, 4)
            if "sax" in r: r["sax"][0] = r["sax"][0] + dx
        if n in HORN_GLYPHS:
            hc, _w = HORN_GLYPHS[n]; HORN_GLYPHS[n] = (transform(hc, (1, 0, 0, 1, dx, 0)), w)
        spacing_fixed.append(n)
    gs = f.getGlyphSet()

# ơ ư: advance grows to hold the horn when hn.advance == "contain" (no kern needed in Word/Excel/Canva)
HORN_CONTAIN = hn.get("advance") == "contain"
if HORN_CONTAIN:
    gs = f.getGlyphSet()
    for n, (hc_, w_) in list(HORN_GLYPHS.items()):
        hx1 = bounds(hc_)[2]
        nw = int(math.ceil(max(w_, hx1 + hn.get("clear", 12) * K)))
        if nw != w_:
            cs_ = contours_of(n); put(n, cs_, nw, False); hmtx.metrics[n] = (nw, hmtx[n][1])
            HORN_GLYPHS[n] = (hc_, nw)
            if n in recipes: recipes[n]["w"] = nw
    gs = f.getGlyphSet()

# kerning: new glyphs inherit the pairs of their plain letter (or body source) — pair-pos format 1 and 2
if "GPOS" in f:
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            if lk.LookupType == 9: st = st.ExtSubTable
            effective_type = getattr(st, "LookupType", lk.LookupType)
            if effective_type != 2: continue
            if not hasattr(st, "Format"): continue
            if st.Format == 2:
                for name, L, horn in added.values():
                    ref = info[L]["src"]
                    c1 = st.ClassDef1.classDefs.get(ref)
                    if ref in st.Coverage.glyphs:
                        st.Coverage.glyphs.append(name)
                        if c1: st.ClassDef1.classDefs[name] = c1
                    c2 = st.ClassDef2.classDefs.get(ref)
                    if c2: st.ClassDef2.classDefs[name] = c2
                st.Coverage.glyphs.sort(key=f.getGlyphID)
            elif st.Format == 1:
                cov = st.Coverage.glyphs; idx = {g: k for k, g in enumerate(cov)}
                for ps in st.PairSet:
                    sec = {r.SecondGlyph: r for r in ps.PairValueRecord}
                    for name, L, horn in added.values():
                        src = (sec.get(L) or sec.get(info[L]["src"])) if SPACING else (sec.get(info[L]["src"]) or sec.get(L))
                        if src is not None:
                            r = copy.deepcopy(src); r.SecondGlyph = name; ps.PairValueRecord.append(r)
                    ps.PairValueRecord.sort(key=lambda r: f.getGlyphID(r.SecondGlyph))
                    ps.PairValueCount = len(ps.PairValueRecord)
                pairs = list(zip(cov, st.PairSet))
                for name, L, horn in added.values():
                    order_ = [L, info[L]["src"]] if SPACING else [info[L]["src"], L]
                    ref = next((x for x in order_ if x in idx), None)
                    if ref is not None: pairs.append((name, copy.deepcopy(st.PairSet[idx[ref]])))
                pairs.sort(key=lambda p: f.getGlyphID(p[0]))
                st.Coverage.glyphs = [p[0] for p in pairs]; st.PairSet = [p[1] for p in pairs]; st.PairSetCount = len(pairs)

# ---------------- horn clearance kerning ----------------
# ơ/ư keep the base advance, so the horn overhangs into the next letter (ươ, ưở, ưt …).
# Add a kern only for pairs where the horn would come closer than `horn_kern` units.
HK = 0 if hn.get("advance") == "contain" else CFG.get("horn_kern", 36) * K
kern_added = 0
if HK and HORN_GLYPHS and "GPOS" in f:
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from fontTools.pens.basePen import BasePen
    class Flat(BasePen):
        def __init__(s, gset=None): super().__init__(gset); s.rings = []; s.cur = []
        def _moveTo(s, p): s.cur = [p]
        def _lineTo(s, p): s.cur.append(p)
        def _curveToOne(s, a, b, c):
            p0 = s.cur[-1]
            for i in range(1, 9):
                t = i / 8; u = 1 - t
                s.cur.append((u**3*p0[0] + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*c[0], u**3*p0[1] + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*c[1]))
        def _closePath(s):
            if len(s.cur) > 2: s.rings.append(s.cur)
            s.cur = []
        _endPath = _closePath
    def poly_of_contours(cs):
        fp = Flat()
        for c in cs: replay(c, fp)
        return unary_union([Polygon(r).buffer(0) for r in fp.rings])
    gsK = f.getGlyphSet()
    def poly_of_glyph(n):
        fp = Flat(gsK); gsK[n].draw(fp)
        return unary_union([Polygon(r).buffer(0) for r in fp.rings]) if fp.rings else None
    import string
    letters = set(string.ascii_letters) | {chr(cp) for cp in added} | set("àáâãèéêìíòóôõùúýđÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝĐ")
    nexts = {}
    for ch in letters:
        g = cmap.get(ord(ch)) or (added.get(ord(ch)) or [None])[0]
        if g and g in gsK:
            pg = poly_of_glyph(g)
            if pg is not None and not pg.is_empty: nexts[g] = pg
    from shapely.affinity import translate
    pairs = {}
    for gname_, (hcs, adv) in HORN_GLYPHS.items():
        hp = poly_of_contours(hcs)
        for nn, npoly in nexts.items():
            moved = translate(npoly, adv, 0)
            d = hp.distance(moved)
            if d >= HK: continue
            lo, hi = 0, 400 * K
            for _ in range(14):
                mid = (lo + hi) / 2
                if hp.distance(translate(npoly, adv + mid, 0)) >= HK: hi = mid
                else: lo = mid
            pairs[(gname_, nn)] = int(math.ceil(hi))
    # merge into the first pair-pos format-1 subtable that already lists the horn glyphs
    target = None
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            st2 = st.ExtSubTable if lk.LookupType == 9 else st
            if getattr(st2, "Format", None) == 1 and hasattr(st2, "PairSet"):
                target = st2; break
        if target: break
    if target is not None:
        cov = target.Coverage.glyphs
        for (a, b), v in pairs.items():
            if a not in cov:
                ps = ot.PairSet(); ps.PairValueRecord = []; ps.PairValueCount = 0
                cov.append(a); target.PairSet.append(ps)
                order_ = sorted(range(len(cov)), key=lambda i: f.getGlyphID(cov[i]))
                target.Coverage.glyphs = cov = [cov[i] for i in order_]; target.PairSet = [target.PairSet[i] for i in order_]
            ps = target.PairSet[cov.index(a)]
            rec = next((r for r in ps.PairValueRecord if r.SecondGlyph == b), None)
            if rec is None:
                rec = ot.PairValueRecord(); rec.SecondGlyph = b
                rec.Value1 = ot.ValueRecord(); rec.Value1.XAdvance = 0
                ps.PairValueRecord.append(rec)
            if not hasattr(rec.Value1, "XAdvance") or rec.Value1.XAdvance is None: rec.Value1.XAdvance = 0
            rec.Value1.XAdvance = max(rec.Value1.XAdvance, 0) + v if rec.Value1.XAdvance < v else rec.Value1.XAdvance
            ps.PairValueRecord.sort(key=lambda r: f.getGlyphID(r.SecondGlyph)); ps.PairValueCount = len(ps.PairValueRecord)
            kern_added += 1
        target.PairSetCount = len(target.PairSet)
        target.ValueFormat1 |= 0x0004

# ---------------- combining marks + ccmp ----------------
# Vietnamese text often arrives decomposed (Unikey "Unicode tổ hợp", some web/phone input, copy-paste):
# a + U+0301 instead of á. A font without U+0300… falls back to another font for the mark and the
# line gets gaps after every accented letter. Add zero-width combining marks (drawn over the previous
# letter) and a ccmp ligature lookup that turns every base+mark sequence into the precomposed glyph.
comb_added = 0
if CFG.get("combining", True) and IS_CFF:
    import itertools
    from fontTools.otlLib.builder import buildLigatureSubstSubtable
    gs = f.getGlyphSet()
    def body_center(ch):
        g = gname(ch) or added.get(ord(ch), [None])[0]
        b = bounds([max(contours_of(g), key=lambda c: abs(area(c)))]); return (b[0] + b[2]) / 2, gs[g].width
    COMBS = {0x300: ("a", None, "grave", False, False), 0x301: ("a", None, "acute", False, False),
             0x302: ("a", "circ", None, False, False), 0x303: ("a", None, "tilde", False, False),
             0x306: ("a", "breve", None, False, False), 0x309: ("a", None, "hook", False, False),
             0x323: ("a", None, None, True, False), 0x31B: ("o", None, None, False, True)}
    cmb_names = {}
    for cp, (L, bm, tone, dot, horn) in COMBS.items():
        if cp in cmap: cmb_names[cp] = cmap[cp]; continue
        _cs, _w, parts = compose(L, bm, tone, dot, horn)
        key = "horn" if horn else ("dot" if dot else (bm if bm else tone))
        key = {"circ": "circ", "breve": "breve"}.get(key, key)
        inst = [m for m in parts["marks"] if m["m"] == key][0]
        mc = transform(mark(key)[0], tuple(inst["t"]))
        cx, w = body_center(L)
        dx = (-w + cx) - info[L]["bx"]
        mc = transform(mc, (1, 0, 0, 1, dx, 0))
        name = "uni%04X" % cp
        put(name, mc, 0, True); order.append(name)
        hmtx.metrics[name] = (0, int(math.floor(bounds(mc)[0])))
        cmb_names[cp] = name; comb_added += 1
    f.setGlyphOrder(order); top.charset = order; f["maxp"].numGlyphs = len(order)
    for t in f["cmap"].tables:
        if t.isUnicode():
            for cp, n in cmb_names.items(): t.cmap[cp] = n
    if "GDEF" in f and f["GDEF"].table.GlyphClassDef:
        for n in cmb_names.values(): f["GDEF"].table.GlyphClassDef.classDefs[n] = 3
    full = dict(cmap); full.update({cp: v[0] for cp, v in added.items()}); full.update(cmb_names)
    ligs = {}
    for cp, lig in full.items():
        d = unicodedata.normalize("NFD", chr(cp))
        if len(d) < 2 or any(ord(m) not in cmb_names for m in d[1:]) or ord(d[0]) not in full: continue
        for perm in set(itertools.permutations(d[1:])):
            for k in range(len(perm)):
                pre = unicodedata.normalize("NFC", d[0] + "".join(perm[:k]))
                if len(pre) != 1 or ord(pre) not in full: continue
                comps = tuple([full[ord(pre)]] + [cmb_names[ord(m)] for m in perm[k:]])
                if len(comps) > 1: ligs.setdefault(comps, lig)
    st = buildLigatureSubstSubtable(ligs)
    if "GSUB" in f:
        G = f["GSUB"].table
    else:
        # Simple CFF fonts may have no substitution table yet. Create a minimal
        # GSUB so the combining-mark ccmp lookup below can be registered.
        from fontTools.ttLib import newTable
        G = ot.GSUB()
        G.Version = 0x00010000
        G.ScriptList = ot.ScriptList(); G.ScriptList.ScriptRecord = []
        G.ScriptList.ScriptCount = 0
        G.FeatureList = ot.FeatureList(); G.FeatureList.FeatureRecord = []
        G.FeatureList.FeatureCount = 0
        G.LookupList = ot.LookupList(); G.LookupList.Lookup = []
        G.LookupList.LookupCount = 0
        gsub = newTable("GSUB"); gsub.table = G; f["GSUB"] = gsub
        for tag in ("DFLT", "latn"):
            lang = ot.LangSys(); lang.LookupOrder = None; lang.ReqFeatureIndex = 0xFFFF
            lang.FeatureIndex = []; lang.FeatureCount = 0
            script = ot.Script(); script.DefaultLangSys = lang
            script.LangSysRecord = []; script.LangSysCount = 0
            record = ot.ScriptRecord(); record.ScriptTag = tag; record.Script = script
            G.ScriptList.ScriptRecord.append(record)
        G.ScriptList.ScriptCount = len(G.ScriptList.ScriptRecord)
    lk = ot.Lookup(); lk.LookupType = 4; lk.LookupFlag = 0; lk.SubTable = [st]; lk.SubTableCount = 1
    seen = set()
    def bump(o):
        if id(o) in seen or o is None: return
        seen.add(id(o))
        if isinstance(o, list):
            for x in o: bump(x)
            return
        if not hasattr(o, "__dict__"): return
        for k2, v in list(vars(o).items()):
            if k2 == "LookupListIndex":
                setattr(o, k2, [i + 1 for i in v] if isinstance(v, list) else v + 1)
            elif isinstance(v, (list, object)) and not isinstance(v, (str, int, float, bytes)):
                bump(v)
    bump(G.FeatureList); bump(G.LookupList)
    G.LookupList.Lookup.insert(0, lk); G.LookupList.LookupCount = len(G.LookupList.Lookup)
    # nhóm ngôn ngữ nào đã có ccmp → THÊM lookup 0 vào ccmp sẵn có; chưa có mới gắn ccmp mới (lỗi 27/10: trước đây luôn gắn ccmp thứ hai
    # → một nhóm ngôn ngữ khai ccmp 2 lần, `serif.regular.condensed.contrast.ttf` VN; kiemword.py mục GSUB / GPOS bắt lỗi này)
    fr = ot.FeatureRecord(); fr.FeatureTag = "ccmp"; fr.Feature = ot.Feature(); fr.Feature.FeatureParams = None
    fr.Feature.LookupListIndex = [0]; fr.Feature.LookupCount = 1
    G.FeatureList.FeatureRecord.append(fr); fi = len(G.FeatureList.FeatureRecord) - 1; G.FeatureList.FeatureCount = fi + 1
    FRs = G.FeatureList.FeatureRecord
    for sr in G.ScriptList.ScriptRecord:
        lss = ([sr.Script.DefaultLangSys] if sr.Script.DefaultLangSys else []) + [l.LangSys for l in sr.Script.LangSysRecord]
        for ls in lss:
            have = [i for i in ls.FeatureIndex if i != fi and FRs[i].FeatureTag == "ccmp"]
            if have:
                for i in have:
                    if 0 not in FRs[i].Feature.LookupListIndex:
                        FRs[i].Feature.LookupListIndex = sorted(FRs[i].Feature.LookupListIndex + [0]); FRs[i].Feature.LookupCount = len(FRs[i].Feature.LookupListIndex)
            else:
                ls.FeatureIndex = sorted(ls.FeatureIndex + [fi]); ls.FeatureCount = len(ls.FeatureIndex)
    if not any(fi in ls.FeatureIndex for sr in G.ScriptList.ScriptRecord
               for ls in ([sr.Script.DefaultLangSys] if sr.Script.DefaultLangSys else []) + [l.LangSys for l in sr.Script.LangSysRecord]):
        FRs.pop(fi); G.FeatureList.FeatureCount = len(FRs)   # mọi nhóm đã có ccmp → bỏ bản ghi mới (đang ở cuối, không lệch chỉ số)
    print("combining marks %d, ccmp ligatures %d" % (comb_added, len(ligs)))

# ---------------- metrics & names ----------------
head, os2 = f["head"], f["OS/2"]
gs2 = f.getGlyphSet()
ymax, ymin = head.yMax, head.yMin
for name in [v[0] for v in added.values()] + list(replaced.values()):
    bp = BoundsPen(gs2); gs2[name].draw(bp)
    if bp.bounds: ymax = max(ymax, math.ceil(bp.bounds[3])); ymin = min(ymin, math.floor(bp.bounds[1]))
head.yMax, head.yMin = ymax, ymin
if IS_CFF: top.FontBBox = [head.xMin, ymin, head.xMax, ymax]
os2.usWinAscent = max(os2.usWinAscent, ymax); os2.usWinDescent = max(os2.usWinDescent, -ymin)
# KHÔNG bật USE_TYPO_METRICS (lỗi 27/10): bật thì Word lấy đỉnh dòng từ typo (thấp) → cắt dấu chồng chữ hoa. Font gốc đã bật mà typo thấp hơn mực → tắt,
# để Word dùng win (đã nâng ở trên). Chế độ vmetrics "fit" bên dưới đặt typo = win nên bật / tắt đều an toàn.
if os2.sTypoAscender < ymax or os2.sTypoDescender > ymin: os2.fsSelection &= ~(1 << 7)
VM = CFG.get("vmetrics", "keep")
if VM == "fit":   # line box holds every mark: Canva / web / Word all use these, nothing pokes out
    hh = f["hhea"]
    asc, desc = int(math.ceil(ymax)), min(int(math.floor(ymin)), f["hhea"].descent, os2.sTypoDescender)
    hh.ascent = os2.sTypoAscender = os2.usWinAscent = asc
    hh.descent = os2.sTypoDescender = desc; os2.usWinDescent = -desc
    hh.lineGap = os2.sTypoLineGap = 0
# a proportional font flagged monospaced makes Windows/GDI and some apps space every glyph alike
advs = [hmtx[g][0] for g in order if hmtx[g][0] > 0]
pitch_fixed = False
if CFG.get("fix_fixed_pitch", True) and len(set(advs)) > 3:
    if f["post"].isFixedPitch: f["post"].isFixedPitch = 0; pitch_fixed = True
    if IS_CFF and getattr(top, "isFixedPitch", 0): top.isFixedPitch = 0; pitch_fixed = True
    if os2.panose.bProportion == 9: os2.panose.bProportion = 0; pitch_fixed = True
os2.xAvgCharWidth = int(round(sum(advs) / len(advs)))

suffix = CFG.get("suffix", "VN")
nm = f["name"]
fam0 = nm.getDebugName(16) or nm.getDebugName(1)
ps0 = nm.getDebugName(6) or fam0.replace(" ", "")
fam = fam0 + " " + suffix
psn = (ps0.split("-")[0] + suffix.replace(" ", "")) + ("-" + ps0.split("-")[1] if "-" in ps0 else "")
for rec in list(nm.names):
    if rec.nameID in (1, 16): nm.setName(fam, rec.nameID, rec.platformID, rec.platEncID, rec.langID)
    elif rec.nameID == 4: nm.setName(fam + ("" if (nm.getDebugName(2) or "Regular") == "Regular" else " " + nm.getDebugName(2)), 4, rec.platformID, rec.platEncID, rec.langID)
    elif rec.nameID == 6: nm.setName(psn, 6, rec.platformID, rec.platEncID, rec.langID)
    elif rec.nameID == 3: nm.setName(str(rec) + ";" + suffix, 3, rec.platformID, rec.platEncID, rec.langID)
if IS_CFF:
    cff.fontNames = [psn]; top.FullName = fam; top.FamilyName = fam
# "sb_fix": {"comma": 2} — đặt lại LSB vài glyph dấu câu (phẩy LSB âm + chữ tròn RSB âm → phẩy dính chữ; đặt bằng LSB dấu chấm)
for _gn, _lsb in CFG.get("sb_fix", {}).items():
    from fontTools.pens.boundsPen import BoundsPen as _BP
    from fontTools.pens.transformPen import TransformPen as _TP
    from fontTools.pens.t2CharStringPen import T2CharStringPen
    _gs = f.getGlyphSet(); _b = _BP(_gs); _gs[_gn].draw(_b); _x0 = _b.bounds[0]; _w = _gs[_gn].width
    _dx = _lsb * K - _x0; _nw = int(round(_w + _dx))
    if IS_CFF:
        _pen = T2CharStringPen(_nw - getattr(top.Private, 'nominalWidthX', 0), None)
        _gs[_gn].draw(_TP(_pen, (1, 0, 0, 1, _dx, 0)))
        csi[_gn] = _pen.getCharString(private=top.Private, globalSubrs=top.GlobalSubrs)
    hmtx[_gn] = (_nw, int(round(_lsb * K)))
    print("sb_fix %s: LSB %d → %d, width %d → %d" % (_gn, _x0, _lsb * K, _w, _nw))
# sanity: CFF charstring widths must equal hmtx, else Windows/Word space glyphs wrongly
if IS_CFF:
    from fontTools.pens.basePen import NullPen
    _bad = []
    for _g in f.getGlyphOrder():
        _c = csi[_g]; _c.draw(NullPen())
        if abs(_c.width - hmtx[_g][0]) > 0.5: _bad.append(_g)
    assert not _bad, "CFF width != hmtx for %d glyphs, e.g. %s" % (len(_bad), _bad[:5])
f.save(A.out)

if A.recipes:
    marks_local = {k: to_json_contours(mark(k)[0]) for k in ["hook", "hook_s", "horn", "dot", "acute", "grave", "tilde", "circ", "breve"]}
    json.dump({"upm": UPM, "tilde_w": round(TILDE_W), "axis": round(SLANT, 2), "marks": marks_local, "glyphs": recipes}, open(A.recipes, "w"))
print("spacing matched on %d accented letters; fixed-pitch flag cleared: %s" % (len(spacing_fixed), pitch_fixed))
print("text axis %.2f° (%s)%s; horn advance: %s; vertical metrics: %s" % (SLANT, SLANT_SRC, " → marks leaned" if TAN else "", "contain" if HORN_CONTAIN else "kern", VM))
print("added %d, rebuilt %d, horn kerns %d; tilde weight %.0f; yMax %d yMin %d → %s" % (len(added), len(replaced), kern_added, TILDE_W, ymax, ymin, A.out))
