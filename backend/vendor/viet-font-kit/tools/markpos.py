"""Đo dấu hỏi / dấu thanh trên chữ đã shape bằng HarfBuzz: khe dấu–thân, lệch tâm dấu so với tâm thân, kích thước dấu.
usage: markpos.py FONT "ảẢủỦỷỶỏỎ"  — tách dấu = phần mực trên đỉnh chữ gốc (pathops)"""
import sys, unicodedata
import uharfbuzz as hb, pathops
from fontTools.ttLib import TTFont
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
path, chars = sys.argv[1], sys.argv[2]
f = TTFont(path); gs = f.getGlyphSet(); order = f.getGlyphOrder()
blob = hb.Blob.from_file_path(path); face = hb.Face(blob); font = hb.Font(face)
def ink(s):
    buf = hb.Buffer(); buf.add_str(s); buf.guess_segment_properties(); hb.shape(font, buf, {"kern": False})
    p = pathops.Path(); x = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        r = DecomposingRecordingPen(gs); gs[order[info.codepoint]].draw(r); r.replay(TransformPen(p.getPen(), (1, 0, 0, 1, x + pos.x_offset, pos.y_offset))); x += pos.x_advance
    return pathops.op(p, pathops.Path(), pathops.PathOp.UNION, fix_winding=True), x
def box(x0, y0, x1, y1):
    p = pathops.Path(); pen = p.getPen(); pen.moveTo((x0, y0)); pen.lineTo((x0, y1)); pen.lineTo((x1, y1)); pen.lineTo((x1, y0)); pen.closePath(); return p
for ch in chars:
    base = unicodedata.normalize("NFD", ch)[0]
    b, w = ink(base); B = b.bounds
    g, _ = ink(ch)
    m = pathops.op(g, box(-500, B[3] + 3, 2000, 3000), pathops.PathOp.INTERSECTION).bounds
    print("%s w%4d thân x%4d-%4d đỉnh %4d | dấu x%4d-%4d y%4d-%4d | khe %4d | tâm dấu - tâm thân %+4d | dấu rộng %3d cao %3d | rộng/cao thân %.2f" % (
        ch, w, B[0], B[2], B[3], m[0], m[2], m[1], m[3], m[1] - B[3], (m[0] + m[2]) / 2 - (B[0] + B[2]) / 2, m[2] - m[0], m[3] - m[1], (B[2]-B[0])/B[3]))
