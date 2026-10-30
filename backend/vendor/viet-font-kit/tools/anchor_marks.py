"""Đặt dấu THEO ANCHOR CỦA FONT GỐC (luật src-marks, “xét dấu font gốc trước”).
Font gốc có GPOS mark / mkmk (font Google hay có) đã định sẵn vị trí + khoảng cách mọi dấu, kể cả dấu chồng
(Â + dấu huyền → dấu huyền nằm trên dấu mũ theo anchor mkmk). Script dựng lại chữ Việt y như HarfBuzz xếp chuỗi
tổ hợp (NFD) trên font gốc:
  * dấu font gốc có (sắc, huyền, ngã, mũ, trăng) → nét gốc, đúng chỗ anchor đặt;
  * dấu font gốc thiếu → mượn anchor:  hỏi = anchor dấu trên (proxy U+0312, không ghép sẵn với nguyên âm),
    đáy dấu hỏi cách anchor bằng đúng khe của dấu sắc gốc;  nặng = anchor dấu dưới (proxy U+0326),
    đỉnh dấu nặng cách anchor như dấu phẩy dưới gốc; dấu nặng chạm thân (ỵ) thì dời phải tới khi đủ khe.
  * chữ có râu (ơ ư…) bỏ qua: horn5.py dựng từ chữ trơn (ỏ ọ…) đã đặt theo anchor.
Chạy sau place_hoi, trước horn5 (build.sh tự gọi khi config.json có "anchor_marks").
usage: anchor_marks.py IN.otf OUT.otf SRC.otf|ttf config.json
config: "anchor_marks": {"stack_hook": "hook"|"hook_s", "dot_gap": 40, "hook_dx": 0,
        "hook_uc": 1.0, "hook_stack": 1.0, "hook_uc_stack_flat": 1.0}   (cỡ dấu hỏi chữ hoa / khi chồng / chữ hoa chồng dẹt — lấy theo font mẫu)
marks: "hook", "hook_s" (+ tuỳ chọn "hook_uc", "hook_s_uc": bản dày bù co giãn, tools/hook_fit.py tạo)
build by @nhatmotion"""
import sys, json, math, unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
import uharfbuzz as hb
import pathops
from shapely.geometry import Polygon
from shapely.ops import unary_union

IN, OUT, SRC, CFGP = sys.argv[1:5]
CFG = json.load(open(CFGP)); AC = CFG.get("anchor_marks", {})
f = TTFont(IN); src = TTFont(SRC)
cff = f["CFF "].cff; top = cff.topDictIndex[0]; csi = top.CharStrings; NOM = getattr(top.Private, "nominalWidthX", 0)
hm = f["hmtx"]; cm = f.getBestCmap(); sgs = src.getGlyphSet(); sorder = src.getGlyphOrder()
face = hb.Face(hb.Blob.from_file_path(SRC)); hfont = hb.Font(face)

# ---- anchor dấu (mark) trong font gốc ----
MA = {}
for lk in src["GPOS"].table.LookupList.Lookup:
    for st in lk.SubTable:
        if lk.LookupType == 9: st = st.ExtSubTable
        t = getattr(st, "LookupType", lk.LookupType)
        if t == 4:
            for g, r in zip(st.MarkCoverage.glyphs, st.MarkArray.MarkRecord): MA.setdefault(g, (r.MarkAnchor.XCoordinate, r.MarkAnchor.YCoordinate))
def rec(gset, g):
    r = DecomposingRecordingPen(gset); gset[g].draw(r); return r.value
def bb_ops(ops):
    b = BoundsPen(None)
    for o, a in ops: getattr(b, o)(*a)
    return b.bounds
def tf_ops(ops, t):
    r = RecordingPen(); tp = TransformPen(r, t)
    for o, a in ops: getattr(tp, o)(*a)
    return r.value
def jc(js): return [(o, tuple(tuple(p) for p in a)) for c in js for o, a in c]
def poly(ops):
    rings, cur, p0 = [], [], None
    for o, a in ops:
        if o == "moveTo": cur = [a[0]]
        elif o == "lineTo": cur.append(a[0])
        elif o in ("curveTo", "qCurveTo"):
            q0 = cur[-1]
            pts = [q0] + list(a)
            for k in range(1, 9):
                t = k / 8
                if len(pts) == 4:
                    u = 1 - t; cur.append(tuple(u**3*pts[0][i] + 3*u*u*t*pts[1][i] + 3*u*t*t*pts[2][i] + t**3*pts[3][i] for i in (0, 1)))
                else: cur.append(tuple(pts[0][i] + (pts[-1][i] - pts[0][i]) * t for i in (0, 1)))
        elif o in ("closePath", "endPath"):
            if len(cur) > 2: rings.append(Polygon(cur).buffer(0))
            cur = []
    return unary_union(rings)

MK = CFG.get("marks", {})
HOOK = jc(MK["hook"]); HOOK_S = jc(MK.get(AC.get("stack_hook", "hook"), MK["hook"])); DOT = jc(MK["dot"])
# dấu hỏi riêng cho chữ hoa / chữ hoa chồng (tuỳ chọn): cùng dáng, bề dày bù cho phép co (dày nhất vẫn = dấu ngã, xem hook_fit.py)
HOOK_UC = jc(MK["hook_uc"]) if "hook_uc" in MK else None
HOOK_S_UC = jc(MK["hook_s_uc"]) if "hook_s_uc" in MK else None
# khe dấu sắc gốc: đáy dấu sắc − y anchor của nó;  dấu phẩy dưới gốc: đỉnh − y anchor
ac_b = bb_ops(rec(sgs, "acutecomb")); GAP_TOP = ac_b[1] - MA["acutecomb"][1]
cb = bb_ops(rec(sgs, "uni0326")) if "uni0326" in sgs else None; GAP_BOT = (cb[3] - MA["uni0326"][1]) if cb else -40
HB_ = bb_ops(HOOK); HSB = bb_ops(HOOK_S); DB = bb_ops(DOT)
PROXY = {"̉": "̒", "̣": "̦"}

