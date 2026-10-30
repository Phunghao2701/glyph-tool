"""Kern sau râu (bản không cần shapely / harfbuzz): làm theo luật autokern_horn.py của kit.
Thân chữ sau ư ơ đặt như sau u o; nếu râu vướng thì lùi tới khi khe râu–chữ sau ≥ max(khe chữ trơn, MIN_GAP). Chỉ khép, không nới.
Đo trên nét thật (đã nghiêng), dải ngang 8 đơn vị. usage: hornkern.py IN.otf OUT.otf [MIN_GAP=50]"""
import sys, os, json, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import contours, flat
from fontTools.ttLib import TTFont
from fontTools.otlLib import builder as ob
IN, OUT = sys.argv[1], sys.argv[2]; MIN_GAP = float(sys.argv[3]) if len(sys.argv) > 3 else 50
f = TTFont(IN); cm = f.getBestCmap(); gs = f.getGlyphSet(); hm = f['hmtx']
# bảng kern hiện có (format 1 + 2)
K1, K2 = {}, []
for lk in f['GPOS'].table.LookupList.Lookup:
    for st in lk.SubTable:
        if lk.LookupType == 9: st = st.ExtSubTable
        if getattr(st, 'LookupType', lk.LookupType) != 2: continue   # chỉ PairPos
        if st.Format == 1:
            for g, ps in zip(st.Coverage.glyphs, st.PairSet):
                for r in ps.PairValueRecord:
                    K1[(g, r.SecondGlyph)] = K1.get((g, r.SecondGlyph), 0) + (getattr(r.Value1, 'XAdvance', 0) or 0)
        elif st.Format == 2: K2.append(st)
def kern(a, b):
    if (a, b) in K1: return K1[(a, b)]
    for st in K2:
        if a in st.Coverage.glyphs:
            c1 = st.ClassDef1.classDefs.get(a, 0); c2 = st.ClassDef2.classDefs.get(b, 0)
            v = getattr(st.Class1Record[c1].Class2Record[c2].Value1, 'XAdvance', 0) or 0
            if v: return v
    return 0
BANDS = range(-320, 1320, 8); PC = {}
def prof(n):
    if n in PC: return PC[n]
    L, R = {}, {}
    segs = []
    for c in contours(gs, n):
        P = flat(c, 16)
        for i in range(len(P)): segs.append((P[i], P[(i + 1) % len(P)]))
    for y in BANDS:
        xs = []
        for (x0, y0), (x1, y1) in segs:
            lo, hi = min(y0, y1), max(y0, y1)
            if hi < y or lo > y + 8: continue
            for yy in (max(lo, y), min(hi, y + 8)):
                xs.append(x0 if y1 == y0 else x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
        if xs: L[y], R[y] = min(xs), max(xs)
    PC[n] = (L, R); return PC[n]
rights = [chr(c) for c in sorted(cm) if chr(c).isalpha() or chr(c) in ".,;:!?'\"()-–—…’”"]
lefts = [chr(c) for c in sorted(cm) if '̛' in unicodedata.normalize('NFD', chr(c)) and c != 0x31B]
pairs, summary = {}, {}
for L in lefts:
    d = unicodedata.normalize('NFD', L); plain = unicodedata.normalize('NFC', d.replace('̛', ''))
    nL, nP = cm[ord(L)], cm[ord(plain)]
    _, Lr = prof(nL); _, Pr = prof(nP)
    hornb = [y for y in Lr if y not in Pr or Lr[y] > Pr[y] + 1]
    for Rc in rights:
        nR = cm[ord(Rc)]; Rl, _ = prof(nR)
        s0 = hm[nP][0] + kern(nP, nR); sL = hm[nL][0] + kern(nL, nR)
        common = [y for y in Pr if y in Rl]
        Tg = min((s0 + Rl[y] - Pr[y] for y in common), default=MIN_GAP)
        hb_ = [y for y in hornb if y in Rl]
        s = s0 if not hb_ else max(s0, max(max(Tg, MIN_GAP) - (Rl[y] - Lr[y]) for y in hb_))
        k = min(0, round(s - sL))
        if abs(k) >= 2: pairs[(nL, nR)] = k
        summary[L + Rc] = k
gpos = f['GPOS'].table
vr = {k: (ob.buildValue({'XAdvance': v}), None) for k, v in pairs.items()}
st = ob.buildPairPosGlyphs(vr, f.getReverseGlyphMap())
lk = ob.buildLookup(st); gpos.LookupList.Lookup.append(lk); gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)
li = len(gpos.LookupList.Lookup) - 1
for fr in gpos.FeatureList.FeatureRecord:
    if fr.FeatureTag == 'kern': fr.Feature.LookupListIndex.append(li); fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
f.save(OUT)
show = ['ươ', 'ưa', 'ưu', 'ưt', 'ưn', 'ưi', 'ơn', 'ơi', 'ƯƠ', 'ƯA', 'ƯN', 'ƠI', 'ư,', 'ơ.']
print('hornkern: %d cặp · ' % len(pairs) + ' '.join('%s %+d' % (p, summary.get(p, 0)) for p in show if p in summary))
json.dump(summary, open(os.path.splitext(OUT)[0] + '.hornkern.json', 'w'), ensure_ascii=False)
