"""glyph → shapely polygon (hỗ trợ cả TTF qCurveTo), dùng để đo nét."""
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon
from shapely.ops import unary_union
class FlatPen(BasePen):
    def __init__(self, gs, n=12):
        super().__init__(gs); self.rings = []; self.cur = []; self.n = n
    def _moveTo(self, p): self.cur = [p]
    def _lineTo(self, p): self.cur.append(p)
    def _curveToOne(self, a, b, c):
        p0 = self.cur[-1]
        for i in range(1, self.n + 1):
            t = i / self.n; u = 1 - t
            self.cur.append((u**3*p0[0]+3*u*u*t*a[0]+3*u*t*t*b[0]+t**3*c[0], u**3*p0[1]+3*u*u*t*a[1]+3*u*t*t*b[1]+t**3*c[1]))
    def _qCurveToOne(self, a, b):
        p0 = self.cur[-1]
        for i in range(1, self.n + 1):
            t = i / self.n; u = 1 - t
            self.cur.append((u*u*p0[0]+2*u*t*a[0]+t*t*b[0], u*u*p0[1]+2*u*t*a[1]+t*t*b[1]))
    def _closePath(self):
        if len(self.cur) > 2: self.rings.append(self.cur)
        self.cur = []
    _endPath = _closePath
def glyph_poly(f, ch):
    gs = f.getGlyphSet(); pen = FlatPen(gs); gs[f.getBestCmap()[ord(ch)]].draw(pen)
    # even-odd: XOR các vòng
    out = None
    for r in pen.rings:
        p = Polygon(r).buffer(0)
        out = p if out is None else out.symmetric_difference(p)
    return out
