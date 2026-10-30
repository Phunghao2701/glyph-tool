"""TrueType contour helpers: contours as lists of (x,y,on)."""
import math
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.recordingPen import RecordingPointPen

def tt_contours(font, gname):
    """decomposed contours as list of [(x,y,on)] (TrueType quadratic points)."""
    gs = font.getGlyphSet(); glyf = font['glyf']
    out = []
    def walk(name, dx, dy, m):
        g = glyf[name]
        if g.isComposite():
            for c in g.components:
                t = c.transform if hasattr(c, 'transform') else [[1,0],[0,1]]
                walk(c.glyphName, dx + c.x, dy + c.y, m)
            return
        if g.numberOfContours <= 0: return
        coords, ends, flags = g.getCoordinates(glyf)
        s = 0
        for e in ends:
            out.append([(x + dx, y + dy, bool(flags[i] & 1)) for i, (x, y) in enumerate(coords[s:e+1], start=s)])
            s = e + 1
    walk(gname, 0, 0, None)
    return out

def bbox_pts(c):
    # on-curve + off-curve hull bbox approximation -> use flattened
    P = flatten(c, 8)
    xs = [p[0] for p in P]; ys = [p[1] for p in P]
    return (min(xs), min(ys), max(xs), max(ys))

def explicit(c):
    """insert implied on-curve points between consecutive off-curves; start at an on-curve point."""
    n = len(c); pts = []
    for i in range(n):
        p = c[i]; q = c[(i + 1) % n]
        pts.append(p)
        if not p[2] and not q[2]:
            pts.append(((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, True))
    if not any(p[2] for p in pts):
        pts.insert(0, ((pts[-1][0] + pts[0][0]) / 2, (pts[-1][1] + pts[0][1]) / 2, True))
    k = next(i for i, p in enumerate(pts) if p[2])
    return pts[k:] + pts[:k]

def segments(c):
    """explicit contour -> list of segments [(p0,p1) line] or [(p0,c,p1) quad]."""
    pts = explicit(c); n = len(pts); segs = []; i = 0
    while i < n:
        p0 = pts[i]; p1 = pts[(i + 1) % n]
        if p1[2]: segs.append(((p0[0], p0[1]), (p1[0], p1[1]))); i += 1
        else:
            p2 = pts[(i + 2) % n]; segs.append(((p0[0], p0[1]), (p1[0], p1[1]), (p2[0], p2[1]))); i += 2
    return segs

def seg_pt(s, t):
    if len(s) == 2: return (s[0][0] + (s[1][0] - s[0][0]) * t, s[0][1] + (s[1][1] - s[0][1]) * t)
    a, b, c = s; u = 1 - t
    return (u*u*a[0] + 2*u*t*b[0] + t*t*c[0], u*u*a[1] + 2*u*t*b[1] + t*t*c[1])

def seg_split(s, t):
    if len(s) == 2:
        m = seg_pt(s, t); return (s[0], m), (m, s[1])
    a, b, c = s
    ab = (a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t); bc = (b[0] + (c[0]-b[0])*t, b[1] + (c[1]-b[1])*t)
    m = (ab[0] + (bc[0]-ab[0])*t, ab[1] + (bc[1]-ab[1])*t)
    return (a, ab, m), (m, bc, c)

def segs_to_contour(segs):
    out = []
    for s in segs:
        if len(s) == 2: out.append((s[0][0], s[0][1], True))
        else: out += [(s[0][0], s[0][1], True), (s[1][0], s[1][1], False)]
    return out

def flatten(c, n=16):
    P = []
    for s in segments(c):
        k = 1 if len(s) == 2 else n
        for j in range(k): P.append(seg_pt(s, j / k))
    return P

def xf(c, fn):
    return [(*fn(x, y), on) for x, y, on in c]

def area(c):
    P = flatten(c); a = 0
    for i in range(len(P)):
        x0, y0 = P[i]; x1, y1 = P[(i+1) % len(P)]; a += x0*y1 - x1*y0
    return a / 2

def dense(c, step=2.0):
    """points along contour with spacing <= step (lines too)."""
    import numpy as np
    out = []
    for s in segments(c):
        P0 = seg_pt(s, 0); P1 = seg_pt(s, 1)
        L = math.dist(P0, P1) + (math.dist(P0, s[1]) + math.dist(s[1], P1) if len(s) == 3 else 0)
        k = max(1, int(L / step))
        for j in range(k): out.append(seg_pt(s, j / k))
    return out
