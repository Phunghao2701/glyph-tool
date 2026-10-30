"""Assemble the font-review page from the VibeEdit review template infrastructure.
usage: build_page.py TPL_DIR R_DIR OUT.html CONTENT.py
CONTENT.py defines ROUND, SLUG, SUMHEAD, TITLE, PAGE (html inside .wrap) using cv(), dec(), fb(), sec_done(), ED_HTML."""
import sys, json, re, html, os, runpy
TPL, R, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
# round text: 4th arg, else R/content.py, else the round-1 example next to this script
CONTENT = sys.argv[4] if len(sys.argv) > 4 else next(p for p in [os.path.join(R, 'content.py'), os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content_template.py')] if os.path.exists(p))
css_parts = open(TPL + '/styles.css').read().split('\n/*----*/\n')
TCSS = '\n'.join('<style>' + c + '</style>' for c in css_parts[1:])   # [0] is the publish skeleton reset
JS = open(TPL + '/script1.js').read()
JS2 = open(TPL + '/script2.js').read()
NOFONT = not os.path.exists(R + '/A.woff2')   # người dùng quên gửi font: trang hiện trạng thái “Chưa có font” (VK.nofont)
P = json.load(open(R + '/panels.json')) if os.path.exists(R + '/panels.json') else {}
EDJS = open(os.environ.get('EDITOR_JS', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'editor.js'))).read()
DATA = (open(R + '/editor.json').read() if os.path.exists(R + '/editor.json') else '{}').replace('</', '<\\/')

# ---- adapt template JS (constants only; infrastructure stays verbatim) ----
def adapt_js(JS, ROUND, SLUG, SUMHEAD):
    D = 'fontvn/%s-r%d' % (SLUG, ROUND)
    JS = JS.replace("placeholder=\"Feedback vòng 11…\"", "placeholder=\"Feedback vòng %d…\"" % ROUND)
    JS = JS.replace("var L = ['VibeEdit · dev_99.37 · vòng 11', ''];", "var L = [%s, ''];" % json.dumps(SUMHEAD, ensure_ascii=False))
    JS = JS.replace("var DOC = 'review/dev99-37', ANNDOC = 'review/dev99-37/ann1/'", "var DOC = '%s', ANNDOC = '%s/ann1/'" % (D, D))
    JS = JS.replace("notesR11: notes, attR11: att, round: 11", "notesR%d: notes, attR%d: att, round: %d" % (ROUND, ROUND, ROUND))
    JS = JS.replace("var n = v.notesR11 || {};", "var n = v.notesR%d || {};" % ROUND).replace("att = v.attR11 || {};", "att = v.attR%d || {};" % ROUND)
    JS = JS.replace("window.__ve37 = { ANN: ANN, picks: picks };", "window.__fv = { ANN: ANN, picks: picks };")
    for a, b in [("setStatus('lưu lỗi (' + ((e && e.code) || 'không rõ') + ') — chép khối Tổng hợp gửi Claude')", "setStatus('lưu lỗi')"),
                 ("setStatus('<b>đã lưu</b> · ' + new Date().toLocaleTimeString('vi-VN'))", "setStatus('<b>đã lưu</b> ' + new Date().toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'}))"),
                 ("'không kết nối được nơi lưu — lựa chọn chỉ nằm trên trang này; chép khối Tổng hợp gửi Claude'", "'chưa lưu được'"),
                 ("'nơi lưu lỗi — chép khối Tổng hợp gửi Claude'", "'lưu lỗi'"),
                 ("'<b>đã nạp lựa chọn cũ</b> · tự lưu khi bấm'", "'<b>tự lưu</b>'"), ("'<b>sẵn sàng</b> · tự lưu khi bấm'", "'<b>tự lưu</b>'"),
                 ("L.push('Ghi chú ' + s + ': '", "L.push('Ghi chú ' + ((window.__SECN || {})[s] || s) + ': '")]:
        JS = JS.replace(a, b)
    JS = JS.replace("'ABCDEFGH'.split('')", "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')")
    JS = JS.replace("  return L.join('\\n').trim();\n}", "  if (window.__asSummary) { var as2 = window.__asSummary(); if (as2) L.push(as2); }\n  if (window.__edSummary) { var es = window.__edSummary(); if (es) L.push(es); }\n  if (window.__bSummary) { var bs = window.__bSummary(); if (bs) L.push(bs); }\n  return L.join('\\n').trim();\n}")
    JS = JS.replace("useP.then(function(d){\n  db = d;", "useP.then(function(d){\n  db = d; if (window.__edDb) window.__edDb(d); if (window.__asDb) window.__asDb(d);")
    for need in [D, "notesR%d" % ROUND, "__edSummary", "__edDb"]:
        assert need in JS, need
    return JS, D

def news(title, items):
    """khối “Điểm mới vòng này” — đặt ĐẦU trang (ngay dưới thanh trạng thái): phát hiện / thay đổi quan trọng nhất của vòng, mỗi ý một dòng"""
    return ('<section class="news" aria-label="%s"><b class="news-t">%s</b><ul>%s</ul></section>' % (html.escape(title), html.escape(title), ''.join('<li>%s</li>' % x for x in items)))

def keynote(round_no, body_html):  # CŨ (tới vòng 7) — từ vòng 8 dùng cite() [n] thay khối nguồn
    """nguồn chính (Donny Trương…): vòng 1 mở sẵn; từ vòng 2 thu gọn — người dùng đã đọc rồi"""
    return ('<div class="keynote">%s</div>' % body_html) if round_no <= 1 else ('<details class="keynote kn-fold"><summary>Nguồn chính · Donny Trương (đã đọc ở vòng 1)</summary>%s</details>' % body_html)

def fb(title, rows):
    """read-only feedback table of an earlier round: rows = [(anh ghi, mình hiểu)]"""
    tr = ''.join('<tr><td class="quote-cell">%s</td><td>%s</td></tr>' % r for r in rows)
    return '<details class="fbold"><summary>%s</summary><div class="tbwrap"><table class="tb"><tr><th>Anh ghi</th><th>Mình hiểu</th></tr>%s</table></div></details>' % (title, tr)

def sec_done(letter, h2, inner):
    return ('<div class="sec is-collapsed" data-sec="%s"><button class="sec-tog" type="button" aria-expanded="false"><div class="badge ok">%s</div>'
            '<div><h2>%s</h2><p>đã chốt hết</p></div><span class="chev">▾</span></button><div class="sec-body">%s</div></div>') % (letter, letter, h2, inner)

def cv(cid, panels, labels, cls):
    x, out, H = 16, [], 0
    for i, lb, c in zip(panels, labels, cls):
        p = P[str(i)]
        out.append('<div class="cvi" style="left:%dpx;top:16px;width:%dpx"><div class="cvl %s">%s</div><img src="%s" width="%d" height="%d" alt="%s"></div>' % (x, p['w'], c, lb, p['uri'], p['w'], p['h'], html.escape(lb)))
        x += p['w'] + 18; H = max(H, p['h'])
    W = x - 18 + 16; Ht = 16 + 24 + H + 16
    return '<div class="cv" id="cv-%s" width="%d" height="%d" style="width:%dpx;height:%dpx">%s</div>' % (cid, W, Ht, W, Ht, ''.join(out))

def dec(key, mk, q, sub, picks, done=None):
    b = ''.join('<button class="pick%s" data-v="%s" aria-pressed="%s"%s><b>%s</b>%s%s</button>' % (
        '', v, 'true' if on else 'false', ' disabled' if done else '', v, txt, ' <span class="rec">đề xuất</span>' if rec else '')
        for v, txt, on, rec in picks)
    return ('<div class="dec%s"><div class="mk">%s<small>%s</small></div><div class="body"><div class="q">%s<small>%s</small></div>'
            '<div class="picks" data-key="%s">%s</div></div></div>') % (' dec-done' if done else ' dec-new', mk, done or 'MỚI', q, sub, key, b)

ED_HTML = '''
<div class="ed" id="ed">
 <div class="ed-left">
  <div class="ed-bar" role="toolbar" aria-label="Công cụ vẽ vector">
    <button type="button" class="ann-b" data-tool="select" aria-pressed="true" title="Chọn / kéo điểm (V)" aria-label="Chọn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3l14 7-6 1.6L10.4 18z"/></svg></button>
    <div class="ed-pg"><button type="button" class="ann-b ed-pgb" aria-pressed="false" aria-expanded="false" aria-haspopup="menu" title="Nhóm bút vector — bấm để mở: bút, thêm / xoá điểm neo, đổi điểm góc" aria-label="Nhóm bút vector"><span class="ed-pgi-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21l-6.5-9.5L8 4h8l2.5 7.5z"/><path d="M12 21v-7.2"/><circle cx="12" cy="12" r="1.7"/><path d="M8 4h8"/></svg></span><span class="ed-pgt" aria-hidden="true"></span></button>
    <div class="ed-pgf" role="menu" aria-label="Nhóm bút vector" hidden><button type="button" class="ed-pgi" role="menuitemradio" data-tool="pen" aria-pressed="false" title="Bấm = điểm góc, bấm kéo = điểm mượt, bấm điểm đầu để khép. Chưa vẽ: bấm lên đường = thêm điểm, bấm vào điểm = xoá điểm, KÉO điểm = dời điểm. Giữ Ctrl / ⌘ = kéo điểm neo, tay nắm như công cụ chọn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21l-6.5-9.5L8 4h8l2.5 7.5z"/><path d="M12 21v-7.2"/><circle cx="12" cy="12" r="1.7"/><path d="M8 4h8"/></svg><span>Bút vector</span><kbd>P</kbd></button><button type="button" class="ed-pgi" role="menuitemradio" data-tool="addpt" aria-pressed="false" title="Bấm lên đường viền để chèn điểm, hình không đổi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 21l-5-8 2-6.5h6l2 6.5z"/><path d="M10 21v-6"/><circle cx="10" cy="13" r="1.4"/><path d="M18.5 3v6M15.5 6h6"/></svg><span>Thêm điểm neo</span><kbd>+</kbd></button><button type="button" class="ed-pgi" role="menuitemradio" data-tool="delpt" aria-pressed="false" title="Bấm vào điểm để bỏ, đường tự nối lại mượt"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M10 21l-5-8 2-6.5h6l2 6.5z"/><path d="M10 21v-6"/><circle cx="10" cy="13" r="1.4"/><path d="M15.5 6h6"/></svg><span>Xoá điểm neo</span><kbd>−</kbd></button><button type="button" class="ed-pgi" role="menuitemradio" data-tool="convert" aria-pressed="false" title="Bấm điểm mượt = thành điểm góc (bỏ tay nắm); bấm kéo điểm góc = kéo ra tay nắm mượt; kéo tay nắm = bẻ góc"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 20L12 6l8 14"/><path d="M6.5 10.5h11" stroke-dasharray="2 2"/><rect x="10.3" y="4.3" width="3.4" height="3.4" fill="currentColor"/></svg><span>Đổi điểm góc / mượt</span><kbd>⇧C</kbd></button></div></div>
    <button type="button" class="ann-b" data-tool="brush" aria-pressed="false" title="Cọ — vẽ tay nét dày, mình sẽ đổi thành outline (B)" aria-label="Cọ"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18.5 3.5a2 2 0 0 1 2.8 2.8L12 15.6 9.2 12.8z"/><path d="M8.5 13.5c-2.5 0-4 1.8-4 4 0 1.3-.7 2.2-1.5 2.5 1 .7 2.4 1 3.8 1 2.6 0 4.7-2 4.7-4.6z"/></svg></button>
    <button type="button" class="ann-b" data-tool="comp" aria-pressed="false" title="Thành phần — bấm chọn 1 phần của chữ (thân, dấu, móc) rồi kéo; mỗi phần có tâm khối riêng (C)" aria-label="Thành phần"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M12 8.5v7M8.5 12h7"/></svg></button>
    <span class="ann-sep"></span>
    <button type="button" class="ann-b" data-ed="undo" title="Hoàn tác (Ctrl+Z)" aria-label="Hoàn tác"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 14L4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11"/></svg></button>
    <button type="button" class="ann-b" data-ed="redo" title="Làm lại (Ctrl+Shift+Z)" aria-label="Làm lại"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14l5-5-5-5"/><path d="M20 9H9.5a5.5 5.5 0 0 0 0 11H13"/></svg></button>
    <span class="ann-sep"></span>
    <button type="button" class="ann-b" data-tool="hand" aria-pressed="false" title="Kéo khung (H, hoặc giữ Alt)" aria-label="Kéo khung"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 13V5.5a1.5 1.5 0 0 1 3 0V12M11 11.5v-7a1.5 1.5 0 0 1 3 0V12M14 11.5V6a1.5 1.5 0 0 1 3 0v8c0 4-2.5 7-6.5 7S5 18.5 4 16l-1.5-3.5a1.5 1.5 0 0 1 2.6-1.4L8 14"/></svg></button>
    <button type="button" class="ann-b" data-ed="zin" title="Phóng to (Ctrl + hoặc lăn chuột)" aria-label="Phóng to"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.3-4.3M8 11h6M11 8v6"/></svg></button>
    <button type="button" class="ann-b" data-ed="zout" title="Thu nhỏ (Ctrl −)" aria-label="Thu nhỏ"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.3-4.3M8 11h6"/></svg></button>
    <button type="button" class="ann-b" data-ed="fit" title="Vừa khung (F)" aria-label="Vừa khung"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg></button>
    <span class="ann-sep"></span>
    <button type="button" class="ann-b" data-ed="reset" title="Về nét gốc của ký tự này (có hỏi xác nhận)" aria-label="Về nét gốc"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v6h6"/><path d="M4.6 15a8 8 0 1 0 1.9-8.3L4 10"/></svg></button>
  </div>
  <div class="ed-main">
    <div class="ed-stage"><div class="ed-corner"></div><svg class="ed-rx" aria-hidden="true"></svg><svg class="ed-ry" aria-hidden="true"></svg><svg class="ed-cv" data-tool="select" aria-label="Khung vẽ glyph"><g id="ed-world" transform="scale(1,-1)"><g id="ed-metrics"></g><g id="ed-ghost"></g><g id="ed-ctx"></g><g id="ed-orig"></g><g id="ed-fill"></g><g id="ed-strokes"></g><g id="ed-handles"></g><g id="ed-nodes"></g><g id="ed-draft"></g><g id="ed-marq"></g></g></svg><div class="ed-resetc" role="alertdialog" aria-labelledby="ed-rct" aria-describedby="ed-rcd" hidden><div class="ed-rcbox"><b id="ed-rct">Về nét gốc?</b><p id="ed-rcd">Bỏ hết nét đã sửa của ký tự này.</p><div class="ed-rcbtn"><button type="button" class="btnx pri" data-a="yes">Về nét gốc</button><button type="button" class="btnx" data-a="no">Thôi</button></div></div></div><span class="ed-save">đang kết nối…</span></div>
    <div class="ed-under">
<div class="ed-opts" role="group" aria-label="Hiển thị trên khung vẽ"><button type="button" class="ed-opt" data-opt="grid" aria-pressed="true" title="Lưới mờ (bấm để bật/tắt)" aria-label="Lưới mờ"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v16H4zM9.3 4v16M14.7 4v16M4 9.3h16M4 14.7h16" stroke-width="1.2"/></svg><span>Lưới mờ</span></button><button type="button" class="ed-opt" data-opt="rulers" aria-pressed="true" title="Thước trên + trái (bấm để bật/tắt)" aria-label="Thước trên + trái"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v5H8v13H3z"/><path d="M11 3v3M15 3v3M19 3v3M3 11h3M3 15h3M3 19h3" stroke-width="1.3"/></svg><span>Thước trên + trái</span></button><button type="button" class="ed-opt" data-opt="metrics" aria-pressed="true" title="Đường chân chữ, x-height, chữ hoa (bấm để bật/tắt)" aria-label="Đường chân chữ, x-height, chữ hoa"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M3 12h18M3 18h18" /><path d="M7 18V9l3-3 3 3v9" stroke-width="1.3"/></svg><span>Đường chân chữ</span></button><button type="button" class="ed-opt" data-opt="orig" aria-pressed="true" title="Nét gốc (viền đứt) (bấm để bật/tắt)" aria-label="Nét gốc (viền đứt)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M6 19 12 5l6 14M8.5 13.5h7" stroke-dasharray="2.4 2.4"/></svg><span>Nét gốc</span></button><button type="button" class="ed-opt" data-opt="adv" aria-pressed="true" title="2 line biên advance + phần tràn (bấm để bật/tắt)" aria-label="2 line biên advance + phần tràn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3v18M19 3v18"/><path d="M8.5 17 12 8l3.5 9"/><rect x="17" y="5" width="5" height="4" fill="currentColor" stroke="none" opacity=".55"/></svg><span>2 line biên advance + phần tràn</span></button><button type="button" class="ed-opt" data-opt="lbox" aria-pressed="true" title="Line biên dọc (hộp dòng) (bấm để bật/tắt)" aria-label="Line biên dọc (hộp dòng)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="18" height="12" fill="currentColor" opacity=".18" stroke="none"/><path d="M3 6h18M3 18h18"/><path d="M12 3v3M12 18v3" stroke-width="1.3"/></svg><span>Line biên dọc</span></button><button type="button" class="ed-opt" data-opt="axis" aria-pressed="true" title="Trục chữ (bấm để bật/tắt)" aria-label="Trục chữ"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M10 21 14 3"/><path d="M6 12h12" stroke-dasharray="2 2.2" stroke-width="1.2"/></svg><span>Trục chữ</span></button><button type="button" class="ed-opt" data-opt="nodes" aria-pressed="true" title="Điểm & tay nắm (bấm để bật/tắt)" aria-label="Điểm & tay nắm"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M5 18C8 8 16 8 19 18"/><rect x="3" y="16" width="4" height="4" fill="currentColor"/><circle cx="12" cy="10.5" r="2" fill="currentColor"/><path d="M8 7.5h8" stroke-width="1.2"/></svg><span>Điểm & tay nắm</span></button><button type="button" class="ed-opt" data-opt="snap" aria-pressed="true" title="Snap — điểm / tâm thành phần dính vào lưới, đường chữ, 2 biên, giữa hộp, trục chữ khi lại gần; giữ Alt để tạm tắt (S)" aria-label="Snap"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4v7a6 6 0 0 0 12 0V4"/><path d="M6 4h3.5v7a2.5 2.5 0 0 0 5 0V4H18" /><path d="M3 20h18" stroke-dasharray="2 2"/></svg><span>Snap</span></button></div>
      <div class="ed-brushrow" hidden><label for="ed-bw">Độ dày cọ</label><input type="range" id="ed-bw" min="20" max="180" value="90"><output id="ed-bwv">90</output><span class="mini">đơn vị font · dấu ngã dày 90</span></div>
    </div>

  </div>
 </div>
  <div class="ed-side">
    <details class="ed-whyd"><summary>Vì sao đặt dấu như vậy?</summary><div class="ed-info"></div></details>
    <div class="ed-tabs" role="group" aria-label="Nhóm ký tự"><button type="button" data-tab="vn" aria-pressed="true">134 chữ Việt</button><button type="button" data-tab="marks" aria-pressed="false">Dấu</button><button type="button" data-tab="latin" aria-pressed="false">Chữ gốc</button></div>
    <input id="ed-find" type="text" placeholder="Gõ ký tự để mở" aria-label="Tìm ký tự">
    <div class="ed-list"></div>
    <label class="ed-notel" for="ed-note">Ghi chú cho ký tự này</label>
    <textarea id="ed-note" rows="3" placeholder="Ví dụ: móc to hơn, đầu tròn như dấu phẩy…"></textarea>
  </div>
 <div class="ed-pvin"><label class="ed-notel" for="ed-pvtext">Chữ mẫu</label>
<textarea id="ed-pvtext" rows="3" spellcheck="false">ẦẤẨẪẬ ẰẮẲẴẶ ỀẾỂỄỆ ỒỐỔỖỘ ỜỚỞỠỢ ỪỨỬỮỰ ỲÝỶỸỴ ÌÍỈĨỊ
ầấẩẫậ ằắẳẵặ ềếểễệ ồốổỗộ ờớởỡợ ừứửữự ỳýỷỹỵ ìíỉĩị
Người ướt sũng, cẩn thận, ẢNH Ở ĐƯỜNG XƯA, đã ĐƯỢC</textarea></div>
 <div class="ed-pv"><div class="ed-pvh"><b>Xem trong chữ</b></div><svg aria-label="Xem trước câu"></svg></div>
</div>'''

UNDO_JS = r"""/* Ctrl+Z / Ctrl+Shift+Z (Ctrl+Y) hoàn tác MỌI thao tác trên trang theo đúng thứ tự: thanh kéo, bàn vẽ, chọn quyết định.
   Mỗi khối gọi __UB.note(khu) khi có thao tác mới, __UB.reg(khu, undo, redo) để bus gọi lại; nút hoàn tác riêng của khối gọi __UB.undone/redone. */
window.__UB = (function(){ var log = [], fut = [], reg = {}, U = {busy: false};
function rm(a, arr){ for (var i = arr.length - 1; i >= 0; i--) if (arr[i] === a){ arr.splice(i, 1); return true; } return false; }
U.reg = function(a, u, r){ reg[a] = {u: u, r: r}; };
U.note = function(a){ if (U.busy) return; log.push(a); if (log.length > 500) log.shift(); fut = []; };
U.undone = function(a){ if (!U.busy && rm(a, log)) fut.push(a); };
U.redone = function(a){ if (!U.busy && rm(a, fut)) log.push(a); };
U.drop = function(a){ if (!U.busy) rm(a, log); };   // thao tác vừa ghi nhưng không đổi gì (bấm không kéo)
function run(redo){ var a = (redo ? fut : log).pop(); if (!a || !reg[a]) return; (redo ? log : fut).push(a); U.busy = true; try { reg[a][redo ? 'r' : 'u'](); } finally { U.busy = false; } }
U.undo = function(){ run(false); }; U.redo = function(){ run(true); };
document.addEventListener('keydown', function(e){ if (!(e.ctrlKey || e.metaKey)) return; var k = (e.key || '').toLowerCase(); if (k !== 'z' && k !== 'y') return;
  var t = document.activeElement; if (t && (t.tagName === 'TEXTAREA' || t.isContentEditable || (t.tagName === 'INPUT' && /^(text|search|email|url)$/.test(t.type)))) return;   // ô chữ: để trình duyệt tự hoàn tác
  e.preventDefault(); e.stopImmediatePropagation(); if (k === 'y' || e.shiftKey) U.redo(); else U.undo(); }, true);
return U; })();"""

INFO_CSS = '''<style>
/* nút i: giải thích ngắn thay cho đoạn chữ dài dưới tiêu đề mục */
.sec-h{position:relative}
.h2box{min-width:0;flex:1}
.h2row{display:flex;align-items:center;gap:8px;flex-wrap:wrap;position:relative}   /* khung info neo ngay dưới hàng tiêu đề (lỗi 27/10: không có cha định vị → neo vào body, nhảy lên cao) */
details.info{display:inline-block}
details.info>summary{list-style:none;display:grid;place-items:center;width:22px;height:22px;border-radius:50%;border:1.5px solid var(--pg-line-2);color:var(--pg-mut);font:italic 700 13px/1 Georgia,serif;cursor:pointer;user-select:none}
details.info>summary::-webkit-details-marker{display:none}
details.info>summary:hover,details.info[open]>summary{color:var(--pg-txt);border-color:var(--pg-txt)}
details.info>summary:focus-visible{outline:2px solid var(--pg-accent);outline-offset:2px}
.info-pop{position:absolute;left:0;right:auto;width:min(640px,100%);top:calc(100% + 6px);z-index:30;background:var(--pg-card);color:var(--pg-txt);border:1px solid var(--pg-line-2);border-radius:10px;padding:10px 14px;font-size:13px;line-height:1.55;box-shadow:0 8px 24px rgba(0,0,0,.18);max-width:640px}
.info-pop p{margin:0 0 6px}.info-pop p:last-child{margin:0}
@media (max-width:620px){.info-pop{left:0}}
.vnote:empty{display:none}
/* nút bật/tắt + công cụ: chưa chọn xám mờ (không gạch ngang), đang chọn tô đặc đảo màu */
.ed-opt[aria-pressed="false"],.ed-bbtn[aria-pressed="false"],.spz button[aria-pressed="false"],.ed-zoom button[aria-pressed="false"],.ed-tabs button[aria-pressed="false"]{background:transparent;color:var(--pg-mut);border-color:var(--pg-line-2);opacity:.6;text-decoration:none}
.ed-opt[aria-pressed="false"] span{text-decoration:none}
.ed-opt[aria-pressed="false"]:hover,.ed-bbtn[aria-pressed="false"]:hover,.spz button[aria-pressed="false"]:hover,.ed-zoom button[aria-pressed="false"]:hover,.ed-tabs button[aria-pressed="false"]:hover{opacity:1}
.ed-opt[aria-pressed="true"],.ed-bbtn[aria-pressed="true"],.spz button[aria-pressed="true"],.ed-zoom button[aria-pressed="true"],.ed-tabs button[aria-pressed="true"],.vtab[aria-pressed="true"],.ann-b[aria-pressed="true"]{background:var(--pg-txt);color:var(--pg-bg);border-color:var(--pg-txt);opacity:1;font-weight:600}
.vtab[aria-pressed="true"] small{color:var(--pg-bg);opacity:.75}
.ann-b[aria-pressed="true"]:hover{background:var(--pg-txt);color:var(--pg-bg)}
</style>'''

ED_CSS = '''<style>
/* bàn vẽ glyph — dùng token của trang duyệt */
.ed{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,290px);gap:10px;align-items:start;margin-top:12px}
.ed-left{display:grid;grid-template-columns:auto minmax(0,1fr);gap:10px;align-items:start;min-width:0}
.ed-bar{display:flex;flex-direction:column;align-items:center;gap:3px;padding:5px;border:1px solid var(--pg-line-2);border-radius:10px;background:var(--pg-card);position:sticky;top:8px}
.ed-bar .ann-sep{width:22px;height:1px;margin:3px 0}
.ed-main{min-width:0;display:flex;flex-direction:column;gap:8px}
.ed-stage{border:1px solid var(--pg-line-2);border-radius:10px;background:var(--pg-card);overflow:hidden;display:grid;grid-template-columns:26px minmax(0,1fr);grid-template-rows:20px auto}
.ed-stage.no-rulers{grid-template-columns:minmax(0,1fr);grid-template-rows:auto}
.ed-stage.no-rulers .ed-corner{display:none}
.ed-corner{background:var(--pg-sunk);border-right:1px solid var(--pg-line);border-bottom:1px solid var(--pg-line)}
.ed-rx,.ed-ry{display:block;background:var(--pg-sunk);font:9px "Space Mono",monospace}
.ed-rx{width:100%;height:20px;border-bottom:1px solid var(--pg-line)}
.ed-ry{grid-row:2;width:26px;height:100%;border-right:1px solid var(--pg-line)}
.ed-rx path,.ed-ry path{stroke:var(--pg-mut-2);stroke-width:1}.ed-rx text,.ed-ry text{fill:var(--pg-mut)}
.ed-stage svg.ed-cv{display:block;width:100%;height:clamp(360px,58vh,600px);touch-action:none;user-select:none;-webkit-user-select:none}
.ed-stage.no-rulers svg.ed-cv{grid-row:1}
.ed-gr{stroke:var(--pg-line);stroke-width:.6;opacity:.55}.ed-gr2{stroke:var(--pg-line-2);stroke-width:.8;opacity:.8}
.ed-lb{fill:var(--pg-ok);fill-opacity:.06}.ed-lbl{stroke:var(--pg-ok);stroke-width:1.2;stroke-dasharray:6 4}.ed-mt.lb{fill:var(--pg-ok)}
.ed-ax{stroke:var(--pg-accent);stroke-width:1.2;stroke-dasharray:8 5}.ed-mt.ax{fill:var(--pg-accent)}
.ed-advl{stroke:var(--pg-warn);stroke-width:1.4}
.ed-boxc{stroke:var(--pg-mut-2);stroke-width:1;stroke-dasharray:2 4}
.ed-snapl{stroke:var(--pg-accent);stroke-width:1}.ed-snapd{fill:var(--pg-accent)}.ed-mt.snap{fill:var(--pg-accent);font-weight:700}
.ed-cx{stroke:var(--pg-mut);stroke-width:1.4}.ed-cx.on{stroke:var(--pg-accent);stroke-width:2}
.ed-cxd{fill:var(--pg-card);stroke:var(--pg-mut);stroke-width:1.2}.ed-cxd.on{fill:var(--pg-accent);stroke:var(--pg-accent)}
.ed-cbb{fill:none;stroke:var(--pg-accent);stroke-width:1;stroke-dasharray:4 3}
.ed-stage svg[data-tool="comp"]{cursor:move}
.ed-over{fill:var(--pg-red);fill-opacity:.22}
.ed-warn{font-size:12.5px;color:var(--pg-red);font-weight:600;line-height:1.4}.ed-okl{font-size:12.5px;color:var(--pg-ok);font-weight:600}
.ed-opts{display:flex;flex-wrap:wrap;gap:4px}
.ed-opt{display:inline-flex;align-items:center;gap:5px;font:inherit;font-size:12px;border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-mut);border-radius:8px;padding:4px 8px 4px 6px;cursor:pointer}
.ed-opt svg{width:17px;height:17px}
.ed-opt[aria-pressed="true"]{border-color:var(--pg-accent);background:var(--pg-accent-bg);color:var(--pg-accent)}
.ed-opt[aria-pressed="false"] span{text-decoration:line-through;text-decoration-thickness:1px}
.ed-opt:focus-visible{outline:2px solid var(--pg-accent);outline-offset:1px}
.ed-stage svg[data-tool="pen"]{cursor:crosshair}.ed-stage svg[data-tool="convert"]{cursor:alias}.ed-stage svg[data-tool="addpt"]{cursor:copy}.ed-stage svg[data-tool="delpt"]{cursor:not-allowed}.ed-stage svg[data-tool="brush"]{cursor:cell}.ed-stage svg[data-tool="hand"]{cursor:grab}
/* bản vẽ nhiều chữ (artboard) */
.ed-boards{display:flex;flex-wrap:wrap;align-items:center;gap:6px;font-size:12.5px;min-width:0}
.ed-bl{font-weight:700;font-size:12px;color:var(--pg-mut)}
.ed-bchips{display:flex;flex-wrap:wrap;gap:4px;min-width:0}
.ed-bc{display:inline-flex;align-items:stretch;border:1px solid var(--pg-line-2);border-radius:8px;overflow:hidden;background:var(--pg-card)}
.ed-bc button{font:inherit;border:0;background:transparent;color:var(--pg-txt);cursor:pointer;min-height:30px}
.ed-bc .bch{font-family:"Font VN",var(--pg-font,sans-serif);font-size:20px;line-height:1;padding:2px 10px}
.ed-bc .bx{padding:0 8px;color:var(--pg-mut);border-left:1px solid var(--pg-line-2);font-size:15px}
.ed-bc .bx:hover{color:var(--pg-red)}
.ed-bc.on{background:var(--pg-txt);border-color:var(--pg-txt)}.ed-bc.on button{color:var(--pg-bg)}.ed-bc.on .bx{border-color:var(--pg-bg)}
.ed-bc button:focus-visible,.ed-bbtn:focus-visible{outline:2px solid var(--pg-accent);outline-offset:1px}
.ed-bbtn{font:inherit;font-size:12px;border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);border-radius:8px;padding:4px 10px;cursor:pointer;min-height:30px}
.ed-bbtn:disabled{opacity:.4;cursor:default}
.ed-bsep{width:1px;height:20px;background:var(--pg-line-2);margin:0 2px}
.ed-bmsg{flex-basis:100%;color:var(--pg-mut);font-size:12px;min-height:1em}
.ed-bmsg:empty{display:none}
.ed-bframe{fill:transparent;stroke:var(--pg-line-2);stroke-width:1;cursor:pointer}
[data-board]:hover .ed-bframe{stroke:var(--pg-accent)}
.ed-bframe.on{fill:none;stroke:var(--pg-accent);stroke-width:1.4;pointer-events:none}
.ed-bfill{fill:var(--pg-txt);fill-opacity:.42}
[data-board]:hover .ed-bfill{fill-opacity:.6}
.ed-bbrush{fill:none;stroke:var(--pg-txt);stroke-opacity:.42;stroke-linecap:round;stroke-linejoin:round}
.ed-bax{stroke:var(--pg-accent);stroke-width:1;stroke-dasharray:6 5;opacity:.55}
.ed-blab{fill:var(--pg-mut);font-family:"Space Mono",monospace}.ed-blab.on{fill:var(--pg-accent);font-weight:700}
.ed-chip.inb::before{content:"";position:absolute;left:28%;right:28%;bottom:2px;height:2px;border-radius:2px;background:var(--pg-accent)}
.ed-ml{stroke:var(--pg-line-2);stroke-width:1}.ed-ml.base{stroke:var(--pg-mut-2)}.ed-ml.adv{stroke:var(--pg-line-2);stroke-dasharray:4 4}
.ed-mt{fill:var(--pg-mut-2);font-family:"Space Mono",monospace}
.ed-ctx{fill:var(--pg-mut-2);fill-opacity:.28}
.ed-orig{fill:none;stroke:var(--pg-warn);stroke-width:1.2;stroke-dasharray:5 4}
.ed-fill{fill:var(--pg-txt);fill-opacity:.82}
.ed-outline{fill:transparent;stroke:var(--pg-accent);stroke-width:1.2;cursor:move}
.ed-brush{fill:none;stroke:var(--pg-accent);stroke-opacity:.55;stroke-linecap:round;stroke-linejoin:round;cursor:move}
.ed-brush.is-sel{stroke-opacity:.85}
.ed-hl{stroke:var(--pg-accent);stroke-width:1}
.ed-h{fill:var(--pg-card);stroke:var(--pg-accent);stroke-width:1.5;vector-effect:non-scaling-stroke;cursor:pointer}
.ed-n{fill:var(--pg-card);stroke:var(--pg-accent);stroke-width:1.6;vector-effect:non-scaling-stroke;cursor:pointer}
.ed-n.on{fill:var(--pg-accent)}.ed-n.first{stroke:var(--pg-ok);stroke-width:3}
.ed-rubber{fill:none;stroke:var(--pg-accent);stroke-width:1;stroke-dasharray:3 3}
.ed-marq{fill:var(--pg-accent-bg);stroke:var(--pg-accent);stroke-width:1;stroke-dasharray:4 3}
.ed-under{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;font-size:13px}
.ed-chk{display:flex;align-items:center;gap:6px}
.ed-brushrow[hidden],.ed-resetc[hidden],.ed-pgf[hidden]{display:none}
.ed-brushrow{display:flex;align-items:center;gap:8px}.ed-brushrow input{accent-color:var(--pg-accent);width:140px}.ed-brushrow output{font-family:"Space Mono",monospace;font-weight:700}
.ed-stage{position:relative}
.ed-resetc{position:absolute;inset:0;z-index:20;display:flex;align-items:center;justify-content:center;background:color-mix(in srgb,var(--pg-bg) 55%,transparent);backdrop-filter:blur(1.5px)}
.ed-rcbox{display:flex;flex-direction:column;gap:8px;max-width:min(320px,90%);padding:16px 18px;border:1px solid var(--pg-line-2);border-radius:12px;background:var(--pg-card);color:var(--pg-txt);box-shadow:0 10px 30px rgba(0,0,0,.18);font-family:'Inter',system-ui,sans-serif}
.ed-rcbox b{font-size:16px}.ed-rcbox p{margin:0;font-size:13px;color:var(--pg-mut)}.ed-rcbtn{display:flex;gap:8px;justify-content:flex-end}
.ed-rcbox .btnx.pri{background:var(--pg-txt);color:var(--pg-bg);border-color:var(--pg-txt)}
/* nhóm bút vector kiểu Illustrator: 1 nút + tam giác góc, bấm mở danh sách */
.news{margin:12px 0 4px;padding:12px 16px;border:1.5px solid var(--pg-txt);border-radius:12px;background:var(--pg-card);font-family:'Inter',system-ui,sans-serif}
.news-t{display:block;font-size:15px;font-weight:800;margin-bottom:4px}.news ul{margin:0;padding-left:18px;font-size:13.5px;line-height:1.5}.news li{margin:3px 0}
.cite{font:600 11px/1 'Inter',system-ui,sans-serif;vertical-align:super;margin-left:1px;color:var(--pg-txt);text-decoration:none;padding:0 2px;border-radius:4px;background:var(--pg-sunk)}
.cite:hover,.cite:focus-visible{background:var(--pg-txt);color:var(--pg-bg);outline:none}
.srcs li.flash{background:var(--pg-sunk);box-shadow:0 0 0 2px var(--pg-txt);border-radius:6px;transition:box-shadow .3s}
.vnow{flex:none;font:600 12px/1 'Inter',system-ui,sans-serif;padding:5px 10px;border-radius:99px;background:var(--pg-txt);color:var(--pg-bg);white-space:nowrap}
.vnow.off{background:var(--pg-sunk);color:var(--pg-mut);white-space:normal}
.kn-fold summary{cursor:pointer;font-weight:600;font-size:13px}.kn-fold[open] summary{margin-bottom:6px}
.ed-bar{z-index:6}   /* danh sách nhóm bút nổi trên khung vẽ */
.ed-pg{position:relative;display:flex}
.ed-pgb{position:relative}.ed-pgi-ic{display:grid;place-items:center}.ed-pgi-ic svg{width:18px;height:18px}
.ed-pgt{position:absolute;right:2px;bottom:2px;width:0;height:0;border-left:5px solid transparent;border-bottom:5px solid currentColor;opacity:.75}
.ed-pgf{position:absolute;left:calc(100% + 8px);top:-4px;z-index:40;display:flex;flex-direction:column;gap:2px;min-width:220px;padding:5px;border:1px solid var(--pg-line-2);border-radius:10px;background:var(--pg-card);box-shadow:0 8px 24px rgba(0,0,0,.16)}
.ed-pgi{display:grid;grid-template-columns:20px minmax(0,1fr) auto;align-items:center;gap:9px;padding:6px 8px;border:0;border-radius:7px;background:transparent;color:var(--pg-txt);font:500 13px/1.2 'Inter',system-ui,sans-serif;text-align:left;cursor:pointer}
.ed-pgi svg{width:18px;height:18px}.ed-pgi kbd{font:11px 'Space Mono',monospace;color:var(--pg-mut)}
.ed-pgi:hover{background:var(--pg-sunk)}.ed-pgi[aria-pressed="true"]{background:var(--pg-txt);color:var(--pg-bg)}.ed-pgi[aria-pressed="true"] kbd{color:var(--pg-bg)}
.ed-pgi:focus-visible,.ed-pgb:focus-visible{outline:2px solid var(--pg-accent);outline-offset:2px}
@media (max-width:620px){.ed-pgf{left:0;top:calc(100% + 6px)}}
/* mục duyệt / chốt: Inter cho đồng bộ (D1, câu hỏi, lựa chọn, bảng góp ý) */
.decs,.dec,.dec .mk,.dec .mk small,.dec .q,.dec .q small,.dec .pick,.dec .pick b,.dec .pick > b:first-child,.decs .pick > b:first-child,.fbold,.fbold summary,.fbold table{font-family:'Inter',system-ui,sans-serif}
.dec .mk{font-weight:800;letter-spacing:-.01em}
.ed-save{display:inline-flex;align-items:center;gap:6px;padding:2px 9px 2px 7px;border-radius:99px;border:1px solid var(--pg-line-2);font-size:11px;font-weight:500;color:var(--pg-mut);white-space:nowrap}
.ed-save::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--pg-mut-2)}.ed-save:has(b)::before{background:var(--pg-ok)}.ed-save b{font-weight:500;color:inherit}
.ed-pvin{grid-column:1 / -1;display:flex;flex-direction:column;gap:6px;min-width:0}
.ed-pvin textarea{width:100%;box-sizing:border-box;font:inherit;font-size:13px;color:var(--pg-txt);background:var(--pg-sunk);border:1px solid var(--pg-line);border-radius:7px;padding:6px 8px;resize:vertical}
.ed-pv{grid-column:1 / -1;border:1px solid var(--pg-line-2);border-radius:10px;background:var(--pg-card);padding:10px 12px;display:flex;flex-direction:column;gap:6px;min-width:0}
.ed-pvh{display:flex;gap:10px;align-items:center;font-size:13px}.ed-pvh .ed-save{margin-left:auto}   /* chip trạng thái sang phải, chỗ nút kern cũ (người dùng 27/10) */
.ed-pv svg{display:block;width:100%;height:auto;max-height:320px}.ed-pv svg path{fill:var(--pg-txt)}.ed-pv svg path.hkp{stroke:var(--pg-txt)}.ed-pv svg path.pvb{fill:none;stroke:var(--pg-txt);stroke-linecap:round;stroke-linejoin:round}
.ed-pv textarea{width:100%;max-width:100%;min-width:0;font:inherit;font-size:13px;color:var(--pg-txt);background:var(--pg-sunk);border:1px solid var(--pg-line);border-radius:7px;padding:6px 8px;resize:vertical}
.ed-side textarea#ed-pvtext{width:100%;box-sizing:border-box;font:inherit;font-size:13px;color:var(--pg-txt);background:var(--pg-sunk);border:1px solid var(--pg-line);border-radius:7px;padding:6px 8px;resize:vertical}
.ed-whyd summary,.more summary{cursor:pointer;font-size:13px;font-weight:600}
.ed-side{min-width:0;display:flex;flex-direction:column;gap:8px;border:1px solid var(--pg-line-2);border-radius:10px;background:var(--pg-card);padding:10px 12px}
.ed-ttl{font-weight:700;font-size:14px}.ed-ttl span{font-weight:400;color:var(--pg-mut);font-size:12.5px}
.ed-stat{font-family:"Space Mono",monospace;font-size:11.5px;color:var(--pg-mut)}.ed-stat b{color:var(--pg-ok)}
.ed-xy{display:flex;gap:8px;align-items:center;font-size:12.5px;flex-wrap:wrap}.ed-xy input{width:72px;font:12px "Space Mono",monospace;color:var(--pg-txt);background:var(--pg-sunk);border:1px solid var(--pg-line);border-radius:6px;padding:3px 6px}
.ed-tabs{display:flex;gap:4px;flex-wrap:wrap}
.ed-tabs button{font:inherit;font-size:12.5px;border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-mut);border-radius:8px;padding:4px 9px;cursor:pointer}
.ed-tabs button[aria-pressed="true"]{background:var(--pg-accent-bg);border-color:var(--pg-accent);color:var(--pg-accent);font-weight:600}
#ed-find{font:inherit;font-size:13px;color:var(--pg-txt);background:var(--pg-sunk);border:1px solid var(--pg-line);border-radius:7px;padding:6px 8px;width:100%}
.ed-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(44px,1fr));gap:5px;max-height:300px;overflow:auto;padding:2px}
.ed-chip{position:relative;font:inherit;border:1px solid var(--pg-line-2);background:var(--pg-sunk);color:var(--pg-txt);border-radius:8px;padding:4px 2px;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:1px;min-width:0}
.ed-chip b{font-family:"Font VN",var(--pg-font,sans-serif);font-size:22px;line-height:1.2;font-weight:400}
.ed-chip small{font-size:9.5px;color:var(--pg-mut);line-height:1.2;text-align:center}
.ed-chip.mk{grid-column:span 2}
.ed-chip:hover{border-color:var(--pg-accent)}.ed-chip.on{border-color:var(--pg-accent);background:var(--pg-accent-bg);box-shadow:inset 0 0 0 1px var(--pg-accent)}
.ed-chip.dirty::after{content:"";position:absolute;top:4px;right:4px;width:7px;height:7px;border-radius:50%;background:var(--pg-ok)}
.ed-chip:focus-visible,.ed-tabs button:focus-visible{outline:2px solid var(--pg-accent);outline-offset:1px}
.ed-notel{font-size:12px;font-weight:600;color:var(--pg-mut)}
.ed-why{display:flex;flex-direction:column;gap:6px;max-height:440px;overflow:auto;border-top:1px solid var(--pg-line);padding-top:8px;font-size:12.5px;line-height:1.45}
.ed-whyh{font-weight:700;font-size:13px}
.ed-whyl{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:4px}
.ed-whyl sup,.ed-whys sup{font:700 10px "Space Mono",monospace;color:var(--pg-mut);margin-left:1px;cursor:help}
.ed-whys{margin:0;padding:6px 0 0;list-style:none;border-top:1px dashed var(--pg-line);display:flex;flex-direction:column;gap:3px;font-size:11.5px;color:var(--pg-mut)}
.ed-whys a{color:var(--pg-txt);text-underline-offset:2px}
.ed-whyn{margin:0;font-size:11.5px;color:var(--pg-mut)}
.ed-whyg{font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--pg-mut);margin-top:4px}.ed-whyg.other{color:var(--pg-warn)}
.ed-zoom{display:inline-flex;gap:4px;align-items:center;margin-left:auto}
.ed-zoom button,.ed-zoom select,.spz button,.spz select{font:inherit;font-size:12px;border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);border-radius:7px;padding:2px 8px;cursor:pointer;min-height:26px}
.ed-zoom button[aria-pressed="false"],.spz button[aria-pressed="false"]{color:var(--pg-mut);text-decoration:line-through}
.ed-zoom button[aria-pressed="true"],.spz button[aria-pressed="true"]{border-color:var(--pg-accent);background:var(--pg-accent-bg)}
.ed-pvh{flex-wrap:wrap}
.ed-pvsc{overflow:auto;max-width:100%}
.spec{border:1px solid var(--pg-line-2);border-radius:10px;background:var(--pg-card);padding:10px 12px;display:flex;flex-direction:column;gap:8px;min-width:0;margin-top:12px}
.spz{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:12.5px}
.spz .spl{font-weight:700;margin-right:auto}
.sprow{display:flex;flex-direction:column;gap:2px;border-top:1px solid var(--pg-line);padding-top:6px;min-width:0}
.sprow small{font-size:11px;color:var(--pg-mut);font-family:"Space Mono",monospace}
.sptx{overflow-x:auto;white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.45;color:var(--pg-txt);padding-top:.15em}
.sptx.lines{white-space:nowrap;overflow-wrap:normal}
.sptx .ab{display:inline-block;box-shadow:inset 1px 0 0 var(--pg-red),inset -1px 0 0 var(--pg-red)}
.sprow small b{font-weight:400}
.vtabs{display:flex;flex-wrap:wrap;gap:6px}
.vtab{font:inherit;display:flex;flex-direction:column;align-items:flex-start;gap:1px;border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);border-radius:10px;padding:8px 14px;cursor:pointer;min-width:120px}
.vtab b{font-size:22px;line-height:1.1;letter-spacing:.02em}.vtab small{font-size:11.5px;color:var(--pg-mut)}
.vtab[aria-pressed="true"]{background:var(--pg-accent);border-color:var(--pg-accent);color:var(--pg-on-accent)}.vtab[aria-pressed="true"] small{color:var(--pg-on-accent);opacity:.8}
.vtab:focus-visible{outline:2px solid var(--pg-accent);outline-offset:2px}
.vtag{font-size:34px;font-weight:800;line-height:1;letter-spacing:.02em}.vsub{font-size:13px;color:var(--pg-mut);margin-right:auto}
.vnote{margin:0;font-size:13px;color:var(--pg-mut)}
.spec textarea{width:100%;font:inherit;font-size:13px;color:var(--pg-txt);background:var(--pg-sunk);border:1px solid var(--pg-line);border-radius:7px;padding:6px 8px;resize:vertical}
.srcs{margin:6px 0 0;padding-left:0;list-style:none;display:flex;flex-direction:column;gap:6px;font-size:13.5px}
.srcs sup{font:700 11px "Space Mono",monospace;scroll-margin:80px;color:var(--pg-mut);margin-right:4px}
.srch{margin:16px 0 0;font-size:14px}
.srcr{margin:4px 0 0;padding-left:18px;font-size:12.5px;color:var(--pg-mut)}
.srcs a{color:var(--pg-txt);text-underline-offset:2px}.srcs small{color:var(--pg-mut)}
#ed-note{width:100%;max-width:100%;min-width:0;font:inherit;font-size:13px;color:var(--pg-txt);background:var(--pg-sunk);border:1px solid var(--pg-line);border-radius:7px;padding:6px 8px;resize:vertical}
.keys{font-size:12.5px;color:var(--pg-mut);margin:8px 0 0}.keys kbd{font:11px "Space Mono",monospace;border:1px solid var(--pg-line-2);border-bottom-width:2px;border-radius:4px;padding:0 4px;background:var(--pg-card);color:var(--pg-txt)}
@media (max-width:980px){.ed{grid-template-columns:minmax(0,1fr)}}
@media (max-width:620px){.ed-left{grid-template-columns:minmax(0,1fr)}.ed-bar{flex-direction:row;flex-wrap:wrap;position:static}.ed-bar .ann-sep{width:1px;height:20px;margin:0 3px}}
</style>'''


# ---- tông trắng đen (luật Ryan 25/10): bỏ ánh tím của khung VibeEdit, chỉ giữ đỏ = tràn/lỗi, xanh = đạt ----
MONO_CSS = """<style>
/* bảng màu ấm như ứng dụng Claude (người dùng 27/10: nền thao tác sáng hơn dải đầu trang, đỡ mỏi mắt) */
:root{--pg-bg:#faf9f5;--pg-card:#ffffff;--pg-sunk:#f3f1ea;--pg-line:#e8e5da;--pg-line-2:#d9d5c8;
  --pg-txt:#1f1e1d;--pg-mut:#5e5d57;--pg-mut-2:#8c8a82;--pg-accent:#1f1e1d;--pg-accent-bg:rgba(0,0,0,.07);--pg-on-accent:#ffffff;
  --pg-ok:#127a46;--pg-ok-bg:rgba(18,122,70,.10);--pg-red:#c4182f;--pg-warn:#9a5b00}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--pg-bg:#262624;--pg-card:#30302e;--pg-sunk:#1f1e1d;--pg-line:#3a3936;--pg-line-2:#4a4844;
  --pg-txt:#f5f4ef;--pg-mut:#b5b3aa;--pg-mut-2:#85837c;--pg-accent:#f5f4ef;--pg-accent-bg:rgba(255,255,255,.10);--pg-on-accent:#1f1e1d;
  --pg-ok:#3ecf8e;--pg-ok-bg:rgba(62,207,142,.13);--pg-red:#ff5a6e;--pg-warn:#f5b942;color-scheme:dark}}
:root[data-theme="dark"]{--pg-bg:#262624;--pg-card:#30302e;--pg-sunk:#1f1e1d;--pg-line:#3a3936;--pg-line-2:#4a4844;
  --pg-txt:#f5f4ef;--pg-mut:#b5b3aa;--pg-mut-2:#85837c;--pg-accent:#f5f4ef;--pg-accent-bg:rgba(255,255,255,.10);--pg-on-accent:#1f1e1d;
  --pg-ok:#3ecf8e;--pg-ok-bg:rgba(62,207,142,.13);--pg-red:#ff5a6e;--pg-warn:#f5b942;color-scheme:dark}
.badge,.btnx.pri,.ann-seg button[aria-pressed="true"],.ann-pop-f button[data-a="ok"],.ann-pill .ann-n{color:var(--pg-on-accent)}
.badge.ok{background:var(--pg-ok);color:#fff}.badge.zero{background:var(--pg-mut-2);color:var(--pg-card)}
.anncmts b{background:var(--pg-accent);color:var(--pg-on-accent)}
.ann-pin path,.ann-pin circle{fill:var(--pg-accent)}.ann-pin text{fill:var(--pg-on-accent)}
.pick[aria-pressed="true"]{background:var(--pg-accent-bg);box-shadow:inset 0 0 0 1.5px var(--pg-accent)}
.dec{border-left-color:var(--pg-txt)}.dec-done{border-left-color:var(--pg-ok)}
.cvl.dx,.cmp figcaption.new,.mk{color:var(--pg-txt)}.dec-done .mk{color:var(--pg-ok)}
.ed-n.on{fill:var(--pg-accent)}.ed-hl{stroke:var(--pg-mut)}
</style>"""
import base64 as _b64, glob as _glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vfk_ui as VK
def _ff(fam, path): return '@font-face{font-family:"%s";src:url(data:font/woff2;base64,%s) format("woff2");font-display:swap}' % (fam, _b64.b64encode(open(path, 'rb').read()).decode())
FONT_CSS = '<style>' + ('' if NOFONT else _ff('Font VN', R + '/A.woff2')) + ''.join(_ff('FV-' + os.path.basename(q)[:-6], q) for q in sorted(_glob.glob(R + '/*.woff2')) if os.path.basename(q) not in ('A.woff2',) and not q.endswith('.bak')) + '</style>'
# kho tài liệu (luật đặt dấu + nguồn) cho bàn vẽ và mục nguồn tham khảo
RULES_PATH = os.environ.get('RULES_JSON', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules.json'))
RULES = json.load(open(RULES_PATH)) if os.path.exists(RULES_PATH) else None

def use_packs(paths):
    """nạp gói luật TÙY CHỌN (vd cẩm nang chưa kiểm chứng) vào kho — mặc định không nạp gói nào.
    Gọi trong content_rN.py: use_packs(['packs/camnang-ryan.json']) hoặc env RULE_PACKS=a.json,b.json. Đường dẫn tương đối tính từ thư mục tools."""
    if not RULES: return
    base = os.path.dirname(RULES_PATH)
    for q in paths:
        q = q if os.path.isabs(q) else os.path.join(base, q)
        pk = json.load(open(q)); have = {x['id'] for x in RULES['sources']}
        RULES['sources'] += [x for x in pk.get('sources', []) if x['id'] not in have]
        RULES['rules'] += pk.get('rules', [])
        RULES.setdefault('packs', []).append(pk.get('name', os.path.basename(q)))
if os.environ.get('RULE_PACKS'): use_packs([x for x in os.environ['RULE_PACKS'].split(',') if x])

def spec(sid, fonts, text, size=32, kern=True, lines=False, title='Gõ thử'):
    """chữ mẫu gõ thật bằng font nhúng — MỌI khung hiện chữ dùng cái này (luật Ryan 25/10: phải zoom được).
    Nút: − / + / chọn cỡ 10–200 px, kern (tắt = Word thân văn bản / Excel), line biên (2 vạch advance của từng chữ), số đo chiều dài dòng.
    fonts = [(nhãn, font-family)]"""
    rows = ''.join('<div class="sprow"><small>%s <b class="spw"></b></small><div class="sptx" style="font-family:\'%s\'">%s</div></div>' % (html.escape(l), f, html.escape(text)) for l, f in fonts)
    sizes = [10, 12, 16, 24, 32, 48, 72, 120, 200]
    opts = ''.join('<option value="%d"%s>%d px</option>' % (v, ' selected' if v == size else '', v) for v in sizes)
    return ('<div class="spec" id="%s" data-px="%d" data-kern="%d" data-lines="%d"><div class="spz"><span class="spl">%s</span><button type="button" data-z="-" aria-label="Thu nhỏ chữ">−</button>'
            '<select aria-label="Cỡ chữ">%s</select><button type="button" data-z="+" aria-label="Phóng to chữ">+</button>'
            '<button type="button" data-z="k" aria-pressed="true" title="Tắt = giống Word thân văn bản / Excel (không kern)">kern</button>'
            '<button type="button" data-z="l" aria-pressed="false" title="Hiện 2 vạch advance (line riêng) của từng chữ — khi bật, mỗi chữ đứng riêng nên không có kern (giống Word tắt kern)">line biên</button></div>'
            '<textarea rows="2" spellcheck="false" aria-label="Chữ mẫu">%s</textarea>%s</div>') % (sid, size, 1 if kern else 0, 1 if lines else 0, html.escape(title), opts, html.escape(text), rows)
def verspec(sid, vers, text, size=48):
    """gõ thử TỪNG ver riêng: tab ver chữ to + một khung chữ duy nhất (đỡ rối khi nhiều ver).
    vers = [(tag "VER 5", phụ đề "1.005 · móc ngắn", font-family, ghi chú ngắn)]"""
    tabs = ''.join('<button type="button" class="vtab" data-fam="%s" data-tag="%s" data-sub="%s" data-note="%s" aria-pressed="%s"><b>%s</b><small>%s</small></button>' % (
        f, html.escape(t), html.escape(sub), html.escape(note), 'true' if i == len(vers) - 1 else 'false', html.escape(t), html.escape(sub)) for i, (t, sub, f, note) in enumerate(vers))
    t0, s0, f0, n0 = vers[-1]
    sizes = [10, 12, 16, 24, 32, 48, 72, 120, 200]
    opts = ''.join('<option value="%d"%s>%d px</option>' % (v, ' selected' if v == size else '', v) for v in sizes)
    return ('<div class="spec vspec" id="%s" data-px="%d" data-kern="1" data-lines="0"><div class="vtabs" role="group" aria-label="Chọn ver">%s</div>'
            '<div class="spz"><span class="vtag" aria-live="polite">%s</span><span class="vsub">%s</span><button type="button" data-z="-" aria-label="Thu nhỏ chữ">−</button>'
            '<select aria-label="Cỡ chữ">%s</select><button type="button" data-z="+" aria-label="Phóng to chữ">+</button>'
            '<button type="button" data-z="k" aria-pressed="true" title="Tắt = giống Word thân văn bản / Excel (không kern)">kern</button>'
            '<button type="button" data-z="l" aria-pressed="false" title="Hiện 2 vạch advance (line riêng) của từng chữ — khi bật, mỗi chữ đứng riêng nên không có kern">line biên</button></div>'
            '<p class="vnote">%s</p><textarea rows="2" spellcheck="false" aria-label="Chữ mẫu">%s</textarea>'
            '<div class="sprow"><small><b class="spw"></b></small><div class="sptx" style="font-family:\'%s\'">%s</div></div></div>') % (
        sid, size, tabs, html.escape(t0), html.escape(s0), opts, html.escape(n0), html.escape(text), f0, html.escape(text))

def verspec2(sid, vers, text, size=48, height=None):
    """Hàng VIÊN THUỐC VER còn được tự chép lên đầu B, C (VERSYNC_JS, dính khi cuộn) — bấm ở đâu cũng đổi cả trang.
    gõ thử từng ver — BỐ CỤC 2 CỘT (luật người dùng 26/10): trái = VIÊN THUỐC chọn VER (bỏ menu xổ, vòng 10) + mô tả + nút cỡ / kern / line biên + ô chữ;
    phải = khung xem trước CỐ ĐỊNH (không xuống dòng tự động, cao cố định theo số dòng, font nạp sẵn hết) nên đổi VER chữ không giật,
    dễ thấy chỗ khác nhau. Phím ↑ ↓ trong menu để lật nhanh giữa các VER. vers = [(tag, phụ đề, font-family, ghi chú)]"""
    opts = ''.join('<button type="button" class="vpill" role="radio" data-i="%d" aria-checked="%s" title="%s">%s</button>' % (i, 'true' if i == len(vers) - 1 else 'false', html.escape(sub, True), html.escape(t)) for i, (t, sub, f, n) in enumerate(vers))
    data = json.dumps([{'t': t, 's': sub, 'f': f, 'n': n} for t, sub, f, n in vers], ensure_ascii=False).replace('</', '<\\/')
    sizes = [10, 12, 16, 24, 32, 48, 72, 120, 200]
    zo = ''.join('<option value="%d"%s>%d px</option>' % (v, ' selected' if v == size else '', v) for v in sizes)
    t0, s0, f0, n0 = vers[-1]
    return ('<div class="vs2" id="%s" data-px="%d"><script type="application/json" class="vs2-data">%s</script>'
            '<div class="vs2-left"><span class="vs2-lab" id="%s-lab">Version</span><div class="vpills" id="%s-sel" role="radiogroup" aria-labelledby="%s-lab">%s</div>'
            '<div class="vs2-tag"><b class="vs2-t">%s</b><span class="vs2-s">%s</span></div><p class="vs2-n">%s</p>'
            '<div class="vs2-ctl"><button type="button" data-z="-" aria-label="Thu nhỏ chữ">−</button><select class="vs2-px" aria-label="Cỡ chữ">%s</select><button type="button" data-z="+" aria-label="Phóng to chữ">+</button>'
            '<button type="button" data-z="k" aria-pressed="true" title="Tắt = giống Word thân văn bản / Excel (không kern)">kern</button>'
            '<button type="button" data-z="l" aria-pressed="false" title="2 vạch advance của từng chữ">line biên</button></div>'
            '<label class="vs2-lab" for="%s-ta">Chữ mẫu</label><textarea id="%s-ta" rows="6" spellcheck="false">%s</textarea>'
            '<p class="vs2-hint mini">Bấm viên thuốc hoặc phím ← → để lật nhanh; khung bên phải giữ nguyên vị trí. B, C cũng có hàng viên thuốc này.</p></div>'
            '<div class="vs2-right"><div class="vs2-view"><div class="sptx vs2-tx" style="font-family:\'%s\'"></div></div><small class="vs2-w"></small></div></div>') % (
        sid, size, data, sid, sid, sid, opts, html.escape(t0), html.escape(s0), html.escape(n0), zo, sid, sid, html.escape(text), f0)
SPEC2_CSS = """<style>
.vs2{display:grid;grid-template-columns:minmax(220px,300px) minmax(0,1fr);gap:14px;margin-top:12px;align-items:start}
.vs2-left{display:flex;flex-direction:column;gap:8px;min-width:0;position:sticky;top:calc(env(safe-area-inset-top,0px) + 8px)}
.vs2-lab{font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--pg-mut)}
.vpills{display:flex;flex-wrap:wrap;gap:6px}
.vpill{font:600 13px/1 'Inter',system-ui,sans-serif;padding:8px 13px;min-height:34px;border-radius:99px;border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);cursor:pointer;white-space:nowrap}
.vpill:hover{border-color:var(--pg-txt)}.vpill[aria-checked="true"]{background:var(--pg-txt);color:var(--pg-bg);border-color:var(--pg-txt)}
.vpill:focus-visible{outline:2px solid var(--pg-txt);outline-offset:2px}.vpill.nodata{border-style:dashed}
.vbar{position:sticky;top:calc(env(safe-area-inset-top,0px) + 6px);z-index:9;display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;margin:4px 0 14px;padding:8px 10px;border-radius:14px;background:color-mix(in srgb,var(--pg-card) 92%,transparent);backdrop-filter:blur(6px);border:1px solid var(--pg-line)}
@media (max-width:760px){.vbar{gap:4px 6px;padding:6px 8px}.vbar .vs2-lab{display:none}.vbar .vpill{padding:6px 10px;min-height:30px;font-size:12px}.vbar .vbar-n{flex-basis:100%}}
.vbar .vs2-lab{margin-right:2px}.vbar .vbar-n{font:500 12px/1.3 'Inter',system-ui,sans-serif;color:var(--pg-mut)}
.vs2-px{font:inherit;font-size:14px;color:var(--pg-txt);background:var(--pg-card);border:1px solid var(--pg-line-2);border-radius:8px;padding:7px 8px;min-width:0;max-width:100%}
.vs2-tag{display:flex;flex-direction:column;gap:2px}.vs2-t{font-size:30px;line-height:1.05;font-weight:800}.vs2-s{font-size:12.5px;color:var(--pg-mut)}
.vs2-n{margin:0;font-size:13px;color:var(--pg-mut);min-height:3.2em}
.vs2-ctl{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.vs2-ctl button{font:inherit;font-size:12px;border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);border-radius:7px;padding:3px 9px;min-height:28px;cursor:pointer}
.vs2-ctl button[aria-pressed="false"]{color:var(--pg-mut);opacity:.6}.vs2-ctl button[aria-pressed="true"]{background:var(--pg-txt);color:var(--pg-bg);border-color:var(--pg-txt)}
.vs2 textarea{width:100%;font:inherit;font-size:13px;color:var(--pg-txt);background:var(--pg-sunk);border:1px solid var(--pg-line);border-radius:7px;padding:6px 8px;resize:vertical;min-width:0}
.vs2-right{min-width:0}
.vs2-view{border:1px solid var(--pg-line-2);border-radius:10px;background:var(--pg-card);overflow:auto;padding:12px 14px}
.vs2-tx{white-space:pre;line-height:1.45;color:var(--pg-txt)}
.vs2-tx .ab{display:inline-block;box-shadow:inset 1px 0 0 var(--pg-red),inset -1px 0 0 var(--pg-red)}
.vs2-w{display:block;margin-top:4px;font:11px "Space Mono",monospace;color:var(--pg-mut)}
@media (max-width:760px){.vs2{grid-template-columns:minmax(0,1fr)}.vs2-left{position:static}}
</style>"""
SPEC2_JS = r"""(function(){var Z=[10,12,16,24,32,48,72,120,200];
function esc(c){return c==='&'?'&amp;':c==='<'?'&lt;':c==='>'?'&gt;':c;}
document.querySelectorAll('.vs2').forEach(function(b){var V=JSON.parse(b.querySelector('.vs2-data').textContent),px=+b.dataset.px||48,kern=true,lines=false,
 sel=b.querySelector('.vpills'),pxs=b.querySelector('.vs2-px'),ta=b.querySelector('textarea'),tx=b.querySelector('.vs2-tx'),view=b.querySelector('.vs2-view'),cur=V.length-1;
 // nạp sẵn mọi font để đổi version không nháy font dự phòng
 if(document.fonts&&document.fonts.load)V.forEach(function(v){document.fonts.load('48px "'+v.f+'"',ta.value||'a');});
 function lock(){ // khung cố định: cao theo số dòng × cỡ chữ, không phụ thuộc version
  var n=ta.value.split('\n').length;view.style.height=Math.ceil(n*px*1.45+28)+'px';}
 function ap(){var v=V[cur];tx.style.fontFamily="'"+v.f+"'";tx.style.fontSize=px+'px';tx.style.fontKerning=kern?'normal':'none';tx.style.fontFeatureSettings=kern?'normal':'"kern" 0';
  tx.innerHTML=ta.value.split('\n').map(function(L){return '<span class="spm">'+Array.from(L).map(function(c){return lines&&c!==' '?'<span class="ab">'+esc(c)+'</span>':esc(c);}).join('')+'</span>';}).join('\n');
  b.querySelector('.vs2-t').textContent=v.t;b.querySelector('.vs2-s').textContent=v.s;b.querySelector('.vs2-n').textContent=v.n;
  sel.querySelectorAll('.vpill').forEach(function(x,i){x.setAttribute('aria-checked',String(i===cur));x.tabIndex=i===cur?0:-1;});pxs.value=String(px);b.querySelector('[data-z="k"]').setAttribute('aria-pressed',String(kern));b.querySelector('[data-z="l"]').setAttribute('aria-pressed',String(lines));
  var w=0;tx.querySelectorAll('.spm').forEach(function(m){w=Math.max(w,m.getBoundingClientRect().width);});b.querySelector('.vs2-w').textContent=v.t+' · dòng dài nhất '+Math.round(w)+' px';lock();}
 function say(){window.__FV_VER=V[cur].t;try{window.dispatchEvent(new CustomEvent('fv-ver',{detail:{tag:V[cur].t,fam:V[cur].f}}));}catch(e){}}   // B, C, So vị trí cũ đổi theo VER đang chọn
 function pick(i,foc){if(i<0||i>=V.length)return;var sl=view.scrollLeft,st=view.scrollTop;cur=i;try{localStorage.setItem('fv-ver2-'+b.id,V[cur].t);}catch(e){}ap();view.scrollLeft=sl;view.scrollTop=st;if(foc)sel.children[i].focus();say();}
 sel.addEventListener('click',function(e){var x=e.target.closest('.vpill');if(x)pick(+x.dataset.i);});
 sel.addEventListener('keydown',function(e){var d={ArrowLeft:-1,ArrowUp:-1,ArrowRight:1,ArrowDown:1}[e.key];if(!d)return;e.preventDefault();pick((cur+d+V.length)%V.length,true);});
 if(!window.__FV_PICK){window.__FV_VERS=V;window.__FV_PICK=function(t){V.forEach(function(v,i){if(v.t===t)pick(i);});};}   // hàng viên thuốc ở B, C gọi vào đây
 window.addEventListener('load',say);
 pxs.addEventListener('change',function(){px=+pxs.value;ap();});ta.addEventListener('input',ap);
 b.querySelector('.vs2-ctl').addEventListener('click',function(e){var x=e.target.closest('button');if(!x)return;var i=Z.indexOf(px);if(i<0)i=5;
  if(x.dataset.z==='-')px=Z[Math.max(0,i-1)];else if(x.dataset.z==='+')px=Z[Math.min(Z.length-1,i+1)];else if(x.dataset.z==='k')kern=!kern;else lines=!lines;ap();});
 try{var sv=localStorage.getItem('fv-ver2-'+b.id);V.forEach(function(v,i){if(v.t===sv)cur=i;});}catch(e){}
 if(document.fonts&&document.fonts.ready)document.fonts.ready.then(ap);ap();});})();"""

SPEC_JS = r"""(function(){var Z=[10,12,16,24,32,48,72,120,200];
function esc(c){return c==='&'?'&amp;':c==='<'?'&lt;':c==='>'?'&gt;':c;}
document.querySelectorAll('.spec').forEach(function(b){var px=+b.dataset.px||32,kern=b.dataset.kern!=='0',lines=b.dataset.lines==='1',ta=b.querySelector('textarea'),sel=b.querySelector('select');
function ap(){var v=ta.value;b.querySelectorAll('.sprow').forEach(function(r){var t=r.querySelector('.sptx');t.style.fontSize=px+'px';t.style.fontKerning=kern?'normal':'none';t.style.fontFeatureSettings=kern?'normal':'"kern" 0';
 t.classList.toggle('lines',lines);
 if(lines){t.innerHTML=v.split('\n').map(function(L){return '<span class="spm">'+Array.from(L).map(function(c){return c===' '?' ':'<span class="ab">'+esc(c)+'</span>';}).join('')+'</span>';}).join('<br>');}
 else{t.innerHTML=v.split('\n').map(function(L){return '<span class="spm">'+Array.from(L).map(esc).join('')+'</span>';}).join('<br>');}
 var w=0;t.querySelectorAll('.spm').forEach(function(m){w=Math.max(w,m.getBoundingClientRect().width);});r.querySelector('.spw').textContent='· dòng dài nhất '+Math.round(w)+' px';});
 sel.value=String(px);b.querySelector('[data-z="k"]').setAttribute('aria-pressed',String(kern));b.querySelector('[data-z="l"]').setAttribute('aria-pressed',String(lines));}
b.querySelector('.spz').addEventListener('click',function(e){var x=e.target.closest('button');if(!x)return;var i=Z.indexOf(px);if(i<0)i=4;if(x.dataset.z==='-')px=Z[Math.max(0,i-1)];else if(x.dataset.z==='+')px=Z[Math.min(Z.length-1,i+1)];else if(x.dataset.z==='k')kern=!kern;else lines=!lines;ap();});
sel.addEventListener('change',function(){px=+sel.value;ap();});ta.addEventListener('input',ap);
b.querySelectorAll('.vtab').forEach(function(v){v.addEventListener('click',function(){b.querySelectorAll('.vtab').forEach(function(o){o.setAttribute('aria-pressed',String(o===v));});
 b.querySelector('.sptx').style.fontFamily="'"+v.dataset.fam+"'";b.querySelector('.vtag').textContent=v.dataset.tag;b.querySelector('.vsub').textContent=v.dataset.sub;b.querySelector('.vnote').textContent=v.dataset.note;
 try{localStorage.setItem('fv-ver-'+b.id,v.dataset.tag);}catch(e){}ap();
 if(document.fonts&&document.fonts.load)document.fonts.load(px+"px '"+v.dataset.fam+"'",ta.value||'a').then(ap,ap);});});
try{var sv=localStorage.getItem('fv-ver-'+b.id);if(sv){var vb=Array.from(b.querySelectorAll('.vtab')).filter(function(o){return o.dataset.tag===sv;})[0];if(vb)vb.click();}}catch(e){}
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(ap);ap();});})();"""

def src_nums():
    """số thứ tự trong từng nhóm: {id: (ký hiệu, n)} — trùng với số trên bàn vẽ"""
    G = (RULES or {}).get('groups', {}); out = {}; cnt = {}
    for g in ('expert', 'other', 'own'):
        for x in (RULES or {}).get('sources', []):
            if x.get('group', 'expert') == g:
                cnt[g] = cnt.get(g, 0) + 1; out[x['id']] = (G.get(g, {}).get('sym', '*'), cnt[g])
    return out
VERSYNC_JS = r"""(function(){   // nhãn “đang xem VER n” ở B, C + trích dẫn [n] bấm nhảy tới Tài liệu tham khảo
var VD={};try{VD=JSON.parse(document.getElementById('fv-verdata').textContent);}catch(e){}
function hasD(t){return t===VD.__base||!!VD[t];}
function bar(sec){if(document.querySelector('.vk-vers'))return null;var S=document.querySelector('.sec[data-sec="'+sec+'"]');if(!S)return null;var b=S.querySelector(':scope > .vbar');if(b)return b;
 b=document.createElement('div');b.className='vbar';b.setAttribute('role','radiogroup');b.setAttribute('aria-label','Version cho mục này');
 b.innerHTML='<span class="vs2-lab">Version</span>'+(window.__FV_VERS||[]).map(function(v){return '<button type="button" class="vpill'+(hasD(v.t)?'':' nodata')+'" role="radio" aria-checked="false" data-t="'+v.t+'" title="'+v.s.replace(/"/g,'&quot;')+(hasD(v.t)?'':' · không có nét dựng')+'">'+v.t+'</button>';}).join('')+'<span class="vbar-n"></span>';
 b.addEventListener('click',function(e){var x=e.target.closest('.vpill');if(x&&window.__FV_PICK)window.__FV_PICK(x.dataset.t);});
 var h=S.querySelector(':scope > .sec-h');if(h)h.after(b);else S.prepend(b);return b;}
window.addEventListener('fv-ver',function(e){var t=e.detail.tag,has=hasD(t);
 if(has)window.__FV_SHOWN=t;
 if(window.__save)setTimeout(window.__save,0);   // khối Tổng hợp ghi “Đang xem: VER n”
 ['R','C'].forEach(function(k){var b=bar(k);if(!b)return;b.querySelectorAll('.vpill').forEach(function(x){x.setAttribute('aria-checked',String(x.dataset.t===t));});
  b.querySelector('.vbar-n').textContent=has?'':t+' là font gốc, không có nét dựng · '+(k==='R'?'B':'C')+' đang giữ '+(window.__FV_SHOWN||VD.__base);});
 document.querySelectorAll('.on-bar button[data-v]').forEach(function(b){if(b.textContent.trim()===t&&b.getAttribute('aria-pressed')!=='true')b.click();});});
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a.cite');if(!a)return;e.preventDefault();
 var li=document.getElementById('src-'+a.dataset.src);if(!li)return;var d=li.closest('details');if(d)d.open=true;
 li.scrollIntoView({behavior:'smooth',block:'center'});li.classList.add('flash');setTimeout(function(){li.classList.remove('flash');},1600);});})();"""

def cite_label(sid):
    """nhãn trích dẫn: nguồn chuyên môn [n] · chưa kiểm chứng [†n] · lựa chọn / đo kiểm của font [#n]"""
    N = src_nums(); sym, n = N.get(sid, ('?', 0))
    return '[%s%d]' % ('' if sym == '*' else sym, n)
def cite(*ids):
    """chèn số trích dẫn bấm được → nhảy xuống mục Tài liệu tham khảo (dùng trong news / fb / MEAS / chữ trên trang)"""
    return ''.join('<a class="cite" href="#src-%s" data-src="%s" title="Xem tài liệu tham khảo">%s</a>' % (i, i, cite_label(i)) for i in ids)
def sources_html():
    """mục cuối trang: nguồn kiến thức đã dùng, chia nhóm — chuyên môn có link (*) · khác chưa kiểm chứng (†) · lựa chọn / đo kiểm của font này (#).
    Nguồn 'other' chỉ hiện khi còn luật nào dùng tới (ý đã có ở nguồn chuyên môn thì không trích)."""
    if not RULES: return ''
    used = set(x for r in RULES['rules'] for x in r['src']); N = src_nums(); G = RULES.get('groups', {}); h = ''
    for g in ('expert', 'other', 'own'):
        items = [x for x in RULES['sources'] if x.get('group', 'expert') == g and (g != 'other' or x['id'] in used)]
        if not items: continue
        rules_of = lambda sid: [r['text'] for r in RULES['rules'] if sid in r['src']]
        li = ''.join('<li id="src-%s"><sup>%s</sup> %s%s</li>' % (x['id'], cite_label(x['id']),
              '<a href="%s" target="_blank" rel="noopener">%s</a>' % (html.escape(x['url']), html.escape(x['title'])) if x.get('url') else html.escape(x['title']),
              ('<ul class="srcr">' + ''.join('<li>%s</li>' % html.escape(t) for t in rules_of(x['id'])) + '</ul>') if g == 'other' else '') for x in items)
        h += '<h3 class="srch">%s %s</h3><ul class="srcs">%s</ul>' % (html.escape(G.get(g, {}).get('sym', '')), html.escape(G.get(g, {}).get('title', g)), li)
    if not RULES.get('packs'): h += '<p class="mini" style="margin-top:8px">Không bật gói cẩm nang chưa kiểm chứng nào — chỉ dùng nguồn chuyên môn và số đo trên font.</p>'
    else: h += '<p class="mini" style="margin-top:8px">Đang bật gói tuỳ chọn: ' + html.escape(', '.join(RULES['packs'])) + ' — chỉ dự án này, người dùng mới mặc định không dùng.</p>'
    return h

def _ver_diffs():
    vd = os.path.join(R, 'vers'); out = {}
    if not os.path.isdir(vd): return out
    if NOFONT: return {}
    be = json.load(open(R + '/editor.json')); hp = R + '/hornui.json'; bh = json.load(open(hp)) if os.path.exists(hp) else {}
    for tag in sorted(os.listdir(vd)):
        d = {}
        ep = os.path.join(vd, tag, 'editor.json')
        if os.path.exists(ep):
            e = json.load(open(ep)); d['ed'] = {}
            for k in ('glyphs', 'recipes', 'marks'):
                a, b = be.get(k, {}), e.get(k, {})
                ch = {n: v for n, v in b.items() if a.get(n) != v}; ch.update({n: None for n in a if n not in b})
                if ch: d['ed'][k] = ch
        hp2 = os.path.join(vd, tag, 'hornui.json')
        if os.path.exists(hp2):
            h = json.load(open(hp2)); d['hu'] = {k: v for k, v in h.items() if k != 'G' and bh.get(k) != v}
            d['hu']['G'] = {c: v for c, v in h.get('G', {}).items() if bh.get('G', {}).get(c) != v}
        out[tag] = d
    return out
VERDATA = _ver_diffs()

C = runpy.run_path(CONTENT, init_globals=dict(NOFONT=NOFONT, cv=cv, dec=dec, fb=fb, news=news, keynote=keynote, cite=cite, sec_done=sec_done, ED_HTML=ED_HTML, P=P, html=html, R=R, json=json, CONTENT_PATH=CONTENT, spec=spec, verspec=verspec, verspec2=verspec2, sources_html=sources_html, VK=VK, RULES=RULES, use_packs=use_packs))
JS, DOCK = adapt_js(JS, C['ROUND'], C['SLUG'], C['SUMHEAD'])
HEAD = ('\n<meta charset="utf-8">\n<title>%s</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">\n') % C['TITLE'] + C.get('EXTRA_HEAD', '')
# Tách CSS (người dùng 27/10 “để css riêng để các component chỉ hiện đúng như hiện tại”): CSS khung trang cũ (tpl/styles.css, INFO, SPEC2)
# vào @layer vk-legacy, CSS bàn vẽ vào @layer vk-ed → mọi luật của thành phần Việt Font Kit (VK.CSS, KN, slider, oldnew — không layer)
# luôn thắng, bất kể độ đặc hiệu (specificity) của bộ chọn cũ. Bộ chọn chung cũ (h1, code, .sec, .fbold…) không còn tự “mặc” lên thành phần mới.
def _layer(css, name):
    return css.replace('<style>', '<style>@layer ' + name + '{').replace('</style>', '}</style>')
LAYERS = '<style>@layer vk-legacy, vk-own, vk-ed;</style>'
# vk_own.css: luật riêng của thành phần VFK (chép từ lớp cũ, bọc :where(.vk)) — thành phần không còn phụ thuộc styles.css
_OWN = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vk_own.css')
if os.path.exists(_OWN): LAYERS += '<style>@layer vk-own{' + open(_OWN).read() + '}</style>'
TCSS, ED_CSS, SPEC2_CSS = _layer(TCSS, 'vk-legacy'), _layer(ED_CSS, 'vk-ed'), _layer(SPEC2_CSS, 'vk-legacy')   # INFO_CSS + MONO_CSS = lớp giao diện đơn sắc của Việt Font Kit → không layer
# vk_base.css: luật cấp trang (:root / html / body) KHÔNG layer — khung artifact chèn body{background:#fff;color:#000} không layer,
# nếu để trong @layer thì luật đó thắng → chế độ tối nền trắng chữ trắng (lỗi 27/10). Kiểm bằng --host (chèn khung giả lập).
_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vk_base.css')
BASE_CSS = '<style>' + open(_BASE).read() + '</style>' if os.path.exists(_BASE) else ''
# lưu dự phòng cho Claude bản Free (người dùng 27/10): vk_localdb.js chạy ĐẦU trang; mọi window.claude.use('db') → window.__vkDb()
_LDB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vk_localdb.js')
_KV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'VERSION')
LDB_JS = ('<script>window.__VK_DOCK=' + json.dumps(DOCK) + ';window.__VK_FONT=' + json.dumps(C.get('FONT_NAME', ''), ensure_ascii=False)
          + ';window.__VK_KITVER=' + json.dumps(open(_KV).read().strip() if os.path.exists(_KV) else '') + ';</script>\n<script>' + open(_LDB).read() + '</script>\n') if os.path.exists(_LDB) else ''
BODY = (HEAD + LDB_JS + '<script>' + UNDO_JS + '</script>\n' + LAYERS + TCSS + BASE_CSS + ED_CSS + MONO_CSS + FONT_CSS + INFO_CSS + C['PAGE']
        + '<script type="application/json" id="fv-data">' + DATA + '</script>\n'
        + ('<script type="application/json" id="fv-rules">' + json.dumps(RULES, ensure_ascii=False).replace('</', '<\\/') + '</script>\n' if RULES else '')
        + "<script>window.__FV_EDDOC = '" + DOCK + "/glyphs';</script>\n"
        + '<script type="application/json" id="fv-verdata">' + json.dumps(dict(VERDATA, __base=C.get('VER_BASE', '')), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>\n'
        + '<script>' + VERSYNC_JS + '</script>\n'
        + '<script>' + SPEC_JS + '</script>\n' + SPEC2_CSS + '<script>' + SPEC2_JS + '</script>\n'
        + ('' if NOFONT else '<script>' + EDJS + '</script>\n') + '<script>' + JS + '</script>\n<script>' + JS2 + '</script>\n'
        + (('<script>' + C['TAIL_JS'] + '</script>\n') if C.get('TAIL_JS') else ''))   # giao diện Việt Font Kit chạy sau cùng
BODY = BODY.replace("window.claude.use('db')", 'window.__vkDb()') if LDB_JS else BODY
assert not LDB_JS or "claude.use('db')" not in BODY.replace("u.call(window.claude, 'db')", '')
if not BODY.lstrip().lower().startswith('<!doctype'): BODY = '<!DOCTYPE html>\n' + BODY   # máy chủ artifact từ chối trang không mở bằng DOCTYPE (lỗi publish 27/10)
open(OUT, 'w').write(BODY)
if os.environ.get('HOST_OUT'):   # bản giả lập khung artifact claude.ai (chèn phần [0] của styles.css trước trang) — mọi test giao diện chạy trên bản này
    open(os.environ['HOST_OUT'], 'w').write('<style>' + css_parts[0] + '</style>' + BODY)
print(len(BODY) // 1024, 'KB', BODY.count('<div'), BODY.count('</div>'))
