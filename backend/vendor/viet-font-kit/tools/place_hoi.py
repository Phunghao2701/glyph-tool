"""Đặt lại dấu hỏi đơn (ả ẻ ỉ ỏ ủ ỷ + hoa) cho đều: khe dấu–đỉnh thân cố định theo chữ thường / hoa,
tâm dấu lệch phải một chút so với tâm thân (đo từ một serif didone: +3…+6 % bề rộng thân).
Dấu hỏi chồng trên dấu mũ / trăng giữ nguyên chỗ vnfont đặt.
usage: place_hoi.py IN.otf OUT.otf SRC.otf hook.json cfg.json
cfg: {"gap_lc":60, "gap_uc":50, "dx_lc":0.04, "dx_uc":0.03, "s_lc":1.0, "s_uc":0.94, "dx_unit": {"a": -26}, "gap_src": true, "src_dy": 0}
     gap_src: đáy dấu hỏi lấy đúng đáy dấu sắc có sẵn của font gốc trên cùng chữ (khe gap_* chỉ dùng khi font gốc không có).
     dx_unit (tuỳ chọn): dời thêm theo đơn vị font cho từng chữ gốc, vd chữ a có chân phải làm tâm thân lệch phải → dời dấu hỏi sang trái cho khớp dấu hỏi trên ẩ."""
import sys, json, math, unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
import pathops

f = TTFont(sys.argv[1]); src = TTFont(sys.argv[3]); HOOK = json.load(open(sys.argv[4])); C = json.load(open(sys.argv[5]))
cff = f["CFF "].cff; top = cff.topDictIndex[0]; csi = top.CharStrings; NOM = getattr(top.Private, "nominalWidthX", 0)
hmtx = f["hmtx"]; cmap = f.getBestCmap(); gs = f.getGlyphSet(); sgs = src.getGlyphSet(); scm = src.getBestCmap()

def contours(gset, n):
    r = RecordingPen(); gset[n].draw(r); cs, cur = [], []
    for o_, a in r.value:
        cur.append((o_, a))
        if o_ == "closePath": cs.append(cur); cur = []
    return cs
def P(cs):
    p = pathops.Path(); pen = p.getPen()
    for c in cs:
        for o_, a in c: getattr(pen, o_)(*a)
    return p
def body_of(L):
    n = "dotlessi" if L == "i" and "dotlessi" in sgs else scm[ord(L)]
    cs = contours(sgs, n)
    if L in "iI":
        big = max(cs, key=lambda c: P([c]).bounds[3] - P([c]).bounds[1]); return P([big]).bounds
    return P(cs).bounds

hook = P([[(o_, tuple(tuple(p) for p in pts)) for o_, pts in c] for c in HOOK])
hb = hook.bounds
done = []
for cp, name in sorted(cmap.items()):
    d = unicodedata.normalize("NFD", chr(cp))
    if "̉" not in d or any(m in d for m in "̛̂̆") or len(d) < 2: continue
    L = d[0]; up = L.isupper()
    B = body_of(L)
    cs = contours(gs, name)
    keep = [c for c in cs if P([c]).bounds[1] < B[3] - 5]           # thân + dấu nặng (nếu có)
    s = C["s_uc" if up else "s_lc"]
    cx = (B[0] + B[2]) / 2 + (B[2] - B[0]) * C["dx_uc" if up else "dx_lc"] + C.get("dx_unit", {}).get(L, 0)
    y0 = B[3] + C["gap_uc" if up else "gap_lc"]
    if C.get("gap_src"):   # luật src-marks: đáy dấu hỏi = đáy dấu sắc GỐC của cùng chữ (á É Ó…), dấu mới theo vị trí dấu font gốc
        sa = scm.get(ord(unicodedata.normalize("NFC", L + "\u0301")))
        if sa:
            mk_ = [c for c in contours(sgs, sa) if P([c]).bounds[1] >= B[3] - 5]
            if mk_: y0 = P(mk_).bounds[1] + C.get("src_dy", 0)
    t = (s, 0, 0, s, cx - (hb[0] + hb[2]) / 2 * s, y0 - hb[1] * s)
    out = P(keep); hook.draw(TransformPen(out.getPen(), t))
    w = gs[name].width
    r = RecordingPen(); out.draw(r)
    t2 = T2CharStringPen(w - NOM, None)
    for o_, a in r.value: getattr(t2, o_)(*a)
    csi.charStringsIndex[csi.charStrings[name]] = t2.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
    hmtx.metrics[name] = (w, int(math.floor(out.bounds[0])))
    done.append(chr(cp))
f.save(sys.argv[2]); print("đặt lại dấu hỏi:", "".join(done))
