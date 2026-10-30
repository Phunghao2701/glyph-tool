import sys, os, math; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import contours, cb, mindist, unslant
from fontTools.ttLib import TTFont
F, ang = sys.argv[1], float(sys.argv[2]); T = math.tan(math.radians(ang))
f = TTFont(F); gs = f.getGlyphSet(); cm = f.getBestCmap()
for row in ['ấầẩẫ', 'ắằẳẵ', 'ẤẦẨẪ', 'ẮẰẲẴ']:
    out = []
    for ch in row:
        cs = unslant(contours(gs, cm[ord(ch)]), T); top = 842 if ch.isupper() else 640
        up = sorted([c for c in cs if cb(c)[1] > top - 5], key=lambda c: cb(c)[1]); a, b = cb(up[0]), cb(up[1])
        out.append('%s %+d/%d/%d' % (ch, ((b[0] + b[2]) - (a[0] + a[2])) / 2, b[1] - a[3], mindist([up[0]], [up[1]])))
    print('  '.join(out))