done, skipped, over = [], [], []
VN = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộùúủũụỳýỷỹỵ"
for ch in VN + VN.upper():
    cp = ord(ch); n = cm.get(cp)
    if not n: continue
    if cp in src.getBestCmap(): continue                      # chữ font gốc có sẵn: giữ nguyên
    if ch in AC.get("skip", "ĩĨ"): continue                     # ĩ Ĩ: giữ dấu ngã đã thu hẹp (addons, lỗi A6) cho khỏi đè chữ bên cạnh
    d = unicodedata.normalize("NFD", ch)
    seq = "".join(PROXY.get(c, c) for c in d)
    buf = hb.Buffer(); buf.add_str(seq); buf.guess_segment_properties(); hb.shape(hfont, buf, {"kern": False})
    names = [sorder[i.codepoint] for i in buf.glyph_infos]
    if any(x == ".notdef" for x in names): skipped.append(ch); continue
    x = 0; ops = []; body = None; stacked = sum(1 for c in d[1:] if c in "̂̆") > 0
    for gi, (info, pos) in enumerate(zip(buf.glyph_infos, buf.glyph_positions)):
        g = names[gi]; ox, oy = x + pos.x_offset, pos.y_offset
        if gi == 0: body = rec(sgs, g); x0b, y0b = ox, oy; ops += tf_ops(body, (1, 0, 0, 1, ox, oy))
        elif g == "uni0312" and "̉" in d:                 # dấu hỏi tại anchor dấu trên
            ax, ay = ox + MA[g][0], oy + MA[g][1]
            H = (HOOK_S_UC or HOOK_S) if (stacked and ch.isupper()) else HOOK_S if stacked else (HOOK_UC or HOOK) if ch.isupper() else HOOK
            B = bb_ops(H)
            cx = ax + AC.get("hook_dx", 0); y0 = ay + GAP_TOP
            # cỡ dấu hỏi theo font mẫu: chữ hoa × hook_uc, dấu chồng × hook_stack, chữ hoa chồng dẹt thêm × hook_uc_stack_flat
            up_ = ch.isupper(); sx_ = (AC.get("hook_stack", 1.0) if stacked else 1.0) * (AC.get("hook_uc", 1.0) if up_ else 1.0)
            sy_ = sx_ * (AC.get("hook_uc_stack_flat", 1.0) if (up_ and stacked) else 1.0)
            ops += tf_ops(H, (sx_, 0, 0, sy_, cx - (B[0] + B[2]) / 2 * sx_, y0 - B[1] * sy_))
        elif g == "uni0326" and "̣" in d:                 # dấu nặng tại anchor dấu dưới
            ax, ay = ox + MA[g][0], oy + MA[g][1]
            ytop = ay + GAP_BOT; t = [1, 0, 0, 1, ax - (DB[0] + DB[2]) / 2, ytop - DB[3]]
            bp = poly(tf_ops(body, (1, 0, 0, 1, x0b, y0b))); need = AC.get("dot_gap", 40) if ch == "ỵ" else AC.get("dot_min", 10)
            for _ in range(80):                                # ỵ: chấm chạm đuôi → dời phải tới khi đủ khe
                if poly(tf_ops(DOT, tuple(t))).distance(bp) >= need: break
                t[4] += 4
            ops += tf_ops(DOT, tuple(t))
        else:
            ops += tf_ops(rec(sgs, g), (1, 0, 0, 1, ox, oy))
        x += pos.x_advance
    w = hm[n][0]
    pp = pathops.Path(); pen = pp.getPen()                    # hợp nét + thống nhất chiều contour (nét gốc .ttf ngược chiều CFF)
    for o, a in ops: getattr(pen, o)(*a)
    pp = pathops.op(pp, pathops.Path(), pathops.PathOp.UNION, fix_winding=True)
    r_ = RecordingPen(); pp.draw(r_); ops = r_.value
    t2 = T2CharStringPen(w - NOM, None)
    for o, a in ops: getattr(t2, o)(*a)
    csi.charStringsIndex[csi.charStrings[n]] = t2.getCharString(private=top.Private, globalSubrs=cff.GlobalSubrs)
    b = bb_ops(ops); hm.metrics[n] = (w, int(math.floor(b[0])))
    bb0 = bb_ops(tf_ops(body, (1, 0, 0, 1, x0b, y0b)))          # chỉ tính phần DẤU chìa ra ngoài hơn thân chữ gốc
    l_, r_ = min(0, b[0] - min(0, bb0[0])), max(0, b[2] - max(w, bb0[2]))
    if l_ < -2 or r_ > 2: over.append("%s %+d/%+d" % (ch, round(l_), round(r_)))
    done.append(ch)
from fontTools.pens.basePen import NullPen
for g in f.getGlyphOrder():
    c = csi[g]; c.draw(NullPen()); assert abs(c.width - hm[g][0]) < 0.5, g
f.save(OUT)
print("anchor_marks: %d chữ theo anchor font gốc · khe trên %d · khe dưới %d%s%s" % (len(done), GAP_TOP, GAP_BOT,
      (" · bỏ qua " + "".join(skipped)) if skipped else "", (" · chìa khỏi advance: " + ", ".join(over)) if over else ""))
