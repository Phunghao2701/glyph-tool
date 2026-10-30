# brotli shim qua libbrotlienc/dec (ctypes) — đủ cho fontTools woff2
import ctypes
_e = ctypes.CDLL('libbrotlienc.so.1'); _d = ctypes.CDLL('libbrotlidec.so.1')
MODE_GENERIC, MODE_TEXT, MODE_FONT = 0, 1, 2
_e.BrotliEncoderMaxCompressedSize.restype = ctypes.c_size_t
def compress(data, mode=0, quality=11, lgwin=22, lgblock=0):
    n = len(data); cap = _e.BrotliEncoderMaxCompressedSize(ctypes.c_size_t(n)) or n + 1024
    out = ctypes.create_string_buffer(cap); sz = ctypes.c_size_t(cap)
    ok = _e.BrotliEncoderCompress(ctypes.c_int(quality), ctypes.c_int(lgwin), ctypes.c_int(mode), ctypes.c_size_t(n), ctypes.c_char_p(bytes(data)), ctypes.byref(sz), out)
    if not ok: raise RuntimeError('brotli compress failed')
    return out.raw[:sz.value]
def decompress(data):
    cap = max(1 << 20, len(data) * 20)
    while True:
        out = ctypes.create_string_buffer(cap); sz = ctypes.c_size_t(cap)
        r = _d.BrotliDecoderDecompress(ctypes.c_size_t(len(data)), ctypes.c_char_p(bytes(data)), ctypes.byref(sz), out)
        if r == 1: return out.raw[:sz.value]
        cap *= 4
        if cap > 1 << 28: raise RuntimeError('brotli decompress failed')
