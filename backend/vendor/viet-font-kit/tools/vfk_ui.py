"""Giao diện trang duyệt Việt Font Kit (bản tối giản, 26/10): thanh tiêu đề gọn → tên phông bằng chính phông đó →
thanh VIÊN THUỐC dính (mục lớn + số đếm, bên phải là viên thuốc VER chung cho cả trang) → từng mục hiện một lúc.
Trong mỗi mục, thứ tự luôn là: khung xem trước → ô nhập chữ ngay dưới → khung chỉnh (ngang hàng bên phải trên máy tính,
xuống dưới cùng trên điện thoại). Mục Xem trước có ô nạp font mẫu: nạp xong là so ngay (trên dưới / chồng lớp).
Dùng trong content_rN.py: vk_page(...) (build_page.py nạp sẵn). Hợp đồng sự kiện giữ như cũ: window.__FV_VERS,
window.__FV_PICK(tag), window.__FV_VER, sự kiện 'fv-ver' → khung kéo, bàn vẽ, So vị trí cũ đổi theo VER."""
import html, json

import os
KIT_NAME = "Việt Font Kit"
KIT_AUTHOR = "Nhật Motion's Space"          # tác giả, dòng nhỏ trên cùng
try: KIT_VER = "ver " + open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "VERSION")).read().strip()
except Exception: KIT_VER = "ver 1.0.0"

ICON = {
    "auto": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="M12 4v16" /><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor" stroke="none"/></svg>',
    "light": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    "dark": '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/></svg>',
    "font": '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20 10 4h1l6 16"/><path d="M6.5 14h8"/><path d="M19 9v6M16 12h6"/></svg>',
}

def top(font_name, ver_label):
    """đầu trang theo cấu trúc cũ: tác giả nhỏ trên cùng → tên bộ kit cỡ lớn (+ số phiên bản) → “Đang Việt hoá” + tên phông
    viết bằng chính phông đó + nhãn vòng. Nút sáng / tối góc phải."""
    th = ''.join('<button type="button" data-th="%s" aria-pressed="%s" title="%s" aria-label="%s">%s</button>' % (k, 'false', t, t, ICON[k])
                 for k, t in (('light', 'Nền sáng'), ('dark', 'Nền tối')))   # 2 nút (người dùng 27/10); chưa bấm thì theo máy
    # dải đen (strip) bao tác giả + tên kit (người dùng 27/10: phân cấp rõ), “Đang Việt hoá” nằm trên nền trang bên dưới
    return ('<header class="vk-top"><div class="vk-strip"><div class="vk-in vk-hero">'
            '<div class="vk-theme" role="group" aria-label="Giao diện sáng / tối">%s</div>'
            '<div class="vk-by">%s</div>'
            '<h1 class="vk-title">%s<span class="vk-kv">%s</span></h1></div></div>'
            '<div class="vk-in"><div class="vk-font"><span class="vk-lab">Đang Việt hoá</span><span class="vk-name" id="vk-heroname">%s</span>%s</div></div>'
            '</header>') % (th, KIT_AUTHOR, KIT_NAME, KIT_VER, html.escape(font_name), ('<span class="vk-round">%s</span>' % html.escape(ver_label)) if ver_label else '')

ICON_DL = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v11"/><path d="M7 10l5 5 5-5"/><path d="M5 20h14"/></svg>'
# nút XUẤT CHỈNH SỬA (bản Free, người dùng 27/10): cạnh nút VER trên thanh dính — mục nào cũng thấy. Ẩn sẵn; vk_localdb.js chỉ hiện khi trang không lưu được (Free).
EXP_BTN = ('<button type="button" class="vk-exp" data-vkexp="file" hidden title="Bản Free: tải file chỉnh sửa rồi gửi vào chat với Claude">' + ICON_DL
           + '<span>Xuất chỉnh sửa</span><span class="vk-exp-n" hidden></span></button><span class="vk-exp-msg" role="status" hidden></span>')

def guide_panel():
    """tab Hướng dẫn (trước Ủng hộ): cài skill · dùng · khác nhau Free / Pro — ngắn gọn."""
    st = ('<p class="vk-gd-mode" data-dbmode data-cloud="Trang này đang tự lưu (Pro / Max / Team) — chỉ cần nhắn “đọc góp ý”." '
          'data-local="Trang này đang lưu trên trình duyệt (bản Free) — xong mỗi vòng bấm “Xuất chỉnh sửa” rồi gửi file vào chat.">Đang kiểm tra cách lưu…</p>')
    return ('<div class="vk-gd">' + st +
            '<ol class="vk-gd-steps">'
            '<li><b>Cài skill</b><span>Tải file <code>viet-font-kit.zip</code> → Claude: <i>Customize → Skills</i> → tải lên. Bật <i>Settings → Capabilities → Create and edit files</i> (Code execution and file creation).</span></li>'
            '<li><b>Bắt đầu</b><span>Gửi file font gốc (.ttf / .otf) vào chat và nhắn “Việt hoá font này”. Claude dựng bản Việt hoá và trang duyệt này.</span></li>'
            '<li><b>Duyệt</b><span>Xem trước · Chỉnh dấu (Đồng loạt / Chi tiết) · Bàn vẽ. Ghi góp ý ở ô cuối mỗi mục.</span></li>'
            '<li><b>Gửi chỉnh sửa cho Claude</b><span data-dbmode data-cloud="Trang tự lưu — quay lại chat nhắn “đọc góp ý”." data-local="Bấm “Xuất chỉnh sửa” (cạnh nút VER, trên cùng) → gửi file .json vào chat, hoặc chép đoạn chữ rồi dán.">Tuỳ gói Claude bạn dùng.</span></li>'
            '<li><b>Chốt</b><span>Nhắn “chốt xuất VER n” → nhận file font + bản test tiếng Việt.</span></li></ol>'
            '<div class="vk-gd-plans">'
                        '<div class="vk-gd-plan" data-plan="local" hidden><h4>Free</h4><p>Artifact bản Free không có chỗ lưu, nên trang lưu trên trình duyệt này. Thêm <b>1 bước</b> mỗi vòng: bấm <b>Xuất chỉnh sửa</b> (cạnh nút VER, trên cùng) → gửi file <code>.json</code> vào chat. Hoặc chép đoạn chữ rồi dán. Ảnh / file minh hoạ thì gửi thẳng trong chat.</p>'
            '<div class="vk-gd-btns" data-vkexp-show hidden><button type="button" data-vkexp="file">' + ICON_DL + '<span>Tải file chỉnh sửa</span></button><button type="button" data-vkexp="copy"><span>Chép đoạn chữ</span></button></div>'
            '<span class="vk-exp-msg" role="status" hidden></span>'
            '<p class="vk-gd-note">Đừng xoá dữ liệu trình duyệt giữa chừng. Hạn mức bản Free thấp — gom góp ý một lần mỗi vòng cho đỡ tốn lượt.</p></div>'
            '</div></div>')

def tabs(items, vers):
    """items = [(khoá, nhãn, số đếm hoặc None, data-sec)] ; vers = [(tag, phụ đề, font-family, ghi chú)]"""
    t = ''.join('<button type="button" role="tab" class="vk-tab" id="tab-%s" data-tab="%s" aria-controls="p-%s" aria-selected="%s">%s%s</button>' % (
        k, k, k, 'true' if i == 0 else 'false', html.escape(lb), ('<span class="vk-n" data-count="%s">%s</span>' % (k, n)) if n is not None else '')
        for i, (k, lb, n, _s) in enumerate(items))
    v = ''.join('<button type="button" class="vk-ver" role="radio" data-i="%d" data-t="%s" aria-checked="%s" title="%s">%s</button>' % (
        i, html.escape(tg, True), 'true' if i == len(vers) - 1 else 'false', html.escape(sub, True), html.escape(tg)) for i, (tg, sub, f, n) in enumerate(vers))
    return ('<nav class="vk-nav"><div class="vk-in vk-navin"><div class="vk-tabs" role="tablist" aria-label="Mục">%s</div>'
            '<div class="vk-vers" role="radiogroup" aria-label="Version">%s</div>' + EXP_BTN + '<span class="vk-vnote" aria-live="polite"></span></div></nav>') % (t, v)

def preview(vers, text, size=48, meas='', outname='', style='Regular', ext='.ttf'):
    """mục Xem trước: khung xem (trái, trên; chip trạng thái lưu ở góc) → ô nhập chữ (ngay dưới) → khung chỉnh (phải):
    tên font xuất, cỡ, kern, line biên, font mẫu. outname = tên mặc định (VFK - <tên gốc>), người dùng sửa → lưu db <DOC>/out/name."""
    data = json.dumps([{'t': t, 's': s, 'f': f, 'n': n} for t, s, f, n in vers], ensure_ascii=False).replace('</', '<\\/')
    sizes = [10, 12, 16, 24, 32, 48, 72, 120, 200]
    zo = ''.join('<option value="%d"%s>%d px</option>' % (v, ' selected' if v == size else '', v) for v in sizes)
    return ('<div class="vk-pv" id="vk-pv" data-px="%d"><script type="application/json" class="vk-data">%s</script>'
            '<div class="vk-main">'
            '<div class="vk-vwrap"><div class="vk-view" tabindex="0" aria-label="Khung xem trước — chụm 2 ngón hoặc lăn chuột để phóng to tại chỗ trỏ; thả file font vào đây để so"><div class="vk-panes"></div><div class="vk-drop" hidden>Thả font mẫu để so</div></div><span class="vk-save" id="status">đang kết nối…</span></div>'
            '<div class="vk-mode"><div class="vk-seg vk-mseg" role="group" aria-label="Kiểu xem"><button type="button" data-v="van" aria-pressed="true">Văn mẫu</button><button type="button" data-v="chu" aria-pressed="false">Bảng chữ</button></div>'
            '<div class="vk-spsel" role="group" aria-label="Bài mẫu"></div><button type="button" class="vk-chip vk-spcap" aria-pressed="false" title="Tiêu đề viết hoa — soi dấu chồng chữ hoa">TIÊU ĐỀ HOA</button></div>'
            '<div class="vk-tawrap"><label class="vk-lab" for="vk-ta">Chữ mẫu</label><textarea id="vk-ta" rows="4" spellcheck="false">%s</textarea></div>'
            '</div>'
            '<aside class="vk-ctl" aria-label="Chỉnh khung xem">'
            '<div class="vk-out" data-style="%s" data-ext="%s"><label class="vk-lab" for="vk-outname">Tên font xuất</label><input id="vk-outname" type="text" spellcheck="false" autocomplete="off" value="%s" data-def="%s"><small class="vk-outps"></small></div>'
            '<div class="vk-row vk-tg"><button type="button" class="vk-chip" data-z="k" aria-pressed="true" hidden>kern</button>'
            '</div>'
            '<div class="vk-ref"><span class="vk-lab">Font mẫu</span>'
            '<label class="vk-load" for="vk-file">%s<span>Nạp font mẫu</span></label><input type="file" id="vk-file" accept=".ttf,.otf,.woff,.woff2,font/*" hidden>'
            '<div class="vk-refon" hidden><div class="vk-refname"><span></span><button type="button" class="vk-x" aria-label="Bỏ font mẫu" title="Bỏ font mẫu">×</button></div>'
            '<div class="vk-seg" role="group" aria-label="Cách so"><button type="button" data-m="stack" aria-pressed="true">Trên dưới</button><button type="button" data-m="overlay" aria-pressed="false">Chồng lớp</button></div></div>'
            '<p class="vk-err" role="alert" hidden></p></div>'
            '<p class="vk-desc"></p>'
            '%s'
            '</aside></div>') % (size, data, html.escape(text), html.escape(style, True), html.escape(ext, True), html.escape(outname, True), html.escape(outname, True), ICON['font'],
            '')   # bỏ “Số đo” (người dùng 27/10: thừa)

def panel(key, sec, inner, first=False):
    return '<section class="sec vk-panel" data-sec="%s" id="p-%s" role="tabpanel" aria-labelledby="tab-%s">%s</section>' % (sec, key, key, inner)

# chữ “a” nền sau thẻ kinh nghiệm: kiểu → họ chữ Google (chỉ để VẼ nền; file kinh nghiệm không ghi tên font, người dùng 28/10)
CHU_NEN = {"didone": "Playfair Display", "serif-dam": "DM Serif Display", "sans-tron": "Fredoka", "viet-tay": "Shadows Into Light"}
KN_TUNE = False   # thanh “Chữ nền” ở tab Kinh nghiệm (chỉnh vị trí / cỡ / mờ chữ “a” nền). Mặc định ở KN_JS: var D={r:18,y:-6,s:230,o:9,f:60}

# ---- tác giả / ủng hộ (tab Ủng hộ — người dùng 27/10) ----
DONATE = dict(bank="ACB", acct="39798267", name="NGUYEN MINH NHAT", mail="nhatmotion@gmail.com", qr="assets/donate-qr.jpg")

def nofont():
    """trạng thái CHƯA CÓ FONT cần Việt hoá (người dùng quên gửi font): khung nét đứt giống ô “Nạp font mẫu”."""
    return ('<div class="vk-nofont" role="status"><span class="vk-nf-ic" aria-hidden="true">%s</span>'
            '<b>Chưa có font cần Việt hoá</b>'
            '<span>Gửi file font gốc (.ttf / .otf) vào khung chat để bắt đầu. Trang sẽ hiện bản xem trước, chỉnh dấu và bàn vẽ sau khi dựng.</span></div>') % ICON['font']

def donate_panel():
    """tab Ủng hộ: lời cảm ơn + lưu ý dùng · liên hệ · mã QR + số tài khoản (bấm để chép)."""
    import os, base64
    q = os.path.join(os.path.dirname(os.path.abspath(__file__)), DONATE["qr"])
    img = ('<img class="vk-dn-qr" alt="Mã QR chuyển khoản %s %s" src="data:image/jpeg;base64,%s" width="248" height="300">' % (
        DONATE["bank"], DONATE["acct"], base64.b64encode(open(q, "rb").read()).decode())) if os.path.exists(q) else ""
    return ('<div class="vk-dn">'
            '<p class="vk-dn-lead">Cảm ơn bạn đã dùng Việt Font Kit!</p>'
            '<p class="vk-dn-txt">Đây là một tool nằm trong bộ công cụ mình tự dựng để tối ưu workflow edit video hằng ngày. Việc đóng gói sẵn thế này giúp tiết kiệm token hơn nhiều vì AI không cần phải build lại từ đầu mỗi lần dùng.</p>'
            '<p class="vk-dn-txt">☕️ Nếu thấy Việt Font Kit hữu ích cho công việc của bạn, có thể ủng hộ mình chút ‘năng lượng’ qua chiếc ví bên dưới. Giá trị tùy hỷ — từ 2k cái kẹo đến ly cà phê đều là động lực lớn để mình ra thêm nhiều món mới.</p>'
            '<p class="vk-dn-note">Công cụ dành cho mục đích phi thương mại. Vui lòng không thương mại hoá những font chưa được cấp phép.</p>'
            '<p class="vk-dn-mail">Liên hệ: <a href="mailto:@@M@@">@@M@@</a></p>'
            '<div class="vk-dn-card">@@IMG@@<div class="vk-dn-name">@@N@@</div>'
            '<button type="button" class="vk-dn-acct" data-copy="@@A@@" title="Bấm để chép số tài khoản">@@B@@ · <span>@@A@@</span><i>chép</i></button></div>'
            '</div>'
            '<script>(function(){var b=document.querySelector(".vk-dn-acct");if(!b)return;b.addEventListener("click",function(){var t=b.dataset.copy,i=b.querySelector("i");'
            'function ok(){i.textContent="đã chép";setTimeout(function(){i.textContent="chép";},1400);}'
            'if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(ok,function(){});else{var r=document.createRange();r.selectNodeContents(b.querySelector("span"));var s=getSelection();s.removeAllRanges();s.addRange(r);ok();}});})();</script>'
            ).replace("@@M@@", DONATE["mail"]).replace("@@N@@", DONATE["name"]).replace("@@A@@", DONATE["acct"]).replace("@@B@@", DONATE["bank"]).replace("@@IMG@@", img)

