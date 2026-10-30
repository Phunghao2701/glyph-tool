"""Học DÁNG dấu hỏi từ font mẫu (đường tâm + phân bố thanh–đậm), dựng lại theo ĐỘ ĐẬM của font đang làm.
Không chép nét: lấy khung xương dấu hỏi font mẫu → đường tâm (khớp lại bằng bezier) + bề dày dọc nét (tỉ lệ),
rồi nhân bề dày theo tỉ lệ thân chữ (thân font mới / thân font mẫu) và đặt chiều cao theo tỉ lệ x-height.
usage: hook_from_ref.py REF.otf|ttf SRC.otf|ttf OUT_cfg.json [CHAR=ả] [--h-ratio auto|0.35] [--w-ratio auto]
  → cfg cho hook_stroke.py: "path" (đường tâm), "profile" ([t, bề dày] theo chiều dài nét), "h", "cut" …
build by @nhatmotion"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, shapely
from shapely.geometry import box
from scipy import ndimage
from skimage.morphology import skeletonize
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
import qhook, fitcurve

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = {sys.argv[i]: sys.argv[i + 1] for i in range(1, len(sys.argv) - 1) if sys.argv[i].startswith("--")}
REF, SRC, OUT = args[:3]; CH = args[3] if len(args) > 3 else "ả"

def cubic_cs(f, ch):
    gs = f.getGlyphSet(); g = f.getBestCmap()[ord(ch)]
    class Cub(BasePen):
        def __init__(s): super().__init__(gs); s.v = []
        def _moveTo(s, p): s.v.append(("moveTo", (p,)))
        def _lineTo(s, p): s.v.append(("lineTo", (p,)))
        def _curveToOne(s, a, b, c): s.v.append(("curveTo", (a, b, c)))
        def _closePath(s): s.v.append(("closePath", ()))
        def _endPath(s): s.v.append(("closePath", ()))
    p = Cub(); gs[g].draw(p); cs, cur = [], []
    for o, a in p.v:
        cur.append((o, a))
        if o == "closePath": cs.append(cur); cur = []
    return cs
def metrics(f):
    xh = qhook.to_poly(cubic_cs(f, "x")).bounds[3]
    st = qhook.to_poly(cubic_cs(f, "l")); b = st.bounds; m = (b[1] + b[3]) / 2
    s = st.intersection(box(-9999, m - .5, 9999, m + .5)).bounds
    return xh, s[2] - s[0]

rf, sf = TTFont(REF), TTFont(SRC)
rxh, rstem = metrics(rf); sxh, sstem = metrics(sf)
P = qhook.to_poly(cubic_cs(rf, CH)); hk = P.intersection(box(-9999, rxh + 20, 9999, 9999))
if hk.geom_type != "Polygon": hk = max(hk.geoms, key=lambda g: g.area)
x0, y0, x1, y1 = hk.bounds
xs = np.arange(x0 - 2, x1 + 2, 1.0); ys = np.arange(y0 - 2, y1 + 2, 1.0); X, Y = np.meshgrid(xs, ys)
m = shapely.contains_xy(hk, X, Y); d = ndimage.distance_transform_edt(m); sk = skeletonize(m)
pts = {(r, c) for r, c in zip(*np.nonzero(sk))}
def nb(p): return [(p[0] + a, p[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1) if (a or b) and (p[0] + a, p[1] + b) in pts]
ends = [p for p in pts if len(nb(p)) == 1]
def bfs(s):
    prev = {s: None}; q = [s]
    for p in q:
        for n in nb(p):
            if n not in prev: prev[n] = p; q.append(n)
    return prev, q[-1]
_, a = bfs(next(iter(ends)) if ends else next(iter(pts)))
prev, b = bfs(a)                                   # đường dài nhất trong khung xương
path = [b]
while prev[path[-1]] is not None: path.append(prev[path[-1]])
P2 = np.array([[xs[c], ys[r]] for r, c in path]); W = np.array([2 * d[r, c] for r, c in path])
# đầu = đầu giọt: đầu nào có bề dày lớn hơn ở 15 % đầu nét
k = max(3, len(P2) // 7)
if W[:k].max() < W[-k:].max(): P2, W = P2[::-1], W[::-1]
# làm mượt + lấy mẫu đều theo chiều dài
def smooth(a, n=7):
    ker = np.ones(n) / n; pad = np.pad(a, ((n // 2, n // 2),) + ((0, 0),) * (a.ndim - 1), mode="edge")
    return np.stack([np.convolve(pad[:, i], ker, "valid") for i in range(a.shape[1])], 1) if a.ndim > 1 else np.convolve(pad, ker, "valid")
# đầu giọt: khung xương chạy lố vào mép bầu (bề dày tụt về 0) → bắt đầu từ TÂM bầu (bề dày lớn nhất ở 25 % đầu nét)
i0 = int(np.argmax(W[:max(4, len(W) // 4)])); P2, W = P2[i0:], W[i0:]
# bầu giọt thật = vòng tròn nội tiếp lớn nhất ở nửa trái dấu (khung xương hay đi lệch tâm bầu) → nối tâm bầu vào đầu nét
dl = d.copy(); dl[:, xs > (x0 + x1) / 2] = 0
br, bc = np.unravel_index(dl.argmax(), dl.shape); B = np.array([xs[bc], ys[br]]); DB = 2 * dl.max()
jn = int(np.argmin(np.linalg.norm(P2[:len(P2) // 3] - B, axis=1)))
lead = np.linspace(B, P2[jn], max(2, int(np.linalg.norm(P2[jn] - B)) + 1))[:-1]
P2 = np.vstack([lead, P2[jn:]]); W = np.r_[np.linspace(DB, W[jn], len(lead) + 1)[:-1], W[jn:]]
# chân: khung xương chạm mép cắt → bề dày tụt; giữ bề dày ở 88 % cho đoạn cuối (chân cụt)
j = int(len(W) * 0.88); W[j:] = np.maximum(W[j:], W[j])
P2 = smooth(P2, 9); W = smooth(W, 9)
seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P2, axis=0), axis=1))]; T = seg / seg[-1]
# chuẩn hoá về toạ độ dấu: chân-giữa = (0,0)
hb = hk.bounds; cx = (hb[0] + hb[2]) / 2
hr = float(opt.get("--h-ratio", "auto")) if opt.get("--h-ratio", "auto") != "auto" else (hb[3] - hb[1]) / rxh
H = hr * sxh                                       # chiều cao dấu theo tỉ lệ x-height
g = H / (hb[3] - hb[1])                            # tỉ lệ hình
wk = sstem / rstem                                 # tỉ lệ độ đậm (thân chữ)
C = (P2 - [cx, hb[1]]) * g
beziers = fitcurve.fit(C, 1.2)
path_cfg = [list(map(lambda v: round(float(v), 1), beziers[0][0]))]
for bz in beziers: path_cfg += [list(map(lambda v: round(float(v), 1), q)) for q in bz[1:]]
prof = [[round(float(t), 3), round(float(w * wk), 1)] for t, w in zip(T[::max(1, len(T) // 40)], W[::max(1, len(W) // 40)])]
if prof[-1][0] < 1: prof.append([1.0, round(float(W[-1] * wk), 1)])
cfg = {"h": round(H), "cut": 4, "path": path_cfg, "profile": prof, "_ref": os.path.basename(REF), "_ref_char": CH,
       "_ghi_chu": "Dáng + phân bố thanh–đậm học từ dấu hỏi font mẫu; bề dày × %.3f (thân %d / %d), cao %.3f x-height." % (wk, sstem, rstem, hr)}
json.dump(cfg, open(OUT, "w"), ensure_ascii=False)
print("hook_from_ref: %s %s → cao %d (%.3f x-height) · rộng / cao %.2f · đậm × %.3f · giọt %.0f · đậm nhất %.0f · mảnh nhất %.0f · %d đoạn cong" % (
    os.path.basename(REF), CH, H, hr, (hb[2] - hb[0]) / (hb[3] - hb[1]), wk, W[:k].max() * wk, W.max() * wk, W[k:-k].min() * wk, len(beziers)))
