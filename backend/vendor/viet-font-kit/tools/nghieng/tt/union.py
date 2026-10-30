"""Boolean union of two closed contours made of line / quadratic segments (no pathops needed).
Segments: ((x,y),(x,y)) line or ((x,y),(x,y),(x,y)) quad. Both contours must be simple and have the same orientation."""
import math
import numpy as np
from geom import seg_pt, seg_split
seg_split = seg_split

def sbb(s):
    xs = [p[0] for p in s]; ys = [p[1] for p in s]
    return min(xs), min(ys), max(xs), max(ys)

def sub(s, t0, t1):
    """sub-segment of s on [t0,t1]"""
    if t0 > 0:
        s = seg_split(s, t0)[1]; t1 = (t1 - t0) / (1 - t0)
    if t1 < 1: s = seg_split(s, t1)[0]
    return s

def _isect(sa, sb, a0, a1, b0, b1, out, depth=0):
    A = sub(sa, a0, a1); B = sub(sb, b0, b1)
    ba = sbb(A); bb = sbb(B)
    if ba[2] < bb[0] - 1e-6 or bb[2] < ba[0] - 1e-6 or ba[3] < bb[1] - 1e-6 or bb[3] < ba[1] - 1e-6: return
    sa_ = max(ba[2] - ba[0], ba[3] - ba[1]); sb_ = max(bb[2] - bb[0], bb[3] - bb[1])
    if (sa_ < 1e-3 and sb_ < 1e-3) or depth > 50:
        out.append(((a0 + a1) / 2, (b0 + b1) / 2)); return
    if sa_ >= sb_:
        m = (a0 + a1) / 2; _isect(sa, sb, a0, m, b0, b1, out, depth + 1); _isect(sa, sb, m, a1, b0, b1, out, depth + 1)
    else:
        m = (b0 + b1) / 2; _isect(sa, sb, a0, a1, b0, m, out, depth + 1); _isect(sa, sb, a0, a1, m, b1, out, depth + 1)

def isect(sa, sb):
    raw = []; _isect(sa, sb, 0, 1, 0, 1, raw)
    res = []
    for ta, tb in sorted(raw):
        p = seg_pt(sa, ta)
        if any(math.dist(p, seg_pt(sa, r[0])) < 0.05 for r in res): continue
        res.append((ta, tb))
    return res

def poly(segs, n=12):
    P = []
    for s in segs:
        k = 1 if len(s) == 2 else n
        for j in range(k): P.append(seg_pt(s, j / k))
    return np.array(P)

def winding(P, pt):
    x, y = pt; w = 0
    X0, Y0 = P[:, 0], P[:, 1]; X1, Y1 = np.roll(X0, -1), np.roll(Y0, -1)
    up = (Y0 <= y) & (Y1 > y); dn = (Y0 > y) & (Y1 <= y)
    cross = (X1 - X0) * (y - Y0) - (x - X0) * (Y1 - Y0)
    w += np.sum(up & (cross > 0)); w -= np.sum(dn & (cross < 0))
    return w

def inside(segs, pt): return winding(poly(segs, 24), pt) != 0

def signed_area(segs):
    P = poly(segs, 24); x, y = P[:, 0], P[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)

def reverse(segs):
    return [tuple(reversed(s)) for s in reversed(segs)]

def split_contour(segs, cuts):
    """cuts[i] = sorted list of (t, point). returns list of [piece, starts_at_node]"""
    n = len(segs); vnode = set()
    for i in range(n):
        for t, p in cuts.get(i, []):
            if t <= 1e-6: vnode.add(i)
            elif t >= 1 - 1e-6: vnode.add((i + 1) % n)
    out = []
    for i, s in enumerate(segs):
        inner = [(t, p) for t, p in cuts.get(i, []) if 1e-6 < t < 1 - 1e-6]
        prev, last, first = 0.0, None, True
        for t, p in inner:
            a = sub(s, prev, t); a = ((last if last else a[0]),) + tuple(a[1:-1]) + (p,)
            out.append([a, (i in vnode) if first else True]); first = False; last = p; prev = t
        a = sub(s, prev, 1.0)
        if last is not None: a = (last,) + tuple(a[1:])
        out.append([a, (i in vnode) if first else True])
    return out

def chains(pieces):
    n = len(pieces)
    k0 = next((i for i in range(n) if pieces[i][1]), None)
    if k0 is None: return [[p for p, _ in pieces]], False
    rot = pieces[k0:] + pieces[:k0]
    ch, cur = [], []
    for p, node in rot:
        if node and cur: ch.append(cur); cur = []
        cur.append(p)
    ch.append(cur)
    return ch, True

def union(A, B):
    """A, B: segment lists (closed). Returns list of contours (segment lists)."""
    if (signed_area(A) > 0) != (signed_area(B) > 0): B = reverse(B)
    ca, cb = {}, {}
    for i, sa in enumerate(A):
        ba = sbb(sa)
        for j, sb in enumerate(B):
            bb = sbb(sb)
            if ba[2] < bb[0] - 1 or bb[2] < ba[0] - 1 or ba[3] < bb[1] - 1 or bb[3] < ba[1] - 1: continue
            for ta, tb in isect(sa, sb):
                p = seg_pt(sa, ta); q = seg_pt(sb, tb); m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                ca.setdefault(i, []).append((ta, m)); cb.setdefault(j, []).append((tb, m))
    for d in (ca, cb):
        for k in d: d[k].sort()
    nI = sum(len(v) for v in ca.values())
    if nI == 0: return None
    PA, PB = poly(A, 24), poly(B, 24)
    chA, _ = chains(split_contour(A, ca)); chB, _ = chains(split_contour(B, cb))
    keep = []
    for ch, P in [(c, PB) for c in chA] + [(c, PA) for c in chB]:
        mid = ch[len(ch) // 2]; mp = seg_pt(mid, 0.5)
        if winding(P, mp) == 0: keep.append(ch)
    # link chains end -> start
    res = []
    used = [False] * len(keep)
    for i in range(len(keep)):
        if used[i]: continue
        cont = list(keep[i]); used[i] = True; start = cont[0][0]
        for _ in range(len(keep)):
            end = cont[-1][-1]
            if math.dist(end, start) < 0.5: break
            j = min((k for k in range(len(keep)) if not used[k]), key=lambda k: math.dist(keep[k][0][0], end), default=None)
            if j is None or math.dist(keep[j][0][0], end) > 1.0: break
            cont += keep[j]; used[j] = True
        res.append(cont)
    return res