def news(items):
    """điểm mới vòng này: 1 dòng nhãn + 2–3 ý ngắn, đầu mục Xem trước"""
    return '<div class="vk-news"><b>Mới</b><ul>%s</ul></div>' % ''.join('<li>%s</li>' % x for x in items)

CSS = r"""<style>
/* Việt Font Kit — bố cục: thanh tiêu đề gọn · tên phông bằng chính phông · thanh viên thuốc dính · 1 mục / lần
   (xem trước → ô nhập → khung chỉnh). Màu lấy từ token --pg-* (trắng đen, đỏ = tràn / lỗi, xanh = đạt). */
:root{--vk-pill:999px;--vk-r:14px;--vk-ui:"Be Vietnam Pro",system-ui,sans-serif;--vk-mono:"Space Mono",ui-monospace,monospace;--vk-nav-bg:color-mix(in srgb,var(--pg-bg) 88%,transparent)}
[hidden]{display:none!important}
/* kính mờ (glass) cho mọi viên thuốc — người dùng 27/10 */
:root{--vk-glass:rgba(255,255,255,.52);--vk-glass-line:rgba(255,255,255,.75);--vk-glass-edge:rgba(0,0,0,.10);--vk-glass-sh:0 6px 22px rgba(0,0,0,.08),inset 0 1px 0 rgba(255,255,255,.7)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--vk-glass:rgba(40,40,40,.42);--vk-glass-line:rgba(255,255,255,.14);--vk-glass-edge:rgba(255,255,255,.10);--vk-glass-sh:0 6px 22px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.08)}}
:root[data-theme="dark"]{--vk-glass:rgba(40,40,40,.42);--vk-glass-line:rgba(255,255,255,.14);--vk-glass-edge:rgba(255,255,255,.10);--vk-glass-sh:0 6px 22px rgba(0,0,0,.4),inset 0 1px 0 rgba(255,255,255,.08)}
/* Văn mẫu: dòng nhỏ đầu · tiêu đề to · tiêu đề phụ · thân bài (cỡ theo khung phóng: thân = px/48 × 20) */
.vk-mode{display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:10px 0 0}
.vk-mode .vk-seg{display:inline-flex;gap:2px;padding:2px;border:1px solid var(--pg-line-2);border-radius:var(--vk-pill);background:var(--pg-card)}
.vk-mode .vk-seg button{white-space:nowrap;font:500 12.5px/1 var(--vk-ui);padding:7px 12px;border:0;border-radius:var(--vk-pill);background:transparent;color:var(--pg-mut);cursor:pointer}
.vk-mode .vk-seg button[aria-pressed="true"]{background:var(--pg-txt);color:var(--pg-bg)}
.vk-spsel{display:flex;flex-wrap:wrap;gap:6px}
.vk-spec{min-width:0!important}
.vk-sp{color:var(--pg-txt);max-width:38em;padding:6px 0 10px;white-space:normal}
.vk-sp .sp-e{font-size:.62em;letter-spacing:.14em;color:var(--pg-mut);margin-bottom:.6em}
.vk-sp .sp-t{font-size:3.2em;line-height:1.08;letter-spacing:-.01em;margin-bottom:.22em;text-wrap:balance}
.vk-sp .sp-s{font-size:1.5em;line-height:1.3;color:var(--pg-mut);margin-bottom:.9em;text-wrap:balance}
.vk-sp .sp-b{font-size:1em;line-height:1.65;white-space:pre-line;max-width:34em}
/* chưa có font (người dùng 27/10): khung nét đứt giống ô Nạp font mẫu */
.vk-nofont{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;text-align:center;min-height:260px;padding:32px 20px;border:1.5px dashed var(--pg-line-2);border-radius:var(--vk-r);background:var(--pg-card);color:var(--pg-txt)}
.vk-nofont b{font-size:17px}.vk-nofont span:last-child{max-width:46ch;font-size:13.5px;line-height:1.55;color:var(--pg-mut)}
.vk-nf-ic{display:grid;place-items:center;width:44px;height:44px;border-radius:var(--vk-pill);background:var(--pg-sunk);color:var(--pg-mut)}.vk-nf-ic svg{width:22px;height:22px}
/* tab Ủng hộ */
.vk-dn{max-width:560px;margin:0 auto 24px;display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px}
.vk-dn p{margin:0}.vk-dn-txt{font-size:15px;line-height:1.65;color:var(--pg-txt);max-width:52ch;margin-bottom:8px!important;text-wrap:pretty}
.vk-dn-lead{font-size:22px;font-weight:700;letter-spacing:-.01em;margin:0 0 10px!important;text-wrap:balance}
.vk-dn-note{font-size:14px;line-height:1.6;color:var(--pg-mut);max-width:44ch}
.vk-dn-mail{margin-top:10px!important;font-size:14px}.vk-dn-mail a{color:var(--pg-txt);font-weight:600;text-underline-offset:3px}
.vk-dn-card{margin-top:18px;padding:18px 18px 14px;border-radius:18px;background:#fff;color:#1f1e1d;border:1px solid var(--pg-line);display:flex;flex-direction:column;align-items:center;gap:6px;box-shadow:0 8px 28px rgba(0,0,0,.08)}
.vk-dn-qr{display:block;width:min(248px,64vw);height:auto}
.vk-dn-name{font-weight:700;font-size:15px;letter-spacing:.02em;margin-top:6px}
.vk-dn-acct{font:500 14px/1 var(--vk-ui);color:#1f1e1d;background:#f3f1ea;border:0;border-radius:var(--vk-pill);padding:8px 12px;cursor:pointer;display:inline-flex;gap:6px;align-items:center}
.vk-dn-acct span{font-family:var(--vk-mono);font-weight:700}.vk-dn-acct i{font-style:normal;font-size:11.5px;color:#5e5d57}
.vk-dn-acct:focus-visible{outline:2px solid #1f1e1d;outline-offset:2px}
/* kính mờ CHỈ cho chip thông tin trong khung xem (trạng thái lưu) — người dùng 27/10: bỏ kính ở mọi nút */
.vk-save,.hu-chip,.ed-save{background:var(--vk-glass)!important;-webkit-backdrop-filter:blur(16px) saturate(170%);backdrop-filter:blur(16px) saturate(170%);border:1px solid var(--vk-glass-edge)!important;box-shadow:var(--vk-glass-sh)}
.vk-ver[aria-checked="true"],.vk-chip[aria-pressed="true"]{background:var(--pg-txt)!important;color:var(--pg-bg);border-color:var(--pg-txt)!important}
.vk-nav{background:transparent;backdrop-filter:none;-webkit-backdrop-filter:none;border-bottom:0}
body{font-family:var(--vk-ui)}
body::before{content:"";position:fixed;inset:0 0 auto;height:env(safe-area-inset-top,0px);z-index:30;background:var(--pg-bg)}
.vk-in{max-width:1220px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
.vk-top{background:transparent}
/* một nền cho cả trang, chuyển nhẹ từ trên xuống (người dùng 27/10: bỏ đường kẻ → không chia mảng màu) */
body{background:var(--pg-bg)}
/* dải đầu trang: tác giả + tên kit — theo chế độ sáng / tối; luôn TỐI HƠN nền thao tác (người dùng 27/10: nền thao tác sáng hơn header, màu ấm như Claude) */
:root{--vk-strip:#efede5}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--vk-strip:#1a1918}}
:root[data-theme="dark"]{--vk-strip:#1a1918}
.vk-strip{background:var(--vk-strip);color:var(--pg-txt)}
.vk-strip .vk-hero{padding-bottom:clamp(24px,3vw,36px)}
.vk-font{margin-top:0!important;padding-top:clamp(18px,2.4vw,26px)!important;padding-bottom:clamp(10px,1.6vw,16px)}
.vk-hero{position:relative;padding-block:clamp(26px,4.4vw,44px) clamp(20px,2.6vw,28px);display:flex;flex-direction:column}
.vk-theme{position:absolute;top:14px;right:max(16px,env(safe-area-inset-right,0px));display:flex;gap:2px;padding:2px;border:1px solid var(--pg-line-2);border-radius:var(--vk-pill)}
.vk-theme button{display:grid;place-items:center;width:28px;height:26px;border:0;border-radius:var(--vk-pill);background:transparent;color:var(--pg-mut);cursor:pointer}
.vk-theme button[aria-pressed="true"]{background:var(--pg-txt);color:var(--pg-bg)}
.vk-by{font:italic 500 clamp(15px,1.6vw,18px)/1.3 "Playfair Display",Georgia,serif;color:var(--pg-mut);margin-bottom:6px}
.vk-title{margin:0;display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 14px;font:900 clamp(40px,8vw,92px)/1.02 "Be Vietnam Pro",system-ui,sans-serif;letter-spacing:-.035em;color:var(--pg-txt);text-wrap:balance}
.vk-kv{white-space:nowrap;font:400 12px/1 var(--vk-mono);letter-spacing:0;color:var(--pg-mut);border:1px solid var(--pg-line-2);border-radius:var(--vk-pill);padding:4px 9px;align-self:center}
.vk-font{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 12px;margin-top:22px;padding-top:14px;min-width:0}
.vk-name{font-family:"Font VN",var(--vk-ui);font-size:clamp(26px,4vw,40px);line-height:1.15;color:var(--pg-txt);overflow-wrap:anywhere;min-width:0}
.vk-round{font-size:12.5px;font-weight:600;color:var(--pg-ok);background:var(--pg-ok-bg);border-radius:var(--vk-pill);padding:2px 10px}
@media (max-width:620px){.vk-theme{position:static;align-self:flex-start;margin-bottom:16px}}
/* thanh viên thuốc */
.vk-nav{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:var(--vk-nav-bg);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px)}
.vk-navin{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;padding-block:10px}
.vk-tabs{display:flex;gap:4px;padding:4px;border-radius:var(--vk-pill);background:var(--pg-sunk);border:1px solid var(--pg-line);overflow-x:auto;scrollbar-width:none;max-width:100%;min-width:0}
.vk-tabs::-webkit-scrollbar{display:none}
.vk-tab{flex:none;display:inline-flex;align-items:center;gap:7px;font:500 14px/1 var(--vk-ui);padding:9px 16px;border:0;border-radius:var(--vk-pill);background:transparent;color:var(--pg-mut);cursor:pointer;white-space:nowrap}
.vk-tab:hover{color:var(--pg-txt)}
.vk-tab[aria-selected="true"]{background:var(--pg-txt);color:var(--pg-bg);font-weight:600}
.vk-n{font:600 11px/1 var(--vk-ui);font-variant-numeric:tabular-nums;padding:3px 7px;border-radius:var(--vk-pill);background:var(--pg-line);color:var(--pg-txt)}
.vk-tab[aria-selected="true"] .vk-n{background:color-mix(in srgb,var(--pg-bg) 22%,transparent);color:var(--pg-bg)}
.vk-n:empty{display:none}
.vk-vers{display:flex;flex-wrap:wrap;gap:4px;margin-left:0}
/* Chỉnh dấu: khung xem Đồng loạt và Chi tiết CÙNG cỡ, cùng kiểu (người dùng 27/10: chuyển chế độ không giật) */
:root{--vk-pvh:clamp(340px,56vh,540px)}
#vk-batch .vb-view,#p-chinh #hu11-view{min-height:var(--vk-pvh);box-sizing:border-box;border:1px solid var(--pg-line-2);border-radius:var(--vk-r);background:var(--pg-card);color:var(--pg-txt)}
#vk-batch .vb-zf{box-sizing:border-box}   /* min-height chung, KHÔNG cố định height: chữ dài hơn khung thì khung cao theo, không cắt chữ (lỗi 28/10 điện thoại) */
#p-chinh #hu11-view{max-height:none;padding:34px 16px 16px;overflow:auto}
#p-chinh .hu11-main{gap:18px;grid-template-columns:minmax(0,1fr) 300px}
@media (max-width:860px){#p-chinh .hu11-main{grid-template-columns:minmax(0,1fr)}}
@media (max-width:620px){#p-chinh #hu11-grpbar .hu-grp,#vk-batch .vb-tabs,#p-chinh .vk-lgd{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;white-space:nowrap}
 #p-chinh #hu11-grpbar .hu-grp::-webkit-scrollbar,#vk-batch .vb-tabs::-webkit-scrollbar,#p-chinh .vk-lgd::-webkit-scrollbar{display:none}
 #p-chinh #hu11-grpbar .hu-grp>*,#vk-batch .vb-tabs>*,#p-chinh .vk-lgd>*{flex:none}}   /* điện thoại: tab loại dấu / chú giải 1 dòng, vuốt ngang → khung xem 2 chế độ cùng chỗ */
#p-chinh #hu11-grpbar{margin:0}#p-chinh #hu11-grpbar .hu-grp,#vk-batch .vb-tabs{margin:0 0 8px;min-height:33px}
.vk-zoomable{scrollbar-width:none;-ms-overflow-style:none}.vk-zoomable::-webkit-scrollbar{display:none;width:0;height:0}   /* khung xem kéo bằng chuột / ngón tay như Google Maps → ẩn thanh cuộn (người dùng 27/10), vẫn cuộn được */
.vk-ver{font:600 12.5px/1 var(--vk-ui);padding:8px 12px;border-radius:var(--vk-pill);border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);cursor:pointer;white-space:nowrap}
.vk-ver:hover{border-color:var(--pg-txt)}
.vk-ver[aria-checked="true"]{background:var(--pg-txt);color:var(--pg-bg);border-color:var(--pg-txt)}
.vk-ver.nodata{border-style:dashed}
.vk-exp{display:inline-flex;align-items:center;gap:6px;font:600 12.5px/1 var(--vk-ui);padding:8px 12px;border-radius:var(--vk-pill);border:0;background:var(--pg-txt);color:var(--pg-bg);cursor:pointer;white-space:nowrap}
.vk-exp[hidden]{display:none}.vk-local .ntaplus{display:none}   /* Free: không có chỗ lưu file → bỏ nút + đính kèm, gửi ảnh trong chat */.vk-exp-n{font:600 11px/1 var(--vk-mono);padding:2px 6px;border-radius:99px;background:var(--pg-bg);color:var(--pg-txt)}
.vk-exp-msg{flex-basis:100%;font-size:12px;color:var(--pg-mut);text-align:right}
#vk-expdlg{position:fixed;inset:0;z-index:2147483000;display:grid;place-items:center;padding:16px;background:rgba(0,0,0,.45)}#vk-expdlg[hidden]{display:none}
.vk-xd{width:min(560px,100%);max-height:86vh;display:flex;flex-direction:column;gap:10px;padding:16px;border-radius:14px;background:var(--pg-card);color:var(--pg-txt);border:1px solid var(--pg-line-2);box-sizing:border-box}
.vk-xd-h{display:flex;align-items:center;justify-content:space-between;font:600 15px/1.2 var(--vk-ui)}
.vk-xd-x{width:32px;height:32px;border:0;border-radius:50%;background:var(--pg-sunk);color:var(--pg-txt);font-size:20px;line-height:1;cursor:pointer}
.vk-xd-p{margin:0;font-size:13px;line-height:1.5;color:var(--pg-mut)}
.vk-xd-ta{width:100%;min-height:160px;flex:1;box-sizing:border-box;font:11.5px/1.45 var(--vk-mono);padding:10px;border-radius:10px;border:1px solid var(--pg-line-2);background:var(--pg-bg);color:var(--pg-txt);resize:vertical}
.vk-xd-b{display:flex;gap:8px;justify-content:flex-end}.vk-xd-b button{font:600 13px/1 var(--vk-ui);padding:9px 14px;border-radius:var(--vk-pill);border:1px solid var(--pg-line-2);background:var(--pg-bg);color:var(--pg-txt);cursor:pointer}
.vk-xd-b .vk-xd-x2{background:var(--pg-txt);color:var(--pg-bg);border-color:var(--pg-txt)}
.vk-gd{max-width:720px;display:flex;flex-direction:column;gap:18px}
.vk-gd-mode{margin:0;font:500 13.5px/1.5 var(--vk-ui);padding:10px 14px;border-radius:10px;background:var(--pg-sunk);color:var(--pg-txt)}
.vk-gd-steps{margin:0;padding:0;list-style:none;counter-reset:g;display:flex;flex-direction:column;gap:12px}
.vk-gd-steps li{counter-increment:g;display:grid;grid-template-columns:26px 1fr;gap:2px 10px;font-size:14px;line-height:1.5}
.vk-gd-steps li::before{content:counter(g);grid-row:span 2;display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--pg-txt);color:var(--pg-bg);font:600 12px/1 var(--vk-ui)}
.vk-gd-steps span{color:var(--pg-mut)}.vk-gd code{font:12.5px var(--vk-mono)}
.vk-gd-plans{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;align-items:start}.vk-gd-plan[hidden]{display:none}   /* chỉ hiện thẻ đúng gói đang dùng (người dùng 27/10) */
.vk-gd-plan{border:1px solid var(--pg-line-2);border-radius:var(--vk-r);background:var(--pg-card);padding:14px 16px}
.vk-gd-plan h4{margin:0 0 6px;font:600 14px/1.2 var(--vk-ui)}.vk-gd-plan p{margin:0;font-size:13.5px;line-height:1.55;color:var(--pg-mut)}.vk-gd-plan p b{color:var(--pg-txt)}
.vk-gd-btns{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.vk-gd-btns[hidden]{display:none}
.vk-gd-btns button{display:inline-flex;align-items:center;gap:6px;font:600 12.5px/1 var(--vk-ui);padding:9px 13px;border-radius:var(--vk-pill);border:1px solid var(--pg-line-2);background:var(--pg-bg);color:var(--pg-txt);cursor:pointer}
.vk-gd-btns button:first-child{background:var(--pg-txt);color:var(--pg-bg);border-color:var(--pg-txt)}
.vk-gd .vk-exp-msg{display:block;text-align:left;margin-top:8px}.vk-gd .vk-exp-msg[hidden]{display:none}
.vk-gd-note{margin-top:10px!important;font-size:12.5px!important}
.vk-vnote{flex-basis:100%;font-size:12px;color:var(--pg-mut);text-align:right}.vk-vnote:empty{display:none}
.vk-tab:focus-visible,.vk-ver:focus-visible,.vk-theme button:focus-visible,.vk-chip:focus-visible,.vk-step button:focus-visible,.vk-seg button:focus-visible,.vk-load:focus-within,.vk-x:focus-visible{outline:2px solid var(--pg-accent);outline-offset:2px}
/* mục */
.vk-body{padding-block:22px 80px}
@media (max-width:620px){.vk-body{padding-top:12px}}
.vk .sec.vk-panel{background:transparent;border:0;border-radius:0;padding:0;margin:0}
.vk-panel[hidden]{display:none}
.vk-news{display:flex;gap:10px;align-items:baseline;margin:0 0 16px;font-size:13px;color:var(--pg-mut)}
.vk-news b{flex:none;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--pg-txt)}
.vk-news ul{margin:0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:4px 18px}
.vk-lab{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--pg-mut)}
/* Xem trước: xem → nhập → chỉnh */
.vk-pv{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:16px;align-items:start}
.vk-main{display:flex;flex-direction:column;gap:8px;min-width:0}
.vk-vwrap{position:relative;min-width:0}
.vk-zoomable{touch-action:pan-x pan-y;overscroll-behavior:contain}
.vk-zoomable>*{transform-origin:0 0}
.vk-zoomable{cursor:grab;-webkit-user-select:none;user-select:none;-webkit-touch-callout:none}.vk-zoomable svg{-webkit-user-drag:none}.vk-zoomable.vk-grab{cursor:grabbing;user-select:none}.vk-zoomable .hu-hit,.vk-zoomable [data-ch]{cursor:pointer}
.zpill{position:absolute;right:12px;bottom:12px;z-index:3;display:flex;padding:3px;gap:2px;border-radius:999px;border:1px solid var(--pg-line-2);background:color-mix(in srgb,var(--pg-card) 88%,transparent);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);box-shadow:0 2px 10px rgba(0,0,0,.12)}
.zpill button{width:34px;height:30px;border:0;border-radius:999px;background:transparent;color:var(--pg-txt);font:500 18px/1 var(--vk-ui);cursor:pointer}
.zpill button:hover{background:var(--pg-sunk)}.zpill button:focus-visible{outline:2px solid var(--pg-accent);outline-offset:1px}
.vk .ed-pv{position:relative}.vk .hu11-vwrap{position:relative}
.vk-save{position:absolute;top:9px;right:10px;z-index:3;display:inline-flex;align-items:center;gap:6px;padding:3px 9px 3px 7px;border-radius:var(--vk-pill);border:1px solid var(--pg-line);background:var(--pg-card);font-size:11px;color:var(--pg-mut);white-space:nowrap;pointer-events:none}
.vk-save::before{content:"";width:7px;height:7px;border-radius:50%;background:var(--pg-mut-2)}.vk-save:has(b)::before{background:var(--pg-ok)}.vk-save b{font-weight:500;color:inherit}
.vk-view{position:relative;border:1px solid var(--pg-line-2);border-radius:var(--vk-r);background:var(--pg-card);overflow:auto;min-height:160px}
.vk-view:focus-visible{outline:2px solid var(--pg-accent);outline-offset:2px}
.vk-view.drag{border-color:var(--pg-txt);border-style:dashed}
.vk-panes{display:flex;flex-direction:column}
.vk-pane{padding:14px calc(18px*var(--vkz,1)) 16px;min-width:max-content}
.vk-pane+.vk-pane{border-top:1px dashed var(--pg-line-2)}
.vk-pl{display:flex;gap:8px;align-items:baseline;font:600 11px/1.3 var(--vk-ui);letter-spacing:.06em;text-transform:uppercase;color:var(--pg-mut);margin-bottom:6px;position:sticky;left:0}
.vk-pl i{font:400 11px var(--vk-mono);letter-spacing:0;text-transform:none;color:var(--pg-mut-2)}
.vk-tx{white-space:pre;color:var(--pg-txt);font-kerning:normal}
.vk-tx .ab{display:inline-block;box-shadow:inset 1px 0 0 var(--pg-red),inset -1px 0 0 var(--pg-red)}
.vk-ov text{fill:var(--pg-txt)}.vk-ov text.r{fill:var(--pg-red);fill-opacity:.62}
.vk-ov{display:block}
.vk-key{display:flex;gap:14px;font-size:11.5px;color:var(--pg-mut);margin-bottom:8px;position:sticky;left:0}
.vk-key span{display:inline-flex;align-items:center;gap:6px}.vk-key span::before{content:"";width:10px;height:10px;border-radius:3px;background:var(--pg-txt)}
.vk-key span.r::before{background:var(--pg-red);opacity:.62}
.vk-drop{position:absolute;inset:0;display:grid;place-items:center;font-weight:600;background:color-mix(in srgb,var(--pg-card) 86%,transparent);color:var(--pg-txt)}
#vk-ta,.vk .ed-pvin textarea,.vk .hu11-txt textarea{width:100%;box-sizing:border-box;font:inherit;font-size:14px;line-height:1.5;color:var(--pg-txt);background:var(--pg-card);border:1px solid var(--pg-line);border-radius:10px;padding:10px 12px;resize:vertical;min-width:0}
#vk-ta:focus,.vk .ed-pvin textarea:focus,.vk .hu11-txt textarea:focus{outline:none;border-color:var(--pg-txt)}
.vk-ctl{display:flex;flex-direction:column;gap:16px;position:sticky;top:calc(env(safe-area-inset-top,0px) + 76px);min-width:0}
.vk-out{display:flex;flex-direction:column;gap:6px;order:9}   /* Tên font xuất nằm CUỐI cột, Font mẫu lên đầu (người dùng 27/10) */   /* không kẻ ngang (người dùng 27/10) — tách nhóm bằng khoảng trống */
#vk-outname{font:inherit;font-size:14px;font-weight:600;color:var(--pg-txt);background:var(--pg-card);border:1px solid var(--pg-line-2);border-radius:10px;padding:9px 11px;min-width:0;width:100%;box-sizing:border-box}
#vk-outname:focus{outline:none;border-color:var(--pg-txt)}
.vk-outps{font:400 11px/1.4 var(--vk-mono);color:var(--pg-mut);overflow-wrap:anywhere}
.vk-row{display:flex;align-items:center;justify-content:flex-start;gap:8px;flex-wrap:wrap}
.vk-step{display:flex;align-items:center;gap:4px}
.vk-step button,.vk-step select{font:inherit;font-size:13px;min-height:32px;border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);border-radius:9px;cursor:pointer}
.vk-step button{width:32px}.vk-step select{padding:0 6px}
.vk-tg{justify-content:flex-start}
.vk-chip{font:500 12.5px/1 var(--vk-ui);padding:8px 12px;border-radius:var(--vk-pill);border:1px solid var(--pg-line-2);background:transparent;color:var(--pg-mut);cursor:pointer}
.vk-chip[aria-pressed="true"]{background:var(--pg-txt);color:var(--pg-bg);border-color:var(--pg-txt);font-weight:600}
.vk-ref{display:flex;flex-direction:column;gap:8px}   /* không kẻ ngang (người dùng 27/10) */
.vk-tg:not(:has(>:not([hidden]))){display:none}   /* hàng nút trống (Văn mẫu ẩn “line biên”) thì không chiếm chỗ */
.vk-load{display:flex;align-items:center;justify-content:center;gap:8px;padding:11px 12px;border:1px dashed var(--pg-line-2);border-radius:12px;font-size:13px;font-weight:600;cursor:pointer;color:var(--pg-txt);background:var(--pg-card)}
.vk-load:hover{border-color:var(--pg-txt)}
.vk-refon{display:flex;flex-direction:column;gap:8px}
.vk-refname{display:flex;align-items:center;gap:6px;justify-content:space-between;padding:7px 8px 7px 12px;border-radius:10px;background:var(--pg-sunk);font-size:12.5px;min-width:0}
.vk-refname span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.vk-x{flex:none;width:24px;height:24px;border:0;border-radius:50%;background:transparent;color:var(--pg-mut);font-size:17px;line-height:1;cursor:pointer}.vk-x:hover{color:var(--pg-red)}
.vk-seg{display:flex;gap:2px;padding:2px;border:1px solid var(--pg-line-2);border-radius:var(--vk-pill)}
.vk-seg button{flex:1;font:500 12px/1 var(--vk-ui);padding:7px 8px;border:0;border-radius:var(--vk-pill);background:transparent;color:var(--pg-mut);cursor:pointer}
.vk-seg button[aria-pressed="true"]{background:var(--pg-txt);color:var(--pg-bg);font-weight:600}
.vk-err{margin:0;font-size:12px;color:var(--pg-red)}
.vk-desc{margin:0;font-size:12.5px;color:var(--pg-mut);line-height:1.5}.vk-desc:empty{display:none}
.vk-more summary{cursor:pointer;font-size:12.5px;font-weight:600}.vk-more .meas{font-size:12.5px;color:var(--pg-mut);margin-top:6px}
.vk .notewrap{margin-top:22px}
.vk-fb{margin-top:18px}.vk .onbox{margin-top:18px}.vk .onbox h3{font-size:15px!important}
/* Chỉnh dấu: khung xem bên trái; cột phải: chữ mẫu → nút → thanh kéo. Bàn vẽ: khung vẽ → chữ mẫu → xem trong chữ */
.vk .hu11-txt{margin:0}.vk .hu11-under{margin-top:0}
.vk .ed{margin-top:0}
@media (max-width:860px){.vk-pv{grid-template-columns:minmax(0,1fr)}.vk-ctl{position:static}}
@media (max-width:620px){.vk-vers{margin-left:0}.vk-vnote{text-align:left}.vk-tab{padding:8px 13px;font-size:13.5px}}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>"""

