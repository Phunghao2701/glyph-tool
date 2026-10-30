"""Tách dấu thanh (sắc huyền hỏi ngã) khỏi nét chữ trong dữ liệu khung gõ thử, để trang dời dấu theo thanh kéo.
usage: tone_split.py FONT.otf IN.json OUT.json
Dấu thanh = các contour của chữ mang dấu không trùng khung (±3) với contour nào của chữ bỏ dấu thanh (ấ − â, ặ − ạ…)."""
import sys, json, math, unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
FONT, IN, OUT = sys.argv[1:4]
f = TTFont(FONT); gs = f.getGlyphSet(); cm = f.getBestCmap()
TONE = {"́": "s", "̀": "f", "̉": "r", "̃": "x"}   # sắc, huyền, hỏi, ngã (kiểu gõ Telex)
def contours(n):
    r = RecordingPen(); gs[n].draw(r); cs, cur = [], []
    for o, a in r.value:
        cur.append((o, tuple(tuple(p) for p in a)))
        if o == "closePath": cs.append(tuple(cur)); cur = []
    return cs
def d_of(cs):
    p = SVGPathPen(None)
    for c in cs:
        for o, a in c: getattr(p, o)(*a)
    return p.getCommands()
def bbox(c):
    b = BoundsPen(None)
    for o, a in c: getattr(b, o)(*a)
    return b.bounds
def ymin(c):
    b = BoundsPen(None)
    for o, a in c: getattr(b, o)(*a)
    return b.bounds[1]
def ymax(c):
    b = BoundsPen(None)
    for o, a in c: getattr(b, o)(*a)
    return b.bounds[3]
D = json.load(open(IN)); G = D["G"]; n_ok = n_bad = 0
REF = {}                                          # tỉ lệ rộng / cao của dấu thanh trên chữ a / A đơn
for t, mark in TONE.items():
    for up in (False, True):
        b0 = "A" if up else "a"; c1 = unicodedata.normalize("NFC", b0 + t)
        if ord(c1) in cm and ord(b0) in cm:
            bs0 = [bbox(c) for c in contours(cm[ord(b0)])]
            mk0 = [c for c in contours(cm[ord(c1)]) if not any(max(abs(u - v) for u, v in zip(bbox(c), q)) <= 3 for q in bs0)]
            if len(mk0) == 1: bb0 = bbox(mk0[0]); REF[(mark, up)] = (bb0[2] - bb0[0]) / max(1, bb0[3] - bb0[1])
for ch, e in G.items():
    d = unicodedata.normalize("NFD", ch); t = [TONE[m] for m in d if m in TONE]
    if not t: continue
    e["t"] = t[0]
    if e.get("h"): continue                      # ư ơ: e.m đã là dấu thanh (râu do trang vẽ)
    base = unicodedata.normalize("NFC", "".join(m for m in d if m not in TONE))
    if ord(base) not in cm: continue
    bs = [bbox(c) for c in contours(cm[ord(base)])]; cs = contours(cm[ord(ch)])
    if "dot" in e: cs = [c for c in cs if ymax(c) >= -20]
    same = lambda c: any(max(abs(u - v) for u, v in zip(bbox(c), b)) <= 3 for b in bs)   # so theo khung, không theo điểm đầu contour
    mk = [c for c in cs if not same(c)]; rest = [c for c in cs if same(c)]
    if len(mk) > 1:                              # dấu chồng (ấ ầ ẩ…): dấu mũ / trăng cũng bị dời nên không trùng khung chữ bỏ dấu
        ref = REF.get((t[0], ch.isupper()))       # → giữ contour có tỉ lệ rộng / cao gần dấu thanh của chữ đơn (á, Á…) nhất
        if ref:
            asp = lambda c: (bbox(c)[2] - bbox(c)[0]) / max(1, bbox(c)[3] - bbox(c)[1])
            best = min(mk, key=lambda c: abs(math.log(max(.01, asp(c)) / ref)))
            rest += [c for c in mk if c is not best]; mk = [best]
    if not mk or len(mk) == len(cs):             # ì í ỉ ĩ Ĩ: thân i không chấm khác contour chữ i → tách theo độ cao
        lim = 690 if ch.isupper() else 600
        mk = [c for c in cs if ymin(c) > lim]; rest = [c for c in cs if ymin(c) <= lim]
        if not mk or not rest: n_bad += 1; continue
    e["d"] = d_of(rest); e["m"] = d_of(mk); n_ok += 1
json.dump(D, open(OUT, "w"), separators=(",", ":"))
print("tone_split:", n_ok, "chữ tách được,", n_bad, "không tách được")
