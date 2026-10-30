"""Khối “So vị trí cũ” cho trang duyệt: chữ VER mới tô đặc + viền nét đứt VER cũ (bật / tắt), bảng số đo dấu chồng.
usage: mk_oldnew.py OLD.otf "VER_cũ" NEW1.otf "VER_mới1" [NEW2.otf "VER_mới2" …] --chars "ấầẩẫắằẳẵẤẦẨẪẮẰẲẴ" --angle 13.9 OUT.html
Chèn OUT.html vào PAGE của content_rN.py (vd ngay trước “Số đo” của mục A). Mặc định mở sẵn (có thay đổi thì luôn hiện); --closed để thu gọn.
Không có số đo dấu chồng (font đứng) thì bỏ bảng số, chỉ còn dải chữ."""
import sys, os, json, re, subprocess, argparse
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
H = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(); ap.add_argument('pairs', nargs='+'); ap.add_argument('--chars', required=True); ap.add_argument('--angle', type=float, default=0); ap.add_argument('--closed', action='store_true')
a = ap.parse_intermixed_args(); *pairs, OUT = a.pairs
fonts = list(zip(pairs[0::2], pairs[1::2]))          # [(path, nhãn)], phần tử đầu = VER cũ
D = {'ch': a.chars, 'v': {}}
def meas(p):
    o = subprocess.run([sys.executable, '-I', os.path.join(H, 'stackdx.py'), p, str(a.angle)], capture_output=True, text=True).stdout
    return {m[0]: m[1:] for m in re.findall(r'(\S) ([+-]\d+)/(\d+)/(\d+)', o)}
M = {}
for i, (p, lab) in enumerate(fonts):
    f = TTFont(p); gs = f.getGlyphSet(); cm = f.getBestCmap(); g = {}
    for c in a.chars:
        pen = SVGPathPen(gs); gs[cm[ord(c)]].draw(pen); g[c] = [pen.getCommands(), gs[cm[ord(c)]].width]
    D['v'][str(i)] = g; M[str(i)] = meas(p)
tab = {}
for i in range(1, len(fonts)):
    k = str(i); h = '<table><tr><th>chữ</th><th>%s: lệch tâm / khe dọc / khe nhỏ nhất</th><th>%s</th><th>đổi</th></tr>' % (fonts[0][1], fonts[i][1])
    for c in a.chars:
        x, y = M['0'].get(c, ['', '', '']), M[k].get(c, ['', '', ''])
        if not any(x) and not any(y): continue          # chữ không có dấu chồng: không in dòng rỗng “/ /”
        h += '<tr><td>%s</td><td>%s / %s / %s</td><td>%s / %s / %s</td><td>%s</td></tr>' % (c, *x, *y, '' if x == y else 'đổi')
    tab[k] = (h + '</table>') if h.count('<tr>') > 1 else ''
t = open(os.path.join(H, 'oldnew_block.tpl.html')).read()
# nút chọn VER mới + nhãn VER cũ
btn = ''.join('<button type="button" data-v="%d" aria-pressed="%s">%s</button>' % (i, 'true' if i == 1 else 'false', fonts[i][1]) for i in range(1, len(fonts)))
t = t.replace('VER 7', '\x00OLD\x00')            # nhãn VER cũ của mẫu — đổi SAU khi chèn nút, kẻo trùng tên VER mới (vd “VER 7”)
t = re.sub(r'<button type="button" data-v="8".*?</button><button type="button" data-v="9".*?</button>', btn, t, flags=re.S)
t = t.replace('\x00OLD\x00', fonts[0][1]).replace("cur='8'", "cur='1'").replace("D.v['7']", "D.v['0']")
t = t.replace('<div class="sec" data-sec="O"><div class="sec-h"><div class="badge">D</div><div class="h2box"><div class="h2row"><h2>So vị trí cũ</h2>',
              '<div class="onbox"><div class="h2row"><h3 style="margin:14px 0 0;font-size:17px">So vị trí cũ · nét đứt = %s</h3>' % fonts[0][1])
t = t.replace('</div></details></div></div></div>\n<div class="on-bar"', '</div></details></div>\n<div class="on-bar"').replace('<div class="notewrap" data-note="O"></div></div>', '</div>')
t = t.replace('__ONDATA__', json.dumps(D, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')).replace('__ONTAB__', json.dumps(tab, ensure_ascii=False).replace('</', '<\\/'))
t = t.replace("var rows=[D.ch.slice(0,8),D.ch.slice(8)]", "var rows=[];for(var i=0;i<D.ch.length;i+=8)rows.push(D.ch.slice(i,i+8))")
# gọn (luật người dùng 26/10): không có số đo dấu chồng (font đứng — stackdx đo cho font nghiêng) thì bỏ bảng số;
# --closed: cả khối thu gọn trong <details>
if not any(M[k] for k in M):
    t = t.replace('<div class="on-tab" id="on-tab"></div>', '').replace("document.getElementById('on-tab').innerHTML=", "var _ot=document.getElementById('on-tab');if(_ot)_ot.innerHTML=")
if a.closed:   # mặc định MỞ (luật người dùng 26/10: có thay đổi thì luôn hiện)
    t = t.replace('<div class="onbox"><div class="h2row"><h3 style="margin:14px 0 0;font-size:17px">So vị trí cũ · nét đứt = %s</h3>' % fonts[0][1],
                  '<details class="more onbox"><summary>So vị trí cũ · nét đứt = %s</summary><div class="h2row" hidden><h3>So vị trí cũ</h3>' % fonts[0][1], 1)
    i = t.index('</div>\n<style>'); t = t[:i] + '</details>' + t[i + len('</div>'):]
open(OUT, 'w').write(t); print('khối so vị trí cũ:', OUT, len(t) // 1024, 'KB')