JS = r"""(function(){
var root=document.documentElement;
/* ---- giao diện sáng / tối ---- */
var tg=document.querySelector('.vk-theme');
/* 2 nút sáng / tối: chưa bấm = theo máy (nút sáng lên theo chế độ máy đang dùng); bấm = chọn hẳn, nhớ trên máy này */
var mq=window.matchMedia?matchMedia('(prefers-color-scheme: dark)'):null;
function eff(v){return v==='light'||v==='dark'?v:(mq&&mq.matches?'dark':'light');}
function th(v,keep){if(v==='light'||v==='dark')root.setAttribute('data-theme',v);else root.removeAttribute('data-theme');
 var e=eff(v);tg.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.th===e));});if(!keep)try{localStorage.setItem('fv-theme',v);}catch(_){}}
var sv='auto';try{sv=localStorage.getItem('fv-theme')||'auto';}catch(e){}th(sv,true);
if(mq&&mq.addEventListener)mq.addEventListener('change',function(){if(!root.getAttribute('data-theme'))th('auto',true);});
tg.addEventListener('click',function(e){var b=e.target.closest('button');if(b)th(b.dataset.th);});
/* ---- thanh viên thuốc: 1 mục / lần, nhớ mục đang mở, #token mở thẳng mục ---- */
var T=[].slice.call(document.querySelectorAll('.vk-tab')),shown={};
function show(k,foc){var ok=T.some(function(b){return b.dataset.tab===k;});if(!ok)k=T[0].dataset.tab;
 T.forEach(function(b){var on=b.dataset.tab===k;b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;var p=document.getElementById('p-'+b.dataset.tab);if(p)p.hidden=!on;if(on&&foc)b.focus();});
 window.__VK_TAB=k;try{localStorage.setItem('vk-tab',k);}catch(e){}
 setTimeout(function(){window.dispatchEvent(new Event('resize'));if(k==='ve'&&!shown.ve){var f=document.querySelector('[data-ed="fit"]');if(f)f.click();}shown[k]=1;vnote();},30);}
window.__VK_SHOW=show;
/* ---- thẻ thanh kéo (Đồng loạt / Chi tiết) căn đỉnh với khung xem, không với hàng tab loại dấu (người dùng 27/10) ---- */
function vkAlign(){[['#vk-batch .vb-view','#vk-batch .vb-ctl'],['#hu11-view','#hu11-ctl']].forEach(function(q){var v=document.querySelector(q[0]),c=document.querySelector(q[1]);if(!v||!c)return;
 if(!v.offsetParent||!c.offsetParent)return;var vb=v.getBoundingClientRect(),cb=c.getBoundingClientRect(),m0=parseFloat(c.style.marginTop)||0;
 if(cb.left<vb.right-4){if(m0)c.style.marginTop='';return;}   /* điện thoại: thẻ nằm dưới khung xem → giữ nguyên */
 var d=Math.max(0,Math.round(vb.top-cb.top+m0));if(Math.abs(d-m0)>1)c.style.marginTop=d+'px';});
 /* Bàn vẽ: thanh công cụ dọc + bảng ký tự ngang đỉnh KHUNG VẼ, khung vẽ kéo dài bằng đáy bảng (người dùng 28/10).
    Không đặt lại 0 rồi đo (gây nhảy layout → ResizeObserver gọi lại liên tục = khung giật): tính từ lề đang có, chỉ ghi khi lệch > 1 px. */
 var eb=document.querySelector('.ed-bar'),es=document.querySelector('.ed-stage'),sd=document.querySelector('.ed-side'),cv=document.querySelector('.ed-stage svg.ed-cv');
 function mt(e){return parseFloat(e.style.marginTop)||0;}
 function setMt(e,v){v=Math.max(0,Math.round(v));if(Math.abs(mt(e)-v)>1)e.style.marginTop=v+'px';}
 if(eb&&es&&eb.offsetParent&&es.offsetParent){var B=eb.getBoundingClientRect(),S=es.getBoundingClientRect();
  if(B.right<=S.left+4)setMt(eb,S.top-B.top+mt(eb));else if(mt(eb))eb.style.marginTop='';}
 if(sd&&es&&cv&&sd.offsetParent&&es.offsetParent){var S2=es.getBoundingClientRect(),D2=sd.getBoundingClientRect();
  if(D2.left>=S2.right-4){setMt(sd,S2.top-D2.top+mt(sd));S2=es.getBoundingClientRect();D2=sd.getBoundingClientRect();
   var cur=cv.getBoundingClientRect().height;if(!cv.__vkH0)cv.__vkH0=cur;
   var want=Math.round(Math.max(cv.__vkH0,cur+(D2.bottom-S2.bottom)));
   if(Math.abs(cur-want)>1){cv.style.height=want+'px';clearTimeout(vkAlign._t);vkAlign._t=setTimeout(function(){window.dispatchEvent(new Event('resize'));},80);}}
  else{if(mt(sd))sd.style.marginTop='';if(cv.style.height)cv.style.height='';}}}
window.__vkAlign=vkAlign;window.addEventListener('resize',function(){requestAnimationFrame(vkAlign);});
document.addEventListener('click',function(){setTimeout(vkAlign,40);},true);
if(window.ResizeObserver){var _ro=new ResizeObserver(function(){requestAnimationFrame(vkAlign);});['p-chinh','p-ve'].forEach(function(id){var e=document.getElementById(id);if(e)_ro.observe(e);});}
setTimeout(vkAlign,300);
window.__VK_GO=function(k,ch){show(k);setTimeout(function(){if(ch&&window.__edOpen&&!window.__edOpen(ch)){var n=document.querySelector('.vk-vnote');if(n)n.textContent='Bàn vẽ chưa có chữ “'+ch+'”';}var p=document.getElementById('p-'+k),nv=document.querySelector('.vk-nav');if(p)window.scrollTo({top:p.getBoundingClientRect().top+window.scrollY-(nv?nv.offsetHeight:0)-14,behavior:'smooth'});},80);};
document.querySelector('.vk-tabs').addEventListener('click',function(e){var b=e.target.closest('.vk-tab');if(b)show(b.dataset.tab);});
document.querySelector('.vk-tabs').addEventListener('keydown',function(e){var d={ArrowLeft:-1,ArrowRight:1}[e.key];if(!d)return;e.preventDefault();var i=T.findIndex(function(b){return b.dataset.tab===window.__VK_TAB;});show(T[(i+d+T.length)%T.length].dataset.tab,true);});
var start=(location.hash||'').slice(1);if(!start){try{start=localStorage.getItem('vk-tab')||'';}catch(e){}}
/* ---- tên font xuất: sửa ở Xem trước → tên ở đầu trang đổi theo, lưu db <DOC>/out/name, ghi vào tóm tắt ---- */
var ON=document.getElementById('vk-outname'),OBOX=ON&&ON.closest('.vk-out'),HN=document.getElementById('vk-heroname'),ODB=null,OT=null;
function psOf(n){return n.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[đĐ]/g,function(c){return c==='đ'?'d':'D';}).replace(/\s+-\s+/g,'-').replace(/[^A-Za-z0-9-]/g,'').slice(0,63);}
function outInfo(){if(!ON)return;var n=ON.value.trim()||ON.dataset.def,ps=psOf(n),st=OBOX.dataset.style||'Regular';
 OBOX.querySelector('.vk-outps').textContent=ps+(st==='Regular'?'':'-'+st)+' · '+ps+'-'+st+(OBOX.dataset.ext||'.ttf');if(HN)HN.textContent=n;}
window.__asSummary=function(){return ON?'Tên font xuất: '+(ON.value.trim()||ON.dataset.def):'';};
function outBase(){return (window.__FV_EDDOC||'').replace(/\/glyphs$/,'');}
if(ON){outInfo();ON.addEventListener('input',function(){outInfo();clearTimeout(OT);OT=setTimeout(function(){
  if(window.__save)window.__save();if(ODB&&outBase())ODB.doc(outBase()+'/out/name').set({name:ON.value.trim()||ON.dataset.def,ps:psOf(ON.value.trim()||ON.dataset.def),at:new Date().toISOString()}).catch(function(){});},700);});
 var up=(window.claude&&window.claude.use)?Promise.resolve().then(function(){return window.claude.use('db');}):Promise.resolve(null);
 up.then(function(d){ODB=d;if(!d||!outBase())return;return d.doc(outBase()+'/out/name').get().then(function(s){if(s.exists){var v=s.data()||{};if(v.name){ON.value=v.name;outInfo();}}});}).catch(function(){});}
/* ---- viên thuốc VER chung + khung xem trước ---- */
var VD={};try{VD=JSON.parse(document.getElementById('fv-verdata').textContent);}catch(e){}
function hasD(t){return t===VD.__base||!!VD[t];}
var P=document.getElementById('vk-pv'),VP=document.querySelector('.vk-vers');
var V=P?JSON.parse(P.querySelector('.vk-data').textContent):[],cur=V.length-1;
VP.querySelectorAll('.vk-ver').forEach(function(b){if(!hasD(b.dataset.t))b.classList.add('nodata');});
function vnote(){var n=document.querySelector('.vk-vnote');if(!n||!V.length)return;var t=V[cur].t,k=window.__VK_TAB;
 n.textContent=(!hasD(t)&&(k==='chinh'||k==='ve'))?t+' là font gốc · mục này giữ '+(window.__FV_SHOWN||VD.__base):'';}
var Z=[10,12,16,24,32,48,72,120,200],px=P?(+P.dataset.px||48):48,kern=true,lines=false,ref=null,mode='stack';
function esc(c){return c==='&'?'&amp;':c==='<'?'&lt;':c==='>'?'&gt;':c;}
function say(){if(!V[cur])return;window.__FV_VER=V[cur].t;try{window.dispatchEvent(new CustomEvent('fv-ver',{detail:{tag:V[cur].t,fam:V[cur].f}}));}catch(e){}}
function pick(i,foc){if(i<0||i>=V.length)return;cur=i;try{localStorage.setItem('fv-ver2-vv',V[cur].t);}catch(e){}
 VP.querySelectorAll('.vk-ver').forEach(function(b,j){b.setAttribute('aria-checked',String(j===cur));b.tabIndex=j===cur?0:-1;if(j===cur&&foc)b.focus();});
 if(P)ap();say();vnote();}
window.__FV_VERS=V;window.__FV_PICK=function(t){V.forEach(function(v,i){if(v.t===t)pick(i);});};
VP.addEventListener('click',function(e){var b=e.target.closest('.vk-ver');if(b)pick(+b.dataset.i);});
VP.addEventListener('keydown',function(e){var d={ArrowLeft:-1,ArrowUp:-1,ArrowRight:1,ArrowDown:1}[e.key];if(!d)return;e.preventDefault();pick((cur+d+V.length)%V.length,true);});
window.addEventListener('fv-ver',function(e){if(hasD(e.detail.tag))window.__FV_SHOWN=e.detail.tag;});
if(P){
 var ta=document.getElementById('vk-ta'),view=P.querySelector('.vk-view'),panes=P.querySelector('.vk-panes'),zpb=null;
 if(document.fonts&&document.fonts.load)V.forEach(function(v){document.fonts.load('48px "'+v.f+'"',ta.value||'a');});
 function rows(fam,lab,sub){var L=ta.value.split('\n'),lh=Math.round(px*1.45);
  var h=L.map(function(s){return Array.from(s).map(function(c){return lines&&c!==' '?'<span class="ab">'+esc(c)+'</span>':esc(c);}).join('');}).join('\n');
  return '<div class="vk-pane"><div class="vk-pl">'+lab+(sub?' <i>'+sub+'</i>':'')+'</div><div class="vk-tx" style="font-family:\''+fam+'\';font-size:'+px+'px;line-height:'+lh+'px;font-kerning:'+(kern?'normal':'none')+';font-feature-settings:'+(kern?'normal':'"kern" 0')+'">'+h+'</div></div>';}
 function overlay(){var L=ta.value.split('\n'),lh=Math.round(px*1.45),pad=Math.round(px*0.4),NS='http://www.w3.org/2000/svg';
  var s=document.createElementNS(NS,'svg');s.setAttribute('class','vk-ov');s.setAttribute('role','img');s.setAttribute('aria-label','Chồng lớp '+V[cur].t+' và font mẫu');
  var W=0;[['FV-ref','r'],[V[cur].f,'']].forEach(function(o){L.forEach(function(line,i){var t=document.createElementNS(NS,'text');t.setAttribute('x','0');t.setAttribute('y',String(pad+lh*i+Math.round(px*1.0)));
   t.setAttribute('class',o[1]);t.style.fontFamily="'"+o[0]+"'";t.style.fontSize=px+'px';t.style.fontKerning=kern?'normal':'none';t.style.whiteSpace='pre';t.textContent=line;s.appendChild(t);});});
  var box=document.createElement('div');box.className='vk-pane';box.innerHTML='<div class="vk-key"><span>'+V[cur].t+'</span><span class="r">Font mẫu</span></div>';box.appendChild(s);panes.innerHTML='';panes.appendChild(box);
  var H=pad*2+lh*L.length;s.setAttribute('height',H);s.setAttribute('width',100);
  s.querySelectorAll('text').forEach(function(t){try{W=Math.max(W,t.getComputedTextLength());}catch(e){}});s.setAttribute('width',Math.ceil(W+4));s.setAttribute('viewBox','0 0 '+Math.ceil(W+4)+' '+H);}
 /* Văn mẫu (người dùng 27/10): xem chữ trong bố cục văn bản thật — dòng nhỏ đầu · tiêu đề to · tiêu đề phụ · thân bài.
    Chỉ dùng văn thơ phạm vi công cộng (Nguyễn Du, Hồ Xuân Hương, ca dao). */
 var SP=[{k:'Truyện Kiều',e:'Nguyễn Du · Truyện Kiều',t:'Trăm năm trong cõi người ta',s:'Chữ tài chữ mệnh khéo là ghét nhau',
   b:'Trải qua một cuộc bể dâu,\nNhững điều trông thấy mà đau đớn lòng.\nLạ gì bỉ sắc tư phong,\nTrời xanh quen thói má hồng đánh ghen.\nCảo thơm lần giở trước đèn,\nPhong tình cổ lục còn truyền sử xanh.'},
  {k:'Bánh trôi nước',e:'Hồ Xuân Hương · Thơ Nôm',t:'Bánh trôi nước',s:'Thân em vừa trắng lại vừa tròn',
   b:'Bảy nổi ba chìm với nước non.\nRắn nát mặc dầu tay kẻ nặn,\nMà em vẫn giữ tấm lòng son.'},
  {k:'Ca dao',e:'Ca dao Việt Nam',t:'Trong đầm gì đẹp bằng sen',s:'Lá xanh bông trắng lại chen nhị vàng',
   b:'Nhị vàng bông trắng lá xanh,\nGần bùn mà chẳng hôi tanh mùi bùn.\n\nCông cha như núi Thái Sơn,\nNghĩa mẹ như nước trong nguồn chảy ra.\nMột lòng thờ mẹ kính cha,\nCho tròn chữ hiếu mới là đạo con.'}];
 var vm='van',si=0,cap=false;try{vm=localStorage.getItem('vk-pvmode')||'van';si=+(localStorage.getItem('vk-spi')||0)||0;cap=localStorage.getItem('vk-spcap')==='1';}catch(e){}
 function escs(x){return String(x).replace(/[&<>]/g,esc);}
 function spec(fam,lab,sub){var d=SP[si]||SP[0],k=kern?'normal':'none',ff='font-family:\''+fam+'\';font-kerning:'+k+';';
  return '<div class="vk-pane vk-spec"><div class="vk-pl">'+lab+(sub?' <i>'+sub+'</i>':'')+'</div><div class="vk-sp" style="'+ff+'font-size:'+(px/48*20).toFixed(2)+'px">'
   +'<div class="sp-e">'+escs(d.e.toUpperCase())+'</div><div class="sp-t">'+escs(cap?d.t.toUpperCase():d.t)+'</div><div class="sp-s">'+escs(d.s)+'</div><div class="sp-b">'+escs(d.b)+'</div></div></div>';}
 var spsel=P.querySelector('.vk-spsel'),spcap=P.querySelector('.vk-spcap'),mseg=P.querySelector('.vk-mseg'),taw=P.querySelector('.vk-tawrap');
 spsel.innerHTML=SP.map(function(d,i){return '<button type="button" class="vk-chip" data-i="'+i+'" aria-pressed="false">'+d.k+'</button>';}).join('');
 function modeUI(){mseg.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.v===vm));});
  spsel.hidden=spcap.hidden=vm!=='van';taw.hidden=vm==='van';spsel.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed',String(+b.dataset.i===si));});spcap.setAttribute('aria-pressed',String(cap));
  var zl=P.querySelector('[data-z="l"]');if(zl)zl.hidden=vm==='van';}
 mseg.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;vm=b.dataset.v;try{localStorage.setItem('vk-pvmode',vm);}catch(_){}modeUI();ap();});
 spsel.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;si=+b.dataset.i;try{localStorage.setItem('vk-spi',si);}catch(_){}modeUI();ap();});
 spcap.addEventListener('click',function(){cap=!cap;try{localStorage.setItem('vk-spcap',cap?'1':'0');}catch(_){}modeUI();ap();});
 modeUI();
 function ap(){var v=V[cur];
  if(vm==='van')panes.innerHTML=spec(v.f,v.t,v.s)+(ref?spec('FV-ref','Font mẫu',ref.name):'');
  else if(ref&&mode==='overlay')overlay();
  else panes.innerHTML=rows(v.f,v.t,v.s)+(ref?rows('FV-ref','Font mẫu',ref.name):'');
  P.querySelector('.vk-desc').textContent=v.n||'';
  P.querySelector('[data-z="k"]').setAttribute('aria-pressed',String(kern));var zl2=P.querySelector('[data-z="l"]');if(zl2)zl2.setAttribute('aria-pressed',String(lines));}
 ta.addEventListener('input',ap);
 P.querySelector('.vk-ctl').addEventListener('click',function(e){var x=e.target.closest('button[data-z]');if(!x)return;if(x.dataset.z==='k')kern=!kern;else lines=!lines;ap();});
 /* font mẫu: nạp file (hoặc thả vào khung xem) → so ngay */
 var file=document.getElementById('vk-file'),on=P.querySelector('.vk-refon'),err=P.querySelector('.vk-err'),drop=P.querySelector('.vk-drop');
 function load(fl){if(!fl)return;err.hidden=true;var rd=new FileReader();
  rd.onload=function(){var ff;try{ff=new FontFace('FV-ref',rd.result);}catch(e){bad();return;}
   ff.load().then(function(f){if(ref&&ref.ff)try{document.fonts.delete(ref.ff);}catch(e){}document.fonts.add(f);ref={name:fl.name.replace(/\.(ttf|otf|woff2?)$/i,''),ff:f};
    on.hidden=false;on.querySelector('.vk-refname span').textContent=ref.name;P.querySelector('.vk-load span').textContent='Đổi font mẫu';ap();}).catch(bad);};
  rd.onerror=bad;rd.readAsArrayBuffer(fl);}
 function bad(){err.textContent='Không đọc được file này. Dùng .ttf, .otf, .woff hoặc .woff2.';err.hidden=false;}
 file.addEventListener('change',function(){load(file.files[0]);file.value='';});
 on.querySelector('.vk-x').addEventListener('click',function(){if(ref&&ref.ff)try{document.fonts.delete(ref.ff);}catch(e){}ref=null;on.hidden=true;P.querySelector('.vk-load span').textContent='Nạp font mẫu';ap();});
 on.querySelector('.vk-seg').addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;mode=b.dataset.m;on.querySelectorAll('.vk-seg button').forEach(function(x){x.setAttribute('aria-pressed',String(x===b));});ap();});
 ['dragenter','dragover'].forEach(function(t){view.addEventListener(t,function(e){e.preventDefault();view.classList.add('drag');drop.hidden=false;});});
 ['dragleave','drop'].forEach(function(t){view.addEventListener(t,function(e){e.preventDefault();view.classList.remove('drag');drop.hidden=true;if(t==='drop'&&e.dataTransfer&&e.dataTransfer.files.length)load(e.dataTransfer.files[0]);});});
 try{var s2=localStorage.getItem('fv-ver2-vv');V.forEach(function(v,i){if(v.t===s2)cur=i;});}catch(e){}
 if(document.fonts&&document.fonts.ready)document.fonts.ready.then(ap);
 pick(cur);
}
/* ---- phóng to / thu nhỏ trong khung xem (người dùng 27/10): lăn chuột trên khung = phóng tại chỗ con trỏ; điện thoại chụm 2 ngón.
   Không có nút − +. Cuộn trang: rê ra ngoài khung hoặc kéo thanh cuộn. get() / set(px) = cỡ chữ thật của khung. ---- */
var VZ={f:null,d0:0,tt:0,on:false};
function vkTouch(){if(VZ.on)return;VZ.on=true;
 function mid(t){return [(t[0].clientX+t[1].clientX)/2,(t[0].clientY+t[1].clientY)/2];}
 function dist(t){return Math.hypot(t[0].clientX-t[1].clientX,t[0].clientY-t[1].clientY);}
 function frOf(t){var el=t&&t.target;if(el&&el.nodeType!==1)el=el.parentElement;return el&&el.closest?el.closest('.vk-zoomable'):null;}
 document.addEventListener('touchstart',function(e){VZ.tt=e.touches.length;if(e.touches.length!==2)return;
  var fr=frOf(e.touches[0])||frOf(e.touches[1]);if(!fr||!fr.__vkzApi)return;e.preventDefault();
  if(VZ.f)VZ.f.commit();var z=fr.__vkzApi;z.commit();var m=mid(e.touches);if(z.begin(m[0],m[1])){VZ.f=z;VZ.d0=dist(e.touches)||1;}},{passive:false,capture:true});
 document.addEventListener('touchmove',function(e){if(!VZ.f||!VZ.d0||e.touches.length!==2)return;if(e.cancelable)e.preventDefault();var m=mid(e.touches);VZ.f.upd(dist(e.touches)/VZ.d0,m[0],m[1]);},{passive:false,capture:true});
 function end(e){VZ.tt=e.touches.length;if(VZ.f&&e.touches.length<2){var z=VZ.f;VZ.f=null;VZ.d0=0;z.commit();}}
 document.addEventListener('touchend',end,true);document.addEventListener('touchcancel',end,true);}
function vkZoom(fr,get,set,lo,hi,opt){if(!fr||fr.__vkz)return;fr.__vkz=1;lo=lo||8;hi=hi||600;opt=opt||{};fr.classList.add('vk-zoomable');
 /* như Google Maps: trong lúc chụm / lăn chỉ phóng ẢNH (CSS transform, GPU, theo tay từng khung hình), thả tay mới vẽ lại chữ thật
    ở cỡ mới rồi đặt lại cuộn để điểm dưới ngón tay / con trỏ đứng yên. Chụm 2 ngón còn kéo theo (pan) như bản đồ. */
 var G=null,raf=0,tmr=0;
 function ct(){return fr.firstElementChild;}
 /* opt.wrap — giữ nguyên chỗ xuống dòng khi phóng (người dùng 27/10: Xem trước phóng lên chữ bị xuống dòng): bề rộng nội dung = bề rộng gốc × tỉ lệ phóng,
    khoảng cách ngang trong khung dùng calc(… * var(--vkz)) nên cả bố cục phóng đều như ảnh, dòng ngắt đúng chỗ cũ */
 var W0=0,S0=0;
 function wrapFix(){if(!opt.wrap)return;var c=ct();if(!c)return;if(!W0){c.style.width='';W0=c.offsetWidth;S0=get();}if(!W0||!S0)return;var k=get()/S0;
  c.style.setProperty('--vkz',String(k));c.style.width=Math.abs(k-1)<1e-3?'':(W0*k)+'px';}
 if(opt.wrap)window.addEventListener('resize',function(){var c=ct();if(!c||!W0)return;var k=get()/S0;c.style.width='';W0=c.offsetWidth;S0=get()/k;wrapFix();});
 function lock(){if(fr.__vkh)return;var h=getComputedStyle(fr).height;if(!parseFloat(h))return;fr.__vkh=h;fr.style.height=h;fr.style.maxHeight=h;fr.style.overflow='auto';}  // khung giữ đúng cỡ mặc định, phóng to / thu nhỏ chỉ đổi chữ bên trong (người dùng 27/10)
 function begin(mx,my){if(!isFinite(mx)||!isFinite(my))return null;lock();var r=fr.getBoundingClientRect(),c=ct();if(!c)return null;var s0=get();if(!s0)return null;if(opt.wrap&&!W0){W0=c.offsetWidth;S0=s0;}
  var host=c;
  /* opt.wrap (Xem trước): khung con (.vk-panes) GIỮ NGUYÊN qua các lần vẽ lại, chỉ ruột được thay → Safari iOS giữ lại lớp ảnh cũ của phần tử
     đã transform, thả tay xong thấy 2 lớp chữ chồng nhau (lỗi 28/10). Phóng một lớp bọc TẠM chứa ruột; vẽ lại (set) thay ruột thì lớp bọc mất theo,
     không còn lớp ảnh cũ nào — giống Chỉnh dấu (svg bị thay cả phần tử nên vốn mượt). */
  if(opt.wrap){var w=document.createElement('div'),cs=getComputedStyle(c);w.className='vk-zw';w.style.display=cs.display;w.style.flexDirection=cs.flexDirection;w.style.gap=cs.gap;
   while(c.firstChild)w.appendChild(c.firstChild);c.appendChild(w);c=w;}
  G={s0:s0,k:1,c:c,host:host,ax:fr.scrollLeft+mx-r.left,ay:fr.scrollTop+my-r.top,mx:mx,my:my,sl:fr.scrollLeft,st:fr.scrollTop,r:r};
  c.style.transformOrigin='0 0';c.style.willChange='transform';return G;}
 function paint(){raf=0;if(!G)return;var x=G.mx-G.r.left,y=G.my-G.r.top,tx=x-G.ax*G.k+G.sl,ty=y-G.ay*G.k+G.st;
  G.c.style.transform='translate('+tx+'px,'+ty+'px) scale('+G.k+')';}
 function upd(k,mx,my){if(!G||!isFinite(k)||k<=0)return;if(!isFinite(mx))mx=G.mx;if(!isFinite(my))my=G.my;G.k=Math.max(lo/G.s0,Math.min(hi/G.s0,k));G.mx=mx;G.my=my;if(!raf)raf=requestAnimationFrame(paint);}
 /* NEO khi thả tay (người dùng 28/10: lăn chuột ở Xem trước / Đồng loạt bị giật): ảnh phóng bằng CSS và chữ vẽ lại ở cỡ mới KHÔNG trùng khít
    (lề, khoảng cách, cỡ làm tròn không nhân theo tỉ lệ) → mỗi lần vẽ lại chữ nhảy. Ghi lại đúng ký tự / phần tử nằm dưới con trỏ trên ảnh đang phóng,
    vẽ lại xong tìm lại nó theo cùng đường dẫn rồi cuộn cho nó về đúng dưới con trỏ → không nhảy, mọi khung (giống Chi tiết vốn khớp sẵn). */
 function anchor(g){var x=g.mx,y=g.my,c=g.c,node=null,off=-1,rect=null;
  try{var cr=null;if(document.caretRangeFromPoint)cr=document.caretRangeFromPoint(x,y);else if(document.caretPositionFromPoint){var cp=document.caretPositionFromPoint(x,y);if(cp){cr=document.createRange();cr.setStart(cp.offsetNode,cp.offset);}}
   if(cr&&cr.startContainer.nodeType===3&&c.contains(cr.startContainer)&&cr.startContainer.data.length){node=cr.startContainer;var o=Math.min(cr.startOffset,node.data.length-1),rr=document.createRange();rr.setStart(node,o);rr.setEnd(node,o+1);
    var q=rr.getBoundingClientRect();if(q.width>0&&q.height>0&&x>=q.left-q.width&&x<=q.right+q.width&&y>=q.top-q.height&&y<=q.bottom+q.height){rect=q;off=o;}else node=null;}}catch(_){node=null;}
  if(!rect){node=document.elementFromPoint(x,y);if(!node||node===c||!c.contains(node))return null;rect=node.getBoundingClientRect();off=-1;if(!(rect.width>0&&rect.height>0))return null;}
  var path=[],n=node;while(n&&n!==c){var p=n.parentNode;if(!p)return null;path.unshift(Array.prototype.indexOf.call(p.childNodes,n));n=p;}if(n!==c)return null;
  return {path:path,off:off,fx:(x-rect.left)/rect.width,fy:(y-rect.top)/rect.height,x:x,y:y};}
 function refind(a,root){var n=root;for(var i=0;i<a.path.length;i++){if(!n||!n.childNodes)return null;n=n.childNodes[a.path[i]];}if(!n)return null;
  if(a.off>=0){if(n.nodeType!==3||n.data.length<=a.off)return null;var rr=document.createRange();rr.setStart(n,a.off);rr.setEnd(n,a.off+1);return rr.getBoundingClientRect();}
  return n.nodeType===1?n.getBoundingClientRect():null;}
 function commit(){if(!G)return;var g=G;if(raf){cancelAnimationFrame(raf);raf=0;}paint();var a=null;try{a=anchor(g);}catch(_){a=null;}G=null;
  g.c.style.transform='';g.c.style.willChange='';set(g.s0*g.k);
  if(g.c!==g.host&&g.c.parentNode){while(g.c.firstChild)g.host.insertBefore(g.c.firstChild,g.c);g.c.remove();}   /* vẽ lại không thay ruột → gỡ lớp bọc tạm */
  wrapFix();var kk=get()/g.s0,x=g.mx-g.r.left,y=g.my-g.r.top;fr.scrollLeft=g.ax*kk-x;fr.scrollTop=g.ay*kk-y;
  if(a){var r=refind(a,ct());if(r&&r.width>0&&r.height>0){fr.scrollLeft+=r.left+a.fx*r.width-a.x;fr.scrollTop+=r.top+a.fy*r.height-a.y;}}}
 // máy tính: lăn chuột / chụm trên touchpad (ctrl + lăn) = phóng tại chỗ con trỏ; vẽ lại sau khi ngừng lăn 140 ms
 fr.addEventListener('wheel',function(e){e.preventDefault();var d=e.deltaMode===1?e.deltaY*16:e.deltaY;if(!G&&!begin(e.clientX,e.clientY))return;
  upd(G.k*Math.exp(-d*(e.ctrlKey?0.012:0.0022)),e.clientX,e.clientY);clearTimeout(tmr);tmr=setTimeout(commit,window.__vkzHold||140);},{passive:false});
 // điện thoại: touch events (không dùng pointer — trình duyệt hay huỷ pointer khi ngón thứ 2 chạm vào lúc đang cuộn).
 // Nghe ở CẢ TRANG (vkTouch), không chỉ trên khung: khung nhỏ (Bàn vẽ ~70 px, Chỉnh dấu trên điện thoại) thì ngón thứ 2 hay rơi ra ngoài khung
 // → khung không nhận touchstart 2 ngón → lúc phóng được lúc không (lỗi 27/10). Chỉ cần 1 ngón nằm trong khung.
 fr.__vkzApi={begin:begin,upd:upd,commit:commit,fr:fr};vkTouch();
 // máy tính như Google Maps: bấm-kéo chuột = kéo khung (pan), bấm đúp = phóng ×2 tại chỗ trỏ (Shift + bấm đúp = thu ×½), có hoạt cảnh
 var M=null;
 fr.addEventListener('pointerdown',function(e){if(e.pointerType!=='mouse'||e.button!==0)return;if(e.target.closest&&e.target.closest('input,textarea,select,button,a,[contenteditable]'))return;
  e.preventDefault();   /* Safari: không chặn thì bấm-kéo thành bôi đen chữ, trình duyệt tự cuộn theo vùng bôi đen → kéo khung “không ăn” (lỗi 27/10) */
  M={x:e.clientX,y:e.clientY,sl:fr.scrollLeft,st:fr.scrollTop,mv:false,id:e.pointerId};});
 fr.addEventListener('pointermove',function(e){if(!M||e.pointerId!==M.id)return;var dx=e.clientX-M.x,dy=e.clientY-M.y;
  if(!M.mv&&Math.hypot(dx,dy)<4)return;if(!M.mv){M.mv=true;fr.classList.add('vk-grab');try{fr.setPointerCapture(e.pointerId);}catch(_){}}
  fr.scrollLeft=M.sl-dx;fr.scrollTop=M.st-dy;e.preventDefault();});
 function mup(){if(!M)return;if(M.mv){fr.classList.remove('vk-grab');var k=function(ev){ev.stopPropagation();ev.preventDefault();fr.removeEventListener('click',k,true);};fr.addEventListener('click',k,true);setTimeout(function(){fr.removeEventListener('click',k,true);},300);}M=null;}
 fr.addEventListener('pointerup',mup);fr.addEventListener('pointercancel',mup);
 // Safari máy Mac: chụm 2 ngón trên touchpad phát gesturestart / gesturechange (không phải ctrl + lăn) → tự xử lý, không để trang phóng cả khung
 // iPhone / iPad CŨNG phát gesture* (không có clientX) song song với touch events → khi đang chạm màn hình thì bỏ qua, để touch events lo
 // (lỗi 27/10: chụm trên điện thoại làm khung xem biến mất — gesture* gọi begin(undefined) → toạ độ NaN)
 var GS=false;
 fr.addEventListener('gesturestart',function(e){e.preventDefault();if(VZ.tt>0)return;GS=true;if(G)commit();var r=fr.getBoundingClientRect();
  begin(isFinite(e.clientX)?e.clientX:r.left+r.width/2,isFinite(e.clientY)?e.clientY:r.top+r.height/2);},{passive:false});
 fr.addEventListener('gesturechange',function(e){e.preventDefault();if(!GS||VZ.tt>0||!G)return;upd(e.scale,isFinite(e.clientX)?e.clientX:G.mx,isFinite(e.clientY)?e.clientY:G.my);},{passive:false});
 fr.addEventListener('gestureend',function(e){e.preventDefault();if(!GS)return;GS=false;commit();},{passive:false});
 fr.addEventListener('dblclick',function(e){if(G)return;if(e.target.closest&&e.target.closest('[data-ch]'))return;   /* bấm đúp vào chữ = mở Bàn vẽ, không phóng */
 e.preventDefault();if(!begin(e.clientX,e.clientY))return;var k1=e.shiftKey?0.5:2,t0=performance.now();
  (function step(t){var u=Math.min(1,(t-t0)/220),ez=1-Math.pow(1-u,3);upd(Math.pow(k1,ez),e.clientX,e.clientY);if(u<1)requestAnimationFrame(step);else setTimeout(commit,30);})(t0);});}
function rng(id){var r=document.getElementById(id);return r?[function(){return +r.value;},function(v){r.value=Math.round(v);r.dispatchEvent(new Event('input'));}]:null;}
window.addEventListener('load',function(){say();
 if(P)vkZoom(P.querySelector('.vk-view'),function(){return px;},function(v){px=Math.round(v);ap();},8,600,{wrap:true});
 if(window.__vbZoom)vkZoom(window.__vbZoom.el,window.__vbZoom.get,window.__vbZoom.set,30,500,{wrap:true});   /* Đồng loạt (người dùng 27/10) */
 var h=rng('hu11-size');if(h)vkZoom(document.getElementById('hu11-view'),h[0],h[1],16,600);
 var o=rng('on-size');if(o)vkZoom(document.getElementById('on-view'),o[0],o[1],30,600);
 if(window.__edPvZoom)vkZoom(window.__edPvZoom.el,window.__edPvZoom.get,window.__edPvZoom.set,6,600);});
show(start);
})();"""

