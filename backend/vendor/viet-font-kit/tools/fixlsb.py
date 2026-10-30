"""TrueType: đặt hmtx lsb = xMin cho mọi glyph có nét (lỗi A36 — chữ dựng mới ghi lsb 0 → FreeType / Chrome / Word dời cả chữ sang trái đúng xMin).
usage: fixlsb.py FONT.ttf [--check]   build by @nhatmotion"""
import sys
from fontTools.ttLib import TTFont
p = sys.argv[1]; f = TTFont(p)
if 'glyf' not in f: print('fixlsb: không phải TrueType, bỏ qua'); sys.exit(0)
g, h, bad = f['glyf'], f['hmtx'], []
for n in f.getGlyphOrder():
    gl = g[n]
    if gl.numberOfContours == 0: continue
    gl.recalcBounds(g)
    if h[n][1] != gl.xMin: bad.append(n); h[n] = (h[n][0], gl.xMin)
if '--check' in sys.argv:
    print('fixlsb: %d glyph lsb ≠ xMin %s' % (len(bad), ' '.join(bad[:12]))); sys.exit(1 if bad else 0)
if bad: f.save(p)
print('fixlsb: sửa %d glyph' % len(bad))
