"""Việt hoá font NGHIÊNG TrueType từ bản ĐỨNG đã Việt hoá (chỉ fontTools).
- Dấu font nghiêng có sẵn (sắc huyền ngã mũ trăng): đặt theo anchor GPOS mark / mkmk của chính font nghiêng (luật src-marks),
  cộng độ lệch / co giãn mà bản đứng VN đã áp so với anchor của nó (vd ĩ Ĩ dấu ngã hẹp).
- Dấu font nghiêng thiếu (hỏi, nặng, râu): chép quan hệ từ bản đứng VN, nghiêng theo trục chuẩn (góc đo từ nét đứng):
  p_it = A_it + (dx + dy·tan, dy), (dx, dy) = p_đứng − A_đứng, A = anchor gắn dấu (anchor thân / anchor mkmk dấu dưới).
  Dấu nặng = chấm chữ i nghiêng, tâm theo cách trên; ị theo trục qua tâm thân i + tâm chấm i.
  Râu = đoạn râu của bản đứng (tách khỏi o / u / O / U), nghiêng quanh gốc râu, hợp nét (union) vào thân nghiêng.
usage: build_it.py SRC_IT.ttf REF_VN.ttf OUT.ttf cfg.json
cfg: {"stack": "top"|"right", "hook": "ref"|"half", "hook_half_font": path?, "hook_tf": {"w","h","head","tail"} (%)}"""
import sys, os, json, math, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.ttLib.tables import otTables as ot
from fontTools.otlLib.builder import buildLigatureSubstSubtable, buildLookup
from geom import tt_contours, bbox_pts, segments, segs_to_contour, flatten, area, seg_pt, dense
from gposanc import anchors
import union as U

SRC, REF, OUT, CFGP = sys.argv[1:5]
CFG = json.load(open(CFGP))
I = TTFont(SRC); R = TTFont(REF)
cmI = I.getBestCmap(); cmR = R.getBestCmap()
bI, mI, mbI, mmI = anchors(I); bR, mR, mbR, mmR = anchors(R)
LOG = []

# ---------- góc trục chuẩn: đo từ nét đứng ----------
def xs_at(cs, y):
    X = []
    for c in cs:
        P = flatten(c, 24)
        for i in range(len(P)):
            (x0, y0), (x1, y1) = P[i], P[(i + 1) % len(P)]
            if (y0 <= y < y1) or (y1 <= y < y0): X.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return sorted(X)
def stem_angle():
    out = []
    for ch, y0, y1, pick in [('l', 100, 650, 'w'), ('I', 100, 620, 'w'), ('H', 100, 300, 'f'), ('T', 100, 600, 'w'), ('E', 100, 300, 'f')]:
        cs = tt_contours(I, cmI[ord(ch)]); ys, xs = [], []
        for y in np.linspace(y0, y1, 20):
            X = xs_at(cs, y); pr = [(X[i], X[i + 1]) for i in range(0, len(X) - 1, 2)]
            if not pr: continue
            a, b = pr[0] if pick == 'f' else max(pr, key=lambda q: q[1] - q[0]); ys.append(y); xs.append((a + b) / 2)
        out.append(math.degrees(math.atan(np.polyfit(ys, xs, 1)[0])))
    return float(np.median(out))
ANG = CFG.get('angle') or stem_angle(); T = math.tan(math.radians(ANG))
LOG.append('trục chuẩn %.2f° (post.italicAngle %.1f)' % (ANG, -I['post'].italicAngle))

def skew_about(c, AR, AI):
    return [(AI[0] + (x - AR[0]) + (y - AR[1]) * T, AI[1] + (y - AR[1]), on) for x, y, on in c]
def move(c, dx, dy): return [(x + dx, y + dy, on) for x, y, on in c]
def bb(cs):
    bs = [bbox_pts(c) for c in cs]
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))
def same_bb(a, b, tol=4): return all(abs(x - y) < tol for x, y in zip(a, b))
def pts(cs, n=10):
    return np.array([p for c in cs for p in dense(c, 3.0)])