def slider_panel(hornui, key='chinh', note=True, batch=''):
    """khung kéo (slider_ui.html) thành một mục của thanh viên thuốc: bỏ tiêu đề chữ cái B, giữ data-sec="R" (khoá góp ý)."""
    import re
    if not hornui: return ''
    h = hornui.replace('<div class="sec" data-sec="R">', '<div class="sec vk-panel" data-sec="R" id="p-%s" role="tabpanel" aria-labelledby="tab-%s">' % (key, key), 1)
    h = re.sub(r'<div class="sec-h">.*?</details></div></div></div>\n?', '', h, count=1, flags=re.S)
    if note: h = h.replace('</div>\n</div>\n<style>', '</div>\n<div class="notewrap" data-note="R"></div>\n</div>\n<style>', 1)
    # chú giải chung cho 2 chế độ (người dùng 27/10): bấm từng mục để bật / tắt — thay các nút “tô đỏ…”, “line biên”
    h = re.sub(r'(<div class="hu11-vwrap">.*?</div>)(\s*<div class="hu11-txt"[ >])', lambda m: m.group(1) + LEGEND + m.group(2), h, count=1, flags=re.S)
    h = h.replace('<div class="notewrap" data-note="R"></div>', LEGEND_JS + '<div class="notewrap" data-note="R"></div>', 1) if '<div class="notewrap" data-note="R"></div>' in h else h + LEGEND_JS
    if batch:   # chế độ Đồng loạt đặt ngay đầu mục (người dùng 27/10)
        h = re.sub(r'(<div class="sec vk-panel" data-sec="R"[^>]*>)', lambda m: m.group(1) + '<div class="vk-cmode"><div class="vk-seg" role="group" aria-label="Cách chỉnh"><button type="button" data-v="batch" aria-pressed="true">Đồng loạt</button><button type="button" data-v="fine" aria-pressed="false">Chi tiết</button></div></div>' + batch, h, count=1)
    return h

