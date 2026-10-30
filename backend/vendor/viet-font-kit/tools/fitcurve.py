"""Philip Schneider's bezier curve fitting (Graphics Gems 1990), for turning polygon outlines into cubic contours."""
import numpy as np

def _q(c, t):
    return ((1-t)**3)[:, None]*c[0] + (3*(1-t)**2*t)[:, None]*c[1] + (3*(1-t)*t**2)[:, None]*c[2] + (t**3)[:, None]*c[3]
def _qp(c, t):
    return (3*(1-t)**2)[:, None]*(c[1]-c[0]) + (6*(1-t)*t)[:, None]*(c[2]-c[1]) + (3*t**2)[:, None]*(c[3]-c[2])
def _qpp(c, t):
    return (6*(1-t))[:, None]*(c[2]-2*c[1]+c[0]) + (6*t)[:, None]*(c[3]-2*c[2]+c[1])

def _chord(p):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    return d / d[-1] if d[-1] else d

def _gen(p, u, t1, t2):
    A = np.stack([t1[None, :] * (3*(1-u)**2*u)[:, None], t2[None, :] * (3*(1-u)*u**2)[:, None]], 1)
    C = np.zeros((2, 2)); X = np.zeros(2)
    for i in range(len(p)):
        C[0, 0] += A[i, 0] @ A[i, 0]; C[0, 1] += A[i, 0] @ A[i, 1]; C[1, 1] += A[i, 1] @ A[i, 1]
        tmp = p[i] - _q(np.array([p[0], p[0], p[-1], p[-1]]), np.array([u[i]]))[0]
        X[0] += A[i, 0] @ tmp; X[1] += A[i, 1] @ tmp
    C[1, 0] = C[0, 1]
    det = C[0, 0]*C[1, 1] - C[0, 1]*C[1, 0]
    a1 = (X[0]*C[1, 1] - X[1]*C[0, 1]) / det if abs(det) > 1e-12 else 0
    a2 = (C[0, 0]*X[1] - C[1, 0]*X[0]) / det if abs(det) > 1e-12 else 0
    seg = np.linalg.norm(p[-1] - p[0]); eps = 1e-6 * seg
    if a1 < eps or a2 < eps:
        a1 = a2 = seg / 3
    return np.array([p[0], p[0] + t1*a1, p[-1] + t2*a2, p[-1]])

def _reparam(c, p, u):
    q, qp, qpp = _q(c, u), _qp(c, u), _qpp(c, u)
    num = ((q - p) * qp).sum(1); den = (qp*qp).sum(1) + ((q - p)*qpp).sum(1)
    out = u - np.where(np.abs(den) > 1e-12, num / np.where(den == 0, 1, den), 0)
    return np.clip(out, 0, 1)

def _maxerr(c, p, u):
    d = ((_q(c, u) - p)**2).sum(1)
    i = int(np.argmax(d)); return d[i], i

def _unit(v):
    n = np.linalg.norm(v); return v / n if n else v

def fit(p, err, t1=None, t2=None):
    p = np.asarray(p, float)
    if t1 is None: t1 = _unit(p[1] - p[0])
    if t2 is None: t2 = _unit(p[-2] - p[-1])
    if len(p) == 2:
        d = np.linalg.norm(p[1]-p[0]) / 3
        return [np.array([p[0], p[0]+t1*d, p[1]+t2*d, p[1]])]
    u = _chord(p); c = _gen(p, u, t1, t2); e, s = _maxerr(c, p, u)
    if e < err*err: return [c]
    if e < 4*err*err:
        for _ in range(20):
            u = _reparam(c, p, u); c = _gen(p, u, t1, t2); e, s = _maxerr(c, p, u)
            if e < err*err: return [c]
    s = min(max(s, 1), len(p) - 2)
    tc = _unit(p[s-1] - p[s+1])
    return fit(p[:s+1], err, t1, tc) + fit(p[s:], err, -tc, t2)

def ring_to_contour(pts, err=1.2, corner_deg=50):
    """Closed polygon ring -> RecordingPen contour of cubic curves, keeping sharp corners."""
    p = np.asarray(pts, float)
    n = len(p)
    if n < 4:
        return [("moveTo", (tuple(p[0]),))] + [("lineTo", (tuple(q),)) for q in p[1:]] + [("closePath", ())]
    # split points: sharp corners, else axis extrema
    ang = []
    for i in range(n):
        a = _unit(p[i] - p[i-1]); b = _unit(p[(i+1) % n] - p[i])
        ang.append(np.degrees(np.arccos(np.clip(a @ b, -1, 1))))
    splits = [i for i in range(n) if ang[i] > corner_deg]
    if len(splits) < 2:
        ext = {int(np.argmin(p[:, 0])), int(np.argmax(p[:, 0])), int(np.argmin(p[:, 1])), int(np.argmax(p[:, 1]))}
        splits = sorted(set(splits) | ext)
    splits = sorted(set(splits))
    out = []
    for k, s0 in enumerate(splits):
        s1 = splits[(k+1) % len(splits)]
        idx = list(range(s0, s1+1)) if s1 > s0 else list(range(s0, n)) + list(range(0, s1+1))
        seg = p[idx]
        corner0, corner1 = ang[s0] > corner_deg, ang[s1] > corner_deg
        t1 = None if corner0 else _unit(p[(s0+1) % n] - p[s0-1])
        t2 = None if corner1 else _unit(p[s1-1] - p[(s1+1) % n])
        out += fit(seg, err, t1, t2)
    ops = [("moveTo", (tuple(np.round(out[0][0], 1)),))]
    for c in out:
        ops.append(("curveTo", tuple(tuple(np.round(q, 1)) for q in c[1:])))
    ops.append(("closePath", ()))
    return ops
