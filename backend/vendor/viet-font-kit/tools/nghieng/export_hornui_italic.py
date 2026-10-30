"""Dữ liệu khung kéo (mục B) cho font NGHIÊNG — cùng khuôn hornui.json của export_preview + export_horn5 + tone_split,
nhưng mọi toạ độ ở không gian dựng thẳng (x' = x - y·tan góc); trang nghiêng lại cả chữ bằng D.slant.
Chỉ dùng fontTools. usage: export_hornui_italic.py FONT_VN.otf SRC.otf horn5.json OUT.json"""
import sys, os, json, math, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import contours, unslant, bounds, cb, flat, xs_at
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
FONT, SRC, H5, OUT = sys.argv[1:5]
ANGLE = float(sys.argv[5]) if len(sys.argv) > 5 else None   # góc trục chuẩn đã đo (recipes.json 'axis')
f = TTFont(FONT); gs = f.getGlyphSet(); cm = f.getBestCmap()
s = TTFont(SRC); sgs = s.getGlyphSet(); scm = s.getBestCmap()
T = math.tan(math.radians(ANGLE if ANGLE is not None else -f['post'].italicAngle))
def U(gset, n): return unslant(contours(gset, n), T)
def d_of(cs):
    p = SVGPathPen(None)
    for c in cs:
        for op, pts in c: getattr(p, op)(*[(round(x, 1), round(y, 1)) for x, y in pts])
    return p.getCommands()