def mindist(A, B):
    a = pts(A); b = pts(B)
    d = np.sqrt(((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)); return float(d.min())

MK = {0x300: 'gravecomb', 0x301: 'acutecomb', 0x302: 'uni0302', 0x303: 'tildecomb', 0x306: 'uni0306'}
TOP = 0  # class index trong lookup MarkBase của cả hai font: (li, 0) trên, (li, 1) dưới
def topkey(anc): return [k for k in anc if k[1] == 0][0]
def botkey(anc): return [k for k in anc if k[1] == 1][0]
def gn(font, ch): return (cmI if font is I else cmR)[ord(ch)]

# ---------- bảng chữ Việt ----------
VOW = "aăâeêioôơuưyAĂÂEÊIOÔƠUƯY"
VN = []
for b in VOW:
    for tmark in ["", "̀", "́", "̉", "̃", "̣"]:
        VN.append(unicodedata.normalize("NFC", b + tmark))
VN += ["đ", "Đ"]

# ---------- râu ----------
def horn_part(L):
    """đoạn râu trong bản đứng VN: (run segments, plain base contour index) — đoạn của contour có râu lệch khỏi nét chữ trơn"""
    P = unicodedata.normalize('NFC', L + '̛')
    HR = tt_contours(R, gn(R, P)); BR = tt_contours(R, gn(R, L))
    outer = max(range(len(HR)), key=lambda i: abs(area(HR[i])))
    hc = HR[outer]; bo = BR[max(range(len(BR)), key=lambda i: abs(area(BR[i])))]
    segs = segments(hc); bp = np.array(dense(bo, 1.5))
    far = []
    for s in segs:
        sp = np.array([seg_pt(s, t) for t in np.linspace(0, 1, 7)])
        d = np.sqrt(((sp[:, None, :] - bp[None, :, :]) ** 2).sum(-1)).min(1)
        far.append(d.max() > 8)
    n = len(segs); idx = [i for i in range(n) if far[i]]
    # cụm đoạn xa lớn nhất (cho phép hở ≤ 3 đoạn) — râu là một cụm liền
    clusters = []
    for i in idx:
        if clusters and (i - clusters[-1][-1]) <= 4: clusters[-1].append(i)
        else: clusters.append([i])
    if len(clusters) > 1 and (clusters[0][0] + n - clusters[-1][-1]) <= 4:
        clusters[0] = clusters.pop() + clusters[0]
    def ext(cl):
        P = np.array([seg_pt(segs[k], t) for k in cl for t in (0, .5, 1)]); return np.ptp(P[:, 0]) + np.ptp(P[:, 1])
    cl = max(clusters, key=ext)
    s0 = cl[0]; ln = (cl[-1] - cl[0]) % n
    run = [segs[(s0 + k) % n] for k in range(ln + 1)]
    return run, bo

def edge_x(cs, y, side='R'):
    X = xs_at(cs, y)
    return X[-1] if side == 'R' else X[0]

def inward_point(base_segs, p, d):
    """điểm cách p một khoảng d vào trong thân (theo pháp tuyến tại điểm gần nhất trên viền)"""
    P = np.array(dense(segs_to_contour(base_segs), 1.0))
    k = int(np.argmin(((P - np.array(p)) ** 2).sum(1)))
    q = P[k]; tng = P[(k + 1) % len(P)] - P[k - 1]; tng /= np.linalg.norm(tng) + 1e-9
    nrm = np.array([-tng[1], tng[0]])
    for sgn in (1, -1):
        c = q + sgn * nrm * d
        if U.winding(P, c) != 0: return tuple(c)
    return tuple(q)

def nearest_on(segs, p):
    best = None
    for i, sg in enumerate(segs):
        for t in np.linspace(0, 1, 81):
            q = seg_pt(sg, t); d = math.dist(q, p)
            if best is None or d < best[0]: best = (d, i, t, q)
    return best

def splice(bsegs, run):
    """thay đoạn viền thân bằng đường râu, cắt đúng giao điểm (không chiếu điểm gần nhất → không gai):
    giao đầu tiên dọc râu = chỗ râu rời thân (mép trên serif), giao cuối = chỗ mép dưới râu nhập thân (mép phải thân).
    Phần viền giữa 2 giao (đuôi serif phải) bị thay → râu đè lên thịt chữ."""
    X = []
    for i, rs in enumerate(run):
        for j, bs in enumerate(bsegs):
            for ta, tb in U.isect(rs, bs): X.append((i + ta, j, tb, seg_pt(rs, ta)))
    X.sort()
    if len(X) < 2: raise RuntimeError('splice: râu không cắt viền thân')
    (ra, ja, ta_, pa), (rb, jb, tb_, pb) = X[0], X[-1]
    # đoạn râu giữa 2 giao
    ia, fa = int(ra), ra - int(ra); ib, fb = int(rb), rb - int(rb)
    if ia == ib:
        hr = [U.sub(run[ia], fa, fb)]
    else:
        hr = [U.sub(run[ia], fa, 1)] + list(run[ia + 1:ib]) + ([U.sub(run[ib], 0, fb)] if fb > 1e-6 else [])
    hr[0] = (pa,) + tuple(hr[0][1:]); hr[-1] = tuple(hr[-1][:-1]) + (pb,)
    # viền thân giữ: từ giao b (nhập thân) đi tới giao a (rời thân)
    n = len(bsegs); keep = []
    keep.append(U.sub(bsegs[jb], tb_, 1)); keep[0] = (pb,) + tuple(keep[0][1:])
    k = (jb + 1) % n
    while k != ja:
        keep.append(bsegs[k]); k = (k + 1) % n
    last = U.sub(bsegs[ja], 0, ta_); keep.append(tuple(last[:-1]) + (pa,))
    ok = lambda L_: [sg for sg in L_ if math.dist(sg[0], sg[-1]) > 0.3 or len(sg) == 3]
    segs = ok(keep + hr)
    LOG.append('ghép râu (cắt đúng giao, thay đuôi serif): %d giao' % len(X))
    # bản tách cho bàn vẽ / Chi tiết: thân bỏ đuôi serif (nối thẳng 2 giao) + râu là hình kín RIÊNG (râu + đường nối)
    body = segs_to_contour(ok(keep + [(pa, pb)]))
    hornc = segs_to_contour(ok(list(hr) + [(pb, pa)]))
    return segs_to_contour(segs), body, hornc

def build_horn(L):
    src = CFG.get('horn_from', {}).get(L, L)   # vd {"U": "O"}: Ư dùng râu của Ơ (người dùng 27/10), gốc đặt theo mép phải thân U cùng độ cao
    run, boR = horn_part(src)
    S, E = run[0][0], run[-1][-1]
    yr = (S[1] + E[1]) / 2; rx = (S[0] + E[0]) / 2
    off = rx - edge_x([boR], yr)
    base = tt_contours(I, gn(I, L)); oi = max(range(len(base)), key=lambda i: abs(area(base[i])))
    xI = edge_x([base[oi]], yr)
    AR = (rx, yr); AI = (xI + off, yr)
    hs = CFG.get('horn_shift', {}).get(L, [0, 0]); AI = (AI[0] + hs[0], AI[1])
    def tf(p): return (AI[0] + (p[0] - AR[0]) + (p[1] - AR[1]) * T + hs[1] * T, p[1] + hs[1])
    hr = [tuple(tf(p) for p in s) for s in run]
    bsegs = segments(base[oi])
    # râu là HÌNH RIÊNG, gốc ĐÂM vào thịt chữ (người dùng 27/10): đường râu + gốc kéo dài vào trong nét theo một hướng chung,
    # thân chữ GIỮ NGUYÊN (không cắt serif) → font gộp nét bằng union; bàn vẽ / Chi tiết giữ râu rời.
    S0, E0 = hr[0][0], hr[-1][-1]
    # ĐUÔI râu (phần chìm trong thân) dựng như râu của bản đứng (horn5 / kit): cổ râu đi TIẾP theo hướng chính nó
    # (2 mép kéo dài theo tiếp tuyến, giữ độ mảnh của cổ) rồi CẮT GỌN bằng một đường song song trục chữ, cách gốc `horn_clip` vào trong
    # — không chụm thành nêm. (người dùng 27/10: “đuôi móc dạng vector … tham khảo regular”)
    a1 = np.array(inward_point(bsegs, S0, 12)) - np.array(S0); a2 = np.array(inward_point(bsegs, E0, 12)) - np.array(E0)
    v = a1 + a2; v = v / (np.linalg.norm(v) + 1e-9)
    PB = U.poly(bsegs, 40)
    def tang(sg, end):
        if end: q, p = sg[-1], sg[-2]
        else: q, p = sg[0], sg[1]
        d_ = np.array(q) - np.array(p); return d_ / (np.linalg.norm(d_) + 1e-9)   # hướng đi RA khỏi râu, vào thân
    dS = tang(hr[0], False); dE = tang(hr[-1], True)
    ax_ = np.array([T, 1.0]); ax_ /= np.linalg.norm(ax_)          # đường cắt song song trục chữ (nghiêng)
    mid = (np.array(S0) + np.array(E0)) / 2
    def hit(P, d_, C):   # tia P + s·d_ cắt đường C + u·ax_
        M = np.array([[d_[0], -ax_[0]], [d_[1], -ax_[1]]])
        if abs(np.linalg.det(M)) < 1e-6: return None
        s_, _ = np.linalg.solve(M, C - np.array(P)); return np.array(P) + max(s_, 4) * d_
    clip = CFG.get('horn_clip', 36) * (1 if L.isupper() else 0.9)
    res = None
    while clip > 8:
        C = mid + v * clip
        Sin, Ein = hit(S0, dS, C), hit(E0, dE, C)
        if Sin is not None and Ein is not None and all(U.winding(PB, tuple(p)) for p in (Sin, Ein, (Sin + Ein) / 2)):
            closed = hr + [(E0, tuple(Ein)), (tuple(Ein), tuple(Sin)), (tuple(Sin), S0)]
            res = U.union(bsegs, closed)
            if res:
                big = [c for c in res if abs(U.signed_area(c)) > 4]
                if len(big) == 1: res = big; break   # đuôi không được khép lỗ với thân (lấp lỗ = đổi dáng chữ) → rút ngắn đuôi
        clip -= 2
    if not (res and len([c for c in res if abs(U.signed_area(c)) > 4]) == 1):
        # đuôi theo cổ râu vẫn để hở túi nhỏ giữa râu và serif (Ư): gộp thêm nêm gốc (đi thẳng vào thân) để lấp đúng các túi đó,
        # như VER 4 — hình râu ở bàn vẽ vẫn là bản đuôi theo cổ
        clip = CFG.get('horn_clip', 36); C = mid + v * clip
        Sin, Ein = hit(S0, dS, C), hit(E0, dE, C)
        closed = hr + [(E0, tuple(Ein)), (tuple(Ein), tuple(Sin)), (tuple(Sin), S0)]
        w = 34
        Ws, We = tuple(np.array(S0) + v * w), tuple(np.array(E0) + v * w)
        wedge = hr + [(E0, We), (We, Ws), (Ws, S0)]
        res = U.union(bsegs, wedge)
        if res: res = [c for c in res if abs(U.signed_area(c)) > 4]
        LOG.append('râu %s: font gộp bằng nêm gốc (đuôi theo cổ để hở túi với serif), bàn vẽ giữ đuôi theo cổ' % L)
    assert res and len(res) == 1, ('horn union failed', L, res and len(res))
    d = clip
    newc = segs_to_contour(res[0]); bodyc, hornc = base[oi], segs_to_contour(closed)
    LOG.append('râu %s: gốc đâm vào thân %.0f đv' % (L, d))
    out = [newc] + [c for i, c in enumerate(base) if i != oi]
    # độ rộng: giữ lề phải của bản đứng trong không gian dựng thẳng
    adv0 = I['hmtx'][gn(I, L)][0]
    PR = unicodedata.normalize('NFC', L + '̛')
    rsbR = R['hmtx'][gn(R, PR)][0] - bb(tt_contours(R, gn(R, PR)))[2]
    if src != L: LOG.append('râu %s: dùng râu của %s' % (PR, unicodedata.normalize('NFC', src + '̛')))
    hp = pts([segs_to_contour(hr)], 12)
    xu = float((hp[:, 0] - hp[:, 1] * T).max())          # mép phải râu, dựng thẳng (quanh đường chân chữ)
    adv = max(adv0, int(round(xu + rsbR)))
    top = bb(out)[3]
    LOG.append('râu %s: rộng %d → %d (%+d), đỉnh %d' % (PR, adv0, adv, adv - adv0, round(top)))
    HSEP[L] = ([bodyc] + [c for i, c in enumerate(base) if i != oi], hornc)   # thân + râu RỜI (bàn vẽ / Chi tiết chỉnh được, tô đỏ được)
    return out, adv

HSEP = {}
HORN = {}
for L in "ouOU":
    HORN[L] = build_horn(L)

# ---------- phân tích bản đứng VN: dấu từng chữ ----------
def base_letter(ch):
    d = unicodedata.normalize('NFD', ch); L = d[0]; ms = d[1:]
    horn = '̛' in ms
    return L, [m for m in ms if m != '̛'], horn

def R_base_cs(L, horn, has_top):
    if horn: return tt_contours(R, gn(R, unicodedata.normalize('NFC', L + '̛')))
    if L == 'i' and has_top: return tt_contours(R, 'dotlessi')
    return tt_contours(R, gn(R, L))

def R_marks(ch):
    L, ms, horn = base_letter(ch)
    tops = [m for m in ms if m != '̣']
    bc = R_base_cs(L, horn, bool(tops)); bbs = [bbox_pts(c) for c in bc]
    cs = tt_contours(R, gn(R, ch))
    rest = [c for c in cs if not any(same_bb(bbox_pts(c), x) for x in bbs)]
    if L == 'i' and not tops: rest = [c for c in rest if bbox_pts(c)[3] < 0]   # ị: chấm i là thân
    up = sorted([c for c in rest if bbox_pts(c)[1] > 0], key=lambda c: bbox_pts(c)[1])
    dn = [c for c in rest if bbox_pts(c)[3] < 0]
    return up, dn

def anc_glyph(font, L, has_top):
    if L == 'i' and has_top: return 'dotlessi'
    return gn(font, L)

def place_tops(font, L, tops):
    """vị trí (dx,dy) từng dấu trên theo anchor (mark / mkmk). Trả [(glyph, pos, attachA)]"""
    b, m, mb, mm = (bI, mI, mbI, mmI) if font is I else (bR, mR, mbR, mmR)
    ag = anc_glyph(font, L, True); out = []
    for j, mk in enumerate(tops):
        g = MK.get(ord(mk))
        if j == 0:
            A = b[ag][topkey(b[ag])]
        else:
            pg, ppos, _ = out[-1]
            pa = mb.get(pg) if pg else None
            if pa is None:   # dấu trước không có trong font (hỏi) → không xảy ra ở tiếng Việt
                raise RuntimeError('stack over missing mark')
            k = list(pa)[0]; A = (ppos[0] + pa[k][0], ppos[1] + pa[k][1])
        if g:
            ma = (m[g][1] if j == 0 else mm[g][1])
            pos = (A[0] - ma[0], A[1] - ma[1])
        else:
            pos = None
        out.append((g, pos, A))
    return out

def ctr_bottom(b): return ((b[0] + b[2]) / 2, b[1])

ITTL = [c for c in tt_contours(I, 'i') if bbox_pts(c)[1] > 520][0]   # chấm i nghiêng
def dot_at(cx, cy):
    b = bbox_pts(ITTL); return move(ITTL, cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2)

def i_axis_x(y):
    """ị: trục qua tâm thân ı (giữa x-height) và tâm chấm i"""
    cs = tt_contours(I, 'dotlessi'); ym = 255
    X = xs_at(cs, ym); stem = (X[0] + X[-1]) / 2 if len(X) == 2 else (X[0] + X[1]) / 2
    tb = bbox_pts(ITTL); tc = ((tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2)
    k = (tc[0] - stem) / (tc[1] - ym)
    return stem + (y - ym) * k

HALF = None
if CFG.get('hook') == 'half':
    HALF = json.load(open(CFG['hook_half']))   # {"contour": [[x,y,on]...]} dấu hỏi từ nửa trên dấu ? (đã nghiêng), gốc toạ độ = tâm đáy

HTF = CFG.get('hook_tf')   # {"w":100,"h":100,"head":100,"tail":100} — số kéo ở Chi tiết › Dấu hỏi (hook_tf.py, cùng công thức trang)
if HTF:
    from hook_tf import hook_tf

def hook_shape(cR, AR, AI):
    if HTF: cR = hook_tf(cR, HTF.get('w', 100), HTF.get('h', 100), HTF.get('head', 100), HTF.get('tail', 100))   # chỉnh dáng ở không gian dựng thẳng, rồi mới nghiêng
    c = skew_about(cR, AR, AI)
    if HALF is None: return c
    # thay dáng: cùng khung (cao, tâm đáy) với dấu hỏi bản đứng đã nghiêng
    b = bbox_pts(c); h = HALF['contour']; hb = bbox_pts(h)
    s = (b[3] - b[1]) / (hb[3] - hb[1])
    cx, cy = ctr_bottom(b); hx, hy = ctr_bottom(hb)
    # tâm đáy trong không gian dựng thẳng
    return [((x - hx) * s + cx + 0 * T, (y - hy) * s + cy, on) for x, y, on in h]

# ---------- dựng từng chữ ----------
NEW = {}   # glyph name -> (contours, adv)
def compose(ch):
    L, ms, horn = base_letter(ch)
    tops = [m for m in ms if m != '̣']; dot = '̣' in ms
    if horn: base, adv = [list(c) for c in HORN[L][0]], HORN[L][1]
    elif L == 'i' and tops: base = tt_contours(I, 'dotlessi'); adv = I['hmtx']['dotlessi'][0]
    else: base = tt_contours(I, gn(I, L)); adv = I['hmtx'][gn(I, L)][0]
    upR, dnR = R_marks(ch)
    assert len(upR) == len(tops), (ch, len(upR), len(tops))
    PI = place_tops(I, L, tops); PR = place_tops(R, L, tops)
    marks = []; placed = []; kinds = []   # placed: italic actual (glyph, pos(after deviation), contours)
    devR = []
    for j, mk in enumerate(tops):
        gI, posI, AI0 = PI[j]; gR, posR, AR0 = PR[j]
        # anchor gắn: nếu dấu trước đã có độ lệch thì anchor dời theo
        if j > 0:
            AI0 = (AI0[0] + devI[0], AI0[1] + devI[1]); AR0 = (AR0[0] + devR_[0], AR0[1] + devR_[1])
            if posI: posI = (posI[0] + devI[0], posI[1] + devI[1])
            if posR: posR = (posR[0] + devR_[0], posR[1] + devR_[1])
        cR = upR[j]
        if gI:
            pred = bbox_pts(move(tt_contours(R, gR)[0], *posR)); act = bbox_pts(cR)
            sx = (act[2] - act[0]) / (pred[2] - pred[0]); sy = (act[3] - act[1]) / (pred[3] - pred[1])
            pc, ac = ctr_bottom(pred), ctr_bottom(act); d = (ac[0] - pc[0], ac[1] - pc[1])
            cI = [move(c, *posI) for c in tt_contours(I, gI)]
            if abs(sx - 1) > .02 or abs(sy - 1) > .02 or abs(d[0]) > 2 or abs(d[1]) > 2:
                ib = bb(cI); o = ctr_bottom(ib)
                def f(x, y):
                    xu = x - (y - o[1]) * T                     # dựng thẳng quanh đáy dấu
                    xu = o[0] + (xu - o[0]) * sx; yy = o[1] + (y - o[1]) * sy
                    return xu + (yy - o[1]) * T + d[0] + d[1] * T, yy + d[1]
                cI = [[(*f(x, y), on) for x, y, on in c] for c in cI]
                LOG.append('%s: chép độ lệch bản đứng cho %s: co %.2f×%.2f dời %+.0f,%+.0f' % (ch, gI, sx, sy, d[0], d[1]))
            devI = (d[0] + d[1] * T, d[1]); devR_ = d
        else:   # dấu hỏi
            cI = [hook_shape(cR, AR0, AI0)]
            devI = (0, 0); devR_ = (0, 0)
        marks += cI; placed.append((gI, posI, cI)); kinds += [KN.get(gI, 'hook')] * len(cI)
    # chồng dấu bên phải (VER phương án)
    if CFG.get('stack') == 'right' and len(tops) == 2 and tops[0] == '̂' and tops[1] in '̀́̉':
        circ = placed[0][2]; tone = placed[1][2]
        cbb = bb(circ); tbb = bb(tone)
        # dựng thẳng quanh đáy dấu mũ: đáy dấu thanh ngang ~55 % cao dấu mũ, mép trái dấu thanh cách mép phải dấu mũ gap
        y0 = cbb[1] + CFG.get('right_y', .55) * (cbb[3] - cbb[1])
        def uns(cs, yb): return [[(x - (y - yb) * T, y, on) for x, y, on in c] for c in cs]
        cu = uns(circ, cbb[1]); tu = uns(tone, cbb[1])
        cub = bb(cu); tub = bb(tu)
        sc = CFG.get('right_scale', 1.0)
        tu = [[(tub[0] + (x - tub[0]) * sc, tub[1] + (y - tub[1]) * sc, on) for x, y, on in c] for c in tu]; tub = bb(tu)
        dx = (cub[0] + cub[2]) / 2 + CFG.get('right_x', .12) * (cub[2] - cub[0]) - tub[0]; dy = y0 - tub[1]
        tu = [move(c, dx, dy) for c in tu]
        for _ in range(60):
            if mindist(tu, cu) >= CFG.get('right_mingap', 18): break
            tu = [move(c, 1, 1.5) for c in tu]
        tone2 = [[(x + (y - cbb[1]) * T, y, on) for x, y, on in c] for c in tu]
        marks = marks[:len(marks) - len(tone)] + tone2
    if dot:
        dR = dnR[0]; br = bbox_pts(dR); cR = ((br[0] + br[2]) / 2, (br[1] + br[3]) / 2)
        agI = gn(I, L) if L != 'i' else 'dotlessi'; agR = gn(R, L) if L != 'i' else 'dotlessi'
        AI_ = bI[agI][botkey(bI[agI])]; AR_ = bR[agR][botkey(bR[agR])]
        cx = AI_[0] + (cR[0] - AR_[0]) + (cR[1] - AR_[1]) * T; cy = AI_[1] + (cR[1] - AR_[1])
        if L == 'i' and CFG.get('i_dot_axis', 'tittle') == 'tittle':
            cx = i_axis_x(cy); LOG.append('ị: dấu nặng theo trục thân i + chấm i, tâm x %.0f' % cx)
        dI = dot_at(cx, cy)
        # khe dấu nặng ↔ thân (ỵ, Ỵ…): giữ ≥ khe của bản đứng
        gR_ = mindist([dR], R_base_cs(L, horn, bool(tops)))
        n_ = 0
        while mindist([dI], base) < min(gR_, CFG.get('dot_gap', 40)) - 0.5 and n_ < 80:
            dI = move(dI, 2, 0); n_ += 1
        if n_: LOG.append('%s: dấu nặng dời phải %d (khe bản đứng %.0f)' % (ch, 2 * n_, gR_))
        marks.append(dI); kinds.append('dot')
    # dấu thanh trên ơ ư: giữ khe ≥ 28 với râu (dời trái ≤ 40 rồi mới nâng)
    if horn and tops:
        mt = marks[-1:] if not dot else marks[-2:-1]
        g0 = mindist(mt, base); k = 0
        while g0 < CFG.get('horn_tone_gap', 28) and k < CFG.get('horn_tone_left', 40) / 2:
            k += 1; mt = [move(c, -2, 0) if k <= 20 else c for c in mt]; g0 = mindist(mt, base)
        while g0 < CFG.get('horn_tone_gap', 28):
            mt = [move(c, 0, 2) for c in mt]; g0 = mindist(mt, base)
        if k: LOG.append('%s: dấu thanh né râu, dời trái %d, khe %.0f' % (ch, 2 * k, g0))
        if not dot: marks[-1:] = mt
        else: marks[-2:-1] = mt
    if horn:
        hk = {'o': 'horn', 'u': 'horn_u', 'O': 'horn_O', 'U': 'horn_U'}[L]
        REC[ch] = (HSEP[L][0], list(zip(kinds, marks)) + [(hk, HSEP[L][1])])
    else:
        REC[ch] = (base, list(zip(kinds, marks)))
    return base + marks, adv

KN = {'gravecomb': 'grave', 'acutecomb': 'acute', 'uni0302': 'circ', 'tildecomb': 'tilde', 'uni0306': 'breve'}
REC = {}
for ch in VN:
    if ord(ch) in cmI and ch not in 'ĩĨũŨ' and ch not in CFG.get('rebuild', ''):
        continue
    L, ms, horn = base_letter(ch)
    if not ms and not horn: continue
    if ch in 'đĐ': continue
    name = 'uni%04X' % ord(ch)
    NEW[name] = (compose(ch), ch)

# ---------- ghi vào font ----------
glyf = I['glyf']; hmtx = I['hmtx']; order = I.getGlyphOrder()
def mkglyph(cs):
    from fontTools.pens.ttGlyphPen import TTGlyphPointPen
    pp = TTGlyphPointPen(None)
    for c in cs:
        # TrueType: có thể có contour toàn off-curve — giữ nguyên
        pp.beginPath()
        for x, y, on in c: pp.addPoint((round(x), round(y)), 'qcurve' if on else None)
        pp.endPath()
    g = pp.glyph(); return g
def fix_qcurve(cs):
    # point pen cần segmentType 'line' / 'qcurve'; điểm on sau điểm on = line
    out = []
    for c in cs:
        out.append(c)
    return out
from fontTools.pens.ttGlyphPen import TTGlyphPointPen
def glyph_from(cs):
    pp = TTGlyphPointPen(None)
    for c in cs:
        n = len(c); pp.beginPath()
        for i, (x, y, on) in enumerate(c):
            prev = c[i - 1]
            st = None if not on else ('qcurve' if not prev[2] else 'line')
            pp.addPoint((round(x), round(y)), st)
        pp.endPath()
    return pp.glyph()

cmap_add = {}
for name, ((cs, adv), ch) in NEW.items():
    if name not in order: order.append(name)
    glyf.glyphs[name] = glyph_from(cs); hmtx[name] = (adv, 0)
    cmap_add[ord(ch)] = name
for L in 'ouOU':
    ch = unicodedata.normalize('NFC', L + '̛'); name = 'uni%04X' % ord(ch)
    if name not in order: order.append(name)
    glyf.glyphs[name] = glyph_from(HORN[L][0]); hmtx[name] = (HORN[L][1], 0); cmap_add[ord(ch)] = name

# dấu tổ hợp rời: hỏi, nặng, móc (rộng 0, theo anchor như dấu khác)
aa = bI['a'][topkey(bI['a'])]; ar = bR['a'][topkey(bR['a'])]
up_a, dn_a = R_marks('ả')
hk = hook_shape(up_a[0], ar, aa)
mx = mI['acutecomb'][1]                 # đặt dấu rời theo mark anchor: dời dấu hỏi về hệ toạ độ anchor (mx)
hk = move(hk, mx[0] - aa[0], mx[1] - aa[1])
up_d, dn_d = R_marks('ạ'); bd = bbox_pts(dn_d[0]); arb = bR['a'][botkey(bR['a'])]; aib = bI['a'][botkey(bI['a'])]
mdot_anchor = (aib[0] - 0, 0)
dcx = (bd[0] + bd[2]) / 2 - arb[0]; dcy = (bd[1] + bd[3]) / 2 - arb[1]
dk = dot_at(200 + dcx + dcy * T, dcy)    # anchor dấu nặng rời tại (200, 0)
hornR = segs_to_contour(horn_part('u')[0])
COMB = {'uni0309': ([hk], 0x309), 'uni0323': ([dk], 0x323)}
for name, (cs, u) in COMB.items():
    if name not in order: order.append(name)
    glyf.glyphs[name] = glyph_from(cs); hmtx[name] = (0, int(round(bb(cs)[0]))); cmap_add[u] = name
if 'uni031B' not in order:
    # móc rời: chép từ bản đứng, nghiêng
    c = tt_contours(R, 'uni031B'); c = [skew_about(x, (0, 500), (0, 500)) for x in c]
    order.append('uni031B'); glyf.glyphs['uni031B'] = glyph_from(c); hmtx['uni031B'] = (0, int(round(bb(c)[0]))); cmap_add[0x31B] = 'uni031B'
I.setGlyphOrder(order)
for t in I['cmap'].tables:
    if t.isUnicode(): t.cmap.update(cmap_add)
for name in list(NEW) + ['uni01A1', 'uni01B0', 'uni01A0', 'uni01AF', 'uni0309', 'uni0323', 'uni031B']:
    glyf[name].recalcBounds(glyf)
    hmtx[name] = (hmtx[name][0], glyf[name].xMin)   # TrueType: lsb PHẢI = xMin, lệch thì FreeType / Chrome / Word dời cả chữ (lỗi A36)
# GDEF
gd = I['GDEF'].table.GlyphClassDef.classDefs
for n in list(NEW) + ['uni01A1', 'uni01B0', 'uni01A0', 'uni01AF']: gd[n] = 1
for n in ['uni0309', 'uni0323', 'uni031B']: gd[n] = 3
# GPOS: thêm dấu hỏi / nặng rời vào lookup mark + mkmk
gp = I['GPOS'].table
def anc(x, y):
    a = ot.Anchor(); a.Format = 1; a.XCoordinate = int(x); a.YCoordinate = int(y); return a
for lk in gp.LookupList.Lookup:
    for st in lk.SubTable:
        if lk.LookupType == 4:
            for name, cls, A in [('uni0309', 0, mx), ('uni0323', 1, (200, 0))]:
                if cls >= st.ClassCount: continue
                r = ot.MarkRecord(); r.Class = cls; r.MarkAnchor = anc(*A)
                st.MarkCoverage.glyphs.append(name); st.MarkArray.MarkRecord.append(r); st.MarkArray.MarkCount += 1
        if lk.LookupType == 6 and 'acutecomb' in st.Mark1Coverage.glyphs:
            r = ot.MarkRecord(); r.Class = 0; r.MarkAnchor = anc(*mx)
            st.Mark1Coverage.glyphs.append('uni0309'); st.Mark1Array.MarkRecord.append(r); st.Mark1Array.MarkCount += 1
# GSUB ccmp: ghép chuỗi NFD → chữ dựng sẵn (cho Word / app không tự chuẩn hoá)
names = {v: k for k, v in I.getBestCmap().items()}
cmNow = I.getBestCmap()
liga = {}
MARKN = {0x300: 'gravecomb', 0x301: 'acutecomb', 0x302: 'uni0302', 0x303: 'tildecomb', 0x306: 'uni0306', 0x309: 'uni0309', 0x323: 'uni0323', 0x31B: 'uni031B'}
for ch in VN:
    d = unicodedata.normalize('NFD', ch)
    if len(d) < 2 or ord(ch) not in cmNow: continue
    tgt = cmNow[ord(ch)]
    bases = [cmNow[ord(d[0])]] + (['dotlessi'] if d[0] == 'i' else [])
    ms = [MARKN[ord(m)] for m in d[1:]]
    seqs = [ms]
    if len(ms) == 2: seqs.append(ms[::-1])
    for bname in bases:
        for s in seqs: liga.setdefault(bname, {})[tuple(s)] = tgt
    # chữ có râu dựng sẵn + dấu (ơ + ́ …)
    if '̛' in d:
        hb_ = cmNow[ord(unicodedata.normalize('NFC', d[0] + '̛'))]
        rest = [MARKN[ord(m)] for m in d[1:] if m != '̛']
        if rest:
            for s in ([rest, rest[::-1]] if len(rest) == 2 else [rest]): liga.setdefault(hb_, {})[tuple(s)] = tgt
    # dấu mũ / trăng dựng sẵn + dấu thanh (â + ́)
    if len(d) == 3 and d[1] in '̂̆':
        pre = unicodedata.normalize('NFC', d[:2])
        if ord(pre) in cmNow: liga.setdefault(cmNow[ord(pre)], {})[(MARKN[ord(d[2])],)] = tgt
lig = {}
for b, m in liga.items():
    for seq, tgt in m.items(): lig[(b,) + seq] = tgt
st = buildLigatureSubstSubtable(lig)
lk = buildLookup([st])
gs = I['GSUB'].table; gs.LookupList.Lookup.append(lk); gs.LookupList.LookupCount = len(gs.LookupList.Lookup)
li = len(gs.LookupList.Lookup) - 1
for fr in gs.FeatureList.FeatureRecord:
    if fr.FeatureTag == 'ccmp':
        fr.Feature.LookupListIndex.insert(0, li); fr.Feature.LookupCount = len(fr.Feature.LookupListIndex)
# ---------- dữ liệu bàn vẽ (recipes: nét tĩnh + dấu = dấu chuẩn × phép biến đổi) ----------
def ops(c):
    c = [(round(x), round(y), on) for x, y, on in c]
    if not any(on for _, _, on in c):
        return [['qCurveTo', [[x, y] for x, y, _ in c] + [None]]]
    k = next(i for i, p in enumerate(c) if p[2]); c = c[k:] + c[:k]
    out = [['moveTo', [[c[0][0], c[0][1]]]]]; offs = []
    for x, y, on in c[1:] + [c[0]]:
        if on:
            out.append(['qCurveTo', offs + [[x, y]]] if offs else ['lineTo', [[x, y]]]); offs = []
        else: offs.append([x, y])
    if out[-1][0] == 'lineTo' and out[-1][1][0] == out[0][1][0]: out.pop()
    return out
CAN = {}; RECS = {}
def fit(a, b):
    A = np.array([[x, y, 1] for x, y, _ in a]); B = np.array([[x, y] for x, y, _ in b])
    M, res, *_ = np.linalg.lstsq(A, B, rcond=None); err = np.abs(A @ M - B).max()
    return M, err
for L in 'ouOU':
    REC[unicodedata.normalize('NFC', L + '\u031b')] = (HSEP[L][0], [({'o': 'horn', 'u': 'horn_u', 'O': 'horn_O', 'U': 'horn_U'}[L], HSEP[L][1])])
for ch, (base, mk) in REC.items():
    name = cmap_add.get(ord(ch)); st_ = [ops(c) for c in base]; mm = []
    for k, c in mk:
        if k not in CAN: CAN[k] = c
        can = CAN[k]
        if len(can) == len(c):
            M, err = fit(can, c)
            if err < 0.8:
                mm.append({'m': k, 't': [round(M[0, 0], 4), round(M[0, 1], 4), round(M[1, 0], 4), round(M[1, 1], 4), round(M[2, 0], 2), round(M[2, 1], 2)]}); continue
        st_.append(ops(c))
    L0 = unicodedata.normalize('NFD', ch)[0]; ga = 'dotlessi' if L0 == 'i' else gn(I, L0); ka = topkey(bI[ga]) if ga in bI else None
    sax0 = (bI[ga][ka][0] - bI[ga][ka][1] * T) if ka else 0   # trục chữ ở bàn vẽ: qua anchor dấu trên của chữ gốc, nghiêng theo trục chuẩn (không phải x = 0)
    RECS[name] = {'u': ord(ch), 'w': hmtx[name][0], 'static': st_, 'marks': mm, 'sax': [round(sax0, 2), round(T, 4)]}
json.dump({'upm': 1000, 'tilde_w': 60, 'axis': ANG, 'marks': {k: [ops(c)] for k, c in CAN.items()}, 'glyphs': RECS},
          open(os.path.splitext(OUT)[0] + '.recipes.json', 'w'))
I.save(OUT)
LOG.append('dựng %d chữ + 4 chữ râu, ccmp %d chuỗi' % (len(NEW), len(lig)))
print('\n'.join(LOG))
json.dump(LOG, open(os.path.splitext(OUT)[0] + '.log.json', 'w'), ensure_ascii=False, indent=0)
