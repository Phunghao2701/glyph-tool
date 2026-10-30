# vẽ chữ + đường trục chuẩn (đọc từ recipes.json: sax = [a, tan]) → PNG
import sys, json
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from geo import contours, flat
from fontTools.ttLib import TTFont
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path; from matplotlib.patches import PathPatch
FONT, REC, OUT, TXT = sys.argv[1:5]
f = TTFont(FONT); gs = f.getGlyphSet(); cm = f.getBestCmap(); R = json.load(open(REC))['glyphs']
rows = TXT.split('|'); fig, ax = plt.subplots(figsize=(2.2 * max(len(r) for r in rows), 3.6 * len(rows)), dpi=110)
for ri, row in enumerate(rows):
    x0 = 0; y0 = -ri * 1700
    for ch in row:
        n = cm[ord(ch)]; verts, codes = [], []
        for c in contours(gs, n):
            P = flat(c, 12); verts += [(x0 + x, y0 + y) for x, y in P] + [(0, 0)]; codes += [Path.MOVETO] + [Path.LINETO] * (len(P) - 1) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), fc='#111', ec='none'))
        r = R.get(n)
        if r and r.get('sax'):
            a, t = r['sax']
            ax.plot([x0 + a + t * -300, x0 + a + t * 1300], [y0 - 300, y0 + 1300], color='#e5243b', lw=1.2)
        ax.plot([x0, x0 + gs[n].width], [y0, y0], color='#bbb', lw=.6)
        x0 += gs[n].width + 160
ax.set_aspect('equal'); ax.autoscale(); ax.axis('off'); plt.savefig(OUT, bbox_inches='tight', facecolor='white')
