"""CỔNG KIỂM WORD — chạy trên MỌI file font trước khi gửi người dùng (người dùng 27/10: “lo user lặp lại lỗi mất dấu ở Word”).
Gom mọi lỗi Word / Windows đã gặp vào một lệnh; chỉ gửi font khi in “KIỂM WORD: ĐẠT”. Premiere / web / Mac hiện đúng KHÔNG có nghĩa Word đúng.

  1. Đủ chữ Việt   134 chữ + đ Đ có trong cmap, có nét (không rỗng)
  2. Đỉnh dòng     USE_TYPO_METRICS bật mà typo thấp hơn mực → Word cắt dấu chồng chữ hoa (Ấ Ễ Ố → Â Ê Ô)   [A32]
  3. Win           usWinAscent / Descent ≥ mực thật (Windows GDI cắt phần vượt win)                          [A30]
  4. Cờ tiếng Việt OS/2 code page 1258 (bit 8) + dải Unicode Việt                                             [A31]
  5. Hinting       lệnh hinting từng glyph chạy không lỗi (FreeType v35 ≈ GDI, cỡ 8–96 px)                    [A32]
  6. GSUB / GPOS   không nhóm ngôn ngữ nào khai cùng một tính năng 2 lần (vd ccmp kép)                       [A32]
  7. Độ rộng CFF   (font .otf) độ rộng trong charstring = hmtx (Word hở khoảng sau chữ có dấu)               [A1]
  8. lsb = xMin    (font .ttf) hmtx lsb của glyph dựng mới = xMin, lệch thì cả chữ bị dời                    [A36]
--fix: tự sửa 2–6 (gọi winfix.py; bỏ lệnh hinting glyph lỗi; gộp tính năng trùng), lưu đè, kiểm lại. 1 và 7 phải sửa ở bước dựng.
usage: kiemword.py FONT [FONT…] [--fix]     mã thoát 0 = mọi file ĐẠT
build by @nhatmotion"""
import sys, os, subprocess
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
T = os.path.dirname(os.path.abspath(__file__))
VN = "àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ"
VN += VN.upper()

def langsyses(t):
    for sr in t.ScriptList.ScriptRecord:
        if sr.Script.DefaultLangSys: yield sr.ScriptTag, "dflt", sr.Script.DefaultLangSys
        for l in sr.Script.LangSysRecord: yield sr.ScriptTag, l.LangSysTag, l.LangSys

def dup_features(f):
    out = []
    for tag in ("GSUB", "GPOS"):
        if tag not in f: continue
        t = f[tag].table
        if not t.ScriptList or not t.FeatureList: continue
        FR = t.FeatureList.FeatureRecord
        for st, lt, ls in langsyses(t):
            tags = [FR[i].FeatureTag for i in ls.FeatureIndex]
            d = sorted(set(x for x in tags if tags.count(x) > 1))
            if d: out.append("%s %s/%s: %s" % (tag, st, lt.strip(), ",".join(d)))
    return out

def merge_dup_features(f):
    n = 0
    for tag in ("GSUB", "GPOS"):
        if tag not in f: continue
        t = f[tag].table; FR = t.FeatureList.FeatureRecord
        for _, _, ls in langsyses(t):
            seen, keep = {}, []
            for i in ls.FeatureIndex:
                tg = FR[i].FeatureTag
                if tg in seen:
                    j = seen[tg]; lk = sorted(set(FR[j].Feature.LookupListIndex) | set(FR[i].Feature.LookupListIndex))
                    FR[j].Feature.LookupListIndex = lk; FR[j].Feature.LookupCount = len(lk); n += 1
                else: seen[tg] = i; keep.append(i)
            ls.FeatureIndex = keep; ls.FeatureCount = len(keep)
        used = set(i for _, _, ls in langsyses(t) for i in ls.FeatureIndex)
        new, nfr = {}, []
        for i, r in enumerate(FR):
            if i in used: new[i] = len(nfr); nfr.append(r)
        for _, _, ls in langsyses(t): ls.FeatureIndex = [new[i] for i in ls.FeatureIndex]
        t.FeatureList.FeatureRecord = nfr; t.FeatureList.FeatureCount = len(nfr)
    return n

def hint_errors(fn):
    try:
        import hintcheck
        bad = {}
        for v in (35, 40):
            b, _ = hintcheck.run(fn, v)
            for k, x in b.items(): bad.setdefault(k, set()).update(x)
        return bad, None
    except Exception as e:   # không có libfreetype → không kiểm được, báo rõ (không coi là đạt)
        return {}, str(e)

