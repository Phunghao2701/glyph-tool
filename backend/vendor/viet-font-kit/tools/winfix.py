"""Nâng OS/2 usWinAscent / usWinDescent cho bằng khung mực THẬT của mọi glyph (Word, Excel, app GDI trên Windows cắt mực
vượt win). Không đụng typo / hhea (khoảng dòng gốc giữ ở Mac / web / Canva). Chạy CUỐI mọi chuỗi dựng (sau anchor_marks,
horn5, stamp…): bước nào đổi vị trí dấu sau lúc nâng win sẽ làm win lại thấp hơn đỉnh — xem loi-font/dau-chong-chu-hoa-vuot-dong.md.
Chỉ cần fontTools.

usage: winfix.py FONT [--check]     --check: chỉ đo, không ghi (trả mã 1 nếu win thấp hơn đỉnh)
In ra: chữ Việt cao nhất / thấp nhất ĐO ĐƯỢC (để ghi đúng vào trang và test-tieng-viet.txt), win trước → sau,
dòng mặc định của Word cao hơn bao nhiêu % so với hhea.
CỜ TIẾNG VIỆT (người dùng 27/10, lỗi `serif.regular.condensed.contrast.ttf` VN: Word không gõ được “Ấ”): font đủ chữ Việt mà OS/2 ulCodePageRange1
thiếu bit 8 (Vietnamese 1258 — Word đọc bit này) → Word coi font không hỗ trợ tiếng Việt, gõ bằng bàn phím tiếng Việt thì
chữ có dấu bị đổi sang font khác / không hiện. winfix bật bit 8 + dải Unicode 1 (Latin-1 Sup… Ext-A), 2 (Ext-B),
6 (dấu tổ hợp U+0300), 29 (Latin Extended Additional U+1E00) nếu font có đủ chữ.
USE_TYPO_METRICS (người dùng 27/10, NGUYÊN NHÂN THẬT của lỗi `serif.regular.condensed.contrast.ttf` VN: Word gõ “NGUYỄN” ra “NGUYÊN”, Ấ mất sắc):
fsSelection bit 7 bật → Word (Windows) lấy đỉnh / đáy dòng từ typo thay vì win → typo thấp hơn mực thì CẮT dấu thanh trên
dấu mũ / trăng chữ hoa. winfix tắt bit 7 khi typo thấp hơn mực (Word chuyển sang dùng win đã nâng); --check báo ✗."""
import sys, math, unicodedata
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

fn = sys.argv[1]; CHECK = "--check" in sys.argv
f = TTFont(fn); gs = f.getGlyphSet(); cm = f.getBestCmap(); o2, hh = f["OS/2"], f["hhea"]
VN = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
VN += VN.upper()
ymax = ymin = 0; rows = []
for n in f.getGlyphOrder():
    bp = BoundsPen(gs); gs[n].draw(bp)
    if not bp.bounds: continue
    ymax = max(ymax, bp.bounds[3]); ymin = min(ymin, bp.bounds[1])
for ch in VN:
    n = cm.get(ord(ch))
    if not n: continue
    bp = BoundsPen(gs); gs[n].draw(bp)
    if bp.bounds: rows.append((ch, round(bp.bounds[3]), round(bp.bounds[1])))
top = sorted(rows, key=lambda r: -r[1]); bot = sorted(rows, key=lambda r: r[2])
def grp(rs, i):
    """gom chữ cùng độ cao: 'Ấ Ầ Ế 1180 · Ẩ 1161'"""
    out, cur, val = [], [], None
    for r in rs[:14]:
        if val is None or abs(r[i] - val) <= 2: cur.append(r[0]); val = r[i] if val is None else val
        else: out.append("%s %d" % (" ".join(cur), val)); cur, val = [r[0]], r[i]
    if cur: out.append("%s %d" % (" ".join(cur), val))
    return " · ".join(out[:4])