B0, BS, NB = -320, 16, 103
def prof(cs):
    L, R = [], []
    segs = []
    for c in cs:
        P = flat(c, 16)
        for i in range(len(P)): segs.append((P[i], P[(i + 1) % len(P)]))
    for i in range(NB):
        y = B0 + i * BS; xs = []
        for (x0, y0), (x1, y1) in segs:
            lo, hi = min(y0, y1), max(y0, y1)
            if hi < y or lo > y + BS: continue
            for yy in (max(lo, y), min(hi, y + BS)):
                xs.append(x0 if y1 == y0 else x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
        if xs: L.append(round(min(xs))); R.append(round(max(xs)))
        else: L.append(None); R.append(None)
    return L, R
TONE = {'́': 's', '̀': 'f', '̉': 'r', '̃': 'x'}
VN = "aăâbcdđeêghiklmnoôơpqrstuưvxyAĂÂBCDĐEÊGHIKLMNOÔƠPQRSTUƯVXYfjwzFJWZ0123456789.,;:!?'\"()-–—/&%·…“”‘’«»*+=#@"
chars = set(VN)
for cp in cm:
    ch = chr(cp); d = unicodedata.normalize('NFD', ch)
    if len(d) > 1 and d[0].lower() in 'aeiouy' and all(m in '̛̣̀́̃̉̂̆' for m in d[1:]): chars.add(ch)
plain_top = {}
def ptop(L):
    if L not in plain_top:
        n = scm[ord(L)] if ord(L) in scm else cm[ord(L)]
        plain_top[L] = bounds(U(sgs if ord(L) in scm else gs, n))[3]
    return plain_top[L]
REC = json.load(open(os.environ['RECIPES'])) if os.environ.get('RECIPES') else None
def rops(cs): return [[(op, [None if q is None else tuple(q) for q in pts]) for op, pts in c] for c in cs]
def unslant_n(cs, t): return [[(op, [None if q is None else (q[0] - q[1] * t, q[1]) for q in pts]) for op, pts in c] for c in cs]
G = {}
for ch in sorted(chars):
    if ord(ch) not in cm: continue
    d = unicodedata.normalize('NFD', ch); horn = '̛' in d; dot = '̣' in d
    src = unicodedata.normalize('NFC', d.replace('̛', '')) if horn else ch
    cs = U(gs, cm[ord(src)]); e = {'w': gs[cm[ord(src)]].width}
    if dot:
        dc = [c for c in cs if cb(c)[3] < -20]; cs = [c for c in cs if cb(c)[3] >= -20]
        b = bounds(dc); e['dot'] = round((b[0] + b[2]) / 2, 1)
    tones = [TONE[m] for m in d if m in TONE]
    L0 = d[0]; base = 'dotlessi' if L0 == 'i' else L0
    top = bounds(U(gs, 'dotlessi' if L0 == 'i' else cm[ord(L0)]))[3]
    if tones:
        e['t'] = tones[0]
        up = sorted([c for c in cs if cb(c)[1] > top - 5], key=lambda c: cb(c)[1])
        if up:
            mk = [up[-1]]                                   # dấu thanh = dấu cao nhất (ấ: trên / phải dấu mũ)
            cs = [c for c in cs if c is not mk[0]]
            e['m'] = d_of(mk)
            pts = []
            for c in mk: pts += flat(c, 8)[::2]
            e['mp'] = [[round(x), round(y)] for x, y in pts]
    if horn:
        e['h'] = L0
        # nét THẬT của chữ có râu (râu đã ghép trong font) — trang vẽ nét này khi thanh râu chưa đổi, khỏi lệch với Xem trước
        rc = U(gs, cm[ord(ch)]); rtop = bounds(U(gs, cm[ord(unicodedata.normalize('NFC', L0 + '̛'))]))[3] if tones else None
        if dot: rc = [c for c in rc if cb(c)[3] >= -20]
        if tones:
            ru = sorted([c for c in rc if cb(c)[1] > rtop - 5], key=lambda c: cb(c)[1])
            if ru: e['rm'] = d_of([ru[-1]]); rc = [c for c in rc if c is not ru[-1]]
        e['rd'] = d_of(rc); e['rw'] = gs[cm[ord(ch)]].width
        # râu RỜI (RECIPES=… từ tools/nghieng/tt/build_it.py): thân không râu + hình râu riêng → Chi tiết tô đỏ râu được
        if REC and cm[ord(ch)] in REC['glyphs']:
            rr = REC['glyphs'][cm[ord(ch)]]
            hm = [m for m in rr['marks'] if m['m'].startswith('horn')]
            if hm:
                st = unslant_n(rops(rr['static']), T)
                if tones:   # dấu thanh nằm trong phần tĩnh (dấu hỏi chép riêng từng chữ) → tách ra rm để tô đỏ / chỉnh dáng được (28/10)
                    su = sorted([c for c in st if cb(c)[1] > top - 5], key=lambda c: cb(c)[1])
                    if su: e['rm'] = d_of([su[-1]]); st = [c for c in st if c is not su[-1]]
                e['rd'] = d_of(st)
                t = hm[0]['t']; hc = [[(op, [None if q is None else (t[0] * q[0] + t[2] * q[1] + t[4], t[1] * q[0] + t[3] * q[1] + t[5]) for q in pts]) for op, pts in c] for c in rops(REC['marks'][hm[0]['m']])]
                e['rh'] = d_of(unslant_n(hc, T))
    e['d'] = d_of(cs); G[ch] = e
    e['lp'] = prof(U(gs, cm[ord(ch)]))[0]
    if horn: e['rp'] = prof(U(gs, cm[ord(src)]))[1]
H = json.load(open(H5))
ui = {'all': H['all'], 'lc_ratio': H.get('lc_ratio', 0.9), 'lc_wratio': H.get('lc_wratio', 0.9), 'g': {}}
if H.get('hook_params') and os.path.exists(H['hook_params']): ui['hook'] = json.load(open(H['hook_params']))   # nhóm thanh “Dấu hỏi” ở khung kéo
else: ui['hook_tf'] = True   # dấu hỏi chép từ bản đứng → Chi tiết chỉnh dáng nét thật (bề ngang, cao, dày đầu / đuôi móc; hook_tf.py)
for L in 'UOuo':
    body = U(sgs, scm[ord(L)]); g = {'d': d_of(body), 'w': sgs[scm[ord(L)]].width}
    top = bounds(U(sgs, scm[ord('U' if L.isupper() else 'u')]))[3]
    if L in 'uU': g['x0'] = round(max(xs_at(body, top - 60)), 1); g['top'] = top
    else:
        B = bounds(body); g['oy'] = [int(B[1] + (B[3] - B[1]) * 0.5), int(B[3]) - 1]
        g['ox'] = [round(max(xs_at(body, y + 0.01) or [0]), 1) for y in range(g['oy'][0], g['oy'][1] + 1)]
    ui['g'][L] = g
ui['tone_gap'] = float(os.environ.get('TONE_GAP', 28))   # khe dấu thanh ↔ râu khi kéo thanh râu (cùng số với lúc dựng)
ui['G'] = G; ui['space'] = gs[cm[32]].width; ui['band'] = [B0, BS, NB]; ui['slant'] = round(T, 5)
ic = U(sgs, scm[ord('i')]); _st = bounds(U(sgs, scm[0x131]))[3] if 0x131 in scm else 560
idot = [c for c in ic if cb(c)[1] > _st - 20] or [max(ic, key=lambda c: cb(c)[1])]; ib = bounds(idot)   # A23: chấm i = contour trên đỉnh thân ı, đo trên font
ui['ndot'] = {'d': d_of([[(op, [(x - (ib[0] + ib[2]) / 2, y - (ib[1] + ib[3]) / 2) for x, y in pts]) for op, pts in c] for c in idot]),
              'w': round(ib[2] - ib[0]), 'h': round(ib[3] - ib[1])}
pb = bounds(U(sgs, scm[ord('.')])); ui['period'] = [round(pb[2] - pb[0]), round(pb[3] - pb[1])]
# đường dóng dấu hỏi (hoa / thường) đo trên chính font
def hook_y(ch, base):
    cs = U(gs, cm[ord(ch)]); top = bounds(U(gs, cm[ord(base)]))[3]
    b = bounds([c for c in cs if cb(c)[1] > top - 5]); return [round(b[1]), round(b[3])]
ui['guide'] = [hook_y('Ả', 'A'), hook_y('ả', 'a')]
json.dump(ui, open(OUT, 'w'), separators=(',', ':'), ensure_ascii=False)
print('hornui nghiêng:', len(G), 'chữ,', os.path.getsize(OUT) // 1024, 'KB · đường dóng', ui['guide'])
