"""Dấu hỏi từ NỬA TRÊN dấu ? của chính font nghiêng (VER 1C): cắt ngang ở cổ (hook_half), giữ vòm + cổ, chân cụt.
Nở nét cho nét đậm nhất bằng nét đậm nhất dấu hỏi bản đứng (đã theo dấu ngã) sau khi thu về cỡ dấu hỏi.
usage: half_hook.py SRC_IT.ttf REF_VN.ttf OUT.json [frac=0.5]"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from fontTools.ttLib import TTFont
from geom import tt_contours, bbox_pts, segments, segs_to_contour, seg_pt, seg_split, dense, area
from scipy.ndimage import distance_transform_edt
from PIL import Image, ImageDraw

SRC, REF, OUT = sys.argv[1:4]; FR = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
I = TTFont(SRC); R = TTFont(REF)
q = max(tt_contours(I, 'question'), key=lambda c: bbox_pts(c)[3] - bbox_pts(c)[1])
b = bbox_pts(q); yc = b[1] + (1 - FR) * (b[3] - b[1])

def roots(sg, y):
    if len(sg) == 2:
        (x0, y0), (x1, y1) = sg
        return [] if y0 == y1 else [t for t in [(y - y0) / (y1 - y0)] if 1e-9 < t < 1 - 1e-9]
    a, c_, d = sg; A = a[1] - 2 * c_[1] + d[1]; B = 2 * (c_[1] - a[1]); C = a[1] - y
    if abs(A) < 1e-9: ts = [-C / B] if abs(B) > 1e-9 else []
    else:
        D = B * B - 4 * A * C
        ts = [] if D < 0 else [(-B + s * math.sqrt(D)) / (2 * A) for s in (1, -1)]
    return sorted(t for t in ts if 1e-9 < t < 1 - 1e-9)

pieces = []
for sg in segments(q):
    ts = roots(sg, yc); prev = 0; cur = sg
    for t in ts:
        tt = (t - prev) / (1 - prev); a, cur = seg_split(cur, tt); pieces.append(a); prev = t
    pieces.append(cur)
above = [seg_pt(p, .5)[1] > yc for p in pieces]
n = len(pieces); k0 = next(i for i in range(n) if above[i] and not above[i - 1])
run = []
for k in range(n):
    i = (k0 + k) % n
    if not above[i]: break
    run.append(pieces[i])
run.append((run[-1][-1], run[0][0]))
c = segs_to_contour(run)

def raster_thick(cs, res=4):
    P = [np.array(dense(x, 1.0)) for x in cs]; allp = np.vstack(P)
    x0, y0 = allp.min(0) - 5; x1, y1 = allp.max(0) + 5
    W, H = int((x1 - x0) * res), int((y1 - y0) * res)
    im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
    for p in P: d.polygon([((x - x0) * res, (y1 - y) * res) for x, y in p], fill=255)
    return 2 * distance_transform_edt(np.array(im) > 0).max() / res

# cỡ đích: dấu hỏi của ả bản đứng (đã nghiêng thì cao giữ nguyên)
cmR = R.getBestCmap()
hR = [x for x in tt_contours(R, cmR[0x1EA3]) if bbox_pts(x)[1] > 520][0]
hb = bbox_pts(hR); s = (hb[3] - hb[1]) / (bbox_pts(c)[3] - bbox_pts(c)[1])
tR = raster_thick([hR]); tQ = raster_thick([c]) * s
# nở nét: dời mỗi điểm theo pháp tuyến đỉnh (TrueType: đúng gần đúng với δ nhỏ)
delta = max(0.0, (tR - tQ) / 2) / s
def embolden(c, d):
    pts = np.array([(x, y) for x, y, _ in c]); n = len(pts); out = []
    sgn = 1 if area(c) < 0 else -1      # TrueType: viền ngoài cùng chiều kim đồng hồ (area âm)
    for i in range(n):
        a = pts[i - 1]; bq = pts[(i + 1) % n]; t = bq - a; t /= (np.linalg.norm(t) + 1e-9)
        nrm = np.array([-t[1], t[0]]) * sgn
        out.append((pts[i][0] + nrm[0] * d, pts[i][1] + nrm[1] * d, c[i][2]))
    return out
c2 = embolden(c, delta)
if raster_thick([c2]) * s < tQ: c2 = embolden(c, -delta)
json.dump({'contour': [[x, y, on] for x, y, on in c2], 'cut_y': yc, 'scale': s, 'thick_ref': tR, 'thick_before': tQ,
           'thick_after': raster_thick([c2]) * s}, open(OUT, 'w'))
print('half hook: cắt ở y=%.0f, thu ×%.2f, nét đậm %.0f → %.0f (bản đứng %.0f)' % (yc, s, tQ, raster_thick([c2]) * s, tR))
