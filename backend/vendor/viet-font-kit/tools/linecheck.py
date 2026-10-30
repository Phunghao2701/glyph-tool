"""Kiểm tra dấu tràn line biên.
usage: linecheck.py FONT [--json out.json]
Ngang: phần mực của DẤU (contour nằm trên x-height/cap hoặc dưới chân chữ, và móc ơ ư) vượt ra ngoài
        2 đường biên advance [0, width]. Word/Excel/Canva mặc định KHÔNG bật kern → phần tràn đè chữ bên cạnh.
Dọc:  yMax/yMin của glyph so với hhea / typo / win ascender-descender (Canva, web dùng hhea/typo)."""
import sys, json, unicodedata
sys.path.insert(0, __import__('os').path.dirname(__file__))
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from shapely.geometry import box
import qhook

def contours(gs, n):
    from fontTools.pens.basePen import BasePen
    class Cub(BasePen):   # .ttf: qCurveTo → bậc 3 để đo như .otf
        def __init__(s): super().__init__(gs); s.value = []
        def _moveTo(s, p): s.value.append(("moveTo", (p,)))
        def _lineTo(s, p): s.value.append(("lineTo", (p,)))
        def _curveToOne(s, a, b, c): s.value.append(("curveTo", (a, b, c)))
        def _closePath(s): s.value.append(("closePath", ()))
        def _endPath(s): s.value.append(("closePath", ()))
    r = Cub(); gs[n].draw(r); out, cur = [], []
    for op, a in r.value:
        cur.append((op, a))
        if op in ('closePath', 'endPath'): out.append(cur); cur = []
    return out

def run(fn):
    f = TTFont(fn); gs = f.getGlyphSet(); cm = f.getBestCmap(); hm = f['hmtx']
    os2, hh = f['OS/2'], f['hhea']
    xh = getattr(os2, 'sxHeight', 0) or 500; cap = getattr(os2, 'sCapHeight', 0) or 700
    VN = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
    VN += VN.upper()
    rows = []
    for ch in VN:
        n = cm.get(ord(ch))
        if not n: continue
        w = hm[n][0]; base = unicodedata.normalize('NFD', ch)[0]
        bn = cm.get(ord(base)); bw = hm[bn][0] if bn else w
        top_line = (cap if ch.isupper() else xh)
        polys = [qhook.to_poly([c]) for c in contours(gs, n)]
        ink = None
        from shapely.ops import unary_union
        allg = unary_union(polys)
        # marks = ink above the letter's top line (+12) or below baseline (-12), horn included (its head is above the top line)
        marks = allg.intersection(box(-2000, top_line + 12, 4000, 4000)).union(allg.intersection(box(-2000, -4000, 4000, -12)))
        horn = allg.intersection(box(bw, top_line - 160, 4000, 4000)) if ch.lower() in "ơờớởỡợưừứửữự" else None
        L = R = 0
        for g in [marks] + ([horn] if horn is not None and not horn.is_empty else []):
            if g.is_empty: continue
            x0, y0, x1, y1 = g.bounds
            L = max(L, -x0); R = max(R, x1 - w)
        x0, y0, x1, y1 = allg.bounds
        rows.append(dict(ch=ch, g=n, w=w, L=round(L), R=round(R), ymax=round(y1), ymin=round(y0)))
    vm = dict(hhea_asc=hh.ascent, hhea_desc=hh.descent, hhea_gap=hh.lineGap, typo_asc=os2.sTypoAscender,
              typo_desc=os2.sTypoDescender, typo_gap=os2.sTypoLineGap, win_asc=os2.usWinAscent, win_desc=os2.usWinDescent,
              use_typo=bool(os2.fsSelection & 128), upm=f['head'].unitsPerEm)
    return vm, rows

if __name__ == '__main__':
    vm, rows = run(sys.argv[1])
    over_h = [r for r in rows if r['L'] > 0 or r['R'] > 0]
    over_v = [r for r in rows if r['ymax'] > vm['typo_asc'] or r['ymin'] < vm['typo_desc']]
    print(vm)
    print('tràn ngang (dấu ra ngoài 2 biên advance): %d / %d' % (len(over_h), len(rows)))
    for r in sorted(over_h, key=lambda r: -max(r['L'], r['R']))[:16]: print('  ', r)
    print('vượt ascender typo/hhea %d: %d glyph, cao nhất %d' % (vm['typo_asc'], len(over_v), max(r['ymax'] for r in rows)))
    if '--json' in sys.argv: json.dump(dict(vm=vm, rows=rows), open(sys.argv[sys.argv.index('--json') + 1], 'w'), ensure_ascii=False)
