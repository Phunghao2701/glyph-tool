"""Việt hoá font nghiêng bằng cách chuyển quan hệ đặt dấu từ bản đứng đã Việt hoá (VER người dùng chốt) sang bản nghiêng.
Mọi phép đặt dấu làm trong "không gian dựng thẳng" (x' = x - y·tan góc nghiêng), rồi nghiêng lại → dấu nằm trên trục nghiêng.
Dấu sắc / huyền / ngã / mũ / trăng: lấy từ chính font nghiêng. Dấu hỏi + râu: lấy từ bản đứng VN (đã chốt), nghiêng theo trục.
Dấu nặng: chấm chữ i của font nghiêng.
usage: build_italic.py SRC_ITALIC.otf REF_UPRIGHT_VN.otf OUT.otf CONFIG.json [RECIPES_OUT.json]
Chỉ dùng fontTools (môi trường không có skia-pathops / shapely): nét râu được nối thẳng vào contour, thanh đ Đ chồng lên thân (non-zero)."""
import sys, os, json, math, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import contours, xform, unslant, slant, move, bounds, cb, area, flat, xs_at, mindist
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.otlLib.builder import buildLigatureSubstSubtable
from fontTools.ttLib.tables import otTables as ot

SRC, REF, OUT, CFGP = sys.argv[1:5]
RECOUT = sys.argv[5] if len(sys.argv) > 5 else None
CFG = json.load(open(CFGP))
it = TTFont(SRC); rf = TTFont(REF)
I = it.getGlyphSet(); R = rf.getGlyphSet()
ORIG = set(it.getGlyphOrder())
ANG_POST = -it["post"].italicAngle                 # góc khai trong font (15)
def stem_angle():
    """góc nghiêng THẬT của font: khớp đường tâm các nét đứng thẳng (l ı I H T E b p), lấy trung vị"""
    import numpy as np
    cmI = it.getBestCmap(); out = []
    for ch, n, y0, y1, pick in [('l', 'l', 150, 700, 'w'), ('ı', 'dotlessi', 150, 550, 'w'), ('I', 'I', 150, 700, 'w'), ('H', 'H', 100, 350, 'f'),
                                ('H', 'H', 100, 350, 'l'), ('T', 'T', 100, 700, 'w'), ('E', 'E', 100, 350, 'f'), ('b', 'b', 150, 700, 'f'), ('p', 'p', -150, 450, 'f')]:
        if n not in I: continue
        cs = contours(I, n); ys, xs = [], []
        for y in np.linspace(y0, y1, 25):
            X = xs_at(cs, y); pr = [(X[i], X[i + 1]) for i in range(0, len(X) - 1, 2)]
            if not pr: continue
            a, b_ = max(pr, key=lambda q: q[1] - q[0]) if pick == 'w' else (pr[0] if pick == 'f' else pr[-1])
            ys.append(y); xs.append((a + b_) / 2)
        out.append(math.degrees(math.atan(np.polyfit(ys, xs, 1)[0])))
    return float(np.median(out)), out
AXIS_MODE = CFG.get('axis', 'mark')                # 'body' = một trục chuẩn cho cả font (góc đo từ nét đứng)
ANG_MEAS, ANG_LIST = stem_angle()
ANG = ANG_MEAS if AXIS_MODE == 'body' else ANG_POST
T = math.tan(math.radians(ANG))
icm = it.getBestCmap(); rcm = rf.getBestCmap()
rname = {v: k for k, v in rcm.items()}

def IU(n): return unslant(contours(I, n), T)        # italic, dựng thẳng
def RC(n): return contours(R, n)                     # bản đứng VN

BASEG = dict(a='a', e='e', i='dotlessi', o='o', u='u', y='y', A='A', E='E', I='I', O='O', U='U', Y='Y', d='d', D='D')
CIRCG = dict(a='acircumflex', e='ecircumflex', i='icircumflex', o='ocircumflex', u='ucircumflex', y='ydieresis',
             A='Acircumflex', E='Ecircumflex', I='Icircumflex', O='Ocircumflex', U='Ucircumflex', Y='Ydieresis')
KIND = {0x300: 'grave', 0x301: 'acute', 0x302: 'circ', 0x303: 'tilde', 0x306: 'breve', 0x309: 'hook', 0x323: 'dot', 0x31B: 'horn'}

def split(cs, base_cs):
    """→ (thân, dấu trên, dấu dưới) theo độ cao so với chữ gốc"""
    top = bounds(base_cs)[3]; body, up, dn = [], [], []
    for c in cs:
        b = cb(c)
        if b[1] > top - 5: up.append(c)
        elif b[3] < -20: dn.append(c)
        else: body.append(c)
    return body, up, dn
def bc(b): return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
def W(b): return b[2] - b[0]
def H(b): return b[3] - b[1]

def axis_info(getc, b):
    base = getc(BASEG[b]); body, up, _ = split(getc(CIRCG[b]), base)
    shift = bounds(body)[0] - bounds(base)[0]
    mb = bounds(up)
    return dict(ax=(mb[0] + mb[2]) / 2 - shift, ml=mb[1], top=bounds(base)[3], bb=bounds(base), circ=mb)
AXI = {b: axis_info(IU, b) for b in CIRCG}
AXR = {b: axis_info(RC, b) for b in CIRCG}

def mark_in(getc, gname, b, which=0):
    """dấu trên thứ `which` (xếp theo ymin) của glyph gname trên gốc b, đã trừ độ dời thân"""
    base = getc(BASEG[b]); body, up, dn = split(getc(gname), base)
    shift = bounds(body)[0] - bounds(base)[0]
    up = sorted(up, key=lambda c: cb(c)[1])
    return [move([c], -shift, 0)[0] for c in up], [move([c], -shift, 0)[0] for c in dn]

def band_cx(cs, L):
    """tâm khối chữ (dựng thẳng) ở dải 20–80 % chiều cao: mép mực trái nhất ↔ phải nhất; i I chỉ lấy nét đứng"""
    top = bounds(cs)[3]; lo, hi, xs = 1e9, -1e9, []
    for k in range(13):
        y = top * (0.2 + 0.6 * k / 12); X = xs_at(cs, y)
        if len(X) < 2: continue
        if L in 'iI':
            pr = [(X[i], X[i + 1]) for i in range(0, len(X) - 1, 2)]; a, c = max(pr, key=lambda q: q[1] - q[0]); xs.append((a + c) / 2)
        else: lo, hi = min(lo, X[0]), max(hi, X[-1])
    return sum(xs) / len(xs) if L in 'iI' else (lo + hi) / 2
