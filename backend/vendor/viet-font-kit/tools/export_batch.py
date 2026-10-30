"""Dữ liệu cho chế độ ĐỒNG LOẠT ở tab Chỉnh dấu (người dùng 27/10): mỗi chữ tiếng Việt của font → thân chữ + từng dấu riêng
(loại dấu, chữ hoa / thường, có chồng trên dấu mũ / trăng không), dạng path SVG toạ độ font (y hướng lên).
Tách theo vị trí: mảnh nằm hẳn trên đỉnh chữ gốc = dấu trên, nằm hẳn dưới đáy = dấu dưới; còn lại là thân (râu ơ ư dính thân → thuộc thân,
chỉnh râu ở chế độ Thanh kéo). Hai dấu trên: dấu có đáy thấp hơn là dấu mũ / trăng, dấu kia là dấu thanh.
Dùng chung cho batch_apply.py (áp thông số người dùng kéo vào font).
usage: export_batch.py FONT OUT.json
build by @nhatmotion"""
import sys, json, unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen

VN = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ"
VN = VN + VN.upper()
TONE = {"́": "acute", "̀": "grave", "̉": "hook", "̃": "tilde"}
ABOVE2 = {"̂": "circ", "̆": "breve"}
KINDS = ["acute", "grave", "hook", "tilde", "dot", "circ", "breve"]

def contours(gs, name):
    """[(ops, bbox)] — ops = [(op, [pts])] đã tách chữ ghép"""
    pen = DecomposingRecordingPen(gs); gs[name].draw(pen); out, cur = [], []
    for op, a in pen.value:
        if op == "moveTo": cur = [(op, list(a))]
        elif op in ("lineTo", "qCurveTo", "curveTo"): cur.append((op, list(a)))
        elif op in ("closePath", "endPath"):
            if cur: cur.append((op, [])); out.append(cur); cur = []
    res = []
    for c in out:
        pts = [p for _, a in c for p in a if p is not None]
        if not pts: continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        res.append((c, (min(xs), min(ys), max(xs), max(ys))))
    return res

