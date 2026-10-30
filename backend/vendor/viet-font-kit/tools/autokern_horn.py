"""Kern tự động sau chữ có râu (ơ ư Ơ Ư + dấu): râu nới advance làm hở chữ sau (ươ, ưa…).
Luật: thân chữ sau đặt như sau chữ trơn (u, o…) nếu râu không vướng; nếu vướng thì lùi tới khi khe râu–chữ sau
≥ max(khe chữ trơn, MIN_GAP). Đo bằng profile ngang theo dải 8 đơn vị, có kern sẵn của font (HarfBuzz).
usage: autokern_horn.py IN.otf OUT.otf [MIN_GAP=50] → in bảng tóm tắt; thêm 1 lookup PairPos vào feature kern."""
import sys, os, unicodedata, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flatpoly import glyph_poly
from shapely.geometry import box
from fontTools.ttLib import TTFont
from fontTools.ttLib import newTable
from fontTools.otlLib import builder as ob
from fontTools.ttLib.tables import otTables as ot
import uharfbuzz as hb
IN, OUT = sys.argv[1], sys.argv[2]; MIN_GAP = float(sys.argv[3]) if len(sys.argv) > 3 else 50
f = TTFont(IN); cm = f.getBestCmap(); hm = f["hmtx"]
blob = hb.Blob.from_file_path(IN); face = hb.Face(blob); font = hb.Font(face)
def shape_adv(a, b):
    buf = hb.Buffer(); buf.add_str(a + b); buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True}); return buf.glyph_positions[0].x_advance
BANDS = range(-320, 1320, 8)
PC = {}
def prof(ch):
    if ch in PC: return PC[ch]
    P = glyph_poly(f, ch); L, R = {}, {}
    if P is not None and not P.is_empty:
        for y in BANDS:
            s = P.intersection(box(-2000, y, 4000, y + 8))
            if not s.is_empty: L[y], R[y] = s.bounds[0], s.bounds[2]
    PC[ch] = (L, R); return PC[ch]
rights = [chr(c) for c in sorted(cm) if chr(c).isalpha() or chr(c) in ".,;:!?'\"()-–—…’”"]
lefts = [chr(c) for c in sorted(cm) if "̛" in unicodedata.normalize("NFD", chr(c)) and c != 0x31B]
pairs = {}; summary = {}
for L in lefts:
    d = unicodedata.normalize("NFD", L); plain = unicodedata.normalize("NFC", d.replace("̛", ""))
    _, Lr = prof(L); _, Pr = prof(plain)
    hornb = [y for y in Lr if y not in Pr or Lr[y] > Pr[y] + 1]
    for R in rights:
        Rl, _ = prof(R)
        s0 = shape_adv(plain, R); sL = shape_adv(L, R)
        common = [y for y in Pr if y in Rl]
        T = min((s0 + Rl[y] - Pr[y] for y in common), default=MIN_GAP)
        hb_ = [y for y in hornb if y in Rl]
        s = s0 if not hb_ else max(s0, max(max(T, MIN_GAP) - (Rl[y] - Lr[y]) for y in hb_))
        k = min(0, round(s - sL))   # chỉ khép lại, không nới thêm
        if abs(k) >= 2: pairs[(cm[ord(L)], cm[ord(R)])] = k
        summary[L + R] = k
# một lookup PairPos riêng, thêm vào mọi feature kern
if pairs:
    if "GPOS" not in f:
        # Fonts without positioning data still need the generated horn kerning.
        # Create the minimal table structure required to expose a `kern` feature.
        gpos = ot.GPOS(); gpos.Version = 0x00010000
        gpos.ScriptList = ot.ScriptList(); gpos.ScriptList.ScriptRecord = []
        gpos.ScriptList.ScriptCount = 0
        gpos.FeatureList = ot.FeatureList(); gpos.FeatureList.FeatureRecord = []
        gpos.FeatureList.FeatureCount = 0
        gpos.LookupList = ot.LookupList(); gpos.LookupList.Lookup = []
        gpos.LookupList.LookupCount = 0
        table = newTable("GPOS"); table.table = gpos; f["GPOS"] = table
        for tag in ("DFLT", "latn"):
            lang = ot.LangSys(); lang.LookupOrder = None; lang.ReqFeatureIndex = 0xFFFF
            lang.FeatureIndex = []; lang.FeatureCount = 0
            script = ot.Script(); script.DefaultLangSys = lang
            script.LangSysRecord = []; script.LangSysCount = 0
            record = ot.ScriptRecord(); record.ScriptTag = tag; record.Script = script
            gpos.ScriptList.ScriptRecord.append(record)
        gpos.ScriptList.ScriptCount = len(gpos.ScriptList.ScriptRecord)
    else:
        gpos = f["GPOS"].table

    vr = {k: (ob.buildValue({"XAdvance": v}), None) for k, v in pairs.items()}
    st = ob.buildPairPosGlyphs(vr, f.getReverseGlyphMap())
    lk = ob.buildLookup(st)
    gpos.LookupList.Lookup.append(lk)
    gpos.LookupList.LookupCount = len(gpos.LookupList.Lookup)
    li = len(gpos.LookupList.Lookup) - 1
    kern_features = [fr for fr in gpos.FeatureList.FeatureRecord if fr.FeatureTag == "kern"]
    if kern_features:
        for fr in kern_features:
            if li not in fr.Feature.LookupListIndex:
                fr.Feature.LookupListIndex.append(li)
                fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
    else:
        feature = ot.FeatureRecord(); feature.FeatureTag = "kern"
        feature.Feature = ot.Feature(); feature.Feature.FeatureParams = None
        feature.Feature.LookupListIndex = [li]; feature.Feature.LookupCount = 1
        gpos.FeatureList.FeatureRecord.append(feature)
        gpos.FeatureList.FeatureCount = len(gpos.FeatureList.FeatureRecord)
        fi = gpos.FeatureList.FeatureCount - 1
        for sr in gpos.ScriptList.ScriptRecord:
            if sr.ScriptTag not in ("DFLT", "latn") or sr.Script.DefaultLangSys is None:
                continue
            lang = sr.Script.DefaultLangSys
            lang.FeatureIndex = sorted(set(lang.FeatureIndex + [fi]))
            lang.FeatureCount = len(lang.FeatureIndex)
f.save(OUT)
show = ["ươ", "ưa", "ưu", "ưt", "ưn", "ưi", "ơn", "ơi", "ƯƠ", "ƯA", "ƯN", "ƠI", "ư,", "ơ."]
print("autokern_horn: %d cặp · " % len(pairs) + " ".join("%s %+d" % (p, summary.get(p, 0)) for p in show if p in summary))
json.dump(summary, open(os.path.splitext(OUT)[0] + ".hornkern.json", "w"), ensure_ascii=False)
