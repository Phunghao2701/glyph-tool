"""Trục chữ ở Bàn vẽ (font nghiêng) — MỘT trục cho cả họ chữ (người dùng 28/10).

Luật:
- Góc: một góc cho cả font (đo từ thân chữ, vd 13,02°) — không chữ nào tự nghiêng theo dáng riêng.
- Họ chữ = mọi chữ cùng chữ gốc khi tách dấu (NFD): o ò ó ỏ õ ọ ô ồ … ơ ờ … là một họ; O là họ khác.
  Cùng một bộ → cùng một trục, kể cả chữ gốc không dấu và chữ có dấu sắc / huyền / hỏi.
- Vị trí trục của họ: mỗi chữ có dấu cho một ứng viên = đường nghiêng qua tâm dấu đặt trên chữ (dấu trên thấp nhất,
  không có thì dấu nặng). Gom ứng viên trùng nhau (lệch ≤ TOL đv); nhóm ĐÔNG NHẤT là trục của họ (trung vị nhóm).
  Dấu sắc / huyền lệch một bên, hai chấm chỉ lấy được một chấm, dấu nặng chữ ụ ị ỵ đặt theo thân… → tự rơi ra ngoài nhóm.
- Chữ lạ (ít, lệch nhóm) vẫn nhận trục chung của họ; danh sách chữ lệch in ra để xem (cột "lệch").
Ghi sax = [x tại chân chữ (dựng thẳng), tan] vào recipes và glyphs của editor.json; editor.js dùng glyphs[n].sax nếu có,
chữ không thuộc họ nào (b c d đ…) thì editor.js đặt trục cùng góc font qua tâm thân chữ.
usage: axis_editor.py FONT.ttf editor.json ANGLE [TOL=4]   build by @nhatmotion"""
import sys, os, json, math, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fontTools.ttLib import TTFont
from geom import tt_contours, bbox_pts, dense
F, E, ANG = sys.argv[1], sys.argv[2], float(sys.argv[3]); TOL = float(sys.argv[4]) if len(sys.argv) > 4 else 4.0
T = math.tan(math.radians(ANG))
f = TTFont(F); cm = f.getBestCmap(); ed = json.load(open(E))
fam = {}   # chữ gốc → [(ký tự, tên glyph, ứng viên x hoặc None)]
for cp, name in cm.items():
    ch = chr(cp); d = unicodedata.normalize('NFD', ch); L = d[0]
    if L.lower() not in 'aeiouy': continue
    x = None
    if len(d) > 1 and any(0x300 <= ord(m) <= 0x323 and ord(m) != 0x31B for m in d[1:]):
        base = 'dotlessi' if L == 'i' else cm.get(ord(L))
        if base:
            top = bbox_pts(max(tt_contours(f, base), key=lambda c: bbox_pts(c)[3]))[3]
            cs = tt_contours(f, name)
            up = [c for c in cs if bbox_pts(c)[1] > top - 5]; dn = [c for c in cs if bbox_pts(c)[3] < -20]
            mk = min(up, key=lambda c: bbox_pts(c)[1]) if up else (dn[0] if dn else None)
            if mk:
                xu = [px - py * T for px, py in dense(mk, 2.0)]; x = (min(xu) + max(xu)) / 2
    fam.setdefault(L, []).append((ch, name, x))
    if L == 'i' and ch == 'i': fam[L].append(('ı', 'dotlessi', None))
n = 0; rep = []
for L, mem in sorted(fam.items()):
    xs = sorted(x for _, _, x in mem if x is not None)
    if not xs: continue
    best = max((([v for v in xs if abs(v - c) <= TOL]) for c in xs), key=len)   # nhóm ứng viên trùng nhau đông nhất
    ax = best[len(best) // 2]; sax = [round(ax, 2), round(T, 4)]
    odd = [ch for ch, _, x in mem if x is not None and abs(x - ax) > TOL]
    rep.append('%s %d/%d (%d%%)%s' % (L, len(best), len(xs), round(100 * len(best) / len(xs)), ' lệch: ' + ''.join(odd) if odd else ''))
    for _, nm, _ in mem:
        for k in ('recipes', 'glyphs'):
            if nm in ed.get(k, {}): ed[k][nm]['sax'] = sax; n += 1
json.dump(ed, open(E, 'w'), separators=(',', ':'))
print('axis_editor: góc %.2f° chung cả font; %d họ chữ, %d chữ nhận trục họ' % (ANG, len(rep), n))
for r in rep: print('  ' + r)
