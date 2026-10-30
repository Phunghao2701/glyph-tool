# bảng đo dấu chồng: viền chữ, khung dấu trăng / mũ + dấu thanh, khe nhỏ nhất (đoạn nối 2 điểm gần nhất), lệch tâm, trục chuẩn
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import contours, flat, cb, bounds
from fontTools.ttLib import TTFont
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.path import Path; from matplotlib.patches import PathPatch, Rectangle
FONT, REC, OUT, TXT = sys.argv[1:5]
f = TTFont(FONT); gs = f.getGlyphSet(); cm = f.getBestCmap(); R = json.load(open(REC))['glyphs']
rows = TXT.split('|'); ncol = max(len(r) for r in rows)
fig, axs = plt.subplots(len(rows), ncol, figsize=(4.2 * ncol, 6.2 * len(rows)), dpi=110, squeeze=False)
for ri, row in enumerate(rows):
    for ci in range(ncol):
        ax = axs[ri][ci]; ax.axis('off')
        if ci >= len(row): continue
        ch = row[ci]; n = cm[ord(ch)]; cs = contours(gs, n)
        top = 842 if ch.isupper() else 640
        up = sorted([c for c in cs if cb(c)[1] > top - 5], key=lambda c: cb(c)[1])
        verts, codes = [], []
        for c in cs:
            P = flat(c, 14); verts += P + [(0, 0)]; codes += [Path.MOVETO] + [Path.LINETO] * (len(P) - 1) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc='#d9d9d9', ec='#111', lw=.8))
        w = gs[n].width; ax.plot([0, 0], [-260, 1300], color='#e8890c', lw=.8); ax.plot([w, w], [-260, 1300], color='#e8890c', lw=.8)
        r = R.get(n)
        if r: a, t = r['sax']; ax.plot([a + t * -250, a + t * 1300], [-250, 1300], color='#c4182f', lw=1, ls='--')
        info = ['%s  rộng %d' % (ch, w)]
        cols = ['#1f6fd1', '#127a46']
        for k, c in enumerate(up[:2]):
            b = cb(c); ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec=cols[k], lw=1.1))
            info.append('%s x %d–%d (tâm %d) · y %d–%d' % (['dấu 1', 'dấu 2'][k], b[0], b[2], (b[0] + b[2]) / 2, b[1], b[3]))
        if len(up) >= 2:
            A = np.array(flat(up[0], 30)); B = np.array(flat(up[1], 30))
            d = np.sqrt(((A[:, None] - B[None]) ** 2).sum(-1)); i, j = np.unravel_index(d.argmin(), d.shape)
            ax.plot([A[i][0], B[j][0]], [A[i][1], B[j][1]], color='#c4182f', lw=2)
            ax.annotate('khe %.0f' % d.min(), ((A[i][0] + B[j][0]) / 2, (A[i][1] + B[j][1]) / 2), xytext=(8, -4), textcoords='offset points', color='#c4182f', fontsize=12, weight='bold')
            b0, b1 = cb(up[0]), cb(up[1])
            info.append('khe nhỏ nhất %.0f · đáy dấu 2 − đỉnh dấu 1 = %d' % (d.min(), b1[1] - b0[3]))
            info.append('tâm dấu 2 − tâm dấu 1 = %+d' % ((b1[0] + b1[2]) / 2 - (b0[0] + b0[2]) / 2))
        ax.set_xlim(-120, 800); ax.set_ylim(-280, 1320); ax.set_aspect('equal')
        ax.text(-110, -275, '\n'.join(info), fontsize=9.5, va='bottom', family='DejaVu Sans')
plt.tight_layout(); plt.savefig(OUT, facecolor='white')
