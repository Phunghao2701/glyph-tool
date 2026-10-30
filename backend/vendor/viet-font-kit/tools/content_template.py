# Mẫu nội dung trang duyệt — giao diện Việt Font Kit ver 1.0.0 (tối giản, thanh viên thuốc).
# Chép thành content_rN.py (để cạnh slider_ui.html, vd trong thư mục tools), sửa khối CẤU HÌNH, rồi chạy:
#   python3 -I tools/build_page.py tools/tpl rN r1/review.html tools/content_rN.py
# rN/ cần: A.woff2 (VER mới nhất, family CSS "Font VN"), <ten>.woff2 cho VER khác (family "FV-<ten>"), editor.json (export_editor.py),
#          panels.json (có thể là {}), hornui.json (export_preview.py + tone_split.py, hoặc nghieng/export_hornui_italic.py … 0 cho font đứng).
# Bố cục: đầu trang (Nhật Motion's Space nhỏ → Việt Font Kit cỡ lớn + ver → Đang Việt hoá + tên phông bằng chính phông đó) →
#   thanh viên thuốc dính: Xem trước · Chỉnh dấu · Bàn vẽ (số chữ dựng) · Nguồn (số nguồn) | VER n (không có VER 0). Không có mục Tổng hợp
#   (tóm tắt vẫn tự lưu vào db). Trạng thái lưu = chip nhỏ trong khung xem của từng mục.
#   Xem trước: khung xem → ô nhập → khung chỉnh (tên font xuất, cỡ, kern, font mẫu). Chỉnh dấu: khung xem trái; phải: chữ mẫu → nút → thanh kéo.
#   Bàn vẽ: khung vẽ + danh sách → chữ mẫu → xem trong chữ.
# build by @nhatmotion
import os
# ---- CẤU HÌNH ----
ROUND = 1
SLUG = "<slug-font>"                                   # khoá db: fontvn/<slug>-r<ROUND>
FONT_NAME = "VFK - <Tên font gốc>"                     # tên font xuất mặc định (stamp.py); người dùng đổi ở ô “Tên font xuất” (db <DOC>/out/name)
OUT_STYLE, OUT_EXT = "Regular", ".ttf"                 # kiểu + đuôi file xuất (hiện tên file dưới ô tên)
KN_ACTIVE = None                                       # file kinh-nghiem-viet-hoa/*.md đang dùng cho font này (thẻ “đang dùng”), vd "viet-tay-net-deu.md"
VER_LABEL = "vòng 1"                                   # vd "VER 3 · đã chốt" khi người dùng chốt
SUMHEAD = FONT_NAME + " · " + VER_LABEL
TITLE = VK.KIT_NAME + " " + VK.KIT_VER                 # “Việt Font Kit ver x.y.z” (số lấy từ file VERSION của kit)
HORN_DOC = "fontvn/%s-r%d/horn/v1" % (SLUG, ROUND)     # nơi lưu số khung kéo; muốn giữ số vòng trước thì trỏ về vòng đó
VER_BASE = "VER 1C"                                     # VER có dữ liệu khung kéo / bàn vẽ ở rN/ (= A.woff2); VER khác: rN/vers/<VER n>/
# use_packs(['packs/camnang-ryan.json'])               # CHỈ bật khi người dùng tự yêu cầu cẩm nang chưa kiểm chứng

# Tên VER theo vòng: vòng N có 1 bản → VER N; nhiều bản → VER NA, NB… (woff2 rN/vNa.woff2 → family FV-vNa).
# Vòng 1 LUÔN có 3 VER: VER 1A dấu thanh BÊN PHẢI dấu mũ (như font hay làm) · VER 1B dấu thanh CHỒNG trên đỉnh dấu mũ ·
#   VER 1C = VER 1A + dấu hỏi vẽ lại từ NỬA TRÊN dấu ? (quick_vn hook_src "half") → thấy sớm điểm mạnh của font, chốt hướng Việt hoá. Vòng sau: VER sửa trước đó · VER hiện tại. KHÔNG hiện VER 0 (người dùng 27/10).
VERS = [
    # ('VER <n-1>', '1.00<n-1>', 'FV-v<n-1>', '<một câu: khác gì>'),
    ('VER 1A', '1.001 · dấu bên phải', 'FV-v1a', 'Dấu thanh đứng bên phải dấu mũ.'),
    ('VER 1B', '1.001 · dấu chồng', 'FV-v1b', 'Dấu thanh chồng trên đỉnh dấu mũ.'),
    ('VER 1C', '1.001 · hỏi nửa trên ?', 'Font VN', 'Như VER 1A, dấu hỏi vẽ lại từ nửa trên dấu ?.')]
TEXT = ('ẦẤẨẪẬ ẰẮẲẴẶ ỀẾỂỄỆ ỒỐỔỖỘ\nầấẩẫậ ằắẳẵặ ềếểễệ ồốổỗộ\nỜỚỞỠỢ ỪỨỬỮỰ ỲÝỶỸỴ ÌÍỈĨỊ\nờớởỡợ ừứửữự ỳýỷỹỵ ìíỉĩị\n'
        'NGƯỜI ƯỚC MƠ · TƯƠNG LAI · ĐẦU TƯ\nngười ươn ưa, cửa, phố cổ, “cổ,” ấm áp, đã')