# TRỤC CHUẨN mỗi chữ gốc (chế độ 'body'): tâm khối + hiệu chỉnh thị giác của chính chữ đó lấy từ bản đứng đã chốt
# (bản đứng: dấu mũ lệch tâm khối a +21, E −15, còn lại ≈ 0) → MỘT đường trục nghiêng ANG đi qua đó, mọi dấu trên / dưới nằm trên nó.
AXB = {L: band_cx(IU(BASEG[L]), L) + (AXR[L]['ax'] - band_cx(RC(BASEG[L]), L)) for L in CIRCG}
def ref_off(kind, caps):
    """độ lệch CHUẨN của một loại dấu so với trục (một số cho cả font): trung vị trên các chữ của bản đứng"""
    vals = []
    for L in ('AEIOUY' if caps else 'aeiouy'):
        m = {'acute': '\u0301', 'grave': '\u0300', 'hook': '\u0309', 'tilde': '\u0303', 'circ': '\u0302', 'breve': '\u0306', 'dot': '\u0323'}[kind]
        ch = unicodedata.normalize('NFC', L + m)
        if len(ch) != 1 or ord(ch) not in rcm: continue
        up, dn = mark_in(RC, rcm[ord(ch)], L); mk = dn if kind == 'dot' else up
        if not mk: continue
        vals.append(bc(cb(mk[0]))[0] - band_cx(RC(BASEG[L]), L) - (AXR[L]['ax'] - band_cx(RC(BASEG[L]), L)))
    vals.sort(); return vals[len(vals) // 2] if vals else 0.0
OFF = {(k, c): ref_off(k, c) for k in ('acute', 'grave', 'hook', 'tilde', 'circ', 'breve', 'dot') for c in (0, 1)}

# ---------- dấu chuẩn (trên a / A) ----------
STD_G = {('acute', 0): 'aacute', ('grave', 0): 'agrave', ('tilde', 0): 'atilde', ('circ', 0): 'acircumflex',
         ('acute', 1): 'Aacute', ('grave', 1): 'Agrave', ('tilde', 1): 'Atilde', ('circ', 1): 'Acircumflex'}
REF_STD_G = dict(STD_G); REF_STD_G.update({('breve', 0): 'uni0103', ('breve', 1): 'uni0102', ('hook', 0): 'uni1EA3', ('hook', 1): 'uni1EA2'})
REF_DOT_G = {0: 'uni1EA1', 1: 'uni1EA0'}
ab = lambda caps: 'A' if caps else 'a'
STD_R = {}
for (k, caps), g in REF_STD_G.items():
    up, _ = mark_in(RC, g, ab(caps)); m = up[0]; b = cb(m); a = AXR[ab(caps)]
    STD_R[(k, caps)] = dict(c=m, b=b, off=bc(b)[0] - a['ax'], rely=b[1] - a['ml'])
for caps, g in REF_DOT_G.items():
    _, dn = mark_in(RC, g, ab(caps)); b = cb(dn[0]); STD_R[('dot', caps)] = dict(c=dn[0], b=b, off=bc(b)[0] - AXR[ab(caps)]['ax'], rely=b[3])
STD_I = {}
for (k, caps), g in STD_G.items():
    up, _ = mark_in(IU, g, ab(caps)); m = up[0]; b = cb(m); a = AXI[ab(caps)]
    STD_I[(k, caps)] = dict(c=m, b=b, off=bc(b)[0] - a['ax'], rely=b[1] - a['ml'])
# trăng: dấu breve rời của font nghiêng, đặt như bản đứng đặt (so với dấu mũ)
brv = IU('breve')[0]
for caps in (0, 1):
    r = STD_R[('breve', caps)]; rr = STD_R[('circ', caps)]
    rs = cb(RC('breve')[0]); sx, sy = W(r['b']) / W(rs), H(r['b']) / H(rs)
    STD_I[('breve', caps)] = dict(c=brv, b=cb(brv), off=r['off'], rely=r['rely'] - rr['rely'] + STD_I[('circ', caps)]['rely'], scale0=(sx, sy))
# hỏi: dấu hỏi bản đứng VN (đã chốt), x theo trục (như dấu mũ), y theo dấu sắc của font nghiêng
for caps in (0, 1):
    r = STD_R[('hook', caps)]
    STD_I[('hook', caps)] = dict(c=r['c'], b=r['b'], off=r['off'] - STD_R[('circ', caps)]['off'] + STD_I[('circ', caps)]['off'],
                                 rely=r['rely'] - STD_R[('acute', caps)]['rely'] + STD_I[('acute', caps)]['rely'] + CFG.get('hook_dy', [0, 0])[caps])
# nặng: chấm chữ i của font nghiêng
_, iu, _ = split(IU('i'), IU('dotlessi')); idot = iu[0]; idot_it = idot
for caps in (0, 1):
    r = STD_R[('dot', caps)]
    STD_I[('dot', caps)] = dict(c=idot, b=cb(idot), off=r['off'], rely=r['rely'] + CFG.get('dot_dy', 0))

def place(c, src_b, cx, y0, sx=1.0, sy=1.0, ytop=False):
    """đặt contour c (khung src_b) có tâm x = cx, đáy = y0 (hoặc đỉnh nếu ytop), co giãn sx sy"""
    ox, oy = bc(src_b)[0], (src_b[3] if ytop else src_b[1])
    out = xform([c], lambda x, y: (cx + (x - ox) * sx, y0 + (y - oy) * sy))[0]
    t = (sx, 0, 0, sy, cx - ox * sx, y0 - oy * sy)      # affine (dựng thẳng)
    return out, t
def shape_of(k, caps, stacked=False):
    if k == 'hook':
        return STD_I[('hook', caps)]['c'], STD_I[('hook', caps)]['b']
    s = STD_I[(k, caps)]; return s['c'], s['b']

def body_cx(cs, b):
    """tâm thân chữ (dựng thẳng) đo ở 8–40 % chiều cao: i I lấy cặp mép dày nhất (nét đứng, bỏ đuôi / chân serif), chữ khác lấy cả bề ngang"""
    top = bounds(cs)[3]; xs = []
    for k in range(9):
        y = top * (0.08 + 0.32 * k / 8); X = xs_at(cs, y)
        if len(X) < 2: continue
        if b in 'iI':
            pr = [(X[i], X[i + 1]) for i in range(0, len(X) - 1, 2)]; a, c = max(pr, key=lambda q: q[1] - q[0]); xs.append((a + c) / 2)
        else: xs.append((X[0] + X[-1]) / 2)
    return sum(xs) / len(xs)

# ---------- dựng một chữ (không râu) ----------
def decomp(ch):
    d = unicodedata.normalize('NFD', ch); return d[0], [KIND[ord(m)] for m in d[1:]]
SAFE = []                                 # ghi chú kiểm tra
GAPSTD = {}                               # khe dấu chồng chuẩn (đo trên a / A)
def build_plain(ch):
    """chữ có dấu trên chữ gốc a e i o u y (không râu). → (contours dựng thẳng, width, inst marks)"""
    L, ks = decomp(ch); caps = int(L.isupper()); b = L
    rg = rcm[ord(ch)]
    base = IU(BASEG[b]); width = I[BASEG[b]].width
    rup, rdn = mark_in(RC, rg, b)
    tops = [k for k in ks if k not in ('dot',)]
    if L == 'i' and not tops: base = IU('i'); width = I['i'].width     # ị giữ chấm i
    out = list(base); inst = []
    prim_it = None
    for j, k in enumerate(tops):
        mref = rup[j]; br = cb(mref)
        if j == 0 or not CFG.get('stack'):
            stdR = STD_R[(k, caps)]; stdI = STD_I[(k, caps)]
            sx, sy = W(br) / W(stdR['b']), H(br) / H(stdR['b'])
            if 'scale0' in stdI: sx, sy = sx * stdI['scale0'][0], sy * stdI['scale0'][1]
            dx = bc(br)[0] - AXR[b]['ax'] - stdR['off']
            dy = br[1] - AXR[b]['ml'] - stdR['rely']
            cx = AXI[b]['ax'] + stdI['off'] + dx
            if AXIS_MODE == 'body': cx = AXB[b] + OFF[(k, caps)]
            y0 = AXI[b]['ml'] + stdI['rely'] + dy
        if j == 1:
            # dấu thanh chồng: giữ quan hệ với dấu mũ / trăng như bản đứng
            rup_u = rup
            if CFG.get('stack_rule') in ('as_circ', 'axis') and tops[0] == 'breve':
                # dấu thanh trên dấu trăng đặt Y NHƯ trên dấu mũ cùng cỡ chữ (lấy quan hệ của ấ ầ ẩ ẫ trong bản đứng)
                chc = unicodedata.normalize('NFC', L + '\u0302' + {'acute': '\u0301', 'grave': '\u0300', 'hook': '\u0309', 'tilde': '\u0303'}[k])
                rup_u, _ = mark_in(RC, rcm[ord(chc)], b); mref = rup_u[1]; br = cb(mref)
            pr = cb(rup_u[0]); stdR = STD_R[(k, caps)]; stdI = STD_I[(k, caps)]
            sx, sy = W(br) / W(stdR['b']), H(br) / H(stdR['b'])
            pi = prim_it
            mode = CFG.get('stack_mode', {}).get(k) or ('top' if br[1] >= pr[3] - 3 else 'right')
            c0, b0 = shape_of(k, caps, True)
            if mode == 'top':
                if br[1] >= pr[3] - 3:
                    gap = br[1] - pr[3]; cx = bc(pi)[0] + (bc(br)[0] - bc(pr)[0])
                else:   # phương án "mọi dấu trên đỉnh" cho dấu vốn đặt bên phải
                    gap = CFG.get('top_gap', {}).get(k, 30); cx = bc(pi)[0] + stdI['off'] - STD_I[('circ', caps)]['off']
                y0 = pi[3] + gap
            else:
                w_it = W(b0) * sx
                xmin = pi[2] + (br[0] - pr[2]); cx = xmin + w_it / 2
                y0 = pi[1] + (br[1] - pr[1])
            if CFG.get('stack_rule') == 'axis':
                # mọi dấu thanh chồng: tâm trên trục chữ (+ độ lệch chuẩn của loại dấu), khe dọc chuẩn theo loại dấu, mọi cỡ chữ
                cx = bc(pi)[0] + OFF[(k, caps)]
                y0 = pi[3] + CFG.get('stack_gapv', {'acute': 28, 'grave': 28, 'hook': 40, 'tilde': 20})[k]
                mode = 'top'
        c0, b0 = shape_of(k, caps)
        m, t = place(c0, b0, cx, y0, sx, sy)
        if j == 1 and mode in ('right', 'top'):
          if mode == 'right' and CFG.get('contain', True) and (b in 'aA' or not CFG.get('even_stack', True)):
            # giữ dấu trong 2 biên advance như bản đứng (Word / Excel không kern), rồi giữ khe với dấu mũ
            lim = width + (br[2] - R[rg].width)
            if cb(m)[2] > lim:
                cx -= cb(m)[2] - lim; m, t = place(c0, b0, cx, y0, sx, sy)
          if True:
            gmin = CFG.get('stack_gap_ag', 18); n_ = 0
            pm = slant([out[-1]], T); pb = cb(out[-1])
            key = (k, caps, tops[0])
            if CFG.get('even_stack', True) and b not in 'aA' and key in GAPSTD:
                # dấu mũ + dấu thanh là MỘT khối cố định: dấu thanh đặt đúng như trên a / A so với dấu mũ / trăng
                # → khe ề = ầ = ồ (không co theo bề rộng chữ); phần chìa khỏi advance ghi vào số đo
                cx, y0 = bc(pb)[0] + GAPSTD[key][0], pb[1] + GAPSTD[key][1]
                m, t = place(c0, b0, cx, y0, sx, sy)
            while mindist(pm, slant([m], T)) < gmin and n_ < 40:
                y0 += 4; n_ += 1; m, t = place(c0, b0, cx, y0, sx, sy)
            if n_: SAFE.append('%s nâng %d' % (ch, 4 * n_))
            if b in 'aA': GAPSTD[key] = (cx - bc(pb)[0], y0 - pb[1])
            SAFE.append('%s khe %.0f' % (ch, mindist(pm, slant([m], T))))
        if j == 0: prim_it = cb(m)
        out.append(m); inst.append((k if not (k == 'hook' and j == 1) else 'hook_s', c0, b0, t))
    if 'dot' in ks:
        mref = rdn[0]; br = cb(mref); stdR = STD_R[('dot', caps)]; stdI = STD_I[('dot', caps)]
        dx = bc(br)[0] - AXR[b]['ax'] - stdR['off']
        if L in 'yY': dx += CFG.get('dot_y_dx', {}).get(L, 0)
        cx = AXI[b]['ax'] + stdI['off'] + dx
        if AXIS_MODE == 'body': cx = AXB[b] + (OFF[('dot', caps)] if L not in 'yY' else 0)   # cùng trục với dấu trên
        if AXIS_MODE == 'body' and L == 'i' and not tops and CFG.get('i_dot_axis', 'tittle') == 'tittle':
            # ị: đo thân i (tâm nét đứng ở dải giữa) rồi so với chấm i trên đầu → trục của chính chữ i đi qua 2 tâm đó;
            # dấu nặng đặt trên đường đó ở độ cao của dấu nặng (chấm i lệch trái thân bao nhiêu thì dấu nặng cân lại phía dưới)
            stem = IU('dotlessi'); ys_ = bounds(stem)[3] * 0.5; xs_ = band_cx(stem, 'i')
            xt, yt = bc(cb(idot_it))
            yd = (br[1] + br[3]) / 2
            cx = xs_ + (yd - ys_) * (xt - xs_) / (yt - ys_)
            SAFE.append('ị trục thân %.0f, chấm i %.0f → dấu nặng %.0f' % (xs_, xt, cx))
        elif L not in 'yY':
            cx = body_cx(IU(BASEG[b]), b) + (0 if b in 'iI' else bc(br)[0] - body_cx(RC(BASEG[b]), b))
        m, t = place(stdI['c'], stdI['b'], cx, br[3] + CFG.get('dot_dy', 0), 1, 1, ytop=True)
        if L in 'yY':   # ỵ Ỵ: dời phải tới khi cách nét đuôi đủ khe (đo trên nét nghiêng thật)
            g = CFG.get('dot_y_gap', 40); n_ = 0
            while mindist(slant([m], T), slant(base, T)) < g and n_ < 60:
                cx += 4; n_ += 1; m, t = place(stdI['c'], stdI['b'], cx, br[3] + CFG.get('dot_dy', 0), 1, 1, ytop=True)
            SAFE.append('%s dời phải %d' % (ch, 4 * n_))
        out.append(m); inst.append(('dot', stdI['c'], stdI['b'], t))
    return out, width, inst, len(base)

# ---------- râu ----------
def cubic_pt(p0, p1, p2, p3, t):
    mt = 1 - t
    return tuple(mt**3 * p0[i] + 3 * mt * mt * t * p1[i] + 3 * mt * t * t * p2[i] + t**3 * p3[i] for i in (0, 1))
def split_cubic(p0, p1, p2, p3, t):
    L = lambda a, b: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b_, c = L(p0, p1), L(p1, p2), L(p2, p3); d, e = L(a, b_), L(b_, c); f = L(d, e)
    return (p0, a, d, f), (f, e, c, p3)
def t_at_y(p0, p1, p2, p3, y):
    lo, hi = 0.0, 1.0; up = p3[1] > p0[1]
    for _ in range(60):
        m = (lo + hi) / 2
        if (cubic_pt(p0, p1, p2, p3, m)[1] < y) == up: lo = m
        else: hi = m
    return (lo + hi) / 2
def segs(c):
    """contour → list of (op, pts, start)"""
    out = []; cur = None
    for op, pts in c:
        if op == 'moveTo': cur = pts[0]; continue
        if op == 'closePath': continue
        out.append([op, list(pts), cur]); cur = pts[-1]
    return out
def rebuild(sg):
    c = [('moveTo', [sg[0][2]])]
    for op, pts, _ in sg: c.append((op, pts))
    c.append(('closePath', [])); return c
def ref_horn(name, base, start, end):
    """lấy đoạn râu (từ điểm start tới điểm end) trong contour bản đứng"""
    for c in RC(name):
        sg = segs(c); pts = [s[1][-1] for s in sg]
        def idx(p): return min(range(len(pts)), key=lambda i: math.dist(pts[i], p))
        i0, i1 = idx(start), idx(end)
        if math.dist(pts[i0], start) < 1 and math.dist(pts[i1], end) < 1:
            return [(op, p) for op, p, _ in sg[i0 + 1:i1 + 1]], pts[i0]
    raise SystemExit('no horn in ' + name)
HR = {'u': ref_horn('uni01B0', 'u', (439, 560), (440, 597)), 'U': ref_horn('uni01AF', 'U', (496, 787), (513, 842)),
      'o': ref_horn('uni01A1', 'o', (384, 564), (359, 589)), 'O': ref_horn('uni01A0', 'O', (407, 791), (381, 813))}
HDY = {L: bounds(IU(L))[3] - bounds(RC(L))[3] for L in 'uU'}      # độ nâng gốc râu để Ư = Ơ, ư = ơ cùng đỉnh
def splice(L, body):
    """nối râu vào contour ngoài của thân (dựng thẳng). → (thân mới, contour râu khép kín cho bàn vẽ, xmax râu)"""
    horn, s_ref = HR[L]
    outer_i = max(range(len(body)), key=lambda i: abs(area(body[i])))
    sg = segs(body[outer_i]); new = None
    def tr(d): return [(op, [(x + d[0], y + d[1]) for x, y in p]) for op, p in horn]
    if L in 'uU':
        top = bounds(body)[3]
        if L == 'u':
            # cạnh phải nét đứng phải: đoạn cong kết thúc ở góc trên phải
            k = max((i for i in range(len(sg)) if sg[i][0] == 'curveTo' and sg[i][1][-1][1] > top - 12), key=lambda i: sg[i][1][-1][0])
            p0 = sg[k][2]; p1, p2, p3 = sg[k][1]
            ys = s_ref[1] + HDY['u']                             # cùng khoảng cách tới đỉnh như bản đứng
            a, b_ = split_cubic(p0, p1, p2, p3, t_at_y(p0, p1, p2, p3, ys))
            S = a[3]; d = (S[0] - s_ref[0], S[1] - s_ref[1]); H_ = tr(d)
            E = H_[-1][1][-1]
            new = sg[:k] + [['curveTo', [a[1], a[2], a[3]], p0]] + [[op, p, None] for op, p in H_] + [['lineTo', [p3], E]] + sg[k + 1:]
        else:
            # U: nét đứng phải lên tới chân chân phải (serif) → thay serif phải bằng râu như bản đứng
            k = next(i for i in range(len(sg)) if sg[i][0] == 'curveTo' and sg[i][2][1] < 600 and sg[i][1][-1][1] > 780 and sg[i][1][-1][0] > 400)
            p0 = sg[k][2]; p1, p2, p3 = sg[k][1]
            a, b_ = split_cubic(p0, p1, p2, p3, t_at_y(p0, p1, p2, p3, s_ref[1] + HDY['U']))
            S = a[3]; d = (S[0] - s_ref[0], S[1] - s_ref[1]); H_ = tr(d)
            j = k + 1
            while not (sg[j][0] == 'lineTo' and abs(sg[j][1][0][1] - top) < 2 and sg[j][1][0][0] < S[0] - 40): j += 1
            new = sg[:k] + [['curveTo', [a[1], a[2], a[3]], p0]] + [[op, p, None] for op, p in H_] + sg[j:]
    else:
        lc = L == 'o'; target_dy = HDY['u' if lc else 'U']
        ys = s_ref[1] + target_dy
        # đoạn cong góc trên phải của contour ngoài: đi từ mép phải (y giữa) lên đỉnh
        k = next(i for i in range(len(sg)) if sg[i][0] == 'curveTo' and sg[i][2][1] < ys < sg[i][1][-1][1] and sg[i][2][0] > sg[i][1][-1][0])
        p0 = sg[k][2]; p1, p2, p3 = sg[k][1]
        t1 = t_at_y(p0, p1, p2, p3, ys)
        a, rest = split_cubic(p0, p1, p2, p3, t1)
        S = a[3]; d = (S[0] - s_ref[0], S[1] - s_ref[1]); H_ = tr(d); E = H_[-1][1][-1]
        # điểm nối lại: điểm trên phần còn lại gần E nhất
        best = min((math.dist(cubic_pt(*rest, t), E), t) for t in [i / 400 for i in range(1, 400)])[1]
        _, tail = split_cubic(*rest, best)
        tail = (E, tail[1], tail[2], tail[3])
        new = sg[:k] + [['curveTo', [a[1], a[2], a[3]], p0]] + [[op, p, None] for op, p in H_] + [['curveTo', [tail[1], tail[2], tail[3]], E]] + sg[k + 1:]
    # sửa điểm đầu từng đoạn
    for i in range(len(new)):
        new[i][2] = new[i - 1][1][-1] if i else sg[0][2]
    if L in 'uU' and L == 'U' and new[0][2] != sg[0][2]: pass
    nb = list(body); nb[outer_i] = rebuild(new)
    # contour râu khép kín (cho bàn vẽ / dấu rời U+031B): râu + 2 cạnh lùi vào trong thân
    E = H_[-1][1][-1]; cl = CFG.get('clip', 36)
    hc = [('moveTo', [S])] + H_ + [('lineTo', [(E[0] - cl, E[1])]), ('lineTo', [(S[0] - cl, S[1])]), ('closePath', [])]
    return nb, hc, bounds([hc])[2], d

# ---------- dựng toàn bộ ----------
VN = ('aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữựyỳýỷỹỵ')
VN += VN.upper()
NEW = {}       # glyph name → dict(cs (dựng thẳng), w, inst, base, ch, static)
REBUILD = set()
if AXIS_MODE == 'body' and CFG.get('rebuild_native', True):
    # chữ Việt có sẵn trong font (á à â ã é …) cũng dựng lại cho nằm trên cùng một trục chuẩn
    REBUILD = {c for c in VN if ord(c) in icm and len(unicodedata.normalize('NFD', c)) > 1 and ord(c) in rcm}
def have_it(ch): return ord(ch) in icm and ch not in REBUILD
def get_u(ch):
    """contours dựng thẳng + width + inst của chữ ch (có sẵn hoặc vừa dựng)"""
    n = rcm[ord(ch)]
    if n in NEW: e = NEW[n]; return e['cs'], e['w'], e['inst']
    n = icm[ord(ch)]; return IU(n), I[n].width, None
    e = NEW[n]; return e['cs'], e['w'], e['inst']
order_build = [c for c in VN if '̛' not in unicodedata.normalize('NFD', c)] + [c for c in VN if '̛' in unicodedata.normalize('NFD', c)]
for ch in order_build:
    if have_it(ch): continue
    name = rcm[ord(ch)]
    d = unicodedata.normalize('NFD', ch)
    if '̛' not in d:
        cs, w, inst, nb0 = build_plain(ch)
        NEW[name] = dict(cs=cs, w=w, inst=inst, ch=ch, base=BASEG[d[0]], nstatic=nb0)
        continue
    # chữ có râu: chữ không râu + râu + dời dấu thanh như bản đứng
    L = d[0]; ch0 = unicodedata.normalize('NFC', d.replace('̛', ''))
    cs0, w0, inst0 = get_u(ch0)
    base = IU(BASEG[L]); body, up, dn = split(cs0, base)
    # dấu thanh của bản đứng: chữ râu so với chữ không râu
    rb = RC(BASEG[L]); _, rup1, _ = split(RC(name), rb); _, rup0, _ = split(RC(rcm[ord(ch0)]), rb)
    up2 = []
    for j, m in enumerate(sorted(up, key=lambda c: cb(c)[1])):
        b1, b0 = cb(sorted(rup1, key=lambda c: cb(c)[1])[j]), cb(sorted(rup0, key=lambda c: cb(c)[1])[j])
        sx, sy = W(b1) / W(b0), H(b1) / H(b0); bm = cb(m)
        mm, _ = place(m, bm, bc(bm)[0] + (bc(b1)[0] - bc(b0)[0]), bm[1] + (b1[1] - b0[1]), sx, sy)
        up2.append(mm)
    nb, hc, hx, dh = splice(L, body)
    gh = CFG.get('horn_tone_gap', 28)
    for j, mm in enumerate(up2):    # dấu thanh né râu: dời trái tối đa 40 rồi mới nâng
        dx_ = dy_ = 0
        while mindist(slant(nb, T), slant([mm], T)) < gh and dy_ < 160:
            if dx_ < 40: dx_ += 4; mm = move([mm], -4, 0)[0]
            else: dy_ += 4; mm = move([mm], 0, 4)[0]
        up2[j] = mm
        if dx_ or dy_: SAFE.append('%s dấu né râu ←%d ↑%d' % (ch, dx_, dy_))
    rw = R[name].width; rhx = bounds(RC(name))[2]
    w = max(w0, round(hx + (rw - rhx)) if rw > R[BASEG[L]].width else w0)
    # inst cho bàn vẽ
    inst = [('horn', hc, None, (1, 0, 0, 1, 0, 0))]
    for m in up2: inst.append(('tone', m, None, (1, 0, 0, 1, 0, 0)))
    for m in dn: inst.append(('dot', m, None, (1, 0, 0, 1, 0, 0)))
    NEW[name] = dict(cs=nb + up2 + dn, w=w, inst=inst, ch=ch, base=BASEG[L], static_cs=body, horn=hc, nstatic=len(body))

# ---------- đ Đ ----------
def bar_glyph(L, y_ref, thick):
    rg = 'dcroat' if L == 'd' else 'Dcroat'
    rx = xs_at(RC(L), y_ref); rxx = xs_at(RC(rg), y_ref)
    ix = xs_at(IU(L), y_ref)
    if L == 'd': l = ix[0] - (rx[0] - rxx[0]); r = ix[1] + (rxx[-1] - rx[1])
    else: l = ix[0] - (rx[0] - rxx[0]); r = ix[1] + (rxx[1] - rx[1])
    y0, y1 = y_ref - thick / 2, y_ref + thick / 2
    body = IU(L); outer = max(body, key=lambda c: abs(area(c)))
    cw = area(outer) > 0
    if CFG.get('merge_bar', True):
        return bar_splice(body, l, r, y0, y1, cw), I[L].width
    pts = [(l, y0), (r, y0), (r, y1), (l, y1)] if cw else [(l, y0), (l, y1), (r, y1), (r, y0)]
    bar = [('moveTo', [pts[0]])] + [('lineTo', [p]) for p in pts[1:]] + [('closePath', [])]
    return body + [bar], I[L].width
def bar_splice(body, l, r, y0, y1, ccw):
    """GỘP NÉT thanh ngang vào thân (không cần pathops): mỗi cạnh contour cắt ngang dải [y0, y1] trong khoảng [l, r]
    được thay bằng đường đi ra mép thanh ở phía trống rồi quay lại (vùng tô luôn nằm bên trái chiều đi nếu contour ngoài ngược chiều kim đồng hồ)"""
    out = []; n_sp = 0
    for c in body:
        sg = segs(c); start = sg[0][2]
        if sg[-1][1][-1] != start: sg.append(['lineTo', [start], sg[-1][1][-1]])
        new = []
        for op, pts, p0 in sg:
            p3 = pts[-1]; lo, hi = min(p0[1], p3[1]), max(p0[1], p3[1])
            if lo < y0 and hi > y1:
                up = p3[1] > p0[1]
                if op == 'curveTo':
                    ta, tb = t_at_y(p0, *pts, y0 if up else y1), t_at_y(p0, *pts, y1 if up else y0)
                    A, rest = split_cubic(p0, *pts, ta); tb2 = (tb - ta) / (1 - ta)
                    _, B = split_cubic(*rest, tb2)
                    PA, PB = A[3], B[0]
                else:
                    f = lambda y: (p0[0] + (y - p0[1]) * (p3[0] - p0[0]) / (p3[1] - p0[1]), y)
                    PA, PB = f(y0 if up else y1), f(y1 if up else y0)
                if l - 1 < PA[0] < r + 1:
                    ex = (r if up else l) if ccw else (l if up else r)       # phía trống của cạnh
                    if op == 'curveTo': new.append(['curveTo', [A[1], A[2], A[3]], p0])
                    else: new.append(['lineTo', [PA], p0])
                    new += [['lineTo', [(ex, PA[1])], None], ['lineTo', [(ex, PB[1])], None], ['lineTo', [PB], None]]
                    if op == 'curveTo': new.append(['curveTo', [B[1], B[2], B[3]], PB])
                    else: new.append(['lineTo', [p3], PB])
                    n_sp += 1; continue
            new.append([op, pts, p0])
        for i in range(len(new)): new[i][2] = new[i - 1][1][-1] if i else start
        out.append(rebuild(new))
    SAFE.append('thanh ngang gộp nét: %d cạnh' % n_sp)
    return out
eb = CFG.get('bar', 30)
for L, y in (('d', 734), ('D', 421)):
    n = 'dcroat' if L == 'd' else 'Dcroat'
    cs, w = bar_glyph(L, y + CFG.get('bar_dy', {}).get(L, 0), eb)
    NEW[n] = dict(cs=cs, w=w, inst=[], ch='đ' if L == 'd' else 'Đ', base=L, nstatic=len(cs))

# ---------- dấu tổ hợp (rộng 0) ----------
COMB = {}
def comb(cp, k):
    if k == 'horn':
        hc = NEW['uni01A1']['horn']; return xform([hc], lambda x, y: (x - I['o'].width, y))
    if k == 'dot':
        e = [x for x in NEW['uni1EA1']['inst'] if x[0] == 'dot'][0]
        m = xform([e[1]], lambda x, y: (e[3][0] * x + e[3][4], e[3][3] * y + e[3][5]))
    elif k in ('hook', 'breve'):
        e = [x for x in NEW[{'hook': 'uni1EA3', 'breve': 'uni0103'}[k]]['inst'] if x[0] == k][0]
        m = xform([e[1]], lambda x, y: (e[3][0] * x + e[3][4], e[3][3] * y + e[3][5]))
    else:
        s = STD_I[(k, 0)]; m = move([s['c']], AXI['a']['ax'] - AXI['a']['ax'], 0)
    return xform(m, lambda x, y: (x - I['a'].width, y))
for cp, k in KIND.items(): COMB['uni%04X' % cp] = comb(cp, k)

# ---------- ghi vào font ----------
cff = it['CFF '].cff; top = cff.topDictIndex[0]; csi = top.CharStrings; NW = getattr(top.Private, 'nominalWidthX', 0)
order = list(it.getGlyphOrder()); hm = it['hmtx']
def put(name, cs_slanted, width):
    pen = T2CharStringPen(width - NW, None)
    for c in cs_slanted:
        for op, pts in c: getattr(pen, op)(*[(round(x), round(y)) for x, y in pts])
    chs = pen.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
    if name in csi.charStrings: csi.charStringsIndex[csi.charStrings[name]] = chs
    else:
        csi.charStringsIndex.append(chs); csi.charStrings[name] = len(csi.charStringsIndex) - 1; order.append(name)
    b = bounds(cs_slanted) if cs_slanted else (0, 0, 0, 0)
    hm.metrics[name] = (width, int(math.floor(b[0])))
added = {}
for n, e in NEW.items():
    put(n, slant(e['cs'], T), e['w']); added[rname[n]] = n
for n, cs in COMB.items():
    put(n, slant(cs, T), 0); added[rname[n]] = n
it.setGlyphOrder(order); top.charset = order; it['maxp'].numGlyphs = len(order)
for t in it['cmap'].tables:
    if t.isUnicode():
        for cp, n in added.items():
            if t.format == 4 and cp > 0xFFFF: continue
            t.cmap[cp] = n
gd = it['GDEF'].table.GlyphClassDef.classDefs
for cp, n in added.items(): gd[n] = 3 if n in COMB else 1

# ---------- ccmp: chép bảng ghép từ bản đứng VN ----------
lig = {}
for lk in rf['GSUB'].table.LookupList.Lookup:
    for st in lk.SubTable:
        if hasattr(st, 'ligatures'):
            for first, L_ in st.ligatures.items():
                for l in L_:
                    if all(g in csi.charStrings for g in [first] + l.Component + [l.LigGlyph]) and any(c.startswith('uni03') for c in l.Component):
                        lig[tuple([first] + l.Component)] = l.LigGlyph
G = it['GSUB'].table
st = buildLigatureSubstSubtable(lig)
lk = ot.Lookup(); lk.LookupType = 4; lk.LookupFlag = 0; lk.SubTable = [st]; lk.SubTableCount = 1
for fr in G.FeatureList.FeatureRecord: fr.Feature.LookupListIndex = [i + 1 for i in fr.Feature.LookupListIndex]
G.LookupList.Lookup.insert(0, lk); G.LookupList.LookupCount = len(G.LookupList.Lookup)
fr = ot.FeatureRecord(); fr.FeatureTag = 'ccmp'; fr.Feature = ot.Feature(); fr.Feature.FeatureParams = None
fr.Feature.LookupListIndex = [0]; fr.Feature.LookupCount = 1
G.FeatureList.FeatureRecord.append(fr); fi = len(G.FeatureList.FeatureRecord) - 1; G.FeatureList.FeatureCount = fi + 1
for sr in G.ScriptList.ScriptRecord:
    for ls in ([sr.Script.DefaultLangSys] if sr.Script.DefaultLangSys else []) + [l.LangSys for l in sr.Script.LangSysRecord]:
        ls.FeatureIndex = sorted(ls.FeatureIndex + [fi]); ls.FeatureCount = len(ls.FeatureIndex)
recs = G.FeatureList.FeatureRecord; od = sorted(range(len(recs)), key=lambda i: (recs[i].FeatureTag, i)); remap = {o: k for k, o in enumerate(od)}
G.FeatureList.FeatureRecord = [recs[i] for i in od]
for sr in G.ScriptList.ScriptRecord:
    for ls in ([sr.Script.DefaultLangSys] if sr.Script.DefaultLangSys else []) + [l.LangSys for l in sr.Script.LangSysRecord]:
        ls.FeatureIndex = sorted(remap[i] for i in ls.FeatureIndex)

# ---------- kern: chữ mới kế thừa cặp kern của chữ gốc ----------
KB = {n: e['base'] for n, e in NEW.items() if n not in ORIG}   # chữ có sẵn dựng lại thì giữ kern cũ
for lk in it['GPOS'].table.LookupList.Lookup:
    for st in lk.SubTable:
        if lk.LookupType == 9: st = st.ExtSubTable
        if getattr(st, 'LookupType', lk.LookupType) != 2: continue   # chỉ PairPos
        if st.Format == 1:
            cov = st.Coverage.glyphs
            for ps in st.PairSet:
                extra = []
                for r in ps.PairValueRecord:
                    for n, b in KB.items():
                        if r.SecondGlyph == b:
                            x = ot.PairValueRecord(); x.SecondGlyph = n; x.Value1 = r.Value1
                            if hasattr(r, 'Value2'): x.Value2 = r.Value2
                            extra.append(x)
                ps.PairValueRecord += extra; ps.PairValueCount = len(ps.PairValueRecord)
            newc, newps = list(cov), list(st.PairSet)
            for n, b in KB.items():
                if b in cov:
                    src = st.PairSet[cov.index(b)]; p = ot.PairSet(); p.PairValueRecord = list(src.PairValueRecord); p.PairValueCount = len(p.PairValueRecord)
                    newc.append(n); newps.append(p)
            gid = it.getReverseGlyphMap(True)
            z = sorted(zip(newc, newps), key=lambda q: gid[q[0]])
            for ps in [q[1] for q in z]: ps.PairValueRecord.sort(key=lambda r: gid[r.SecondGlyph])
            st.Coverage.glyphs = [q[0] for q in z]; st.PairSet = [q[1] for q in z]; st.PairSetCount = len(st.PairSet)
        elif st.Format == 2:
            c1, c2 = st.ClassDef1.classDefs, st.ClassDef2.classDefs; cov = st.Coverage.glyphs
            for n, b in KB.items():
                if b in c1: c1[n] = c1[b]
                if b in c2: c2[n] = c2[b]
                if b in cov and n not in cov: cov.append(n)
            gid = it.getReverseGlyphMap(True); st.Coverage.glyphs = sorted(cov, key=lambda g: gid[g])

# ---------- thông số ----------
gs2 = it.getGlyphSet(); ymax = it['head'].yMax; ymin = it['head'].yMin
for n in added.values():
    bp = BoundsPen(gs2); gs2[n].draw(bp)
    if bp.bounds: ymax = max(ymax, math.ceil(bp.bounds[3])); ymin = min(ymin, math.floor(bp.bounds[1]))
it['head'].yMax, it['head'].yMin = ymax, ymin; top.FontBBox = [it['head'].xMin, ymin, it['head'].xMax, ymax]
os2 = it['OS/2']; os2.usWinAscent = max(os2.usWinAscent, ymax); os2.usWinDescent = max(os2.usWinDescent, -ymin)
if CFG.get('italic_bit', True):
    os2.fsSelection |= 1; it['head'].macStyle |= 2
advs = [hm[g][0] for g in order if hm[g][0] > 0]; os2.xAvgCharWidth = int(round(sum(advs) / len(advs)))
# tên
nm = it['name']
FAM, STY, PS, FULL = CFG['family'], CFG['style'], CFG['ps'], CFG['full']
TF, TS = CFG.get('typo_family', FAM), CFG.get('typo_style', STY)
for r in nm.names:
    if r.nameID == 1: r.string = FAM
    elif r.nameID == 2: r.string = STY
    elif r.nameID == 4: r.string = FULL
    elif r.nameID == 6: r.string = PS
    elif r.nameID == 16: r.string = TF
    elif r.nameID == 17: r.string = TS
    elif r.nameID == 3: r.string = 'Version 1.000;;%s;2022;FL801;VN' % PS
top.FullName = FULL; top.FamilyName = TF
cff.fontNames = [PS]
it.save(OUT)
chk = TTFont(OUT); tdx = chk['CFF '].cff.topDictIndex[0]; bad = 0
for g in chk.getGlyphOrder():
    c = tdx.CharStrings[g]; c.draw(BoundsPen(None))
    if c.width != chk['hmtx'][g][0]: bad += 1
print('trục: góc đo %.2f° (từng nét %s), góc khai %.0f°, dùng %.2f° · chế độ %s · dựng lại %d chữ có sẵn' % (ANG_MEAS, [round(a, 1) for a in ANG_LIST], ANG_POST, ANG, AXIS_MODE, len(REBUILD))); print('độ lệch chuẩn từng loại dấu:', {'%s%s' % (k, 'H' if c else ''): round(v) for (k, c), v in OFF.items()}); print('CFF width != hmtx:', bad); print('ghi chú:', SAFE)
print('added', len(NEW), 'glyphs +', len(COMB), 'combining; ccmp', len(lig), '; yMax', ymax, 'yMin', ymin, '; winAscent', os2.usWinAscent)
for n in ('uni01B0', 'uni01A1', 'uni01AF', 'uni01A0'):
    print(' ', NEW[n]['ch'], 'w', NEW[n]['w'], 'base w', I[NEW[n]['base']].width, 'yMax', round(bounds(NEW[n]['cs'])[3]))

# ---------- dữ liệu bàn vẽ ----------
if RECOUT:
    js = lambda cs: [[[op, [[round(x, 1), round(y, 1)] for x, y in p]] for op, p in c] for c in cs]
    def tslant(t):
        sx, _, _, sy, tx, ty = t; return [sx, 0, (sy - sx) * T, sy, tx + ty * T, ty]
    marks = {}; recipes = {}
    MKEY = {'acute': 'acute', 'grave': 'grave', 'tilde': 'tilde', 'circ': 'circ', 'breve': 'breve', 'hook': 'hook', 'hook_s': 'hook_s', 'dot': 'dot'}
    for (k, caps), s in STD_I.items():
        if caps == 0: marks[k] = js(slant([s['c']], T))
    marks['hook_s'] = marks['hook']; marks['horn'] = js(slant([NEW['uni01A1']['horn']], T))
    for n, e in NEW.items():
        st_ = slant(e['cs'][:e['nstatic']], T); mm = []     # nét tĩnh = đúng phần thân đã dựng (đ Đ có thanh ngang, ị có chấm i)
        if 'horn' in e:
            st_ = slant(e['static_cs'], T)
            hcs = slant([e['horn']], T)
            # râu là contour riêng của chữ này → đưa vào nét tĩnh + một dấu 'horn' dịch tới đúng chỗ
            if unicodedata.normalize('NFD', e['ch'])[0] == 'o':
                hb = cb(hcs[0]); mb = cb(slant([NEW['uni01A1']['horn']], T)[0])
                mm.append({'m': 'horn', 't': [1, 0, 0, 1, round(hb[0] - mb[0], 2), round(hb[1] - mb[1], 2)]})
            else: st_ = st_ + hcs
            for k, c, b, t in e['inst'][1:]:
                st_ = st_ + slant([c], T)
        else:
            for k, c, b, t in e['inst']:
                mk = MKEY.get(k)
                if k in ('acute', 'grave', 'tilde', 'circ', 'breve', 'dot', 'hook', 'hook_s'):
                    base_c = STD_I[('hook' if k == 'hook_s' else k, 0)]['c']
                    if c is base_c:
                        mm.append({'m': mk, 't': [round(v, 4) for v in tslant(t)]}); continue
                st_ = st_ + slant([xform([c], lambda x, y: (t[0] * x + t[4], t[3] * y + t[5]))[0]], T)
        L_ = unicodedata.normalize('NFD', e['ch'])[0]
        axx = (AXB if AXIS_MODE == 'body' else {k: v['ax'] for k, v in AXI.items()}).get(L_, None)
        if axx is None: axx = band_cx(IU(e['base']), L_)
        recipes[n] = {'u': rname[n], 'w': e['w'], 'static': js(st_), 'marks': mm, 'sax': [round(axx, 2), round(T, 4)]}
    # KIỂM: ghép lại từ dữ liệu bàn vẽ phải ra đúng glyph trong font (số contour + khung bao), không thì dừng
    bad = []
    for n, r in recipes.items():
        cs_ = [[(op_, [tuple(p) for p in pts]) for op_, pts in c] for c in r['static']]
        for mi in r['marks']:
            t = mi['t']; src = marks[mi['m']]
            cs_ += [[(op_, [(t[0] * x + t[2] * y + t[4], t[1] * x + t[3] * y + t[5]) for x, y in pts]) for op_, pts in c] for c in src]
        real = slant(NEW[n]['cs'], T)
        b1, b2 = bounds(cs_), bounds(real)
        if len(cs_) - len(real) != (1 if 'horn' in NEW[n] else 0) or max(abs(a - b) for a, b in zip(b1, b2)) > 2: bad.append('%s %d/%d' % (NEW[n]['ch'], len(cs_), len(real)))
    if bad: raise SystemExit('bàn vẽ lệch glyph: ' + ', '.join(bad))
    json.dump({'upm': 1000, 'tilde_w': 60, 'axis': ANG, 'marks': marks, 'glyphs': recipes}, open(RECOUT, 'w'))
    print('kiểm bàn vẽ: %d chữ khớp glyph' % len(recipes))
    print('recipes', len(recipes))
