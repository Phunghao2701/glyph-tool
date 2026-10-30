"""Mark shapes for Vietnamizing a font. Outlines are lists of contours in RecordingPen form."""
import math
from shapely.geometry import Point, MultiPoint
from shapely.ops import unary_union


def bez(p0, p1, p2, p3, n=24):
    pts = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        pts.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return pts


def poly_to_contours(g, simplify=0.6, curves=True):
    """shapely geometry -> contours. With curves=True the polygon is refit as smooth cubic beziers."""
    from shapely.geometry.polygon import orient
    from fitcurve import ring_to_contour
    g = g.simplify(simplify)
    polys = [g] if g.geom_type == "Polygon" else list(g.geoms)
    cs = []
    for poly in polys:
        poly = orient(poly, sign=1.0)  # exterior CCW, holes CW (PostScript/CFF convention)
        for ring in [poly.exterior] + list(poly.interiors):
            pts = list(ring.coords)[:-1]
            if curves:
                cs.append(ring_to_contour(pts))
            else:
                cs.append([("moveTo", (pts[0],))] + [("lineTo", (p,)) for p in pts[1:]] + [("closePath", ())])
    return cs


def vstroke(points, widths):
    """Variable-width round stroke: union of hulls of consecutive discs."""
    discs = [Point(p).buffer(w / 2, quad_segs=16) for p, w in zip(points, widths)]
    parts = [MultiPoint(list(a.exterior.coords) + list(b.exterior.coords)).convex_hull
             for a, b in zip(discs, discs[1:])]
    return unary_union(parts)


def lerp_widths(n, stops):
    """stops: list of (t, width) with t in 0..1"""
    out = []
    for i in range(n):
        t = i / (n - 1)
        for (t0, w0), (t1, w1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0 or 1)
                k = k * k * (3 - 2 * k)
                out.append(w0 + (w1 - w0) * k)
                break
    return out


# ---- dấu hỏi (hook above) ----
def hook_v2(w_head=90, w_tail=78):
    """Heavy question-mark hook. Stroke ~ tilde weight (≈90u). Origin irrelevant (placed later)."""
    a = bez((0, 118), (4, 182), (122, 196), (128, 128), 26)      # head arc, left -> right
    b = bez((128, 128), (132, 82), (70, 84), (66, 44), 18)[1:]   # back down to the centre
    c = [(66, 44 - 14 * i) for i in range(1, 3)]                  # short tail
    pts = a + b + c
    ws = lerp_widths(len(pts), [(0, w_head * 0.86), (0.35, w_head), (0.75, w_head * 0.94), (1, w_tail)])
    return poly_to_contours(vstroke(pts, ws))


# ---- móc ơ ư (horn) ----
def horn_stroke(xa, ya, s=1.0, w0=96, w1=84):
    """Thick curved horn: leaves the shoulder heading right, bends up into a round terminal."""
    pts = bez((xa - 50*s, ya - 30*s), (xa + 62*s, ya - 26*s), (xa + 112*s, ya + 30*s), (xa + 96*s, ya + 122*s), 30)
    ws = lerp_widths(len(pts), [(0, w0 * s), (0.55, w0 * s * 0.95), (1, w1 * s)])
    return vstroke(pts, ws)


def hook_v3(r=40, w=88, w_tail=78, a0=200, a1=-55, tail=40, lean=0):
    """Heavy hỏi: arc of radius r around (0,0) from angle a0 clockwise to a1, then a short tail
    dropping to below centre. w = stroke weight (match tilde ≈ 85–95)."""
    import math
    pts = []
    n = 34
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((r * math.cos(a), r * math.sin(a)))
    ex, ey = pts[-1]
    # curve from arc end back under the centre, then down
    pts += bez((ex, ey), (ex - 6, ey - 22), (lean + 4, ey - 18), (lean, ey - 38), 12)[1:]
    pts += [(lean, ey - 38 - tail * k / 3) for k in range(1, 4)]
    ws = lerp_widths(len(pts), [(0, w * 0.9), (0.4, w), (0.75, w * 0.95), (1, w_tail)])
    return poly_to_contours(vstroke(pts, ws))


def hook_v4(rx=60, ry=44, w=86, w_tail=80, a0=195, a1=-78, tail=24, n=40):
    """Hỏi with an open counter: elliptical head (rx, ry) + short straight tail under the centre."""
    import math
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((rx * math.cos(a), ry * math.sin(a)))
    ex, ey = pts[-1]
    pts += [(ex - ex * k / 4, ey - tail * k / 4) for k in range(1, 5)]
    ws = lerp_widths(len(pts), [(0, w * 0.88), (0.35, w), (0.8, w * 0.97), (1, w_tail)])
    return poly_to_contours(vstroke(pts, ws))


def hook_v5(s=1.0, w=98, w_start=64, w_tail=90, stem=26, lx=-56, ly=6, bx=62, top=104, neck=8, wbowl=0.97):
    """Hỏi drawn like a heavy '?': tapered left terminal, thick head, comes back to centre, short stem.
    Coordinates are pre-scale; s scales the skeleton (not the weight).
    Gentle-tweak knobs (defaults = v1.003): bx right edge of the bowl, top height of the arch,
    neck x where the return stroke meets the stem, wbowl weight factor in the bowl.
    Bigger bx/top + smaller wbowl open the inner counter without changing the character."""
    a = bez((lx, ly), (lx - 4, 92), (bx + 2, top), (bx, 24), 24)
    b = bez((bx, 24), (bx - 2, -18), (neck, -12), (6, -46), 14)[1:]
    c = [(6, -46 - stem * k / 3) for k in range(1, 4)]
    pts = [(x * s, y * s) for x, y in a + b + c]
    ws = lerp_widths(len(pts), [(0, w_start), (0.25, w), (0.7, w * wbowl), (1, w_tail)])
    return poly_to_contours(vstroke(pts, ws))


def horn_arc(xa, ya, s=1.0, r=80, w0=108, wm=94, w1=118, a_end=14, lead=20):
    """Horn as a thick quarter-curl (like the tail of a comma turned upward).
    (xa, ya) = point on the shoulder where the horn grows out."""
    import math
    cx, cy = xa + 14 * s, ya + r * s * 0.92
    pts = [(xa - lead * s, ya - 4 * s)]
    n = 30
    for i in range(n + 1):
        a = math.radians(-100 + (a_end + 100) * i / n)
        pts.append((cx + r * s * math.cos(a), cy + r * s * 0.92 * math.sin(a)))
    ws = lerp_widths(len(pts), [(0, w0 * s), (0.45, wm * s), (0.85, w1 * s), (1, w1 * s * 0.96)])
    return vstroke(pts, ws)


def horn_shelf(s=1.0, w0=100, wm=96, w1=124, reach=72, rise=60):
    """Horn after Ryan's round-1 drawing (Ư): a thick neck leaving the stem top flush with the
    letter's top line, running right, then rising into a round comma-like head.
    Origin (0,0) = top-right corner of the stem / shoulder where the horn grows out."""
    pts = bez((-70, -50), (6, -56), (reach + 2, -16), (reach, rise), 32)
    pts = [(x * s, y * s) for x, y in pts]
    ws = lerp_widths(len(pts), [(0, w0 * s), (0.45, wm * s), (0.82, w1 * s), (1, w1 * s * 0.97)])
    return vstroke(pts, ws)