NEWS = ['<ý mới 1>', '<ý mới 2>']                     # 2–3 ý ngắn, ý dựa nguồn thì gắn cite('id')
MEAS = ''                                              # số đo VER mới (độ rộng tăng, kern, đỉnh dấu…) — để trống thì không hiện
FB_ROWS = []                                           # vòng ≥ 2: góp ý vòng trước → VER mới làm gì: [(anh ghi, mình làm)]
# ---- HẾT CẤU HÌNH ----

_ON = os.path.join(R, 'oldnew.html')                    # khối “So vị trí cũ” — KHÔNG chèn nữa (người dùng 27/10 bỏ); giữ biến cho mẫu cũ
OLDNEW = open(_ON).read() if os.path.exists(_ON) else ''
_HJ = os.path.join(R, 'hornui.json')
HORNUI = open(os.path.join(os.path.dirname(os.path.abspath(CONTENT_PATH)), 'slider_ui.html')).read().replace('__HORN_DATA__', open(_HJ).read()).replace('__HORN_DOC__', HORN_DOC) if os.path.exists(_HJ) else ''
NOFONT = globals().get('NOFONT', not os.path.exists(os.path.join(R, 'A.woff2')))   # chưa có font: hiện khung “Chưa có font cần Việt hoá”
N_GLYPH = 0 if NOFONT else len(json.load(open(os.path.join(R, 'editor.json'))).get('recipes', {}))
N_SRC = sources_html().count('<li id="src-')
KN_HTML, N_KN = VK.kn_panel(active=KN_ACTIVE)          # mục Kinh nghiệm: thẻ ngắn, bấm mở rộng (không gồm loi-font/)

KEYS = ('<p class="keys"><kbd>V</kbd> chọn · <kbd>P</kbd> bút · <kbd>B</kbd> cọ · <kbd>C</kbd> thành phần · <kbd>H</kbd> kéo khung · '
        '<kbd>S</kbd> snap · <kbd>F</kbd> vừa khung · <kbd>Ctrl</kbd>+<kbd>C</kbd> / <kbd>V</kbd> chép / dán dấu · Shift + bấm chữ = thêm vào bản vẽ</p>')

TABS = [('xem', 'Xem trước', None, 'V'), ('chinh', 'Chỉnh dấu', None, 'R'), ('ve', 'Bàn vẽ', N_GLYPH, 'C'), ('kn', 'Kinh nghiệm', N_KN or None, 'K'), ('huongdan', 'Hướng dẫn', None, 'H'), ('nguon', 'Nguồn', N_SRC, 'N'), ('donate', 'Ủng hộ', None, 'D')]
if not HORNUI or NOFONT: TABS = [t for t in TABS if t[0] != 'chinh']
if NOFONT: TABS = [t for t in TABS if t[0] != 've']; VERS = []; FONT_NAME, VER_LABEL = 'Chưa có font', ''

PAGE = (VK.CSS + VK.KN_CSS + VK.BATCH_CSS + VK.LEGEND_CSS + '<div class="vk">' + VK.top(FONT_NAME, VER_LABEL) + VK.tabs(TABS, VERS) + '<main class="vk-in vk-body">'
  + VK.panel('xem', 'V', VK.nofont() if NOFONT else (VK.news(NEWS) if NEWS else '') + VK.preview(VERS, TEXT, 48, MEAS, outname=FONT_NAME, style=OUT_STYLE, ext=OUT_EXT)
                    + '<div class="notewrap" data-note="V"></div>' if not NOFONT else VK.nofont())
  + ('' if NOFONT else VK.slider_panel(HORNUI, 'chinh', batch=VK.batch_panel(os.path.join(R, 'batch.json'))))   # Chỉnh dấu: Đồng loạt (rN/batch.json — export_batch.py) + Chi tiết
  + ('' if NOFONT else VK.panel('ve', 'C', ED_HTML + '<details class="vk-more" style="margin-top:12px"><summary>Phím tắt</summary>' + KEYS + '</details><div class="notewrap" data-note="C"></div>'))
  + VK.panel('kn', 'K', KN_HTML)
  + VK.panel('huongdan', 'H', VK.guide_panel())   # Hướng dẫn: cài skill + Free / Pro (người dùng 27/10)
  + VK.panel('nguon', 'N', '<div class="srcopen">' + sources_html() + '</div>')
  + VK.panel('donate', 'D', VK.donate_panel())
  + '</main></div>'
  + '<div hidden><pre class="sum" id="sum"></pre><textarea class="fallback" id="fallback" readonly aria-label="Tóm tắt"></textarea></div>'   # tóm tắt vẫn lưu vào db (summary), không hiện mục riêng
  + '<script>window.__SECN={V:"Xem trước",R:"Chỉnh dấu",C:"Bàn vẽ",K:"Kinh nghiệm",N:"Nguồn",H:"Hướng dẫn",D:"Ủng hộ"};</script>')
TAIL_JS = VK.JS
EXTRA_HEAD = ('<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,500&family=Be+Vietnam+Pro:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">\n')