def check(fn):
    f = TTFont(fn); o2 = f["OS/2"]; cm = f.getBestCmap(); gs = f.getGlyphSet(); R = []
    def add(ok, name, msg): R.append((ok, name, msg))
    # 1 đủ chữ
    miss = [c for c in VN if ord(c) not in cm]
    empty = []
    for c in VN:
        if ord(c) in cm:
            bp = BoundsPen(gs); gs[cm[ord(c)]].draw(bp)
            if not bp.bounds: empty.append(c)
    add(not miss and not empty, "Đủ chữ Việt", "thiếu: %s · rỗng: %s" % ("".join(miss) or "—", "".join(empty) or "—"))
    # đo mực
    ymax = ymin = 0; top = {}
    for n in f.getGlyphOrder():
        bp = BoundsPen(gs); gs[n].draw(bp)
        if bp.bounds: ymax = max(ymax, bp.bounds[3]); ymin = min(ymin, bp.bounds[1])
    for c in VN:
        if ord(c) in cm:
            bp = BoundsPen(gs); gs[cm[ord(c)]].draw(bp)
            if bp.bounds: top[c] = bp.bounds[3]
    # 2 USE_TYPO_METRICS
    ut = bool(o2.fsSelection >> 7 & 1)
    line_top = o2.sTypoAscender if ut else o2.usWinAscent
    cut = "".join(c for c, y in top.items() if y > line_top)
    typo_bad = ut and (o2.sTypoAscender < ymax or o2.sTypoDescender > ymin)
    add(not typo_bad, "Đỉnh dòng Word", "USE_TYPO_METRICS %s · Word lấy đỉnh %d · chữ bị cắt: %s" % ("bật" if ut else "tắt", line_top, cut or "—"))
    # 3 win
    add(o2.usWinAscent >= ymax and o2.usWinDescent >= -ymin, "Win ≥ mực", "win %d / %d · mực %d / %d" % (o2.usWinAscent, o2.usWinDescent, round(ymax), round(ymin)))
    # 4 cờ tiếng Việt
    cp = bool(getattr(o2, "ulCodePageRange1", 0) >> 8 & 1)
    add(cp, "Cờ tiếng Việt", "code page 1258 %s" % ("có" if cp else "THIẾU"))
    # 5 hinting
    if "glyf" in f and ("fpgm" in f or "prep" in f):
        bad, err = hint_errors(fn)
        if err: add(False, "Hinting", "không chạy được FreeType (%s) — kiểm tay bằng hintcheck.py" % err)
        else: add(not bad, "Hinting", "glyph lỗi: %s" % (", ".join(list(bad)[:8]) or "—"))
    else: add(True, "Hinting", "không có hinting")
    # 6 tính năng trùng
    d = dup_features(f)
    add(not d, "GSUB / GPOS", "tính năng khai 2 lần: %s" % ("; ".join(d[:4]) or "—"))
    # 7 CFF width
    if "CFF " in f:
        cff = f["CFF "].cff; td = cff.topDictIndex[0]; cs = td.CharStrings; hm = f["hmtx"]; wrong = []
        for n in f.getGlyphOrder():
            c = cs[n]; c.decompile()
            w = c.width if hasattr(c, "width") else None
            if w is not None and w != hm[n][0]: wrong.append(n)
        add(not wrong, "Độ rộng CFF", "lệch hmtx: %s" % (", ".join(wrong[:8]) or "—"))
    # 8 lsb TrueType = xMin (A36: lệch → FreeType / Chrome / Word dời cả chữ sang trái đúng xMin)
    if "glyf" in f:
        g = f["glyf"]; hm = f["hmtx"]; bl = []
        for n in f.getGlyphOrder():
            gl = g[n]
            if gl.numberOfContours == 0: continue
            gl.recalcBounds(g)
            if hm[n][1] != gl.xMin: bl.append(n)
        add(not bl, "lsb = xMin", "lệch: %s" % (", ".join(bl[:8]) + (" (+%d)" % (len(bl) - 8) if len(bl) > 8 else "") or "—"))
    return R

def fix(fn):
    subprocess.run([sys.executable, "-X", "utf8", "-I", os.path.join(T, "fixlsb.py"), fn], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, "-X", "utf8", "-I", os.path.join(T, "winfix.py"), fn], check=True, stdout=subprocess.DEVNULL)
    f = TTFont(fn); changed = False
    if merge_dup_features(f): changed = True
    if "glyf" in f:
        bad, err = hint_errors(fn)
        if bad and not err:
            from fontTools.ttLib.tables import ttProgram
            for n in bad:
                if n.startswith("<"): continue
                g = f["glyf"][n]; g.expand(f["glyf"])
                p = ttProgram.Program(); p.fromBytecode(b""); g.program = p
            changed = True; print("  bỏ lệnh hinting lỗi: %s" % ", ".join(n for n in bad if not n.startswith("<")))
    if changed: f.save(fn)

def main():
    FIX = "--fix" in sys.argv
    FILES = [a for a in sys.argv[1:] if not a.startswith("--")]
    ALL = True
    for fn in FILES:
        if FIX: fix(fn)
        R = check(fn); ok = all(r[0] for r in R); ALL &= ok
        print("== %s" % os.path.basename(fn))
        for good, name, msg in R: print("  %s %-14s %s" % ("✓" if good else "✗", name, msg))
        print("KIỂM WORD: %s" % ("ĐẠT" if ok else "CHƯA ĐẠT — %s" % ("sửa ở bước dựng rồi chạy lại" if FIX else "chạy lại với --fix")))
    sys.exit(0 if ALL else 1)

if __name__ == '__main__':
    main()
