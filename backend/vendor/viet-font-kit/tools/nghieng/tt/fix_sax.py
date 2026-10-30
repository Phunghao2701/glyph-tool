"""Trục chữ cho bàn vẽ: sax = [x tại đường chân chữ, tan] lấy từ anchor dấu trên của chữ gốc (font nghiêng), không phải 0.
usage: fix_sax.py SRC_IT.ttf recipes.json [recipes.json…]"""
import sys, json, math, unicodedata, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontTools.ttLib import TTFont
from gposanc import anchors
I = TTFont(sys.argv[1]); cm = I.getBestCmap(); b, *_ = anchors(I)
T = None
for p in sys.argv[2:]:
    R = json.load(open(p)); n = 0
    for name, r in R['glyphs'].items():
        ch = chr(r['u']); L = unicodedata.normalize('NFD', ch)[0]
        g = 'dotlessi' if L == 'i' else cm[ord(L)]
        anc = b.get(g, {}); k = [k for k in anc if k[1] == 0]
        if not k: continue
        ax, ay = anc[k[0]]; t = r['sax'][1]
        r['sax'] = [round(ax - ay * t, 2), t]; n += 1
    json.dump(R, open(p, 'w')); print(p, 'sax', n)
