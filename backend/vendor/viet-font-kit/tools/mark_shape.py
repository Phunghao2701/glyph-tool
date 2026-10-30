"""Dáng nét dấu (tab Chỉnh dấu · Chi tiết, người dùng 27/10) — CÙNG công thức với trang (slider_ui.html):
- taper(P, head, tail, horiz): dấu sắc / huyền (trục dọc, đầu = đầu trên) · dấu ngã (horiz: đầu = trái, đuôi = phải).
  Trục chính (PCA) của mọi điểm viền; mỗi điểm: t ∈ [0,1] dọc trục (0 = đuôi, 1 = đầu), khoảng cách tới đường tâm (giữa mép trên / dưới
  của từng khúc, 20 khúc) nhân k = (đuôi + (đầu − đuôi)·t) / 100 → nét dày / mảnh ở đầu, ở đuôi mà đường tâm (dáng cong) giữ nguyên.
- round_(P, r): dấu nặng — mỗi điểm viền kéo về đường tròn bán kính trung bình quanh tâm khung bao, r % (0 = giữ, 100 = tròn hẳn).
P = list các vòng điểm [(x, y)…]. build by @nhatmotion"""
import math

def _pca(pts):
    n = len(pts); cx = sum(p[0] for p in pts) / n; cy = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - cx) ** 2 for p in pts) / n; syy = sum((p[1] - cy) ** 2 for p in pts) / n; sxy = sum((p[0] - cx) * (p[1] - cy) for p in pts) / n
    a = 0.5 * math.atan2(2 * sxy, sxx - syy)
    return (cx, cy), (math.cos(a), math.sin(a))

def taper(rings, head=100, tail=100, horiz=False, bins=20):
    pts = [p for R in rings for p in R]
    if len(pts) < 3 or (head == 100 and tail == 100): return rings
    (cx, cy), (ax, ay) = _pca(pts)
    if (horiz and ax < 0) or (not horiz and ay < 0): ax, ay = -ax, -ay
    bx, by = -ay, ax
    S = [((x - cx) * ax + (y - cy) * ay, (x - cx) * bx + (y - cy) * by) for x, y in pts]
    s0 = min(s for s, _ in S); s1 = max(s for s, _ in S); L = (s1 - s0) or 1
    lo = [None] * bins; hi = [None] * bins
    for s, n in S:
        i = min(bins - 1, int((s - s0) / L * bins)); lo[i] = n if lo[i] is None else min(lo[i], n); hi[i] = n if hi[i] is None else max(hi[i], n)
    nc = [None if lo[i] is None else (lo[i] + hi[i]) / 2 for i in range(bins)]
    known = [i for i in range(bins) if nc[i] is not None]
    for i in range(bins):
        if nc[i] is None:
            j = min(known, key=lambda k: abs(k - i)); nc[i] = nc[j]
    def ncat(t):
        u = t * bins - 0.5; i = max(0, min(bins - 1, int(math.floor(u)))); j = min(bins - 1, i + 1); f = min(1, max(0, u - i)); return nc[i] + (nc[j] - nc[i]) * f
    out = []
    for R in rings:
        Q = []
        for x, y in R:
            s = (x - cx) * ax + (y - cy) * ay; n = (x - cx) * bx + (y - cy) * by; t = (s - s0) / L
            c = ncat(t); k = (tail + (head - tail) * t) / 100.0; n2 = c + (n - c) * k
            Q.append((cx + ax * s + bx * n2, cy + ay * s + by * n2))
        out.append(Q)
    return out

def round_(rings, r=0):
    pts = [p for R in rings for p in R]
    if not pts or not r: return rings
    x0 = min(p[0] for p in pts); x1 = max(p[0] for p in pts); y0 = min(p[1] for p in pts); y1 = max(p[1] for p in pts)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    R0 = sum(math.hypot(x - cx, y - cy) for x, y in pts) / len(pts); f = r / 100.0
    return [[(cx + (x - cx) * (1 + f * (R0 / (math.hypot(x - cx, y - cy) or 1) - 1)), cy + (y - cy) * (1 + f * (R0 / (math.hypot(x - cx, y - cy) or 1) - 1))) for x, y in R] for R in rings]
