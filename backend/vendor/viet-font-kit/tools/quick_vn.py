"""quick_vn.py — dựng chữ Việt DỰ PHÒNG khi máy chặn pypi (không có skia-pathops / shapely / uharfbuzz).
Chỉ cần fontTools + numpy + Pillow + scikit-image (có sẵn trong máy cloud). Hợp với font .ttf nét đều / viết tay.

  python3 -I quick_vn.py SRC.ttf OUT.ttf [--recipes recipes.json] [--horn horn5.json] [--cfg quick.json]

Cách dựng (luật src-marks: tôn trọng dấu font gốc):
  * dấu sắc / huyền / ngã / mũ / trăng: lấy đúng glyph dấu của font, vị trí theo chữ ghép sẵn (á Â ã…); chữ chưa có
    thì suy từ tâm dấu của các chữ ghép sẵn cùng chữ gốc;
  * dấu hỏi: khung xương dấu ? của font → co về cỡ dấu → vẽ lại nét đều, dày bằng chỗ dày nhất của dấu ngã (hook-weight-tilde);
  * chữ hoa (uc_sync, mặc định): mọi dấu trên đặt giữa thân, đáy cách đỉnh chữ một khe chung UC_GAP — đồng bộ cả chữ ghép sẵn của font;
  * dấu nặng: đúng contour chấm chữ i (luật dot);
  * dấu chồng: dấu thanh bên phải dấu mũ (khe đều), dấu ngã / dấu trên dấu trăng đặt giữa trên đỉnh;
    --cfg {"stack_place": "top"} = mọi dấu thanh chồng trên đỉnh dấu mũ (vòng 1 luôn dựng cả 2 hướng để chọn);
    --cfg {"hook_src": "half"} = dấu hỏi vẽ từ NỬA TRÊN dấu ? (vòng 1 luôn có 1 VER này);
    --cfg {"hook_src": "notail"} = cả thân dấu ? nhưng bỏ đuôi móc cong ở chân;
    --cfg {"hook_s_xstretch": 1.35} = dấu hỏi khi chồng rộng ngang hơn dấu đơn (mặc định 1,35);
    --cfg {"stack_rel": {"acute": [-92, -11]}} = dấu thanh trên dấu mũ đặt theo số đo chữ người dùng vẽ (góc trái-dưới dấu so với phải / đỉnh dấu mũ);
        chữ hẹp chìa quá stack_overhang (40) thì dời cả cụm sang trái ≤ stack_shift_max (0,15) × bề ngang dấu mũ;
    --cfg {"stack_dx": {"acute": 40}, "stack_dx_ch": {"ổ": 20}} = dấu chồng trên đỉnh dời ngang (theo dấu / theo chữ, đơn vị font);
    --cfg {"stack_place": "top", "stack_right": ["acute"]} = dấu chồng trên đỉnh, riêng dấu sắc bên phải dấu mũ (người dùng 27/10);
    --cfg {"acute_len": 1.3, "grave_len": 1.3} = kéo dài dấu sắc / huyền (giữ bề dày, giữ đáy), sửa luôn glyph dấu của font;
    --cfg {"hook_weight": "acute_grave"} = dấu hỏi dày theo sắc / huyền (đầu dày, thuôn về chân) thay vì dày đều = dấu ngã;
  * râu ơ ư: công thức horn5 (kệ + thanh đậm), nối vào vai o / đỉnh chân phải u, cắt gốc trong nét;
  * đ: d + thanh ngang từ dấu gạch nối; Đ: chép Ð (U+00D0) của font.
Hợp nét: tô raster các mảnh rồi dò viền (skimage) → khớp đường cong (fitcurve) → bậc 2 (Cu2QuPen). Không chồng nét thừa.
Glyph mới tên uniXXXX, giữ nguyên mọi glyph gốc (có hinting). Không thêm ccmp (gõ tổ hợp NFD dùng font dự phòng)."""
import sys, os, json, math, argparse, unicodedata
import numpy as np
from PIL import Image, ImageDraw
from skimage import measure
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.boundsPen import BoundsPen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fitcurve import ring_to_contour

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--recipes"); ap.add_argument("--horn"); ap.add_argument("--cfg")
A = ap.parse_args()
CFG = json.load(open(A.cfg)) if A.cfg else {}
f = TTFont(A.src); gs = f.getGlyphSet(); cm = f.getBestCmap(); UPM = f["head"].unitsPerEm
glyf, hmtx = f["glyf"], f["hmtx"]

# ---------------- hình học ----------------
def contours(name):
    p = DecomposingRecordingPen(gs); gs[name].draw(p); out, cur = [], []
    for op, pts in p.value:
        if op == "moveTo": cur = [(op, list(pts))]
        elif op in ("closePath", "endPath"): cur.append(("closePath", [])); out.append(cur); cur = []
        else: cur.append((op, list(pts)))
    return out
def tf(cs, t):
    a, b, c, d, e, g = t
    return [[(op, [None if pt is None else (a * pt[0] + c * pt[1] + e, b * pt[0] + d * pt[1] + g) for pt in pts]) for op, pts in cn] for cn in cs]
def mv(cs, dx, dy): return tf(cs, (1, 0, 0, 1, dx, dy))
def draw(cs, pen):
    for c in cs:
        for op, pts in c: getattr(pen, op)(*pts)
def bb(cs):
    bp = BoundsPen(None); draw(cs, bp); return bp.bounds
class FlatPen(BasePen):
    def __init__(s, n=10): super().__init__(None); s.P = []; s.cur = []; s.n = n
    def _moveTo(s, p): s.cur = [p]
    def _lineTo(s, p): s.cur.append(p)
    def _curveToOne(s, a, b, c):
        p0 = s.cur[-1]
        for i in range(1, s.n + 1):
            t = i / s.n; u = 1 - t
            s.cur.append((u**3*p0[0] + 3*u*u*t*a[0] + 3*u*t*t*b[0] + t**3*c[0], u**3*p0[1] + 3*u*u*t*a[1] + 3*u*t*t*b[1] + t**3*c[1]))
    def _qCurveToOne(s, a, b):
        p0 = s.cur[-1]
        for i in range(1, s.n + 1):
            t = i / s.n; u = 1 - t
            s.cur.append((u*u*p0[0] + 2*u*t*a[0] + t*t*b[0], u*u*p0[1] + 2*u*t*a[1] + t*t*b[1]))
    def _closePath(s):
        if len(s.cur) > 2: s.P.append(s.cur)
        s.cur = []
    _endPath = _closePath