need_a, need_d = int(math.ceil(ymax)), int(math.ceil(-ymin))
ok = o2.usWinAscent >= need_a and o2.usWinDescent >= need_d
typo_bad = bool(o2.fsSelection >> 7 & 1) and (o2.sTypoAscender < need_a or -o2.sTypoDescender < need_d)
cut = [r[0] for r in rows if r[1] > o2.sTypoAscender] if typo_bad else []
print("USE_TYPO_METRICS: %s%s" % ("bật" if o2.fsSelection >> 7 & 1 else "tắt",
      (" · typo %d / %d thấp hơn mực → Word cắt dấu: %s ✗" % (o2.sTypoAscender, o2.sTypoDescender, "".join(cut[:20]))) if typo_bad else " ✓"))
# cờ tiếng Việt cho Word
full_vn = all(ord(c) in cm for c in VN)
UR = {1: [0x102, 0x103, 0x110, 0x111, 0x128, 0x129, 0x168, 0x169], 2: [0x1A0, 0x1A1, 0x1AF, 0x1B0], 6: [0x300, 0x301, 0x303, 0x309, 0x323], 29: [0x1EA0, 0x1EF9]}
def ur_get(b): return (getattr(o2, "ulUnicodeRange%d" % (b // 32 + 1)) >> (b % 32)) & 1
def ur_set(b): setattr(o2, "ulUnicodeRange%d" % (b // 32 + 1), getattr(o2, "ulUnicodeRange%d" % (b // 32 + 1)) | (1 << (b % 32)))
cp_ok = bool(o2.ulCodePageRange1 >> 8 & 1) if hasattr(o2, "ulCodePageRange1") else False
ur_miss = [b for b, cps in UR.items() if any(c in cm for c in cps) and not ur_get(b)]
flag_ok = (not full_vn) or (cp_ok and not ur_miss)
print("cờ tiếng Việt: %s · code page 1258 (bit 8) %s · dải Unicode thiếu %s %s" % (
    "đủ chữ Việt" if full_vn else "THIẾU chữ Việt", "có" if cp_ok else "THIẾU", ur_miss or "—", "✓" if flag_ok else "✗ Word có thể không gõ / đổi font chữ có dấu"))
if CHECK: sys.exit(0 if (ok and flag_ok and not typo_bad) else 1)
if typo_bad:
    o2.fsSelection &= ~(1 << 7)
    print("winfix: tắt USE_TYPO_METRICS — Word dùng win %d / %d (đủ mực), không cắt dấu chồng" % (max(o2.usWinAscent, need_a), max(o2.usWinDescent, need_d)))
if not flag_ok:
    if o2.version < 1: o2.version = 1
    o2.ulCodePageRange1 |= 1 << 8
    for b in ur_miss: ur_set(b)
    print("winfix: bật cờ tiếng Việt (code page 1258%s)" % ((", dải Unicode " + ", ".join(map(str, ur_miss))) if ur_miss else ""))
print("cao nhất (đo): %s · thấp nhất: %s" % (grp(top, 1), grp(bot, 2)))
print("đỉnh mọi glyph %d / đáy %d · hhea %d / %d · typo %d / %d · win %d / %d %s" % (
    need_a, -need_d, hh.ascent, hh.descent, o2.sTypoAscender, o2.sTypoDescender, o2.usWinAscent, o2.usWinDescent,
    "✓" if ok else "✗ win thấp hơn mực → Word cắt đỉnh dấu"))
if not ok:
    a0, d0 = o2.usWinAscent, o2.usWinDescent
    o2.usWinAscent = max(a0, need_a); o2.usWinDescent = max(d0, need_d)
    base = hh.ascent - hh.descent
    print("winfix: win %d / %d → %d / %d · Word (Windows) dòng mặc định cao hơn hhea %+.0f %%" % (
        a0, d0, o2.usWinAscent, o2.usWinDescent, 100.0 * ((o2.usWinAscent + o2.usWinDescent) / base - 1)))
else:
    print("winfix: win đã đủ")
if not ok or not flag_ok or typo_bad: f.save(fn)
else: print("winfix: không có gì để ghi")
