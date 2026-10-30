"""Chỉnh DÁNG dấu hỏi có sẵn (chép từ bản đứng) bằng 4 số — cùng công thức với nhóm thanh “Dấu hỏi” ở Chi tiết (slider_ui.html hookTF):
  w    bề ngang %   (giãn ngang ĐƯỜNG TÂM quanh giữa dấu, nét không dày lên)
  h    chiều cao %  (giãn dọc đường tâm quanh đáy dấu)
  head dày đầu móc %  (bề dày nét ở đầu giọt)
  tail dày đuôi móc % (bề dày nét ở chân) — giữa đầu và chân đổi dần theo chiều dài nét.
Cách làm: đầu móc = điểm trái nhất (giọt), đuôi = cạnh thấp nhất (chân cụt). Hai mép nét đi từ đầu tới đuôi, đo theo
chiều dài (0 → 1); điểm cùng tỉ lệ trên hai mép → tâm nét + nửa bề dày. Điểm mới = tâm (đã giãn) + nửa bề dày × hệ số.
Dữ liệu dựng thẳng: T = 0; dữ liệu nghiêng: truyền T (tan góc) để làm trong không gian x − y·T rồi nghiêng lại.
Chỉ dùng thư viện chuẩn. build by @nhatmotion"""
import math


def _cum(P, ch):
    s = [0.0]
    for k in range(1, len(ch)):
        (x0, y0), (x1, y1) = P[ch[k - 1]][:2], P[ch[k]][:2]; s.append(s[-1] + math.hypot(x1 - x0, y1 - y0))
    L = s[-1] or 1.0
    return [v / L for v in s]


def _at(P, ch, ts, t):
    for k in range(1, len(ch)):
        if ts[k] >= t:
            u = 0 if ts[k] == ts[k - 1] else (t - ts[k - 1]) / (ts[k] - ts[k - 1])
            (x0, y0), (x1, y1) = P[ch[k - 1]][:2], P[ch[k]][:2]
            return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    return P[ch[-1]][:2]


def hook_tf(c, w=100, h=100, head=100, tail=100, T=0.0):
    """c: [(x, y, on), …] một vòng kín. Trả vòng mới cùng số điểm."""
    if (w, h, head, tail) == (100, 100, 100, 100) or len(c) < 6: return [tuple(p) for p in c]
    P = [(x - y * T, y) for x, y, *_ in c]; n = len(P)
    hd = min(range(n), key=lambda i: (P[i][0], -P[i][1]))
    e = min(range(n), key=lambda i: P[i][1] + P[(i + 1) % n][1])   # cạnh thấp nhất = chân cụt (e, e+1)
    ta, tb = e, (e + 1) % n
    # chiều thuận từ đầu gặp đầu mút nào của chân trước → mép 1; chiều nghịch tới mút còn lại → mép 2
    i, A = hd, [hd]
    while i not in (ta, tb): i = (i + 1) % n; A.append(i)
    other = tb if i == ta else ta
    j, B = hd, [hd]
    while j != other: j = (j - 1) % n; B.append(j)
    if len(A) + len(B) - 1 < n: return [tuple(p) for p in c]   # dáng lạ: bỏ qua
    tA, tB = _cum(P, A), _cum(P, B)
    xs = [p[0] for p in P]; bx = (min(xs) + max(xs)) / 2; yb = min(p[1] for p in P)
    out = list(P)
    for ch, ts, oc, ots in ((A, tA, B, tB), (B, tB, A, tA)):
        for k, idx in enumerate(ch):
            t = ts[k]; q = _at(P, oc, ots, t); x, y = P[idx]
            cx, cy = (x + q[0]) / 2, (y + q[1]) / 2
            m = (head + (tail - head) * t) / 100.0
            out[idx] = (bx + (cx - bx) * w / 100.0 + (x - cx) * m, yb + (cy - yb) * h / 100.0 + (y - cy) * m)
    return [(x + y * T, y) + tuple(p[2:]) for (x, y), p in zip(out, c)]


if __name__ == '__main__':
    import sys, json
    from fontTools.ttLib import TTFont
    sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
    from geom import tt_contours, bbox_pts
    F, G = sys.argv[1], sys.argv[2]; a = [float(v) for v in sys.argv[3:7]]
    f = TTFont(F); cs = tt_contours(f, G); top = max(cs, key=lambda c: bbox_pts(c)[1])
    print(json.dumps({'before': [list(p) for p in top], 'after': [list(p) for p in hook_tf(top, *a)]}))