def polys(cs, n=10):
    p = FlatPen(n); draw(cs, p); return p.P
def xs_at(cs, y):
    X = []
    for P in polys(cs, 16):
        for i in range(len(P)):
            (x0, y0), (x1, y1) = P[i], P[(i + 1) % len(P)]
            if (y0 <= y < y1) or (y1 <= y < y0): X.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return X
def pts_of(cs): return np.array([p for P in polys(cs, 8) for p in P], float)
def mindist(a, b):
    A_, B_ = pts_of(a), pts_of(b)
    if not len(A_) or not len(B_): return 1e9
    return float(np.sqrt(((A_[:, None, :] - B_[None, :, :]) ** 2).sum(-1)).min())

# ---- raster: hợp nét + dò viền (thay pathops) ----
RES = 4   # điểm ảnh / đơn vị font
class Canvas:
    def __init__(s, box, pad=12):
        s.x0, s.y0 = box[0] - pad, box[1] - pad
        s.W = int((box[2] - box[0] + 2 * pad) * RES) + 1; s.H = int((box[3] - box[1] + 2 * pad) * RES) + 1
        s.im = Image.new("L", (s.W, s.H), 0); s.d = ImageDraw.Draw(s.im)
    def px(s, p): return ((p[0] - s.x0) * RES, (s.H - 1) - (p[1] - s.y0) * RES)
    def disc(s, p, r):
        x, y = s.px(p); r *= RES; s.d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    def poly(s, P): s.d.polygon([s.px(p) for p in P], fill=255)
    def glyph(s, cs):   # tô theo even-odd (lòng chữ rỗng)
        lay = np.zeros((s.H, s.W), bool)
        for P in polys(cs, 14):
            im = Image.new("1", (s.W, s.H), 0); ImageDraw.Draw(im).polygon([s.px(p) for p in P], fill=1); lay ^= np.array(im, bool)
        s.im = Image.fromarray(np.maximum(np.array(s.im), lay.astype(np.uint8) * 255)); s.d = ImageDraw.Draw(s.im)
    def clip_x(s, xmin):
        a = np.array(s.im); c = int((xmin - s.x0) * RES)
        if c > 0: a[:, :c] = 0
        s.im = Image.fromarray(a); s.d = ImageDraw.Draw(s.im)
    def contours(s, err=1.0):
        a = np.pad(np.array(s.im, float) / 255.0, 1)
        out = []
        for c in measure.find_contours(a, 0.5):
            P = [((x - 1) / RES + s.x0, (s.H - 1 - (y - 1)) / RES + s.y0) for y, x in c][:-1]
            P = measure.approximate_polygon(np.array(P), 0.12)[:-1].tolist()
            if len(P) < 4: continue
            ar = 0.5 * sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))
            if abs(ar) < 30: continue
            out.append((ar, P))
        cs = []
        for ar, P in out:
            # TrueType: viền ngoài theo chiều kim đồng hồ (diện tích âm), lòng ngược lại
            inner = any(_inside(P[0], Q) for a2, Q in out if Q is not P and abs(a2) > abs(ar))
            if (ar > 0) != inner: P = P[::-1]
            c = ring_to_contour([tuple(p) for p in P], err=err)
            # khớp đường cong đôi khi bắn tay nắm dài → gai mảnh lòi ra ngoài (dấu hỏi nửa trên, cỡ nhỏ). Lệch khung bao > 1,5 đv
            # so với đa giác gốc thì giữ đa giác (lineTo) cho đoạn đó — hình đúng quan trọng hơn ít điểm.
            pb = (min(p[0] for p in P), min(p[1] for p in P), max(p[0] for p in P), max(p[1] for p in P))
            fp = polys([c], 16); fb = (min(q[0] for Q in fp for q in Q), min(q[1] for Q in fp for q in Q), max(q[0] for Q in fp for q in Q), max(q[1] for Q in fp for q in Q)) if fp else pb
            if max(abs(u - v) for u, v in zip(pb, fb)) > 1.5:
                c = [("moveTo", [tuple(P[0])])] + [("lineTo", [tuple(q)]) for q in P[1:]] + [("closePath", [])]
            cs.append(c)
        return cs
def _inside(p, Q):
    x, y = p; c = False
    for i in range(len(Q)):
        (x0, y0), (x1, y1) = Q[i], Q[i - 1]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0): c = not c
    return c
def stroke(cv, pts, ws):
    """nét đầu tròn bề dày thay đổi = hợp các đĩa + bao lồi từng cặp (như marks.vstroke)"""
    for (p, w), (q, w2) in zip(zip(pts, ws), zip(pts[1:], ws[1:])):
        cv.disc(p, w / 2); cv.disc(q, w2 / 2)
        dx, dy = q[0] - p[0], q[1] - p[1]; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
        cv.poly([(p[0] + nx * w / 2, p[1] + ny * w / 2), (q[0] + nx * w2 / 2, q[1] + ny * w2 / 2), (q[0] - nx * w2 / 2, q[1] - ny * w2 / 2), (p[0] - nx * w / 2, p[1] - ny * w / 2)])

def thickness(cs, q=None):
    """bề dày nét: 2 × khoảng cách tới mép, đo trên khung xương — trung vị, hoặc phân vị q (95 = chỗ dày nhất, bỏ nhiễu)"""
    from scipy.ndimage import distance_transform_edt
    from skimage.morphology import skeletonize
    b = bb(cs); cv = Canvas(b, 4); cv.glyph(cs); m = np.array(cv.im) > 127
    dt = distance_transform_edt(m); sk = skeletonize(m)
    v = dt[sk]; return float((np.percentile(v, q) if q else np.median(v)) * 2 / RES) if len(v) else 40.0