def to_d(cs):
    s = []
    for c, _ in cs:
        for op, a in c:
            if op == "moveTo": s.append("M%g %g" % tuple(a[0]))
            elif op == "lineTo": s.append("L%g %g" % tuple(a[0]))
            elif op == "curveTo": s.append("C" + " ".join("%g %g" % tuple(p) for p in a))
            elif op == "qCurveTo":
                pts = [p for p in a if p is not None]
                if len(pts) == 1: s.append("L%g %g" % tuple(pts[0])); continue
                for i in range(len(pts) - 1):   # TrueType: nhiều điểm điều khiển → tách thành Q một điểm (điểm giữa ngầm)
                    c1 = pts[i]; e = pts[i + 1] if i == len(pts) - 2 else ((pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2)
                    s.append("Q%g %g %g %g" % (c1[0], c1[1], e[0], e[1]))
            elif op in ("closePath", "endPath"): s.append("Z")
    return "".join(s)

def bbu(bs):
    return (min(b[0] for b in bs), min(b[1] for b in bs), max(b[2] for b in bs), max(b[3] for b in bs))

def split(font, ch):
    """→ dict(ch, w, body=[contours], marks=[dict(k, cs, bb, uc, st)]) hoặc None"""
    gs = font.getGlyphSet(); cm = font.getBestCmap()
    if ord(ch) not in cm: return None
    d = unicodedata.normalize("NFD", ch); L = d[0]; ms = d[1:]
    above = [m for m in ms if m in TONE or m in ABOVE2]; below = "̣" in ms
    base = "ı" if (L == "i" and above and ord("ı") in cm) else L
    if ord(base) not in cm: base = L
    if ord(base) not in cm: return None
    B = contours(gs, cm[ord(base)]); bb0 = bbu([b for _, b in B])
    G = contours(gs, cm[ord(ch)]); tol = 6
    def same(b, c): return all(abs(x - y) <= 2.5 for x, y in zip(b, c))
    used = [False] * len(B); body, up, dn = [], [], []
    for c, b in G:
        k = next((i for i, (_, b2) in enumerate(B) if not used[i] and same(b, b2)), None)
        if k is not None: used[k] = True; body.append((c, b)); continue          # mảnh y hệt chữ gốc = thân
        if above and b[1] >= bb0[3] - tol: up.append((c, b))
        elif below and b[3] <= max(0, bb0[1]) + 10: dn.append((c, b))         # dấu nặng: dưới đường cơ sở (ỵ: cạnh đuôi y)
        else: body.append((c, b))                                               # râu ơ ư dính thân…
    # gom mảnh dấu trên: mảnh nằm trong mảnh khác (lòng dấu) nhập trước, rồi nhập cặp gần nhau nhất tới khi đủ số dấu
    import math
    def pts(g): return [p for c, _ in g for _, a in c for p in a if p is not None]
    def gap(g, h):
        P, Q = pts(g)[::3] or pts(g), pts(h)[::3] or pts(h)
        return min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in P for q in Q)
    groups = [[x] for x in up]
    for g in list(groups):
        b = g[0][1]
        for h in groups:
            if h is not g and h and (lambda hb: hb[0] <= b[0] and hb[1] <= b[1] and hb[2] >= b[2] and hb[3] >= b[3])(bbu([x[1] for x in h])):
                h.extend(g); g.clear(); break
    groups = [g for g in groups if g]
    nmax = max(1, len([m for m in above]))
    while len(groups) > nmax:
        best = min(((gap(groups[i], groups[j]), i, j) for i in range(len(groups)) for j in range(i + 1, len(groups))))
        _, i, j = best; groups[i].extend(groups[j]); groups.pop(j)
    kinds_above = [ABOVE2[m] for m in above if m in ABOVE2] + [TONE[m] for m in above if m in TONE]
    marks = []
    if groups:
        groups.sort(key=lambda g: bbu([x[1] for x in g])[1])          # đáy thấp nhất trước = dấu mũ / trăng
        st = any(m in ABOVE2 for m in above)
        if len(groups) == len(kinds_above):
            for g, k in zip(groups, kinds_above):
                marks.append(dict(k=k, cs=g, bb=bbu([x[1] for x in g]), st=st and k in TONE.values()))
        else:   # dấu dính nhau, không tách được → coi cả cụm là dấu mũ / trăng (hoặc dấu thanh nếu chỉ có một)
            marks.append(dict(k=kinds_above[0], cs=[x for g in groups for x in g], bb=bbu([x[1] for g in groups for x in g]), st=False, merged=True))
    if dn: marks.append(dict(k="dot", cs=dn, bb=bbu([x[1] for x in dn]), st=False))
    return dict(ch=ch, w=gs[cm[ord(ch)]].width, body=body, marks=marks, uc=L.isupper(), name=cm[ord(ch)])

def main():
    fn, out = sys.argv[1], sys.argv[2]
    f = TTFont(fn); os2 = f["OS/2"]; chars = []
    xh = getattr(os2, "sxHeight", 0) or 500; cap = getattr(os2, "sCapHeight", 0) or 700
    for ch in VN:
        r = split(f, ch)
        if not r: continue
        chars.append(dict(ch=ch, w=r["w"], uc=r["uc"], body=to_d(r["body"]),
                          m=[dict(k=m["k"], d=to_d(m["cs"]), bb=[round(v, 1) for v in m["bb"]], st=m["st"]) for m in r["marks"]]))
    # chữ thường không dấu (câu mẫu): ASCII in được + đ Đ
    gs = f.getGlyphSet(); cm = f.getBestCmap(); plain = {}
    for ch in [chr(c) for c in range(32, 127)] + ["đ", "Đ", "“", "”", "’", "—", "–", "·"]:
        if ord(ch) in cm: plain[ch] = dict(w=gs[cm[ord(ch)]].width, d=to_d(contours(gs, cm[ord(ch)])))
    D = dict(upm=f["head"].unitsPerEm, asc=f["hhea"].ascent, desc=f["hhea"].descent, xh=xh, cap=cap, chars=chars, plain=plain, kinds=KINDS)
    json.dump(D, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    n = sum(len(c["m"]) for c in chars)
    print("export_batch: %d chữ · %d dấu · %d KB" % (len(chars), n, len(json.dumps(D)) // 1024))

if __name__ == "__main__":
    main()
