"""Rà lệnh hinting TrueType từng glyph (người dùng 27/10) bằng FreeType hệ thống qua ctypes — không cần pip. Chế độ PEDANTIC, interpreter v35 (gần GDI / Word) + v40.
Mã lỗi hay gặp: 0x86 Invalid_Reference (lệnh trỏ điểm / CVT không có — thường do sửa nét mà giữ lệnh cũ). Sửa: bỏ lệnh của glyph đó (glyph.program rỗng).
usage: hintcheck.py FONT [FONT…]  → in glyph lỗi + cỡ + mã lỗi; 0 lỗi mới gửi font"""
import ctypes, ctypes.util, sys
from fontTools.ttLib import TTFont
libname = ctypes.util.find_library('freetype')
if not libname:
    libname = 'freetype.dll' if sys.platform == 'win32' else 'libfreetype.so.6'
lib = ctypes.CDLL(libname)
lib.FT_Property_Set.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_void_p]
def run(fn, ver=35):
    L=ctypes.c_void_p(); assert lib.FT_Init_FreeType(ctypes.byref(L))==0
    v=ctypes.c_uint(ver); lib.FT_Property_Set(L, b"truetype", b"interpreter-version", ctypes.byref(v))
    F=ctypes.c_void_p(); e=lib.FT_New_Face(L, fn.encode(), 0, ctypes.byref(F)); assert e==0, e
    tt=TTFont(fn); order=tt.getGlyphOrder(); cm=tt.getBestCmap(); rev={}
    for k,n in cm.items(): rev.setdefault(n,chr(k))
    bad={}
    for sz in (8,9,10,11,12,13,14,15,16,18,20,22,24,28,32,36,48,72,96):
        e=lib.FT_Set_Pixel_Sizes(F,0,sz)
        if e: bad.setdefault('<size>',set()).add((sz,hex(e))); continue
        for gi,n in enumerate(order):
            e=lib.FT_Load_Glyph(F, gi, 0x80 | 0x8)   # PEDANTIC | NO_BITMAP
            if e: bad.setdefault(n,set()).add((sz,hex(e)))
    return bad, rev
if __name__=='__main__':
    for fn in sys.argv[1:]:
        for ver in (35,40):
            bad,rev=run(fn,ver)
            print('==',fn.split('/')[-1],'v%d'%ver,'glyph lỗi:',len(bad))
            for n,v in list(bad.items())[:60]: print('   ',n,rev.get(n,''),'cỡ',sorted(x[0] for x in v)[:6],'mã',sorted(set(x[1] for x in v)))