def skeleton(cs):
    """đường tâm có thứ tự của một nét (dấu ?): đi từ đầu mút cao-trái tới đầu kia"""
    from skimage.morphology import skeletonize
    b = bb(cs); cv = Canvas(b, 4); cv.glyph(cs); m = np.array(cv.im) > 127
    sk = skeletonize(m); P = set(zip(*np.nonzero(sk)))
    def nb(p): r, c = p; return [(r + i, c + j) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i or j) and (r + i, c + j) in P]
    ends = [p for p in P if len(nb(p)) == 1]
    toxy = lambda p: (p[1] / RES + cv.x0, (cv.H - 1 - p[0]) / RES + cv.y0)
    ymid = (b[1] + b[3]) / 2
    up = [p for p in ends if toxy(p)[1] > ymid] or ends
    start = min(up, key=lambda p: toxy(p)[0]); path, seen, cur = [start], {start}, start
    while True:
        nx_ = [q for q in nb(cur) if q not in seen]
        if not nx_: break
        cur = min(nx_, key=lambda q: abs(q[0] - path[-1][0]) + abs(q[1] - path[-1][1])); path.append(cur); seen.add(cur)
    return [toxy(p) for p in path]
def resample(pts, n=60, k=9):
    P = np.array(pts, float)
    if len(P) > k:
        ker = np.ones(k) / k
        P = np.c_[np.convolve(np.pad(P[:, 0], k // 2, mode="edge"), ker, "valid"), np.convolve(np.pad(P[:, 1], k // 2, mode="edge"), ker, "valid")]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]; t = np.linspace(0, d[-1], n)
    return list(zip(np.interp(t, d, P[:, 0]), np.interp(t, d, P[:, 1])))
def bez(p0, p1, p2, p3, n=60):
    return [((1-t)**3*p0[0] + 3*(1-t)**2*t*p1[0] + 3*(1-t)*t*t*p2[0] + t**3*p3[0], (1-t)**3*p0[1] + 3*(1-t)**2*t*p1[1] + 3*(1-t)*t*t*p2[1] + t**3*p3[1]) for t in (i / n for i in range(n + 1))]

# ---------------- dấu của font ----------------
def gname(ch): return cm.get(ord(ch))
MARKG = {"acute": "´", "grave": "`", "tilde": "˜", "circ": "ˆ", "breve": "˘"}
MK = {k: contours(gname(v)) for k, v in MARKG.items() if gname(v)}
# kéo dài dấu sắc / huyền (người dùng 26/10 “độ dài dấu sắc ngắn quá”): giãn dọc theo trục chính của dấu, giữ nguyên bề dày,
# giữ đáy (đầu dưới) đứng yên, KHÔNG đặt lại tâm (đặt lại tâm làm chân dấu lùi trái) → khe tới chữ không đổi. Ghi đè luôn glyph dấu của font nên mọi chữ ghép
# (á é ó… có sẵn) dài theo. acute_len / grave_len = hệ số (1 = giữ nguyên).
MLEN = {}
_ACH0 = bb(MK["acute"])[3] - bb(MK["acute"])[1]          # cỡ dấu sắc GỐC: cỡ dấu hỏi không chạy theo khi kéo dài sắc
def _stretch(k, f):
    P = np.array([q for Q in polys(MK[k], 10) for q in Q]); c = P.mean(0)
    w, v = np.linalg.eigh(np.cov((P - c).T)); ax = v[:, np.argmax(w)]
    if ax[1] < 0: ax = -ax                                  # trục hướng lên
    lo = P[np.argmin((P - c) @ ax)]                          # đầu dưới của dấu = điểm cố định
    b0 = bb(MK[k]); M = np.eye(2) + (f - 1) * np.outer(ax, ax)
    def T(x, y):
        q = M @ (np.array([x, y]) - lo) + lo; return (float(q[0]), float(q[1]))
    cs = [[(op, [None if pt is None else T(*pt) for pt in pts]) for op, pts in cn] for cn in MK[k]]
    b1 = bb(cs); dx = 0; dy = b0[1] - b1[1]   # đầu dưới đứng yên (vòng 4: đặt lại tâm làm chân dấu sắc lùi trái)
    t = (M[0, 0], M[1, 0], M[0, 1], M[1, 1], lo[0] - M[0, 0] * lo[0] - M[0, 1] * lo[1] + dx, lo[1] - M[1, 0] * lo[0] - M[1, 1] * lo[1] + dy)
    return mv(cs, dx, dy), t
for _k, _ck in (("acute", "acute_len"), ("grave", "grave_len")):
    if CFG.get(_ck, 1) != 1 and _k in MK:
        MK[_k], MLEN[_k] = _stretch(_k, CFG[_ck])
# dáng nét dấu (tab Chỉnh dấu · Chi tiết): {"mark_shape": {"acute": {"h": 120, "t": 80}, "grave": {…}, "tilde": {…}, "dot": {"round": 40}}}
# — h / t = đầu / đuôi dày % (ngã: trái / phải), round = độ tròn % dấu nặng. Cùng công thức với trang (mark_shape.py).
from mark_shape import taper as _taper, round_ as _round
MSHAPE = set()
def _reshape(cs, fn):
    rings = fn([list(map(tuple, Q)) for Q in polys(cs, 14)]); b = bb(cs)
    cv = Canvas((b[0] - 60, b[1] - 60, b[2] + 60, b[3] + 60), 6)
    for Q in rings: cv.poly(Q)
    return cv.contours()
for _k, _sp in (CFG.get("mark_shape") or {}).items():
    if _k in ("acute", "grave", "tilde") and _k in MK and (_sp.get("h", 100) != 100 or _sp.get("t", 100) != 100):
        MK[_k] = _reshape(MK[_k], lambda R, _sp=_sp, _k=_k: _taper(R, _sp.get("h", 100), _sp.get("t", 100), horiz=(_k == "tilde"))); MSHAPE.add(_k)
MBB = {k: bb(v) for k, v in MK.items()}
G2K = {gname(v): k for k, v in MARKG.items() if gname(v)}
# vị trí dấu theo chữ ghép sẵn: PL[chữ gốc][dấu] = (dx, dy)
PL = {}
for n in f.getGlyphOrder():
    g = glyf[n]
    if g.isComposite() and len(g.components) == 2 and g.components[1].glyphName in G2K and g.components[0].x == 0 and g.components[0].y == 0:
        PL.setdefault(g.components[0].glyphName, {})[G2K[g.components[1].glyphName]] = (g.components[1].x, g.components[1].y)
def mcx(k): b = MBB[k]; return (b[0] + b[2]) / 2
def is_uc(L): return L.isupper()
UC_SYNC = CFG.get("uc_sync", True)
def _uc_gap():
    """khe dấu thanh trên chữ hoa: trung vị khe (đáy dấu − đỉnh chữ) của chữ hoa ghép sẵn có khe hợp lý (bỏ chữ dấu chìm / quá cao)"""
    gs_ = []
    for bn, v in PL.items():
        if len(bn) == 1 and bn.isupper() and bn in "AEIOUY":
            top = bb(contours(bn))[3]
            for k, (dx, dy) in v.items():
                if k in ("acute", "grave", "tilde"):
                    g = MBB[k][1] + dy - top
                    if 20 <= g <= 80: gs_.append(g)
    return sorted(gs_)[len(gs_) // 2] if gs_ else 42
UC_GAP = CFG.get("uc_gap") or _uc_gap()
_UCA = {}
def uc_axis(L):
    """trục dấu chữ hoa = giữa phần mực ở 1/4 trên của chữ (đỉnh A, giữa 2 càng U Y, đỉnh vòm O) — không lấy giữa khung bao
    vì chữ viết tay có nét chìa (gạch ngang A kéo dài sang phải)."""
    if L not in _UCA:
        cs = contours(gname(L)); b = bb(cs); h = b[3] - b[1]; xs = []
        for y in np.linspace(b[3] - 0.25 * h, b[3] - 2, 12): xs += xs_at(cs, y)
        _UCA[L] = (min(xs) + max(xs)) / 2 if xs else (b[0] + b[2]) / 2
    return _UCA[L]
def place(L, k):
    """(dx, dy) cho dấu k trên chữ gốc L.
    Chữ hoa (uc_sync, mặc định bật — người dùng 26/10 “dấu bị thấp, sửa lại nhớ đồng bộ”): mọi dấu trên đặt giữa thân chữ,
    đáy dấu cách đỉnh chữ đúng UC_GAP — kể cả chữ ghép sẵn của font (À Á Ú Ô… font gốc đặt lệch, có dấu chìm vào chữ)."""
    if UC_SYNC and is_uc(L) and k in MBB:
        b = bb(contours(gname(L))); lean = CFG.get("ag_lean", 0.15) * (MBB[k][2] - MBB[k][0]) * (1 if k == "acute" else -1 if k == "grave" else 0)   # sắc lệch nhẹ phải, huyền lệch nhẹ trái
        return (uc_axis(L) - mcx(k) + lean, b[3] + UC_GAP - MBB[k][1])
    base = gname(L); have = PL.get(base, {})
    if k in have: return have[k]
    cx = [dx + mcx(kk) for kk, (dx, dy) in have.items()]
    b = bb(contours(base))
    x = sum(cx) / len(cx) if cx else (b[0] + b[2]) / 2
    same = [v[k][1] for bn, v in PL.items() if k in v and len(bn) == 1 and bn.isalpha() and bn.isupper() == is_uc(L)]
    dy = sorted(same)[len(same) // 2] if same else 0
    if is_uc(L) and not same: dy = CFG.get("uc_dy", 200)
    return (x - mcx(k), dy)
def anchor(L):
    """trục đặt dấu trên của chữ L = trung bình tâm các dấu ghép sẵn"""
    have = PL.get(gname(L), {})
    if have: return sum(dx + mcx(k) for k, (dx, dy) in have.items()) / len(have)
    b = bb(contours(gname(L))); return (b[0] + b[2]) / 2

ST = thickness(MK["acute"])                     # nét dấu sắc
STEM = thickness(contours(gname("l")))           # nét thân
print("nét dấu sắc %.1f · nét thân %.1f" % (ST, STEM))
# đáy dấu sắc chữ thường / hoa (luật gap_src: đáy dấu hỏi = đáy dấu sắc gốc)
ACB_LC = MBB["acute"][1] + place("a", "acute")[1]
ACB_UC = MBB["acute"][1] + place("A", "acute")[1]
ACH = _ACH0

# ---- dấu hỏi từ khung xương dấu ? ----
q = contours(gname("?")); q = sorted(q, key=lambda c: bb([c])[1])
qbody = q[1:] if len(q) > 1 else q
SK_FULL = resample(skeleton(qbody), 64, 9)
# hook_src "full": cả thân dấu ? (bỏ chấm) → dấu hỏi · "half" (người dùng 26/10): CHỈ NỬA TRÊN dấu ? — vòm + đầu cổ, cắt ở
# hook_half (0,5 = nửa chiều cao thân ?) — dấu hỏi tiếng Việt là phần móc trên, không mang cả đuôi cong dưới của dấu ?.
HOOK_SRC = CFG.get("hook_src", "full")
def _half(sk, frac):
    ys = [p[1] for p in sk]; cut = max(ys) - frac * (max(ys) - min(ys)); out = []
    for p in sk:
        out.append(p)
        if p[1] < cut and len(out) > 8: break
    return resample(out, 56, 5)
def _notail(sk):
    """bỏ ĐUÔI MÓC dưới chân dấu ? (người dùng 26/10): đi theo khung xương tới điểm trái nhất ở 45 % dưới (đáy nét chéo),
    cắt ở đó — giữ vòm + cổ chéo, bỏ phần cong ngược sang phải ở chân"""
    ys = [p[1] for p in sk]; lim = min(ys) + 0.45 * (max(ys) - min(ys))
    low = [i for i, p in enumerate(sk) if p[1] <= lim]
    if not low: return sk
    i = min(low, key=lambda j: sk[j][0])
    return resample(sk[:i + 1], 56, 3)
SK = _half(SK_FULL, CFG.get("hook_half", 0.5)) if HOOK_SRC == "half" else _notail(SK_FULL) if HOOK_SRC == "notail" else SK_FULL
def hook_shape(h, w, w_tail=None, xstretch=None):
    """w: bề dày đầu móc; w_tail: bề dày cuối nét (chân) — thuôn dần như nét bút dạ khi nhấc bút (theo dấu sắc / huyền)"""
    xs = [p[0] for p in SK]; ys = [p[1] for p in SK]; wm = (w + (w_tail if w_tail else w)) / 2; s = (h - wm) / (max(ys) - min(ys))
    xst = xstretch or CFG.get("hook_xstretch", 1.2 if HOOK_SRC == "full" else 1.0)
    pts = [((x - min(xs)) * s * xst, (y - min(ys)) * s) for x, y in SK]
    n = len(pts) - 1
    ws = [(w + ((w_tail if w_tail else w) - w) * (i / n) ** 1.2) * (0.85 + 0.15 * min(1, i / 12)) for i in range(n + 1)]
    W = max(ws); cv = Canvas((-W, -W, max(p[0] for p in pts) + W, h + W), 6); stroke(cv, pts, ws)
    cs = cv.contours(); b = bb(cs); tail = pts[-1][0]
    return mv(cs, -(b[0] + b[2]) / 2, -b[1]), tail - (b[0] + b[2]) / 2
TILDE_W = thickness(MK["tilde"], 75)              # độ dày thân dấu ngã font gốc (phân vị 75: bỏ cục mực ở chỗ bẻ nét)
# hook_weight "tilde" (mặc định, luật hook-weight-tilde): dấu hỏi dày đều = thân dấu ngã.
# hook_weight "acute_grave" (người dùng 26/10 “độ dày dấu hỏi follow theo dấu huyền và sắc”): đầu móc dày = chỗ dày nhất của
#   sắc / huyền (phân vị 90), thuôn về chân = chỗ mảnh của sắc / huyền (phân vị 25, trung bình 2 dấu) — cùng nhịp nét bút.
# Nét dày lên thì dấu phải cao + rộng theo (cao ≥ 4,4 × dày) để lòng móc không bị lấp thành cục. Ở mọi cỡ giữ nguyên độ dày.
HOOK_WEIGHT = CFG.get("hook_weight", "tilde")
if HOOK_WEIGHT == "acute_grave":
    HOOK_W = CFG.get("hook_w", max(thickness(MK["acute"], 90), thickness(MK["grave"], 90)))
    HOOK_WT = CFG.get("hook_w_tail", (thickness(MK["acute"], 25) + thickness(MK["grave"], 25)) / 2)
else:
    HOOK_W = CFG.get("hook_w", TILDE_W); HOOK_WT = CFG.get("hook_w_tail", HOOK_W)
HOOK_H = CFG.get("hook_h", max(ACH * (1.4 if HOOK_SRC == "half" else 1.65), (HOOK_W + HOOK_WT) / 2 * (3.4 if HOOK_SRC == "half" else 4.4)))
HOOK, HOOK_TAIL = hook_shape(HOOK_H, HOOK_W, HOOK_WT)
# dấu hỏi khi chồng: rộng ngang hơn dấu đơn (hook_s_xstretch × bề ngang dấu đơn) cho rõ ở cỡ nhỏ (người dùng 27/10)
HOOK_S, HOOK_S_TAIL = hook_shape(HOOK_H * 0.82, HOOK_W, HOOK_WT, CFG.get("hook_s_xstretch", 1.35) * CFG.get("hook_xstretch", 1.2 if HOOK_SRC == "full" else 1.0))
# ---- dấu nặng = chấm chữ i ----
ic = contours(gname("i")); stem_top = bb(contours(gname("ı")))[3] if gname("ı") else 560
idot = [c for c in ic if bb([c])[1] > stem_top - 20] or [min(ic, key=lambda c: bb([c])[3] - bb([c])[1])]
db = bb(idot); DOT = mv(idot, -(db[0] + db[2]) / 2, -(db[1] + db[3]) / 2); DOT_H = db[3] - db[1]
_rd = ((CFG.get("mark_shape") or {}).get("dot") or {}).get("round", 0)
if _rd: DOT = _reshape(DOT, lambda R: _round(R, _rd)); db = bb(DOT); DOT_H = db[3] - db[1]   # độ tròn dấu nặng
DOT_GAP = CFG.get("dot_gap", max(30, ACB_LC - bb(contours(gname("a")))[3]))

# ---------------- râu ơ ư (công thức horn5) ----------------
H5 = json.load(open(A.horn)) if A.horn and os.path.exists(A.horn) else {}
HK = dict(reach=60, rise=80, thin=round(STEM * 0.75), head=round(STEM * 1.35), p=2.15, t0=0.29, dyO=0, dyU=0, clip=36)
HK.update(H5.get("all", {})); LCR = H5.get("lc_ratio", 0.9); LCW = H5.get("lc_wratio", 1.0)
def horn(L, body):
    up = L.isupper(); s = 1.0 if up else LCR
    ref = contours(gname("U" if up else "u")); top = bb(ref)[3]
    y0 = top + HK["dyU"] * s + (HK["dyO"] if L in "oO" else 0)
    xs = xs_at(body, y0 - (60 if L in "uU" else 50 * s))
    x0 = (max(xs) if xs else bb(body)[2]) - (0 if L in "uU" else 8)
    pts = [(x0 + x * s, y0 + y * s) for x, y in bez((-70, -50), (6, -56), (HK["reach"] + 2, -16), (HK["reach"], HK["rise"]))]
    n = len(pts) - 1; ws = []
    for i in range(n + 1):
        u = max(0.0, (i / n - HK["t0"]) / (1 - HK["t0"]))
        ws.append((HK["thin"] + (HK["head"] - HK["thin"]) * u ** HK["p"]) * (1.0 if up else LCW))
    b = bb([[("moveTo", [p]) for p in pts]]) if False else (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
    cv = Canvas((b[0] - 80, b[1] - 80, b[2] + 80, b[3] + 80), 4); stroke(cv, pts, ws); cv.clip_x(x0 - HK["clip"] * s)
    return cv.contours(), (x0, y0)

# ---------------- dựng ----------------
TONE = {"́": "acute", "̀": "grave", "̉": "hook", "̃": "tilde"}
VN = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
VN = VN + VN.upper()
GAP_STACK = CFG.get("stack_gap", max(22, round(ST * CFG.get("stack_gap_k", 0.95))))   # khe dấu thanh ↔ dấu mũ / trăng ≈ 1 nét dấu (0,55 nét: nhìn xa như dính — vòng 4)
new, recipes, report = {}, {}, []
def mark_cs(k, L, stacked=False):
    """contour dấu k đặt trên chữ gốc L (chưa xét dấu chồng)"""
    up = L.isupper()
    if k == "hook" and up and UC_SYNC:      # chữ hoa: chân dấu hỏi trên trục giữa thân, đáy cách đỉnh chữ UC_GAP
        b = bb(contours(gname(L))); t = (1, 0, 0, 1, uc_axis(L) - HOOK_TAIL, b[3] + UC_GAP)
        return tf(HOOK, t), ("hook", t)
    if k == "hook":
        ax = anchor(L) + CFG.get("hook_dx", 0.035) * (bb(contours(gname(L)))[2] - bb(contours(gname(L)))[0])
        ax -= HOOK_TAIL   # chân dấu hỏi (cuối nét) đặt trên trục, không phải tâm khung bao (dấu bỏ đuôi có chân lệch trái tâm)
        return mv(HOOK, ax, ACB_UC if up else ACB_LC), ("hook", (1, 0, 0, 1, ax, ACB_UC if up else ACB_LC))
    dx, dy = place(L, k); return mv(MK[k], dx, dy), (k, (1, 0, 0, 1, dx, dy))
_CUR_CH = [""]   # chữ đang dựng (cho stack_dx_ch)
SHIFTED = []    # chữ hẹp dời cụm dấu chồng sang trái (stack_rel)
def stack(base_mark, bk, tone, L):
    """dấu thanh chồng trên dấu mũ / trăng: ngã + mọi dấu trên trăng đặt giữa trên đỉnh; sắc huyền hỏi trên mũ đặt bên phải"""
    mb = bb(base_mark); sc = CFG.get("stack_scale", 0.82)
    src = HOOK_S if tone == "hook" else MK[tone]
    key = "hook_s" if tone == "hook" else tone
    sb = bb(src)
    rel = CFG.get("stack_rel", {})
    if bk == "circ" and tone in rel:
        # stack_rel {"acute": [dx, dy]}: góc trái-dưới khung bao dấu thanh = (phải dấu mũ + dx, đỉnh dấu mũ + dy) — số đo lấy từ chữ người dùng
        # tự vẽ trên Bàn vẽ (vòng 8: ấ ầ ẩ) → mọi chữ có dấu mũ cùng quan hệ dấu thanh ↔ dấu mũ (dấu mũ cùng một hình) = đều.
        dx0, dy0 = rel[tone]
        t = (sc, 0, 0, sc, mb[2] + dx0 - sc * sb[0], mb[3] + dy0 - sc * sb[1])
        return tf(src, t), (key, t)
    top_ = CFG.get("stack_place", "right") == "top" and tone not in CFG.get("stack_right", [])   # stack_right: dấu đặt bên phải dù "top" (vd ["acute"])
    if tone == "tilde" or bk == "breve" or top_:   # "top": dấu chồng trên đỉnh (VER so sánh vòng 1)
        cx = (mb[0] + mb[2]) / 2 + (8 if tone == "acute" else -8 if tone == "grave" else 0) - (HOOK_S_TAIL * sc if tone == "hook" else 0)   # dấu hỏi chồng: chân trên trục dấu mũ
        # dời ngang thêm khi chồng trên đỉnh: stack_dx {"acute": 40} theo dấu (đơn vị font, thay số +8 mặc định của sắc / huyền),
        # stack_dx_ch {"ổ": 20} theo từng chữ (cộng dồn) — người dùng 27/10: sắc chồng lệch phải NHẸ (không ra hẳn bên phải), hỏi trên ổ nhích phải
        _sd = CFG.get("stack_dx", {})
        if tone in _sd: cx += _sd[tone] - (8 if tone == "acute" else -8 if tone == "grave" else 0)
        cx += CFG.get("stack_dx_ch", {}).get(_CUR_CH[0], 0)
        t = (sc, 0, 0, sc, cx - sc * (sb[0] + sb[2]) / 2, mb[3] + GAP_STACK - sc * sb[1])
        cs = tf(src, t)
        while mindist(cs, base_mark) < GAP_STACK: t = t[:5] + (t[5] + 4,); cs = tf(src, t)
        return cs, (key, t)
    # bên phải dấu mũ: đáy dấu thanh ngang nửa dấu mũ, nhích tới khi đủ khe
    t = [sc, 0, 0, sc, mb[2] - sc * sb[0] - 0.15 * sc * (sb[2] - sb[0]), mb[1] + 0.45 * (mb[3] - mb[1]) - sc * sb[1]]
    cs = tf(src, t)
    while mindist(cs, base_mark) < GAP_STACK: t[4] += 3; t[5] += 2; cs = tf(src, t)
    return cs, (key, tuple(t))
for ch in VN:
    if ord(ch) in cm: continue
    d = unicodedata.normalize("NFD", ch); L = d[0]; ms = d[1:]
    name = "uni%04X" % ord(ch)
    if ch in "đĐ":
        if ch == "Đ" and gname("Ð"):
            new[name] = (contours(gname("Ð")), gs[gname("Ð")].width, [])
            recipes[name] = dict(u=ord(ch), ch=ch, w=gs[gname("Ð")].width, base="Eth", sax=[0, 0], static=contours(gname("Ð")), marks=[])
            continue
        DB = "d" if ch == "đ" else "D"; body = contours(gname(DB))
        hy = contours(gname("-")); hb = bb(hy); b = bb(body)
        yb = b[3] * CFG.get("dbar_y", 0.74) if ch == "đ" else b[3] * 0.48
        xs = sorted(xs_at(body, yb)); stem = (xs[-2] + xs[-1]) / 2 if ch == "đ" and len(xs) >= 2 else (b[0] + 40)
        bw = CFG.get("dbar_w", (b[2] - b[0]) * 0.62); sx = bw / (hb[2] - hb[0]); sy = CFG.get("dbar_sy", 0.9)
        cx = stem + (0 if ch == "đ" else bw * 0.25)
        t = (sx, 0, 0, sy, cx - sx * (hb[0] + hb[2]) / 2, yb - sy * (hb[1] + hb[3]) / 2)
        cv = Canvas((min(b[0], cx - bw), b[1], max(b[2], cx + bw), b[3]), 6); cv.glyph(body); cv.glyph(tf(hy, t))
        cs = cv.contours(); w = max(gs[gname(DB)].width, int(bb(cs)[2] + 10))
        new[name] = (cs, w, []); recipes[name] = dict(u=ord(ch), ch=ch, w=w, base=gname("d"), sax=[0, 0], static=body, marks=[], _bar=(hy, t))
        continue
    horn_ = "̛" in ms; dot = "̣" in ms
    basech = "ı" if L == "i" and not dot else L
    bodyL = L
    if dot and L == "i": basech = "i"
    body = contours(gname(basech)); w = gs[gname(basech)].width; parts, recipe_m = [], []
    above = None; bk = None
    if "̂" in ms or "̆" in ms:
        bk = "circ" if "̂" in ms else "breve"
        above, r = mark_cs(bk, L); parts += above; recipe_m.append(r)
    tone = next((TONE[m] for m in ms if m in TONE), None)
    if tone:
        if above is not None:
            _CUR_CH[0] = ch; cs, r = stack(above, bk, tone, L)
            if bk == "circ" and tone in CFG.get("stack_rel", {}):
                # chữ hẹp (o, ô): cụm dấu mũ + dấu thanh bên phải chìa quá xa khỏi độ rộng chữ → dời cả cụm sang trái
                # (căn khác nhau theo chữ — người dùng 27/10), tối đa stack_shift_max × bề ngang dấu mũ
                lim = CFG.get("stack_overhang", 40); ov = bb(cs)[2] - w
                if ov > lim:
                    mbw = bb(above)[2] - bb(above)[0]; sh = min(ov - lim, CFG.get("stack_shift_max", 0.15) * mbw)
                    parts = mv(parts, -sh, 0); cs = mv(cs, -sh, 0)
                    k0, t0 = recipe_m[-1]; recipe_m[-1] = (k0, tuple(t0[:4]) + (t0[4] - sh, t0[5]))
                    r = (r[0], tuple(r[1][:4]) + (r[1][4] - sh, r[1][5]))
                    SHIFTED.append("%s −%d" % (ch, sh))
        elif L == "i" and gname("í"):
            # chữ i: đáy dấu = đáy dấu sắc trên í (font vẽ sẵn), tâm theo thân ı
            ib = bb(contours(gname("ı"))); ia = [c for c in contours(gname("í")) if bb([c])[1] > ib[3] - 10]
            yb_ = bb(ia)[1] if ia else ACB_LC + 100; cx = (ib[0] + ib[2]) / 2
            if tone == "hook": t = (1, 0, 0, 1, cx + 6, yb_); cs = tf(HOOK, t); r = ("hook", t)
            else: t = (1, 0, 0, 1, cx - mcx(tone), yb_ - MBB[tone][1]); cs = tf(MK[tone], t); r = (tone, t)
        else: cs, r = mark_cs(tone, L)
        parts += cs; recipe_m.append(r)
    hcs = []
    if horn_:
        hcs, _ = horn(L, body)
        if parts:   # dấu thanh né râu: dời trái ≤ 40 rồi mới nâng, khe ≥ 28
            need = CFG.get("tone_gap", 28); sh = up_ = 0
            while mindist(mv(parts, -sh, 0), hcs) < need and sh < 40: sh += 4
            while mindist(mv(parts, -sh, up_), hcs) < need and up_ < 200: up_ += 4
            parts = mv(parts, -sh, up_); recipe_m = [(k, (t[0], t[1], t[2], t[3], t[4] - sh, t[5] + up_)) for k, t in recipe_m]
        w = int(max(w, bb(hcs)[2] + CFG.get("clear", 10)))
    if dot:
        bL = bb(contours(gname("ı" if L == "i" else L)))
        cx = (bL[0] + bL[2]) / 2
        if L in "yY":   # ỵ: dời phải tránh đuôi
            cx = bL[2] - (db[2] - db[0]) / 2 - CFG.get("ydot_inset", 30)
        if L == "i": ib = bb(contours(gname("ı"))); cx = (ib[0] + ib[2]) / 2
        bot = min(0, bb(contours(gname("ı" if L == "i" else L)))[1]) if L not in "yY" else 0
        t = (1, 0, 0, 1, cx, bot - DOT_GAP - DOT_H / 2); parts += tf(DOT, t); recipe_m.append(("dot", t))
    static = body + hcs
    allc = static + parts
    new[name] = (allc, w, [])
    recipes[name] = dict(u=ord(ch), ch=ch, w=w, base=gname(basech), sax=[0, 0], static=static, marks=[{"m": k, "t": [round(v, 4) for v in t]} for k, t in recipe_m])

from fontTools.pens.transformPen import TransformPen as _TP
for _k, _t in MLEN.items():
    if _k in MSHAPE: continue   # đã đổi dáng → ghi thẳng nét mới bên dưới
    gn = gname(MARKG[_k]); pen = TTGlyphPen(gs); gs[gn].draw(_TP(pen, _t)); glyf[gn] = pen.glyph(); glyf[gn].recalcBounds(glyf)
    hmtx[gn] = (hmtx[gn][0], glyf[gn].xMin)
for _k in MSHAPE:   # dáng nét dấu mới → ghi vào glyph dấu của font (á é ó… ghép sẵn đổi theo)
    gn = gname(MARKG[_k]); pen = TTGlyphPen(None); draw(MK[_k], Cu2QuPen(pen, 1.0, reverse_direction=False)); glyf[gn] = pen.glyph(); glyf[gn].recalcBounds(glyf)
    hmtx[gn] = (hmtx[gn][0], glyf[gn].xMin)
if MSHAPE: print("đổi dáng nét dấu:", ", ".join("%s đầu %s%% / đuôi %s%%" % (k, CFG["mark_shape"][k].get("h", 100), CFG["mark_shape"][k].get("t", 100)) for k in sorted(MSHAPE)))
if SHIFTED: print("dấu chồng bên phải — chữ hẹp dời cụm sang trái:", " · ".join(SHIFTED))
if MLEN: print("kéo dài dấu:", ", ".join("%s ×%.2f" % (k, CFG[k + "_len"]) for k in MLEN))
# ---------------- đồng bộ chữ hoa ghép sẵn (À Á Ú Ô…): cùng khe, cùng trục với chữ mới ----------------
resync = []
if UC_SYNC:
    for n in f.getGlyphOrder():
        g = glyf[n]
        if not (g.isComposite() and len(g.components) == 2 and g.components[1].glyphName in G2K): continue
        bn = g.components[0].glyphName
        if not (len(bn) == 1 and bn in "AEIOUY"): continue
        k = G2K[g.components[1].glyphName]; dx, dy = place(bn, k)
        c = g.components[1]; nx, ny = int(round(dx)), int(round(dy))
        if (c.x, c.y) != (nx, ny): resync.append("%s %+d/%+d" % (n, nx - c.x, ny - c.y)); c.x, c.y = nx, ny
        g.recalcBounds(glyf); hmtx[n] = (hmtx[n][0], g.xMin)
# ---------------- ghi font ----------------
order = f.getGlyphOrder()
for name, (cs, w, _) in new.items():
    pen = TTGlyphPen(None); draw(cs, Cu2QuPen(pen, 1.0, reverse_direction=False))
    g = pen.glyph(); glyf[name] = g
    if name not in order: order.append(name)
    b = bb(cs); hmtx[name] = (int(round(w)), int(math.floor(b[0])) if b else 0)
f.setGlyphOrder(order)
for t in f["cmap"].tables:
    if t.isUnicode():
        for name, (cs, w, _) in new.items():
            u = int(name[3:], 16)
            if t.format == 4 and u > 0xFFFF: continue
            t.cmap[u] = name
if "post" in f and f["post"].formatType == 2:
    f["post"].extraNames = []; f["post"].mapping = {}
# thông số dọc: dấu chồng chữ hoa không ló khỏi dòng (vmetrics fit)
ymax = max(bb(cs)[3] for cs, w, _ in new.values()); ymin = min(bb(cs)[1] for cs, w, _ in new.values())
o2, hh = f["OS/2"], f["hhea"]; grow = ""
if ymax > hh.ascent:
    old = hh.ascent; hh.ascent = o2.usWinAscent = int(math.ceil(ymax + 10)); o2.sTypoAscender = max(o2.sTypoAscender, hh.ascent)
    grow = "dòng trên +%d (%d → %d)" % (hh.ascent - old, old, hh.ascent)
if -ymin > o2.usWinDescent: o2.usWinDescent = int(math.ceil(-ymin + 10)); hh.descent = min(hh.descent, -o2.usWinDescent)
f.save(A.out)
print("quick_vn: thêm %d chữ · %s · dấu hỏi (%s, %s) cao %d dày %d→%d (dấu ngã %d) · râu thin %d head %d · khe dấu chữ hoa %d" % (len(new), grow or "không đổi thông số dọc", HOOK_SRC, HOOK_WEIGHT, HOOK_H, HOOK_W, HOOK_WT, TILDE_W, HK["thin"], HK["head"], UC_GAP))
if resync: print("đồng bộ chữ hoa ghép sẵn (dx/dy):", " · ".join(resync))
# ---- recipes cho bàn vẽ (export_editor.py) + horn5.json cho khung kéo ----
if A.recipes:
    def J(cs): return [[[op, [[round(x, 1), round(y, 1)] for x, y in pts]] for op, pts in c] for c in cs]
    oh, _ = horn("O", contours(gname("O")))
    ML = {"hook": HOOK, "hook_s": HOOK_S, "dot": DOT, "horn": oh}
    ML.update(MK)
    out = {}
    for n, r in recipes.items():
        st = r["static"]
        if "_bar" in r: st = new[n][0]            # đ: thanh đã hợp nét vào thân
        out[n] = dict(u=r["u"], ch=r["ch"], w=new[n][1], base=r["base"], sax=r["sax"], static=J(st), marks=r["marks"])
    json.dump({"upm": UPM, "tilde_w": round(thickness(MK["tilde"])), "axis": 0, "marks": {k: J(v) for k, v in ML.items()}, "glyphs": out}, open(A.recipes, "w"))
def _hook_params():
    """đường tâm dấu hỏi (đã co + giãn như dấu thật) → chuỗi Bézier bậc 3 (Catmull-Rom) cho slider_ui “taper”"""
    xs = [p[0] for p in SK]; ys = [p[1] for p in SK]; wm = (HOOK_W + HOOK_WT) / 2; s_ = (HOOK_H - wm) / (max(ys) - min(ys))
    xst = CFG.get("hook_xstretch", 1.2 if HOOK_SRC == "full" else 1.0)
    pts = [((x - min(xs)) * s_ * xst, (y - min(ys)) * s_) for x, y in SK]
    K = [pts[int(round(i * (len(pts) - 1) / 9))] for i in range(10)]; path = [list(map(lambda v: round(v, 1), K[0]))]
    for i in range(len(K) - 1):
        a, b_, c, d = K[max(0, i - 1)], K[i], K[i + 1], K[min(len(K) - 1, i + 2)]
        path += [[round(b_[0] + (c[0] - a[0]) / 6, 1), round(b_[1] + (c[1] - a[1]) / 6, 1)], [round(c[0] - (d[0] - b_[0]) / 6, 1), round(c[1] - (d[1] - b_[1]) / 6, 1)], [round(c[0], 1), round(c[1], 1)]]
    return {"mode": "taper", "path": path, "h": round(HOOK_H), "ball": round(HOOK_W), "foot": round(HOOK_WT), "taper_p": 1.2, "stress_mix": 0, "cut": 0.1, "wcomp": True,
            "src": HOOK_SRC, "weight": HOOK_WEIGHT}
if A.horn:
    hp_ = os.path.join(os.path.dirname(os.path.abspath(A.out)), "hook.params.json"); json.dump(_hook_params(), open(hp_, "w"))
    if os.path.exists(A.horn):
        _h5 = json.load(open(A.horn)); _h5["hook_params"] = hp_; json.dump(_h5, open(A.horn, "w"), indent=1, ensure_ascii=False)
if A.horn and not os.path.exists(A.horn):
    json.dump({"src": A.src, "all": {k: HK[k] for k in ("reach", "rise", "thin", "head", "p", "t0", "dyO", "dyU")}, "lc_ratio": LCR, "lc_wratio": LCW, "hook_params": hp_,
               "_ghi_chu": "quick_vn.py: thông số râu đo theo nét thân font (thin = 0,75 × thân, head = 1,35 × thân)."}, open(A.horn, "w"), indent=1, ensure_ascii=False)
