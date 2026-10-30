"""Dấu hỏi lấy từ dấu chấm hỏi của chính font (luật Ryan vòng 3).
hook_from_question(contours_of_question, target_h, weight, xstretch, upm) -> contours (local, bottom-centre at 0,0)
- bỏ phần chấm (contour thấp nhất), giữ thân "?"
- thu nhỏ đều về chiều cao target_h, rồi bù độ dày nét bằng buffer để đạt `weight`
- đo lòng (counter): đường kính vòng tròn lớn nhất lọt trong lòng dấu"""
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import scale, translate

def flat(c, n=10):
    pts, cur = [], None
    for op, a in c:
        if op in ("moveTo", "lineTo"): cur = a[0]; pts.append(cur)
        elif op == "curveTo":
            p0 = cur
            for i in range(1, n + 1):
                t = i / n; u = 1 - t
                pts.append((u**3*p0[0] + 3*u*u*t*a[0][0] + 3*u*t*t*a[1][0] + t**3*a[2][0], u**3*p0[1] + 3*u*u*t*a[0][1] + 3*u*t*t*a[1][1] + t**3*a[2][1]))
            cur = a[2]
    return pts

def to_poly(cs):
    polygons = []
    for contour in cs:
        pts = flat(contour)
        if len(pts) < 3:
            continue
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        if len(pts) < 4 or len(set(pts[:-1])) < 3:
            continue
        poly = Polygon(pts).buffer(0)
        if not poly.is_empty and poly.area > 0:
            polygons.append(poly)
    return unary_union(polygons) if polygons else Polygon()

def stroke_w(g):
    from scipy import ndimage
    from skimage.morphology import skeletonize
    from matplotlib.path import Path
    x0, y0, x1, y1 = g.bounds
    xs = np.arange(x0 - 3, x1 + 3, 1.0); ys = np.arange(y0 - 3, y1 + 3, 1.0)
    X, Y = np.meshgrid(xs, ys)
    import shapely
    m = shapely.contains_xy(g, X, Y)
    d = ndimage.distance_transform_edt(m)
    return float(np.median(d[skeletonize(m)] * 2))

def counter_d(g):
    """diameter of the largest circle that fits in the hook's counter (convex hull minus ink)"""
    from scipy import ndimage
    import shapely
    hole = g.convex_hull.difference(g)
    if hole.is_empty: return 0.0
    x0, y0, x1, y1 = hole.bounds
    xs = np.arange(x0 - 2, x1 + 2, 1.0); ys = np.arange(y0 - 2, y1 + 2, 1.0)
    X, Y = np.meshgrid(xs, ys)
    m = shapely.contains_xy(hole, X, Y)
    return float(ndimage.distance_transform_edt(m).max() * 2)

def hook_from_question(qcs, target_h=230, weight=88, xstretch=1.0):
    parts = sorted(qcs, key=lambda c: min(p[1] for p in flat(c)))
    body = to_poly(parts[1:]) if len(parts) > 1 else to_poly(parts)   # drop the dot (lowest contour)
    x0, y0, x1, y1 = body.bounds
    w0 = stroke_w(body)
    k = target_h / (y1 - y0)
    g = scale(body, xfact=k * xstretch, yfact=k, origin=(0, 0))
    # weight compensation: scaled stroke = w0*k -> grow/shrink each side
    g = g.buffer((weight - w0 * k) / 2, join_style="round", quad_segs=12)
    gx0, gy0, gx1, gy1 = g.bounds
    g = translate(g, -(gx0 + gx1) / 2, -gy0)
    return g


def skeleton_path(poly, res=1.0):
    """ordered centre-line of a stroke-like polygon (the '?' body): skeletonize, then walk from the
    end point with the highest-left position to the other end. Returns [(x,y)…] in font units."""
    import numpy as np, shapely
    from skimage.morphology import skeletonize
    x0, y0, x1, y1 = poly.bounds
    xs = np.arange(x0 - 2, x1 + 2, res); ys = np.arange(y0 - 2, y1 + 2, res)
    X, Y = np.meshgrid(xs, ys)
    m = shapely.contains_xy(poly, X, Y)
    sk = skeletonize(m)
    pts = set(zip(*np.nonzero(sk)))
    def nb(p):
        r, c = p
        return [(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr or dc) and (r + dr, c + dc) in pts]
    ends = [p for p in pts if len(nb(p)) == 1]
    # start: the end that is highest-left after the curl (the '?' terminal) -> smallest x among ends above mid
    ymid = (y0 + y1) / 2
    def fy(p): return ys[p[0]]
    def fx(p): return xs[p[1]]
    upper = [p for p in ends if fy(p) > ymid] or ends
    start = min(upper, key=fx)
    path, seen, cur = [start], {start}, start
    while True:
        nxt = [q for q in nb(cur) if q not in seen]
        if not nxt: break
        # prefer straight continuation
        cur = nxt[0] if len(nxt) == 1 else min(nxt, key=lambda q: abs(q[0] - path[-1][0]) + abs(q[1] - path[-1][1]))
        path.append(cur); seen.add(cur)
    return [(fx(p), fy(p)) for p in path]


def smooth_resample(pts, n=60, k=7):
    import numpy as np
    P = np.array(pts, float)
    if len(P) > k:
        ker = np.ones(k) / k
        P = np.c_[np.convolve(np.pad(P[:, 0], k // 2, mode='edge'), ker, 'valid'), np.convolve(np.pad(P[:, 1], k // 2, mode='edge'), ker, 'valid')]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    t = np.linspace(0, d[-1], n)
    return list(zip(np.interp(t, d, P[:, 0]), np.interp(t, d, P[:, 1])))


def hook_from_skeleton(qcs, target_h=220, weight=84, w_start=0.8, w_end=0.92, xstretch=1.0, trim_tail=0.0, flatten=1.0):
    """Dấu hỏi dạng NÉT MÓC (không phải '?' thu nhỏ): lấy khung xương của dấu '?' trong font, làm mượt,
    co về cỡ dấu rồi vẽ lại bằng nét đơn đầu tròn, độ dày theo font. Lòng móc tự mở vì nét mảnh hơn '?'
    thu nhỏ đều. flatten<1 làm dẹt (chữ hoa)."""
    import marks as MK
    parts = sorted(qcs, key=lambda c: min(p[1] for p in flat(c)))
    body = to_poly(parts[1:]) if len(parts) > 1 else to_poly(parts)
    sk = skeleton_path(body)
    if trim_tail: sk = sk[:int(len(sk) * (1 - trim_tail))]
    sk = smooth_resample(sk, 64, 9)
    xs = [p[0] for p in sk]; ys = [p[1] for p in sk]
    h = max(ys) - min(ys); s = (target_h - weight) / h
    pts = [((x - min(xs)) * s * xstretch, (y - min(ys)) * s * flatten) for x, y in sk]
    ws = MK.lerp_widths(len(pts), [(0, weight * w_start), (0.2, weight), (0.75, weight), (1, weight * w_end)])
    g = MK.vstroke(pts, ws)
    gx0, gy0, gx1, gy1 = g.bounds
    from shapely.affinity import translate
    return translate(g, -(gx0 + gx1) / 2, -gy0), (pts[-1][0] - (gx0 + gx1) / 2)   # shape, x of the tail (visual axis)