def kn_panel(kit_dir=None, active=None):
    """Mục Kinh nghiệm: mỗi file kinh-nghiem-viet-hoa/*.md (trừ README) thành 1 thẻ ngắn — tên loại font, 1 câu đặc điểm,
    vài tag; bấm mở rộng xem toàn bộ (markdown → HTML). active = tên file đang dùng cho font này (thẻ có nhãn “đang dùng”, xếp đầu).
    Không lấy loi-font/ (lỗi file font, không phải kinh nghiệm theo loại font). Trả (html, số thẻ)."""
    import os, re, glob
    try:
        import markdown as _md
    except Exception:   # máy không có gói markdown: hiện chữ thô
        _md = None
    kit_dir = kit_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    files = sorted(f for f in glob.glob(os.path.join(kit_dir, "kinh-nghiem-viet-hoa", "*.md")) if not f.endswith("README.md"))
    if active: files.sort(key=lambda f: os.path.basename(f) != active)
    cards = []; GF = {}
    for f in files:
        t = open(f, encoding="utf-8").read()
        m = re.search(r"^#\s+(.+)$", t, re.M); title = re.sub(r"^Kinh nghiệm Việt hoá:\s*", "", m.group(1)).strip() if m else os.path.basename(f)
        m = re.search(r"\*\*Đặc điểm nổi bật:\*\*\s*(.+)", t); summ = m.group(1).strip() if m else ""
        summ = re.sub(r"[*`]", "", summ)
        m = re.search(r"\*\*Tag:\*\*\s*(.+)", t); tags = re.findall(r"`#([^`]+)`", m.group(1)) if m else []
        st = re.search(r"Trạng thái:\s*\*\*(.+?)\*\*", t); st = st.group(1) if st else ""
        body = re.sub(r"^#\s+.+\n", "", t, count=1, flags=re.M)
        body = re.sub(r"^>\s*build by.*\n", "", body, flags=re.M)
        body = re.sub(r"^\*build by @nhatmotion\*\s*$", "", body, flags=re.M)
        body = re.sub(r"\*\*Đặc điểm nổi bật:\*\*.+\n", "", body, count=1)
        body = re.sub(r"\*\*Tag:\*\*.+\n", "", body, count=1)
        # thẻ thu gọn (người dùng 27/10: mọi thẻ cùng một cỡ, chỉ vài ý chính): dòng “**Thẻ:** tên ngắn | ý 1 · ý 2 · ý 3”
        m = re.search(r"\*\*Thẻ:\*\*\s*(.+)", t); short, pts = title, []
        if m:
            sp = m.group(1).split("|", 1); short = sp[0].strip() or title
            pts = [x.strip() for x in (sp[1] if len(sp) > 1 else "").split(" · ") if x.strip()][:3]
        body = re.sub(r"\*\*Thẻ:\*\*.+\n", "", body, count=1)
        if summ: body = "**Đặc điểm:** " + summ + "\n\n" + body
        on = active and os.path.basename(f) == active
        chips = "".join('<span class="kn-tag">#%s</span>' % html.escape(x) for x in tags[:3]) + (('<span class="kn-tag more">+%d</span>' % (len(tags) - 3)) if len(tags) > 3 else "")
        st = st[:1].lower() + st[1:].lower() if st.isupper() else st          # “ĐÃ CHỐT VER 10” → “đã chốt VER 10”
        st = re.sub(r"\bver\b", "VER", st)
        meta = ('<span class="kn-badge">đang dùng</span>' if on else "") + (('<span class="kn-st">%s</span>' % html.escape(st)) if st else "")
        mid = ('<ul class="kn-pts">%s</ul>' % "".join('<li>%s</li>' % html.escape(x) for x in pts)) if pts else '<p class="kn-s">%s</p>' % html.escape(summ)
        # chữ “a” nền: **Chữ nền:** kiểu (didone / serif-dam / sans-tron / viet-tay, xem CHU_NEN) | độ đậm [| italic]
        m = re.search(r"\*\*Chữ nền:\*\*\s*(.+)", t); gf = [x.strip() for x in m.group(1).split("|")] if m else []
        body = re.sub(r"\*\*Chữ nền:\*\*.+\n", "", body, count=1)
        h = _md.markdown(body, extensions=["tables", "fenced_code"]) if _md else "<pre>%s</pre>" % html.escape(body)
        h = h.replace("<table>", '<div class="kn-tb"><table>').replace("</table>", "</table></div>")
        bg = ""
        if gf:
            fam, wt, it = gf[0], (gf[1] if len(gf) > 1 else "400"), (len(gf) > 2 and gf[2].lower().startswith("ital"))
            fam = CHU_NEN.get(fam, fam)   # file kinh nghiệm ghi KIỂU chữ nền (không ghi tên font) → họ Google để vẽ
            GF.setdefault(fam, set()).add((it, wt))
            bg = '<span class="kn-bg" aria-hidden="true"><span class="kn-a" style="font-family:&quot;%s&quot;,serif;font-weight:%s;font-style:%s">a</span></span>' % (html.escape(fam), html.escape(wt), "italic" if it else "normal")
        cards.append(('<article class="kn-card%s" tabindex="0" role="button" aria-haspopup="dialog" aria-label="Xem kinh nghiệm: %s">%s'
                      '<div class="kn-h"><b title="%s">%s</b></div><div class="kn-meta">%s</div>%s<div class="kn-tags">%s</div>'
                      '<template class="kn-src"><div class="kn-mh"><h2>%s</h2><div class="kn-meta">%s</div><div class="kn-tags all">%s</div></div>'
                      '<div class="kn-body">%s<p class="kn-file">%s</p></div></template></article>') % (
            " on" if on else "", html.escape(title), bg, html.escape(title), html.escape(short), meta, mid, chips,
            html.escape(title), meta, "".join('<span class="kn-tag">#%s</span>' % html.escape(x) for x in tags), h,
            html.escape("kinh-nghiem-viet-hoa/" + os.path.basename(f))))
    # một link Google Fonts cho mọi chữ nền, chỉ tải đúng chữ “a” (text=a)
    fams = []
    for fam, vs in sorted(GF.items()):
        its = sorted(vs)
        if any(i for i, _ in its): fams.append("family=%s:ital,wght@%s" % (fam.replace(" ", "+"), ";".join("%d,%s" % (int(i), w) for i, w in its)))
        else: fams.append("family=%s:wght@%s" % (fam.replace(" ", "+"), ";".join(sorted(w for _, w in its))))
    link = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?%s&text=a&display=swap">' % "&".join(fams)) if fams else ""
    # thanh chỉnh chữ nền chỉ là CÔNG CỤ chỉnh giao diện (người dùng 27/10: đã đẹp, bỏ khỏi trang) — cần chỉnh lại thì đặt KN_TUNE = True
    tools = '' if not KN_TUNE else ('<div class="kn-bar"><button type="button" class="kn-tune-b" aria-expanded="false" aria-controls="kn-tune">Chữ nền</button>'
             '<div class="kn-tune" id="kn-tune" hidden>'
             + "".join('<label><span>%s</span><input type="range" data-v="%s" min="%s" max="%s" step="1"><output></output></label>' % x for x in (
                 ("Cách mép phải", "r", 8, 140), ("Dọc", "y", -80, 80), ("Cỡ", "s", 80, 420), ("Đậm nhạt", "o", 2, 40), ("Mờ từ dưới", "f", 0, 100)))
             + '<button type="button" class="kn-reset">Về mặc định</button></div></div>')
    ov = ('<div class="kn-ov" id="kn-ov" hidden><div class="kn-ovbg" data-close></div><div class="kn-dlg" role="dialog" aria-modal="true" aria-label="Kinh nghiệm">'
          '<button type="button" class="kn-x" data-close aria-label="Đóng">%s</button><div class="kn-dc"></div></div></div>') % (
          '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>')
    if not cards:   # bản public: chưa có file kinh nghiệm nào
        return '<div class="vk-nofont kn-empty" role="status"><b>Kinh nghiệm đang trống</b><span>Hãy bắt đầu Việt hoá để có kinh nghiệm.</span></div>', 0
    return link + tools + '<div class="kn-grid" id="kn-grid">%s</div>' % "".join(cards) + ov + KN_JS, len(cards)

