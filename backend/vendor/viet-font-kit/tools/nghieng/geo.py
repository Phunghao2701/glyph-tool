# helpers: contours as list of (op, pts) ; fontTools only
import math
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
T = math.tan(math.radians(15))
from fontTools.pens.basePen import BasePen
class _Rec(BasePen):
    """ghi contour, tách chữ ghép (composite .ttf) và qCurveTo nhiều điểm / contour toàn điểm điều khiển (font TrueType)"""
    def __init__(s, gs): super().__init__(gs); s.out = []; s.cur = []
    def _moveTo(s, p): s.cur = [('moveTo', [p])]
    def _lineTo(s, p): s.cur.append(('lineTo', [p]))
    def _curveToOne(s, a, b, c): s.cur.append(('curveTo', [a, b, c]))
    def _qCurveToOne(s, a, b): s.cur.append(('qCurveTo', [a, b]))
    def _closePath(s): s.cur.append(('closePath', [])); s.out.append(s.cur); s.cur = []
    _endPath = _closePath
def contours(gs, name):
    rp = _Rec(gs); gs[name].draw(rp)
    if rp.cur: rp.out.append(rp.cur)
    return rp.out
def xform(cs, f):
    return [[(op, [f(*p) for p in pts]) for op, pts in c] for c in cs]
def unslant(cs, t=T): return xform(cs, lambda x, y: (x - y * t, y))
def slant(cs, t=T): return xform(cs, lambda x, y: (x + y * t, y))
def move(cs, dx, dy): return xform(cs, lambda x, y: (x + dx, y + dy))
def scale(cs, sx, sy, ox=0, oy=0): return xform(cs, lambda x, y: (ox + (x - ox) * sx, oy + (y - oy) * sy))
def draw(cs, pen):
    for c in cs:
        for op, pts in c:
            getattr(pen, op)(*pts)
def bounds(cs):
    bp = BoundsPen(None); draw(cs, bp); return bp.bounds
def area(c):
    # signed area via flattened polygon
    P = flat(c)
    return 0.5 * sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))
def flat(c, n=12):
    P = []; last = None
    for op, pts in c:
        if op == 'moveTo': last = pts[0]; P.append(last)
        elif op == 'lineTo': last = pts[0]; P.append(last)
        elif op == 'curveTo':
            p0 = last; p1, p2, p3 = pts
            for i in range(1, n + 1):
                t = i / n; mt = 1 - t
                P.append((mt**3*p0[0]+3*mt*mt*t*p1[0]+3*mt*t*t*p2[0]+t**3*p3[0], mt**3*p0[1]+3*mt*mt*t*p1[1]+3*mt*t*t*p2[1]+t**3*p3[1]))
            last = p3
        elif op == 'qCurveTo':
            # treat as polyline of points (approx)
            for p in pts: P.append(p)
            last = pts[-1]
    return P
def cb(c): return bounds([c])
def same(c1, c2, tol=2.5):
    b1, b2 = cb(c1), cb(c2)
    return all(abs(a - b) <= tol for a, b in zip(b1, b2))
def diff_contours(full, base, tol=2.5):
    """contours of full not matching any contour of base (by bbox)"""
    rest = list(base); out = []
    for c in full:
        m = next((i for i, b in enumerate(rest) if same(c, b, tol)), None)
        if m is None: out.append(c)
        else: rest.pop(m)
    return out, rest
def xs_at(cs, y):
    """x crossings of outline at height y"""
    X = []
    for c in cs:
        P = flat(c, 24)
        for i in range(len(P)):
            (x0, y0), (x1, y1) = P[i], P[(i + 1) % len(P)]
            if (y0 <= y < y1) or (y1 <= y < y0):
                X.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return sorted(X)
import numpy as _np
from matplotlib.path import Path as _MP
def _pts(cs, n=16):
    return [_np.array(flat(c, n)) for c in cs]
def mindist(A, B):
    """khoảng cách nhỏ nhất giữa 2 nhóm contour (0 nếu chạm / chồng)"""
    PA, PB = _pts(A), _pts(B)
    a = _np.vstack(PA); b = _np.vstack(PB)
    for poly in PB:
        if _MP(poly).contains_points(a).any(): return 0.0
    for poly in PA:
        if _MP(poly).contains_points(b).any(): return 0.0
    d = _np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1))
    return float(d.min())
