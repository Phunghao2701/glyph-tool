# tìm glyph có 2 contour cắt nhau (chồng nét) — chỉ cần fontTools + numpy
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import contours, flat
from fontTools.ttLib import TTFont
import numpy as np
def segs(P): P = np.array(P); return P, np.roll(P, -1, axis=0)
def cross(a1, a2, b1, b2):
    d = lambda p, q, r: (q[..., 0] - p[..., 0]) * (r[..., 1] - p[..., 1]) - (q[..., 1] - p[..., 1]) * (r[..., 0] - p[..., 0])
    A1, A2 = a1[:, None], a2[:, None]; B1, B2 = b1[None], b2[None]
    return ((d(A1, A2, B1) * d(A1, A2, B2) < 0) & (d(B1, B2, A1) * d(B1, B2, A2) < 0)).any()
f = TTFont(sys.argv[1]); gs = f.getGlyphSet(); bad = []
for cp, n in sorted(f.getBestCmap().items()):
    cs = [flat(c, 10) for c in contours(gs, n)]
    S = [segs(P) for P in cs if len(P) > 2]
    if any(cross(*S[i], *S[j]) for i in range(len(S)) for j in range(i + 1, len(S))): bad.append(chr(cp))
print('chồng nét:', ''.join(bad) or 'không có')