KN_CSS = r"""<style>
/* Kinh nghiệm (người dùng 27/10): thẻ cùng một cỡ, không mũi tên; bấm thẻ → lớp phủ xem đủ có nút ×.
   Sau mỗi thẻ: chữ “a” to mờ của một họ chữ Google cùng kiểu (dòng **Chữ nền:**), chỉnh vị trí / cỡ / đậm nhạt / mờ từ dưới bằng nút “Chữ nền”. */
.kn-bar{display:flex;justify-content:flex-end;margin:0 0 10px;position:relative}
.kn-tune-b{font:500 12.5px/1 var(--vk-ui);padding:8px 14px;border-radius:var(--vk-pill);border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);cursor:pointer}
.kn-tune-b[aria-expanded="true"]{background:var(--pg-txt);border-color:var(--pg-txt);color:var(--pg-bg)}
.kn-tune{position:absolute;right:0;top:calc(100% + 6px);z-index:30;width:min(300px,calc(100vw - 32px));padding:12px 14px;border-radius:14px;background:var(--pg-card);border:1px solid var(--pg-line-2);box-shadow:0 12px 32px rgba(0,0,0,.18);display:flex;flex-direction:column;gap:8px}
.kn-tune label{display:grid;grid-template-columns:78px minmax(0,1fr) 44px;align-items:center;gap:8px;font-size:12.5px;color:var(--pg-mut)}
.kn-tune input{width:100%;accent-color:var(--pg-txt)}.kn-tune output{font:11px var(--vk-mono);text-align:right;color:var(--pg-txt)}
.kn-reset{align-self:flex-end;font:12px var(--vk-ui);padding:5px 10px;border-radius:var(--vk-pill);border:1px solid var(--pg-line-2);background:transparent;color:var(--pg-mut);cursor:pointer}
.kn-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,300px),1fr));gap:12px;--kn-ar:18px;--kn-ay:-6%;--kn-as:230px;--kn-ao:.09;--kn-fade:60%}
.kn-card{position:relative;overflow:hidden;height:178px;padding:14px 16px 12px;display:flex;flex-direction:column;gap:6px;border:1px solid var(--pg-line-2);border-radius:var(--vk-r);background:var(--pg-card);min-width:0;cursor:pointer;transition:border-color .15s,transform .15s}
.kn-card:hover{border-color:var(--pg-mut-2)}.kn-card.on{border-color:var(--pg-txt)}
.kn-card:focus-visible{outline:2px solid var(--pg-accent);outline-offset:2px}
.kn-card>*:not(.kn-bg){position:relative;z-index:1}
.kn-bg{position:absolute;inset:0;overflow:hidden;pointer-events:none;z-index:0;-webkit-mask-image:linear-gradient(to top,transparent 0,#000 var(--kn-fade));mask-image:linear-gradient(to top,transparent 0,#000 var(--kn-fade))}
.kn-a{position:absolute;right:var(--kn-ar);top:var(--kn-ay);font-size:var(--kn-as);line-height:1;opacity:var(--kn-ao);color:var(--pg-txt);white-space:nowrap;user-select:none}
.kn-h b{display:block;font-size:15px;line-height:1.35;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kn-meta{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.kn-meta:empty{display:none}
.kn-badge{font-size:11px;font-weight:600;padding:2px 8px;border-radius:var(--vk-pill);background:var(--pg-txt);color:var(--pg-bg)}
.kn-st{font-size:11px;padding:2px 8px;border-radius:var(--vk-pill);background:var(--pg-sunk);color:var(--pg-mut)}
.kn-pts{list-style:none;margin:2px 0 0;padding:0;font-size:13px;line-height:1.5;color:var(--pg-mut)}
.kn-pts li{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.kn-pts li::before{content:"–";margin-right:7px;color:var(--pg-mut-2)}
.kn-s{margin:0;font-size:13px;line-height:1.5;color:var(--pg-mut);display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.kn-tags{display:flex;flex-wrap:wrap;gap:4px}.kn-card>.kn-tags{flex-wrap:nowrap;overflow:hidden;margin-top:auto}
.kn-tag{font:400 11px/1 var(--vk-mono);padding:4px 7px;border-radius:var(--vk-pill);background:var(--pg-sunk);color:var(--pg-mut);white-space:nowrap}
/* lớp phủ xem đủ */
html{scrollbar-gutter:stable}html.kn-lock{overflow:hidden}
.kn-ov{position:fixed;inset:0;z-index:1000;display:flex}   /* mở TOÀN MÀN HÌNH, phủ cả đầu trang (người dùng 27/10) */
.kn-ov[hidden]{display:none!important}
.kn-ovbg{position:absolute;inset:0;background:rgba(0,0,0,.42);opacity:0;transition:opacity .22s ease-out}
.kn-dlg{position:relative;flex:1;width:100%;height:100vh;height:100dvh;display:flex;flex-direction:column;background:var(--pg-bg);color:var(--pg-txt);overflow:hidden;opacity:0;transform:translate3d(0,16px,0) scale(.985);transform-origin:50% 0;transition:opacity .22s cubic-bezier(.2,.7,.2,1),transform .26s cubic-bezier(.2,.7,.2,1);will-change:opacity,transform;contain:layout paint}
.kn-ov.out .kn-dlg{transition-duration:.14s}
.kn-ov.in .kn-ovbg,.kn-ov.in .kn-dlg{opacity:1;transform:none}
.kn-x{position:absolute;top:max(12px,env(safe-area-inset-top,0px));right:max(12px,env(safe-area-inset-right,0px));z-index:2;width:36px;height:36px;display:grid;place-items:center;border-radius:var(--vk-pill);border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);cursor:pointer}
.kn-x:focus-visible{outline:2px solid var(--pg-accent);outline-offset:2px}
.kn-dc{flex:1;overflow:auto;overscroll-behavior:contain;padding:clamp(20px,4vw,48px) max(16px,env(safe-area-inset-right,0px)) 40px max(16px,env(safe-area-inset-left,0px))}
.kn-dc>*{max-width:900px;margin-left:auto;margin-right:auto}
.kn-mh{display:flex;flex-direction:column;gap:8px;padding-right:44px;margin-bottom:6px}.kn-mh h2{margin:0;font-size:22px;line-height:1.25;text-wrap:balance}
.kn-body{font-size:13.5px;line-height:1.6;min-width:0}
.kn-body h2{font-size:16px;margin:20px 0 6px}.kn-body h3{font-size:14px;margin:14px 0 4px}
.kn-body p,.kn-body ul,.kn-body ol{margin:6px 0}.kn-body li{margin:3px 0}
.kn-body hr{border:0;margin:14px 0}
.kn-body code{font:12px var(--vk-mono);background:var(--pg-sunk);padding:1px 4px;border-radius:4px;overflow-wrap:anywhere}
.kn-body pre{background:var(--pg-sunk);padding:10px 12px;border-radius:8px;overflow:auto}.kn-body pre code{background:none;padding:0}
.kn-body blockquote{margin:8px 0;padding:6px 12px;border-left:2px solid var(--pg-line-2);color:var(--pg-mut)}
.kn-tb{overflow-x:auto;margin:8px 0}.kn-tb table{border-collapse:collapse;font-size:12.5px;min-width:520px}
.kn-tb th,.kn-tb td{border:1px solid var(--pg-line);padding:5px 8px;text-align:left;vertical-align:top}.kn-tb th{background:var(--pg-sunk)}
.kn-file{font:11px var(--vk-mono);color:var(--pg-mut-2);margin-top:12px}

@media (prefers-reduced-motion:reduce){.kn-dlg,.kn-ovbg,.kn-card{transition:none}}
</style>"""

