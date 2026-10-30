"""So hai bản font: liệt kê MỌI chữ có hình / độ rộng đổi (để biết thay đổi có lan ra ngoài yêu cầu không — người dùng 27/10:
“chỉnh sửa không trong yêu cầu thì phải hỏi tôi có áp dụng không”). Chạy trước khi đưa VER mới lên trang.
usage: glyphdiff.py OLD.ttf NEW.ttf [--expect "ấầẩ…"]   → in các chữ đổi; chữ đổi NGOÀI --expect đánh dấu ⚠ (phải hỏi người dùng)
Đo: độ rộng, khung bao từng mảnh (contour) sau khi tách chữ ghép; dịch ≥ 2 đơn vị coi là đổi."""
import sys, argparse, unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
ap = argparse.ArgumentParser(); ap.add_argument('old'); ap.add_argument('new'); ap.add_argument('--expect', default=''); ap.add_argument('--tol', type=float, default=2)
a = ap.parse_args()
def load(p):
    f = TTFont(p); gs = f.getGlyphSet(); cm = f.getBestCmap(); out = {}
    for u, n in cm.items():
        pen = DecomposingRecordingPen(gs); gs[n].draw(pen); cs, cur = [], []
        for op, args in pen.value:
            if op == 'moveTo': cur = [args[0]]
            elif op in ('lineTo', 'qCurveTo', 'curveTo'): cur += [q for q in args if q]
            elif cur: cs.append((min(p[0] for p in cur), min(p[1] for p in cur), max(p[0] for p in cur), max(p[1] for p in cur))); cur = []
        out[chr(u)] = (gs[n].width, sorted(cs))
    return out
A, B = load(a.old), load(a.new); bad, ok = [], []
for ch in sorted(set(A) & set(B), key=ord):
    (wa, ca), (wb, cb) = A[ch], B[ch]
    if wa == wb and len(ca) == len(cb) and all(max(abs(x - y) for x, y in zip(p, q)) < a.tol for p, q in zip(ca, cb)): continue
    d = 'rộng %d→%d' % (wa, wb) if wa != wb else ''
    if len(ca) == len(cb):
        mv = [(round((q[0] + q[2] - p[0] - p[2]) / 2), round((q[1] + q[3] - p[1] - p[3]) / 2)) for p, q in zip(ca, cb) if max(abs(x - y) for x, y in zip(p, q)) >= a.tol]
        d += ' mảnh dời ' + ' '.join('%+d/%+d' % m for m in mv)
    else: d += ' số mảnh %d→%d' % (len(ca), len(cb))
    (ok if ch in a.expect else bad).append('%s %s' % (ch, d.strip()))
print('đổi đúng yêu cầu (%d): %s' % (len(ok), ' · '.join(ok) or '—'))
print('⚠ đổi NGOÀI yêu cầu (%d) — hỏi người dùng trước khi giữ: %s' % (len(bad), ' · '.join(bad) or '—'))