KN_JS = r"""<script>(function(){
var G=document.getElementById('kn-grid'),OV=document.getElementById('kn-ov');if(!G||!OV)return;
document.body.appendChild(OV);   /* đưa lớp phủ ra thẳng body: không bị khung cha (transform / z-index) giới hạn */
var DC=OV.querySelector('.kn-dc'),X=OV.querySelector('.kn-x'),last=null;
function open(c){var t=c.querySelector('template.kn-src');if(!t)return;DC.innerHTML='';DC.appendChild(t.content.cloneNode(true));last=c;
 OV.classList.remove('in','out');OV.hidden=false;document.documentElement.classList.add('kn-lock');DC.scrollTop=0;void OV.offsetWidth;   /* ép trình duyệt vẽ trạng thái đầu rồi mới chuyển → không nhảy cóc */
 requestAnimationFrame(function(){OV.classList.add('in');});try{X.focus({preventScroll:true});}catch(_){}}
function close(){if(OV.hidden)return;OV.classList.add('out');OV.classList.remove('in');
 setTimeout(function(){OV.hidden=true;DC.innerHTML='';OV.classList.remove('out');document.documentElement.classList.remove('kn-lock');},160);if(last)try{last.focus({preventScroll:true});}catch(_){}}
window.__knOpen=function(i){var c=G.querySelectorAll('.kn-card')[i||0];if(c)open(c);};window.__knClose=close;
G.addEventListener('click',function(e){var c=e.target.closest('.kn-card');if(c)open(c);});
G.addEventListener('keydown',function(e){if((e.key==='Enter'||e.key===' ')&&e.target.classList&&e.target.classList.contains('kn-card')){e.preventDefault();open(e.target);}});
OV.addEventListener('click',function(e){if(e.target.closest('[data-close]'))close();});
document.addEventListener('keydown',function(e){if(OV.hidden)return;if(e.key==='Escape'){close();return;}
 if(e.key==='Tab'){var f=[].slice.call(OV.querySelectorAll('button,a[href],[tabindex]:not([tabindex="-1"])'));if(!f.length)return;var a=f[0],z=f[f.length-1];
  if(e.shiftKey&&document.activeElement===a){e.preventDefault();z.focus();}else if(!e.shiftKey&&document.activeElement===z){e.preventDefault();a.focus();}}});
/* chữ “a” nền: thanh chỉnh — lưu trên máy (localStorage) + db fontvn/vk-ui (để lần sau đặt làm mặc định của kit) */
var D={r:18,y:-6,s:230,o:9,f:60},U={r:'px',y:'%',s:'px',o:'%',f:'%'},K='vk-kn-bg',V={},db=null,tm=0;
for(var k in D)V[k]=D[k];try{var L=JSON.parse(localStorage.getItem(K)||'null');if(L&&L.x!==undefined&&L.r===undefined)L=null;if(L)for(var k2 in D)if(typeof L[k2]==='number')V[k2]=L[k2];}catch(_){}
var T=document.getElementById('kn-tune'),B=G.parentNode.querySelector('.kn-tune-b');
if(!T)for(var k3 in D)V[k3]=D[k3];   /* không có thanh chỉnh (KN_TUNE=False) → luôn dùng mặc định của kit, bỏ giá trị cũ lưu trên máy */
function ap(){G.style.setProperty('--kn-ar',Math.max(8,V.r)+'px');G.style.setProperty('--kn-ay',V.y+'%');G.style.setProperty('--kn-as',V.s+'px');G.style.setProperty('--kn-ao',V.o/100);G.style.setProperty('--kn-fade',V.f+'%');
 if(T)[].forEach.call(T.querySelectorAll('input[data-v]'),function(r){r.value=V[r.dataset.v];r.nextElementSibling.textContent=V[r.dataset.v]+U[r.dataset.v];});}
function save(){clearTimeout(tm);tm=setTimeout(function(){try{localStorage.setItem(K,JSON.stringify(V));}catch(_){}
 if(db)db.doc('fontvn/vk-ui').set({kn:V,at:new Date().toISOString()}).catch(function(){});},500);}
if(T){T.addEventListener('input',function(e){var r=e.target;if(!r.dataset||!r.dataset.v)return;V[r.dataset.v]=+r.value;ap();save();});
 T.querySelector('.kn-reset').addEventListener('click',function(){for(var k in D)V[k]=D[k];ap();save();});}
if(B)B.addEventListener('click',function(){var o=T.hidden;T.hidden=!o;B.setAttribute('aria-expanded',o?'true':'false');});
document.addEventListener('click',function(e){if(T&&!T.hidden&&!e.target.closest('.kn-bar')){T.hidden=true;B.setAttribute('aria-expanded','false');}});
ap();
/* “Cách mép phải” tính tới MỰC của chữ a, không tới hộp chữ: mỗi font có khoảng trắng phải khác nhau → đo bằng canvas, bù bằng margin-right (em) */
function ink(){var cv=document.createElement('canvas').getContext('2d');[].forEach.call(G.querySelectorAll('.kn-a'),function(el){var cs=getComputedStyle(el);
 cv.font=cs.fontStyle+' '+cs.fontWeight+' 200px '+cs.fontFamily;var m=cv.measureText('a');if(!m||!m.width)return;var rsb=m.width-(m.actualBoundingBoxRight||m.width);el.style.marginRight=(-rsb/200).toFixed(3)+'em';});}
ink();if(document.fonts&&document.fonts.ready)document.fonts.ready.then(ink);if(document.fonts&&document.fonts.addEventListener)document.fonts.addEventListener('loadingdone',ink);
if(window.claude&&window.claude.use)Promise.resolve().then(function(){return window.claude.use('db');}).then(function(d){db=d;if(!d||!T)return;
 return d.doc('fontvn/vk-ui').get().then(function(s){if(s&&s.exists){var v=(s.data()||{}).kn;if(v){for(var k in D)if(typeof v[k]==='number')V[k]=v[k];ap();}}});}).catch(function(){});
})();</script>"""

# ---------------- Chỉnh dấu · chế độ ĐỒNG LOẠT (người dùng 27/10, tham khảo cách “hiệu chỉnh đồng loạt”) ----------------
# Dữ liệu: export_batch.py FONT rN/batch.json (thân + từng dấu của mỗi chữ Việt). Thông số người dùng kéo lưu db <DOC>/batch/p,
# Claude đọc rồi áp vào font bằng batch_apply.py. Mỗi loại dấu: ngang · dọc · cỡ · chữ hoa thêm dọc · (dấu thanh) khi chồng ngang / dọc;
# “Mọi dấu”: dọc + cỡ cho mọi dấu trên. Dấu thanh chồng đi theo dấu mũ / trăng bên dưới nó.
BATCH_KINDS = [("acute", "Dấu sắc"), ("grave", "Dấu huyền"), ("hook", "Dấu hỏi"), ("tilde", "Dấu ngã"), ("dot", "Dấu nặng"),
               ("circ", "Dấu mũ"), ("breve", "Dấu trăng"), ("all", "Mọi dấu")]
BATCH_SENT = {"acute": "Cá rán giòn, lá thắm, đất mới, ướt át. TIẾNG HÁT ẤM ÁP", "grave": "Chiều tà, người về bờ đầm. NGƯỜI VỀ ĐẦU LÀNG",
              "hook": "Thủy triều phẳng lặng, cửa bể cổ kính. CỬA BỂ CỔ KÍNH", "tilde": "Lũ trẻ vẫn nghĩ mãi, gỗ mỡ đã cũ. NGÃ BA ĐÃ CŨ",
              "dot": "Mặt trời lặn, gạo nặng, đọc chậm. MỘT TRĂM NGỌN NẾN", "circ": "Cây cầu ấy, nắng lên đầy sân. ÂM VANG ĐẦU LÊN",
              "breve": "Trăng rằm, mặt nước lặng, năm mới. TRĂM NĂM SẮC SẢO", "all": "Trăm năm trong cõi người ta, chữ tài chữ mệnh khéo là ghét nhau."}

def batch_panel(path):
    """HTML + JS cho chế độ Đồng loạt; path = rN/batch.json (không có thì trả '')."""
    import os
    if not path or not os.path.exists(path): return ''
    data = open(path).read().replace('</', '<\\/')
    meta = json.dumps(dict(kinds=BATCH_KINDS, sent=BATCH_SENT), ensure_ascii=False)
    return ('<div class="vb" id="vk-batch"><script type="application/json" id="vb-data">%s</script><script type="application/json" id="vb-meta">%s</script>'
            '<div class="vb-grid"><div class="vb-main"><div class="vb-tabs" role="tablist" aria-label="Loại dấu"></div>'
            '<p class="vb-info" hidden></p><div class="vb-view"><span class="hu-status hu-chip vb-st" id="vb-status">đang kết nối…</span><div class="vb-zf" aria-label="Khung xem đồng loạt — chụm 2 ngón hoặc lăn chuột để phóng"><div class="vb-rows"></div></div></div>'
            '</div>'
            '<aside class="vb-ctl" aria-label="Thanh kéo đồng loạt"></aside></div></div>') % (data, meta) + BATCH_JS


LEGEND = ('<div class="vk-lgd" role="group" aria-label="Chú giải — bấm để bật / tắt">'
          '<button type="button" data-l="hi" aria-pressed="true" title="Bật / tắt tô đỏ dấu đang chỉnh"><i class="sw hi"></i>dấu đang chỉnh</button>'
          '<button type="button" data-l="gh" aria-pressed="true" data-m="batch" title="Bật / tắt viền vị trí cũ"><i class="sw gh"></i>vị trí cũ</button>'
          '<button type="button" data-l="lim" aria-pressed="true" data-m="batch" title="Bật / tắt vạch giới hạn dòng (Word cắt mực vượt vạch)"><i class="sw lim"></i>giới hạn dòng</button>'
          '<button type="button" data-l="adv" aria-pressed="false" data-m="fine" title="Bật / tắt 2 vạch độ rộng của từng chữ"><i class="sw adv"></i>line biên</button></div>')
LEGEND_CSS = r"""<style>
/* chú giải chung (Đồng loạt + Chi tiết): một hàng, bấm để bật / tắt */
.vk-lgd{display:flex;flex-wrap:wrap;align-items:center;gap:4px 6px;margin:8px 0 0}
.vk-lgd button{display:inline-flex;align-items:center;gap:7px;font:500 12.5px/1 var(--vk-ui);padding:6px 10px;border:0;border-radius:var(--vk-pill);background:transparent;color:var(--pg-txt);cursor:pointer}
.vk-lgd button:hover{background:var(--pg-sunk)}.vk-lgd button[aria-pressed="false"]{color:var(--pg-mut-2)}.vk-lgd button[aria-pressed="false"] .sw{opacity:.35}
.vk-lgd button:focus-visible{outline:2px solid var(--pg-accent);outline-offset:1px}
.vk-lgd .sw{display:inline-block;flex:none;width:12px;height:12px;border-radius:3px;box-sizing:border-box}
.vk-lgd .sw.hi{background:#e5243b}.vk-lgd .sw.gh{border:1.5px dashed var(--pg-mut)}
.vk-lgd .sw.lim{height:0;width:14px;border-radius:0;border-top:2px dashed #e5243b}.vk-lgd .sw.adv{width:2px;height:13px;border-radius:1px;background:#e8890c}
.vb.lg-hi-off .vb-g path.hi{fill:var(--pg-txt)}.vb.lg-gh-off .vb-g path.gh{display:none}.vb.lg-lim-off .vb-g line.lim{display:none}
</style>"""
LEGEND_JS = r"""<script>(function(){
var L=document.querySelector('#p-chinh .vk-lgd');if(!L)return;var S={hi:true,gh:true,lim:true,adv:false},mode='fine';
try{var o=JSON.parse(localStorage.getItem('vk-lgd')||'null');if(o)for(var k in S)if(typeof o[k]==='boolean')S[k]=o[k];}catch(_){}
function setCb(id,v){var c=document.getElementById(id);if(c&&c.checked!==v){c.checked=v;c.dispatchEvent(new Event('change',{bubbles:true}));c.dispatchEvent(new Event('input',{bubbles:true}));}}
function ap(){L.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed',String(S[b.dataset.l]));b.hidden=!!b.dataset.m&&b.dataset.m!==mode;});
 setCb('hu11-hl',S.hi);setCb('hu11-adv',S.adv);var B=document.getElementById('vk-batch');
 if(B){B.classList.toggle('lg-hi-off',!S.hi);B.classList.toggle('lg-gh-off',!S.gh);B.classList.toggle('lg-lim-off',!S.lim);}}
L.addEventListener('click',function(e){var b=e.target.closest('button[data-l]');if(!b)return;S[b.dataset.l]=!S[b.dataset.l];try{localStorage.setItem('vk-lgd',JSON.stringify(S));}catch(_){}ap();});
/* đặt chú giải ngay dưới khung xem của chế độ đang mở */
window.__vkLgd=function(m){mode=m==='batch'?'batch':'fine';var host=mode==='batch'?document.querySelector('#vk-batch .vb-view'):document.querySelector('#p-chinh .hu11-vwrap');
 if(host&&host.nextElementSibling!==L)host.parentNode.insertBefore(L,host.nextSibling);ap();};
function init(){if(!document.getElementById('vk-batch'))window.__vkLgd('fine');else ap();}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();</script>"""

BATCH_CSS = r"""<style>
/* Chỉnh dấu · Đồng loạt */
.vk-cmode{display:flex;margin:0 0 14px}
.vk-cmode .vk-seg{display:inline-flex;gap:2px;padding:2px;border:1px solid var(--pg-line-2);border-radius:var(--vk-pill);background:var(--pg-card)}
.vk-cmode .vk-seg button{white-space:nowrap;font:500 13px/1 var(--vk-ui);padding:8px 14px;border:0;border-radius:var(--vk-pill);background:transparent;color:var(--pg-mut);cursor:pointer}
.vk-cmode .vk-seg button[aria-pressed="true"]{background:var(--pg-txt);color:var(--pg-bg)}
.vb-grid{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:18px;align-items:start}
@media (max-width:860px){.vb-grid{grid-template-columns:minmax(0,1fr)}}
.vb-tabs{display:flex;flex-wrap:wrap;gap:4px 14px;margin-bottom:8px}
.vb-tabs button{font:500 14px/1.2 var(--vk-ui);padding:6px 0 8px;border:0;border-bottom:2px solid transparent;background:none;color:var(--pg-mut);cursor:pointer;white-space:nowrap}
.vb-tabs button[aria-selected="true"]{color:var(--pg-txt);border-bottom-color:var(--pg-txt);font-weight:600}
.vb-tabs button .dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:#e5243b;margin-left:5px;vertical-align:middle}
.vb-info{margin:0 0 10px;font-size:12.5px;color:var(--pg-mut)}
.vb-view{position:relative;border:1px solid var(--pg-line-2);border-radius:var(--vk-r);background:var(--pg-card);overflow:hidden}
.vb-zf{padding:34px calc(16px*var(--vkz,1)) 16px;overflow:auto;border-radius:inherit}.vb-zf>.vb-rows{padding:0}
/* chip lưu: MỘT vị trí, MỘT cỡ ở cả 3 tab Xem trước / Chỉnh dấu (Đồng loạt + Chi tiết) / Bàn vẽ (người dùng 28/10: chip “tự lưu” mỗi tab một chỗ)
   → góc phải trên của khung xem, cách viền ngoài 10 px; Bàn vẽ thì dưới thước 20 px. Đổi ở đây, đừng đặt lại top/right ở chỗ khác. */
#status.vk-save,#hu11-status,#vb-status,.ed-stage>.ed-save{position:absolute!important;top:10px!important;right:10px!important;left:auto!important;bottom:auto!important;margin:0!important;z-index:3;display:inline-flex!important;align-items:center;gap:6px;padding:3px 10px 3px 8px!important;border-radius:99px!important;font:500 12px/1.4 var(--vk-ui)!important;color:var(--pg-mut)!important;opacity:1!important;white-space:nowrap;pointer-events:none}
#vb-status{top:9px!important;right:9px!important}   /* cha .vb-view có viền 1 px */
.ed-stage>.ed-save{top:30px!important}.ed-stage.no-rulers>.ed-save{top:10px!important}
.vb-row{display:flex;flex-wrap:wrap;align-items:flex-end;gap:0 calc(6px*var(--vkz,1));margin-bottom:6px}
.vb-row svg{display:block;overflow:visible}
.vb-sent{display:flex;flex-wrap:wrap;gap:calc(.3em*var(--vkz,1)) calc(.35em*var(--vkz,1));padding-top:calc(14px + .25em);margin-top:8px;border-top:1px solid var(--pg-line)}
.vb-g{overflow:visible}   /* dấu chồng chữ hoa cao hơn ascender (tới ~1180) → không cắt đầu dấu ở câu mẫu (lỗi 28/10); khoảng dòng câu mẫu chừa chỗ cho phần vượt */
.vb-sent .w{display:inline-flex;align-items:flex-end}
.vb-g path{fill:var(--pg-txt)}.vb-g path.hi{fill:#e5243b}.vb-g path.gh{fill:none;stroke:var(--pg-mut-2);stroke-width:1.2;stroke-dasharray:3 3;vector-effect:non-scaling-stroke}
.vb-g line{stroke:var(--pg-line-2);stroke-width:1;vector-effect:non-scaling-stroke}.vb-g line.lim{stroke:#e5243b;stroke-opacity:.45;stroke-dasharray:4 3}
.vb-g.over line.lim{stroke-opacity:1}
.vb-key{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:12px;color:var(--pg-mut);margin:8px 0 0}
.vb-key i{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:-1px;margin-right:4px}
.vb-key i.hi{background:#e5243b}.vb-key i.gh{border:1.5px dashed var(--pg-mut-2)}.vb-key i.ln{height:0;border-top:2px dashed #e5243b;border-radius:0;vertical-align:3px}
.vb-ctl{display:flex;flex-direction:column;gap:6px;padding:14px 16px;border:1px solid var(--pg-line-2);border-radius:var(--vk-r);background:var(--pg-card)}
.vb-ctl h4{margin:0 0 6px;font-size:14px}.vb-ctl h4 small{font-weight:400;font-size:11.5px;color:var(--pg-mut)}.vb-ctl p{margin:0;font-size:12px;color:var(--pg-mut);line-height:1.5}
.vb-sl{display:grid;grid-template-columns:78px minmax(0,1fr) 52px 26px;gap:6px;align-items:center;font-size:12.5px}
.vb-sl label{color:var(--pg-txt);white-space:nowrap}
.vb-rev{display:grid;place-items:center;width:26px;height:26px;padding:0;border:0;border-radius:6px;background:none;color:var(--pg-mut);cursor:pointer}.vb-rev:hover{background:var(--pg-sunk);color:var(--pg-txt)}
.vb-sl input[type=range]{width:100%;accent-color:var(--pg-txt)}
.vb-sl input[type=number]{-moz-appearance:textfield;appearance:textfield}.vb-sl input[type=number]::-webkit-inner-spin-button,.vb-sl input[type=number]::-webkit-outer-spin-button{-webkit-appearance:none;margin:0}
.vb-sl input[type=number]{width:52px;text-align:right;font:12px var(--vk-mono);padding:4px 6px;border:1px solid var(--pg-line-2);border-radius:6px;background:var(--pg-bg);color:var(--pg-txt)}
.vb-sub{font:600 11px/1 var(--vk-ui);letter-spacing:.08em;text-transform:uppercase;color:var(--pg-mut);margin-top:4px}
.vb-btns{display:flex;gap:8px;flex-wrap:wrap}
.vb-btns button{font:500 12.5px var(--vk-ui);padding:7px 12px;border-radius:var(--vk-pill);border:1px solid var(--pg-line-2);background:var(--pg-card);color:var(--pg-txt);cursor:pointer}
</style>"""

BATCH_JS = r"""<script>(function(){
var D=JSON.parse(document.getElementById('vb-data').textContent),M=JSON.parse(document.getElementById('vb-meta').textContent);
var ROOT=document.getElementById('vk-batch');if(!ROOT)return;
var TABS=ROOT.querySelector('.vb-tabs'),ROWS=ROOT.querySelector('.vb-rows'),CTL=ROOT.querySelector('.vb-ctl'),INFO=ROOT.querySelector('.vb-info'),ST=document.getElementById('vb-status');
var TONES={acute:1,grave:1,hook:1,tilde:1},CAPS={circ:1,breve:1},NAME={};M.kinds.forEach(function(k){NAME[k[0]]=k[1];});
var SL=[['dx','ngang ← →',-150,150,0,'Dời ngang mọi dấu loại này'],['dy','dọc ↓ ↑',-150,150,0,'Dời dọc mọi dấu loại này'],['sc','cỡ %',60,150,100,'Co / giãn quanh tâm đáy dấu'],['uy','hoa ↓ ↑',-150,150,0,'Chữ hoa: dời dọc thêm']];
var SLT=[['sx','chồng ← →',-150,150,0,'Khi nằm trên dấu mũ / trăng: dời ngang thêm'],['sy','chồng ↓ ↑',-150,150,0,'Khi nằm trên dấu mũ / trăng: dời dọc thêm']];
var SLA=[['dy','dọc ↓ ↑',-150,150,0,'Dời dọc mọi dấu trên'],['sc','cỡ %',60,150,100,'Co / giãn mọi dấu trên']];
function blank(){var P={};D.kinds.concat(['all']).forEach(function(k){P[k]={dx:0,dy:0,sc:100,uy:0,sx:0,sy:0};});return P;}
var P=blank(),K='acute',db=null,saveT=0,loaded=false,ZK=1;   /* ZK = tỉ lệ phóng khung Đồng loạt */
function changed(k){var p=P[k];return p&&(p.dx||p.dy||p.sc!==100||p.uy||p.sx||p.sy);}
function shift(m,uc,capS){var p=P[m.k]||{},a=P.all,above=m.k!=='dot';
 var dx=(p.dx||0)+(m.st?(p.sx||0)+capS.dx:0),dy=(p.dy||0)+(uc?(p.uy||0):0)+(m.st?(p.sy||0)+capS.dy:0)+(above?a.dy:0),sc=(p.sc||100)/100*(above?a.sc/100:1);
 return {dx:dx,dy:dy,sc:sc};}
function glyphSVG(c,px){var uc=c.uc,cap={dx:0,dy:0};
 c.m.forEach(function(m){if(CAPS[m.k]){var s=shift(m,uc,{dx:0,dy:0});cap={dx:s.dx,dy:s.dy};}});
 var asc=D.asc,desc=D.desc,H=asc-desc,w=Math.max(c.w,60),top=-Infinity,body='<path d="'+c.body+'"/>',mk='';
 c.m.forEach(function(m){var s=shift(m,uc,cap),b=m.bb,ax=(b[0]+b[2])/2,ay=m.k==='dot'?b[3]:b[1],hi=(K==='all'?m.k!=='dot':m.k===K);
  var tf='translate('+(ax+s.dx)+' '+(ay+s.dy)+') scale('+s.sc+') translate('+(-ax)+' '+(-ay)+')',moved=s.dx||s.dy||s.sc!==1;
  if(moved&&hi)mk+='<path class="gh" d="'+m.d+'"/>';
  mk+='<path'+(hi?' class="hi"':'')+' d="'+m.d+'" transform="'+tf+'"/>';
  if(m.k!=='dot')top=Math.max(top,ay+s.dy+(b[3]-ay)*s.sc);});
 var over=top>asc,h=px*H/D.upm,wpx=w/D.upm*px;   /* px = cỡ chữ (1 em) */
 return '<svg class="vb-g'+(over?' over':'')+'" width="'+wpx.toFixed(1)+'" height="'+h.toFixed(1)+'" viewBox="0 '+(-asc)+' '+w+' '+H+'"><g transform="scale(1,-1)">'
  +'<line x1="0" x2="'+w+'" y1="'+(uc?D.cap:D.xh)+'" y2="'+(uc?D.cap:D.xh)+'"/><line class="lim" x1="0" x2="'+w+'" y1="'+asc+'" y2="'+asc+'"/>'+body+mk+'</g></svg>';}
var BY={};D.chars.forEach(function(c){BY[c.ch]=c;});
function plainSVG(ch,px){var g=D.plain[ch];if(!g)return '';var H=D.asc-D.desc;return '<svg class="vb-g" width="'+(g.w/D.upm*px).toFixed(1)+'" height="'+(px*H/D.upm).toFixed(1)+'" viewBox="0 '+(-D.asc)+' '+g.w+' '+H+'"><g transform="scale(1,-1)"><path d="'+g.d+'"/></g></svg>';}
function sent(t,px){return t.split(' ').map(function(w){return '<span class="w">'+Array.from(w).map(function(ch){return BY[ch]?glyphSVG(BY[ch],px):plainSVG(ch,px);}).join('')+'</span>';}).join('');}
var raf=0;function render(){raf=0;var list=D.chars.filter(function(c){return K==='all'?c.m.length:c.m.some(function(m){return m.k===K;});});
 var lc=list.filter(function(c){return !c.uc;}),uc=list.filter(function(c){return c.uc;}),big=(window.innerWidth<600?56:84)*ZK;
 INFO.textContent=list.length+' chữ có '+NAME[K]+(K==='all'?'':'')+' · kéo thanh bên cạnh, xem trước cập nhật ngay';
 ROWS.innerHTML='<div class="vb-row">'+lc.map(function(c){return glyphSVG(c,big);}).join('')+'</div><div class="vb-row">'+uc.map(function(c){return glyphSVG(c,big);}).join('')+'</div>'
  +'<div class="vb-sent">'+sent(M.sent[K]||M.sent.all,(window.innerWidth<600?32:44)*ZK)+'</div>';}
function rr(){if(!raf)raf=requestAnimationFrame(render);}
window.__vbZoom={el:ROOT.querySelector('.vb-zf'),get:function(){return ZK*100;},set:function(v){ZK=v/100;if(raf){cancelAnimationFrame(raf);raf=0;}render();}};
function tabs(){TABS.innerHTML=M.kinds.filter(function(k){return k[0]==='all'||D.chars.some(function(c){return c.m.some(function(m){return m.k===k[0];});});}).map(function(k){
 return '<button type="button" role="tab" data-k="'+k[0]+'" aria-selected="'+(k[0]===K)+'">'+k[1]+(changed(k[0])?'<span class="dot" title="đã chỉnh"></span>':'')+'</button>';}).join('');}
var REV='<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v6h6"/><path d="M4.6 15a8 8 0 1 0 1.9-8.3L4 10"/></svg>';
function sl(def,p){var id='vb-'+K+'-'+def[0];return '<div class="vb-sl" title="'+(def[5]||def[1])+'"><label for="'+id+'">'+def[1]+'</label><input type="range" id="'+id+'" data-f="'+def[0]+'" min="'+def[2]+'" max="'+def[3]+'" step="1" value="'+p[def[0]]+'"><input type="number" data-f="'+def[0]+'" min="'+def[2]+'" max="'+def[3]+'" step="1" value="'+p[def[0]]+'" aria-label="'+def[1]+'"><button type="button" class="vb-rev" data-r="'+def[0]+'" title="Về mặc định ('+def[4]+')" aria-label="Về mặc định: '+def[1]+'">'+REV+'</button></div>';}
function ctl(){var p=P[K],h='<h4>'+NAME[K].charAt(0).toUpperCase()+NAME[K].slice(1)+'</h4>';
 if(K==='all')h+=SLA.map(function(d){return sl(d,p);}).join('');
 else{h+=SL.map(function(d){return sl(d,p);}).join('');if(TONES[K])h+=SLT.map(function(d){return sl(d,p);}).join('');}
 CTL.innerHTML=h;}
CTL.addEventListener('input',function(e){var f=e.target.dataset.f;if(!f)return;var v=+e.target.value;if(!isFinite(v))return;P[K][f]=v;
 CTL.querySelectorAll('[data-f="'+f+'"]').forEach(function(x){if(x!==e.target)x.value=v;});rr();tabs();save();});
CTL.addEventListener('click',function(e){var r=e.target.closest&&e.target.closest('.vb-rev');if(!r)return;var f=r.dataset.r;P[K][f]=f==='sc'?100:0;ctl();rr();tabs();save();});
TABS.addEventListener('click',function(e){var b=e.target.closest('button[data-k]');if(!b)return;K=b.dataset.k;try{localStorage.setItem('vb-k',K);}catch(_){}tabs();ctl();render();});
function summary(){var L=[];Object.keys(P).forEach(function(k){if(!changed(k))return;var p=P[k],x=[];['dx','dy','sc','uy','sx','sy'].forEach(function(f){var d=f==='sc'?100:0;if(p[f]!==d)x.push(f+' '+p[f]);});L.push((NAME[k]||k)+': '+x.join(', '));});
 return L.length?'Chỉnh đồng loạt — '+L.join(' · '):'';}
window.__bSummary=summary;
function base(){return (window.__FV_EDDOC||'').replace(/\/glyphs$/,'');}
window.__vkChip=window.__vkChip||function(t,k,load){   /* MỘT trạng thái lưu cho cả Chỉnh dấu: chip Đồng loạt và Chi tiết luôn cùng chữ, cùng chấm màu (người dùng 28/10) */
 var cur=window.__vkChipT||'';if(load&&t==='tự lưu'&&/^đã lưu|^đang lưu/.test(cur))return;
 if(load&&t==='chưa lưu được'&&cur&&cur!=='đang kết nối…')return;
 window.__vkChipT=t;['hu11-status','vb-status'].forEach(function(id){var e=document.getElementById(id);if(!e)return;e.textContent=t;if(k)e.dataset.s=k;else delete e.dataset.s;});};
function sst(t,k,load){window.__vkChip(t,k,load);}
function hm(){return new Date().toLocaleTimeString('vi-VN',{hour:'2-digit',minute:'2-digit'});}
function save(){sst('đang lưu…','busy');clearTimeout(saveT);saveT=setTimeout(function(){
 if(!db||!base()){sst('chưa lưu được');return;}
 db.doc(base()+'/batch/p').set({p:P,at:new Date().toISOString()}).then(function(){sst('đã lưu '+hm(),'ok');if(window.__save)window.__save();}).catch(function(){sst('lưu lỗi, thử lại');});},600);}
try{var k0=localStorage.getItem('vb-k');if(k0&&P[k0])K=k0;}catch(_){}
tabs();ctl();render();window.addEventListener('resize',rr);
if(window.claude&&window.claude.use)Promise.resolve().then(function(){return window.claude.use('db');}).then(function(d){db=d;if(!d||!base()){sst('chưa lưu được',null,true);return;}
 return d.doc(base()+'/batch/p').get().then(function(s){var v=s&&s.exists?(s.data()||{}).p:null;
  if(v){Object.keys(v).forEach(function(k){if(P[k])Object.assign(P[k],v[k]);});sst('tự lưu','ok',true);tabs();ctl();render();}else sst('tự lưu','ok',true);});}).catch(function(){sst('chưa lưu được',null,true);});
else sst('chưa lưu được',null,true);
/* chuyển chế độ trong tab Chỉnh dấu: Đồng loạt | Chi tiết */
var PN=document.getElementById('p-chinh');if(PN){var seg=PN.querySelector('.vk-cmode');
 function md(v){[].forEach.call(PN.children,function(ch){if(ch===seg||ch.tagName==='SCRIPT'||ch.tagName==='STYLE')return;if(ch===ROOT)ch.hidden=v!=='batch';else if(ch.classList.contains('notewrap'))ch.hidden=false;else ch.hidden=v==='batch';});
  seg.querySelectorAll('button').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.v===v));});try{localStorage.setItem('vk-cmode',v);}catch(_){}if(v==='batch')rr();if(window.__vkLgd)window.__vkLgd(v);}
 function init(){var v0='batch';try{v0=localStorage.getItem('vk-cmode')||'batch';}catch(_){}md(v0);}
 if(seg){seg.addEventListener('click',function(e){var b=e.target.closest('button');if(b)md(b.dataset.v);});if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();}}   /* chạy sau khi cả mục đã dựng xong (script nằm giữa mục) */
})();</script>"""
