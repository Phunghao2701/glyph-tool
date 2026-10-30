# Quy tắc trang duyệt (artifact) — Việt hoá font

> build by @nhatmotion

Trang duyệt là **một** artifact HTML, giữ **cùng URL** qua mọi vòng: luôn ghi đè cùng file `r1/review.html` rồi publish lại.

**Người dùng gửi font yêu cầu Việt hoá thì render trang này ngay trong lượt đầu** để họ duyệt từng VER: VER 1… = bản dựng, mỗi VER một tab gõ thử. **Không hiện VER 0 (font gốc)** (người dùng 27/10) — so với gốc bằng Nạp font mẫu.

**Vòng 1 luôn có 3 VER: VER 1A dấu thanh bên phải dấu mũ · VER 1B dấu thanh trên đỉnh · VER 1C dấu hỏi vẽ từ nửa trên dấu ?** **Từ vòng 2: VER người dùng thích / VER sửa trước đó · VER hiện tại** (mở sẵn VER hiện tại), không có VER 0.

**Khi một VER đổi vị trí dấu / nét so với VER trước: luôn vẽ thêm một lớp nét đứt thể hiện vị trí cũ**, có nút bật / tắt (mặc định bật, nhớ theo máy). Áp dụng cho bàn vẽ (viền đứt VER trước chồng lên chữ đang xem), khung kéo và ảnh đo (`tools/nghieng/stackmeasure.py`, `axisproof.py`): người dùng phải thấy ngay dấu đã dời bao nhiêu, không phải so 2 tab bằng mắt.

## 1 · Hợp đồng artifact (bắt buộc)

**Publish:**
- Lần đầu publish với `icon:"type"` và `capabilities:{db:{},user:{},assets:{}}`.
- Các vòng sau giữ nguyên `file_path`, bỏ `icon` / `capabilities` để giữ nguyên.
- Trước khi publish trang lần đầu, nạp skill `artifact-design`. Trước khi viết code `window.claude.*`, nạp skill `artifact-capabilities`.

**Page:**
- `<title>`: **“Việt Font Kit ver x.y.z”** (số đọc từ `VERSION` của kit — `VK.KIT_VER`).
- HEAD có `<meta charset="utf-8">` (đã có sẵn trong `build_page.py`).

**Màu và giao diện sáng / tối:**
- Màu khai báo bằng token trên `:root` (`--pg-bg`, `--pg-card`, `--pg-txt`, `--pg-mut`, `--pg-line`, `--pg-accent`, `--pg-ok`…).
- Dark mode đặt trong `@media (prefers-color-scheme: dark)` với `:root:not([data-theme="light"])`, và lặp lại cho `:root[data-theme="dark"]`.
- `body` có nền rõ ràng.
- **Không hard-code `#fff` cho nút.** Nền trắng + chữ kế thừa màu trắng ở dark mode sẽ ra ô xám không chữ.

**Thư viện ngoài:**
- Script chỉ lấy từ cdnjs / jsdelivr / unpkg, có số phiên bản cụ thể.
- Font chỉ lấy từ Google Fonts. Font thêm cho tiêu đề truyền qua `EXTRA_HEAD` trong content.

**Lưu trữ:**
- Dữ liệu cần giữ (lựa chọn, góp ý, số kéo, nét vẽ) lưu vào db của artifact (`window.claude.use('db')`).
- `localStorage` chỉ dùng cho tiện ích từng máy (giao diện sáng / tối, nhóm thanh kéo đang mở), luôn bọc `try/catch`.
- Đọc lại bằng `ArtifactData`.

**Khổ màn hình:** không tràn ngang ở 390 px. Kiểm cả nền sáng lẫn nền tối.

## 2 · Bố cục — giao diện Việt Font Kit (tối giản, người dùng 26/10)

Dựng bằng `tools/content_template.py` + `tools/vfk_ui.py` (build_page.py nạp sẵn `VK`). Ít chữ: tên mục đã nằm trên viên thuốc, không viết lại tiêu đề / đoạn giải thích trong mục.

| Phần | Nội dung |
|---|---|
| **Đầu trang (giữ cấu trúc cũ)** | Dòng nhỏ trên cùng: tác giả **“Nhật Motion's Space”** (Playfair Display nghiêng) → tên lớn **“Việt Font Kit”** (Be Vietnam Pro 900) + nhãn `ver x.y.z` → đường kẻ → “Đang Việt hoá” + **tên phông viết bằng chính phông đó** (đổi theo ô Tên font xuất) + nhãn vòng. Góc phải: Tự động / Sáng / Tối dạng icon. |
| **Thanh viên thuốc (dính khi cuộn)** | Mục lớn KHÔNG đánh A, B, C mà là viên thuốc: **Xem trước · Chỉnh dấu · Bàn vẽ (số chữ dựng mới) · Kinh nghiệm (số thẻ) · Nguồn (số nguồn)**. **Không có mục Tổng hợp** (tóm tắt vẫn tự lưu vào db `summary`, `#sum` / `#fallback` ẩn). Viên đang mở tô đặc. Mỗi lần hiện **một mục**; nhớ mục đang mở theo máy; `#xem`, `#chinh`, `#ve`, `#nguon` mở thẳng mục. Bên phải thanh: **viên thuốc VER chung cho cả trang** (VER không có nét dựng viền đứt). Chọn VER ở đây thì khung kéo, bàn vẽ, So vị trí cũ đổi theo (sự kiện `fv-ver`, `VER_BASE`, `rN/vers/<VER n>/`). Ở Chỉnh dấu / Bàn vẽ mà chọn VER 0 → 1 dòng nhỏ “VER 0 là font gốc · mục này giữ VER n”. |
| **Xem trước** | Dòng “Mới” (2–3 ý, `VK.news`) → cột trái: khung xem cố định (không tự xuống dòng, cuộn ngang trong khung, font nạp sẵn nên đổi VER không giật) → ô Chữ mẫu ngay dưới. Cột phải (dính): **Tên font xuất** → cỡ − / + (không ghi nhãn “Cỡ”) · kern · line biên → **Font mẫu** → mô tả 1 câu của VER → “Số đo” thu gọn. Điện thoại: 1 cột theo đúng thứ tự đó. |
| **Tên font xuất** | Ô nhập, mặc định `FONT_NAME` (“VFK - <tên gốc>”). Gõ là tên ở đầu trang đổi theo, dưới ô hiện tên PostScript + tên file (bỏ dấu, như `stamp.py`). Lưu db `fontvn/<slug>-rN/out/name` `{name, ps}` và dòng “Tên font xuất: …” trong tóm tắt. Khi xuất: `FAMILY="<name>"`. |
| **Font mẫu (so ngay)** | Nút “Nạp font mẫu” (.ttf .otf .woff .woff2) hoặc **thả file vào khung xem** → nạp bằng `FontFace` ngay trên máy người xem (không tải lên đâu), hiện tên + nút ×; 2 cách so: **Trên dưới** và **Chồng lớp** (SVG, cùng đường chân chữ; font mẫu đỏ mờ) để soi vị trí dấu. File lỗi → 1 dòng đỏ. |
| **Chỉnh dấu** | Luôn có nhóm thanh **Dấu hỏi** (cỡ, đầu, đuôi, độ thuôn, pha): đường dựng nào cũng phải xuất thông số dấu hỏi (`hook.params.json` → `horn5.json` `hook_params` → `hornui.json` `hook`); `quick_vn.py` tự xuất kiểu `taper`. `slider_ui.html` qua `VK.slider_panel()`: **cột trái: khung xem (chữ vẽ bằng nét thật) → ô Chữ mẫu ngay dưới** (người dùng 26/10); **cột phải: nút (cỡ chữ, đường dóng dấu hỏi, line biên, kern sau râu, hoàn tác / làm lại, tô đỏ dấu đang chỉnh) → nhóm thanh kéo** (mục 4). **Bấm một chữ trong khung xem → nhảy sang Bàn vẽ, bản vẽ chỉ còn đúng chữ đó** (`window.__VK_GO("ve", ch)` → `window.__edOpen(ch)`). |
| **Bàn vẽ** | `ED_HTML` + `editor.js`: **khung vẽ + danh sách ký tự → ô Chữ mẫu → “Xem trong chữ”** (mục 5). Mở lần đầu tự “vừa khung”. Phím tắt thu gọn. |
| **Kinh nghiệm** | Viên thuốc sau Bàn vẽ, số đếm = số thẻ. `VK.kn_panel(active=KN_ACTIVE)`: mỗi file `kinh-nghiem-viet-hoa/*.md` (trừ README) thành **thẻ ngắn** — tên loại font, 1 câu “Đặc điểm nổi bật” (cắt 2 dòng), 5 tag đầu + “+n”, nhãn trạng thái nếu có; **bấm mở rộng** xem toàn bộ (markdown → HTML, bảng cuộn ngang), thẻ mở chiếm cả hàng. Thẻ loại font đang làm có nhãn “đang dùng”, xếp đầu. **Không** hiện `loi-font/` (lỗi file font, không phải kinh nghiệm theo loại font). |
| **Kính mờ (glass)** | **Chỉ chip thông tin trong khung xem** (trạng thái lưu `.vk-save`, `.hu-chip`, `.ed-save`): nền trong suốt + `backdrop-filter: blur(16px) saturate(170%)`, token `--vk-glass*` sáng / tối. Mọi nút, thanh mục, viên thuốc VER, sáng / tối: nền đặc, không blur (người dùng 27/10, thay quy tắc “mọi viên thuốc kính mờ” trước đó). |
| **Phóng to / thu nhỏ** | **Không có nút** (người dùng 27/10: bỏ viên thuốc − +). Mọi khung xem (Xem trước, Chỉnh dấu, Xem trong chữ, So vị trí cũ): máy tính **lăn chuột trên khung = phóng tại chỗ con trỏ** (giữ điểm dưới con trỏ đứng yên, cuộn trang thì rê ra ngoài khung); điện thoại **chụm 2 ngón**, 1 ngón vẫn cuộn khung; chuột **bấm-kéo = kéo khung** (con trỏ bàn tay), **bấm đúp = phóng ×2** có hoạt cảnh (Shift + bấm đúp = thu ×½). Cảm giác phải như Google Maps: **trong cử chỉ chỉ đổi `transform: translate() scale()`** trên phần tử con đầu của khung (rAF), **nhả tay / lăn dừng 140 ms mới `set(cỡ × k)`** dựng lại chữ rồi chỉnh scroll cho điểm neo đứng yên. Chụm dùng **touch events nghe ở cả trang** (`vkTouch`, `passive:false`, capture — chỉ cần 1 ngón trong khung), không dùng pointer events (trình duyệt huỷ pointer khi ngón thứ 2 chạm). Kéo chuột xong nuốt cú click kế tiếp để không nhảy sang Bàn vẽ. **Bấm-kéo chặn bôi đen** (`preventDefault` ở pointerdown + `user-select:none`): Safari bôi đen chữ rồi tự cuộn theo vùng bôi đen, kéo khung “không ăn” (lỗi 27/10). **Safari Mac chụm touchpad** = `gesturestart/gesturechange/gestureend`, tự xử lý — **nhưng bỏ qua khi đang chạm màn hình** (iPhone phát cả gesture* lẫn touch, để touch events lo; lỗi 27/10). **Khung không đổi cỡ khi phóng** (người dùng 27/10): `vkZoom` khoá `height` = cỡ mặc định ở cử chỉ đầu, `overflow: auto`. Hàm `vkZoom(khung, get, set)` trong `VK.JS`; khung có `touch-action: pan-x pan-y`. Bàn vẽ đưa cỡ qua `window.__edPvZoom`, khung kéo / So vị trí cũ qua ô range ẩn (`hu11-size`, `on-size`). **Phóng không đổi chỗ xuống dòng** (người dùng 27/10): `vkZoom(…, {wrap:true})` — bề rộng nội dung = bề rộng gốc × tỉ lệ phóng, khoảng cách ngang dùng `calc(… * var(--vkz,1))`, nên phóng như ảnh, dòng ngắt đúng chỗ cũ, kéo ngang để xem phần tràn. Khung **Đồng loạt** cũng phóng được (khung cuộn `.vb-zf`, chip trạng thái đứng yên). Test `tools/t_zoomwrap.js`. |
| **Tên VER** | Theo vòng duyệt: vòng có 1 bản → VER N; nhiều bản → VER NA, NB… (SKILL nguyên tắc 4). Đổi cách đặt tên giữa chừng thì ghi bảng đổi tên cũ → mới ở “Số đo”. |
| **Trạng thái lưu** | Không viết câu dài, không đặt ở đầu trang: **chip nhỏ trong khung xem** của từng mục (Xem trước: góc khung xem; Chỉnh dấu: góc khung xem; Bàn vẽ: cạnh chữ “Xem trong chữ”) — chấm xám “đang kết nối… / chưa lưu được”, chấm xanh “tự lưu / đã lưu 22:51”. |
| **Nguồn** | `sources_html()`, hiện sẵn. Trích dẫn **[n]** (`cite(id)`) ở bất cứ đâu bấm nhảy tới đây. |

**Lời trên trang:**
- Không đánh chữ cái mục, không tiêu đề h2 trong mục, không khối nguồn dài: **viên thuốc là tên mục**.
- Mọi mục người dùng chỉnh / duyệt có ô góp ý (`<div class="notewrap" data-note="…">`), khoá giữ như cũ: V (Xem trước), R (Chỉnh dấu), C (Bàn vẽ). Tóm tắt ghi “Ghi chú Bàn vẽ: …” (tên mục, `window.__SECN`).
- **Không làm quyết định “Chọn ver”**: người dùng chốt bằng “chốt VER 4” / “chốt VER 3A” trong chat / ô góp ý.
- Chỉ những gì cần thấy ngay mới để mở; số đo, phím tắt thu gọn. Giải thích một câu.
- **Mọi khung hiện chữ phải zoom được**: gõ bằng font nhúng, không dùng ảnh tĩnh cho chữ.
- Bố cục cũ (hero “Bộ kit”, mục A–E, `verspec2()`) vẫn chạy được bằng các hàm cũ trong `build_page.py`, chỉ dùng khi người dùng muốn kiểu cũ.

## 3 · Nút và trạng thái

**Nút bật / tắt** (kern, line biên, tuỳ chọn khung vẽ, ô tick trong khung kéo):
- Chưa chọn: xám mờ (`opacity .6`), **không gạch ngang**, vì gạch ngang trông như bị khoá.
- Đang chọn: **tô đặc đảo màu** (nền `--pg-txt`, chữ `--pg-bg`).

**Tab và nút chọn nhóm:** cùng kiểu, đang chọn thì tô đặc.

**Thanh công cụ bàn vẽ:**
- Công cụ đang chọn tô đặc đảo màu.
- Nhóm theo thứ tự: chọn · bút · cọ · thành phần | góc / mượt · xoá | hoàn tác · làm lại | kéo khung · phóng to · thu nhỏ · vừa khung | về nét gốc.

**Icon:**
- Bút vector: ngòi bút.
- Thành phần: ô vuông có dấu cộng.
- Hoàn tác / làm lại: mũi tên cong kiểu undo-2 / redo-2, dùng chung cho mọi khung.

**Trạng thái lưu:** chấm màu kèm chữ ngắn (“đã lưu 22:51”), không viết câu dài.

## 4 · Khung kéo (`slider_ui.html`)

**Bố cục:**
- Khung xem trước bên trái, dính (sticky) khi cuộn cột thanh kéo.
- Ô Chữ mẫu ngay dưới khung xem (cột trái). Cột phải từ trên xuống: nút bật / tắt → nhóm thanh kéo.
- Mỗi chữ trong khung xem có vùng bấm (`rect.hu-hit[data-ch]`): bấm → mở chữ đó ở Bàn vẽ.
- Chữ vẽ bằng nét font thật, ghép râu / dấu theo số đang kéo.

**Thanh kéo:**
- Nút chọn nhóm (**Râu ơ ư / Dấu thanh / Dấu nặng**), chỉ hiện thanh của nhóm đang chọn.
- **Mỗi đại lượng một thanh**, chung cho chữ hoa và chữ thường. Chữ thường suy ra theo thanh tỉ lệ.
  - Râu: nét mảnh, nét đậm, thuôn, giữ mảnh tới, vươn, cao, **gốc râu Ư ↓ ↑** (`dyU`: dời gốc trên mép phải thân U, gốc Ơ đi theo để đỉnh Ư = Ơ), Ơ lên / xuống, cỡ chữ thường ×, độ dày chữ thường ×.
  - **Dấu hỏi** (khi có `hook_params`): kiểu `taper` → cỡ, đầu (đậm), đuôi (mảnh), độ thuôn, pha thanh–đậm; kiểu thanh–đậm → cỡ, nét đậm (dọc), nét mảnh (ngang), bầu giọt, cổ giọt, độ dài giọt, chân — cùng công thức `hook_stroke.py`; vẽ dấu bằng MỘT path cùng chiều + viền 0,4 px cùng màu (nhiều mảnh chồng → vệt trắng khử răng cưa).
  - Dấu thanh: sắc / huyền / hỏi / ngã, mỗi dấu có ← → và ↓ ↑.
  - Dấu nặng: cỡ × chấm i, ← →, ↓ ↑.
- Mỗi thanh có **ô gõ số** và nút **↺ riêng** bên phải:
  - bấm ↺: lùi từng bước của riêng thanh đó;
  - bấm đúp ↺: về mặc định.
  - Không có nút reset cả khung.

**Tô đỏ dấu đang chỉnh** (nút bật / tắt “tô đỏ dấu đang chỉnh” dưới khung xem trước, nhớ theo máy):
- Chọn nhóm: tô đỏ cả loại dấu của nhóm (Râu → râu; Dấu thanh → sắc huyền hỏi ngã; Dấu nặng → dấu nặng).
- Bấm / chạm vào một thanh: chỉ tô đỏ dấu thanh đó điều khiển, cùng các dấu của thanh đang link với nó. Không đổi màu tên thanh.

**Nút link chỉ có ở thanh link được** (vị trí dấu thanh / dấu nặng: ngang với ngang, dọc với dọc). Thanh râu, cỡ dấu nặng, tỉ lệ chữ thường không có nút (ô trống giữ thẳng cột).

**Nút link** (icon mắt xích, bên trái ↺ mỗi thanh; chưa link = icon có **gạch chéo**, đang link = icon thường, không tô nền):
- Các thanh cùng bật link và **cùng loại** (ngang với ngang, dọc với dọc, râu với râu) chạy cùng nhau theo cùng độ lệch, ví dụ sắc ↓↑ và nặng ↓↑. Bỏ link thì chỉnh độc lập.
- **Mặc định link** mọi thanh vị trí dấu (sắc / huyền / hỏi / ngã / nặng, ngang với ngang, dọc với dọc). Thanh râu và cỡ dấu nặng mặc định không link vì đơn vị khác nhau.
- Một lần kéo các thanh link = **một bước hoàn tác**. Trạng thái link lưu cùng số kéo (`linkset`).

**Hoàn tác:**
- **Hoàn tác nhiều bước** cho cả khung bằng nút ↶ ↷. Mỗi lần thả thanh là một bước.
- **Phím tắt chung cho cả trang** (`UNDO_JS` / `window.__UB` trong `build_page.py`, nạp ở HEAD):
  - Ctrl+Z hoàn tác, Ctrl+Shift+Z hoặc Ctrl+Y làm lại (cả khi thao tác nằm ở mục đang ẩn);
  - áp dụng cho **mọi thao tác** theo đúng thứ tự đã làm: thanh kéo, nét bàn vẽ, lựa chọn quyết định;
  - khi đang gõ trong ô chữ, để trình duyệt tự hoàn tác chữ.
- Khối mới thêm vào trang phải gọi `__UB.note(khu)` khi có thao tác, `__UB.reg(khu, undo, redo)` một lần, và `__UB.undone / redone(khu)` trong nút hoàn tác riêng của khối.

**Tuỳ chọn và số đo:**
- Nút bật / tắt: đường dóng dấu hỏi, line biên, kern sau râu.
- Dòng số đo chỉ giữ “Rộng thêm … · kern … · dời dấu …”. Chi tiết (đỉnh râu, độ dày, cỡ dấu nặng) để trong “Số đo chi tiết”. **Từ 27/10: ẩn cả dòng này** (xem mục Chỉnh dấu · Chi tiết).

**Lưu:** `fontvn/<slug>-rN/horn/v1` gồm `all`, `lc_ratio`, `lc_wratio`, `dot`, `tone`, `hook`, `linkset`, `text`.

## 5 · Bàn vẽ (`editor.js`)

**Bố cục:**
- Khung vẽ bên trái. Thanh công cụ dọc **chỉ dính trong khối khung vẽ** (`.ed-left`), không được đè lên cột phải hay phần xem trước khi cuộn.
- Cột phải: “Vì sao đặt dấu như vậy?” (thu gọn, có dấu hỏi), danh sách ký tự, ghi chú cho ký tự.
- Dưới khung vẽ, trải ngang: ô Chữ mẫu → “Xem trong chữ” (chip trạng thái lưu cạnh tiêu đề).
- Dữ liệu glyph đưa vào bàn vẽ chỉ có `Q` MỘT điểm điều khiển: `export_editor.py` tự tách `qCurveTo` nhiều điểm của font .ttf.

**Công cụ:** Chọn (V) · **Nhóm bút vector** · Cọ (B) · Thành phần (C) · Tay (H) · Snap (S). Phóng to / thu nhỏ: Ctrl + / Ctrl − hoặc lăn chuột.
- **Nhóm bút vector** (như Illustrator): một nút trên thanh công cụ, icon = công cụ bút đang dùng, tam giác nhỏ ở góc; bấm → mở danh sách: Bút vector (P) · Thêm điểm neo (+) · Xoá điểm neo (−) · Đổi điểm góc / mượt (Shift+C). Bấm ra ngoài / Esc để đóng. Danh sách nổi trên khung vẽ (thanh công cụ `z-index` cao hơn khung).
- Đổi điểm góc / mượt: bấm điểm mượt = thành góc (bỏ tay nắm); bấm kéo điểm góc = kéo ra tay nắm mượt; kéo một tay nắm = bẻ góc.
- Không có nút thùng rác: xoá điểm đang chọn bằng Delete / Backspace.
- **Bút vector dời được điểm neo** (người dùng 26/10 “không thể dùng bút vector di chuyển điểm neo”): khi chưa vẽ đường mới, bấm-KÉO điểm neo = dời điểm, bấm thả không kéo = xoá điểm; **giữ Ctrl / ⌘ khi cầm bất kỳ công cụ bút nào = công cụ chọn trực tiếp** (kéo điểm neo, tay nắm) như Illustrator. Rung tay < 4 px chưa tính là kéo.
- **Về nét gốc**: hộp xác nhận nổi GIỮA khung vẽ (nền mờ phía sau), ghi rõ ký tự nào; Esc hoặc bấm ra ngoài = Thôi.
- Thêm điểm: cắt đoạn cong tại chỗ bấm, hình không đổi. Xoá điểm: khớp lại một đoạn cong qua 2 điểm bên cạnh, giữ hướng tay nắm. Bút vector khi chưa vẽ đường mới: bấm lên đường = thêm, bấm vào điểm = xoá (như Illustrator).

**Liên kết B → C:** kéo thanh ở B (râu, vị trí dấu, cỡ dấu nặng) thì “Xem trong chữ” của C vẽ lại theo số B, trừ chữ / dấu đã vẽ tay ở C (nét C ưu tiên).

**Hàng bật / tắt:** lưới, thước, đường chân chữ, nét gốc, 2 line biên + tô tràn, line biên dọc, trục, điểm, Snap.

**Trục chữ:** font đứng thì trục thẳng đứng; chỉ font nghiêng mới vẽ trục chéo.

**Bản vẽ nhiều chữ (kiểu artboard Illustrator):**
- Thanh “Bản vẽ” ngay trên khung: các chữ đang có, nút **+ Thêm chữ** (bật rồi bấm chữ ở danh sách, hoặc Shift + bấm), nút × bỏ chữ. Tối đa 8 chữ.
- Chữ đang sửa luôn ở gốc toạ độ, có khung màu nhấn và đủ điểm / tay nắm; chữ khác xếp hai bên, tô mờ, có trục chữ riêng. Bấm vào chữ khác (trên khung hoặc trên thanh) để sửa chữ đó, chỗ nhìn giữ nguyên.
- Tab danh sách theo thứ tự **134 chữ Việt (mặc định, mở sẵn chữ a) → Dấu → Chữ gốc**.
- Bấm chữ ở danh sách (không Shift) = thay chữ đang sửa. Dấu (tab Dấu) vẫn sửa riêng một mình, các chữ trên bản vẽ được giữ lại.
- **Chép dấu / Dán / Dán thay** (Ctrl+C, Ctrl+V; Ctrl+Shift+V = đúng toạ độ cũ):
  - chọn bằng công cụ Thành phần (cả dấu) hoặc chọn điểm;
  - Dán giữ **độ lệch so với trục chữ** và **khoảng cách tới đỉnh chữ** (chép từ chữ thường sang chữ hoa thì tự nâng theo cap − x-height);
  - Dán thay xoá phần đang chọn, đặt dấu mới giữa theo x và cùng đáy với phần cũ.
- Hoàn tác giữ **một thứ tự chung cho mọi chữ** (`EH` / `EF`): Ctrl+Z mở lại đúng chữ vừa sửa rồi lùi. Bấm mà không kéo thì bỏ bước rỗng (`__UB.drop`).
- Phím tắt bàn vẽ chạy khi vừa bấm vào bàn vẽ (không chỉ khi rê chuột), vì thanh “Bản vẽ” dựng lại nút khi đổi chữ.

**Nét người dùng vẽ:** lấy ý rồi vẽ lại cho hợp font, không chép từng điểm.

## 6 · Khoá db và đọc góp ý

| Khoá | Nội dung |
|---|---|
| `fontvn/<slug>-rN` | `picks`, `notesRN` (góp ý từng mục), `summary` |
| `fontvn/<slug>-rN/horn/v1` | số khung kéo |
| `fontvn/<slug>-rN/glyphs/<m-dấu\|g-glyph>` | nét bàn vẽ |
| `fontvn/<slug>-rN/ann1/<id>` | vẽ góp ý trên ảnh |

Khi người dùng nói “có góp ý trong artifact”:
1. Chạy `ArtifactData list collection:"fontvn"` và đọc vòng mới nhất.
2. Ưu tiên điều người dùng nói trong chat.

## 7 · Kiểm tra trước khi publish

```bash
python3 -I tools/build_page.py tools/tpl rN r1/review.html tools/content_rN.py
VERS="VER a,VER b" node tools/itest6.js $PWD/r1/review.html rN/t_    # đổi VER phải đổi font thật, không lỗi, không tràn 390 px
node tools/itest4.js $PWD/r1/review.html rN/ed.png                   # khi đụng bàn vẽ
```

Chụp màn hình ở cả 3 cỡ (1280, 800, 390) và cả sáng / tối, **từng viên thuốc** (mục ẩn không lộ ra khi test trang đầu). Phải kiểm:
- thanh công cụ không đè khi cuộn;
- nút đọc được ở nền tối;
- khung kéo hoàn tác đúng từng bước;
- nạp font mẫu (`setInputFiles('#vk-file', …)`) hiện đủ 2 cách so, không lỗi;
- `[hidden]` thắng `display` của class (CSS có sẵn `[hidden]{display:none!important}`).

Lỗi tải Google Fonts trong máy test là bình thường.

---
*build by @nhatmotion*

## CSS riêng cho thành phần (người dùng 27/10)

> “Để css riêng để các component chỉ hiện đúng như hiện tại — có vài component tự ý mặc css.”

- **Lớp (cascade layer):** `build_page.py` bọc CSS khung trang cũ (`tpl/styles.css`, SPEC2) vào `@layer vk-legacy`, CSS bàn vẽ vào `@layer vk-ed`, thứ tự `vk-legacy, vk-own, vk-ed`. CSS của thành phần Việt Font Kit (`vfk_ui.py` CSS / KN_CSS, `slider_ui.html`, `nghieng/oldnew_block.tpl.html`, INFO / MONO) **không layer → luôn thắng**, bất kể độ đặc hiệu của bộ chọn cũ.
- **`tools/vk_own.css`** (`@layer vk-own`): luật riêng của thành phần, chép từ lớp cũ và bọc `:where(.vk)` (giữ nguyên độ đặc hiệu). Sửa giao diện thành phần thì sửa ở đây hoặc `vfk_ui.py`, **không sửa `styles.css`**. Thêm thành phần mới dùng class cũ → chạy lại `node tools/gen_own.js trang.html tools/vk_own.css`.
- **Kiểm sau mọi lần sửa CSS:** `node tools/snap_css.js trang.html truoc.json` (trước) rồi `… sau.json`, `python3 tools/cmp_snap.py truoc.json sau.json` — chụp computed style mọi phần tử trong `.vk`, 5 tab, sáng / tối, 1280 / 390. Chỉ được khác đúng chỗ định sửa.
- **Luật cấp trang (`:root`, `html`, `body`) KHÔNG được nằm trong layer** (lỗi 27/10): khung artifact claude.ai tự chèn `body{background:#fff;color:#000}` không layer — luật không layer luôn thắng luật trong `@layer`, nên trang tối thành nền trắng. `tools/vk_base.css` (sinh cùng `gen_own.js … vk_own.css vk_base.css`) giữ các luật đó ngoài layer. **Mọi test giao diện chạy trên bản giả lập khung**: `HOST_OUT=host.html python3 build_page.py …` (chèn phần [0] của `tpl/styles.css` trước trang).
- **Không tô màu cứng** trong khung xem (`#fff`, `#111`): nền `var(--pg-card)`, chữ `currentColor` + `color: var(--pg-txt)` để chế độ tối đúng (lỗi khung Chỉnh dấu nền trắng khi tối, 27/10).

## Thẻ Kinh nghiệm (người dùng 27/10)

- **Mọi thẻ cùng một cỡ** (cao 178 px, lưới cột ≥ 300 px), **không mũi tên**: tên ngắn 1 dòng · nhãn (đang dùng / trạng thái, không có thì ẩn) · **≤ 3 ý chính, mỗi ý 1 dòng** · tag 1 dòng (3 tag + “+N”) ở đáy.
- Nội dung thẻ lấy từ dòng `**Thẻ:** tên ngắn | ý 1 · ý 2 · ý 3` trong file kinh nghiệm (mỗi ý ≤ ~45 ký tự).
- **Bấm thẻ → mở TOÀN MÀN HÌNH** (người dùng 27/10: không chừa đầu trang; cả máy tính lẫn điện thoại): nền `--pg-bg`, nội dung rộng ≤ 900 px ở giữa, tên đầy đủ, nhãn, toàn bộ tag, đặc điểm, nội dung; **nút × cố định góc phải**, Esc cũng đóng. Lớp phủ được chuyển ra thẳng `body` lúc tải (không bị khung cha giới hạn).
- **Chữ nền:** sau mỗi thẻ là chữ “a” to, mờ, của một họ chữ Google cùng kiểu (dòng `**Chữ nền:** Họ chữ | độ đậm [| italic]`; một link Google Fonts chung, `text=a` chỉ tải đúng chữ a). Nút “Chữ nền” mở thanh chỉnh: **cách mép phải** (px, ≥ 8 — một số dùng cho mọi cỡ màn hình, người dùng 27/10), dọc, cỡ, đậm nhạt, mờ từ dưới lên (mask gradient theo thẻ). Chữ neo theo mép phải thẻ, khoảng cách tính tới **mực** chữ a (canvas `measureText` bù khoảng trắng phải của từng font) — không neo theo % từ trái (thẻ hẹp trên điện thoại lệch khác máy tính). Giá trị lưu trên máy + db `fontvn/vk-ui` (`kn`) — đọc db này để đặt làm mặc định của kit (`.kn-grid` `--kn-ar/ay/as/ao/fade`).

## Nền và nút (người dùng 27/10)

- **Không đường kẻ ngang** ở đầu trang. **Phân cấp bằng dải đầu trang** (`.vk-strip`, `--vk-strip`) **theo chế độ sáng / tối** (người dùng 27/10: không phải lúc nào cũng đen): **dải luôn tối hơn nền thao tác**: tối #1a1918 / nền #262624, sáng #efede5 / nền #faf9f5; chữ dùng token của trang: chỉ bao tác giả + tên kit + nút sáng / tối. Phần còn lại (“Đang Việt hoá”, thanh tab dính, nội dung) **một màu nền `--pg-bg`, không gradient** — thanh tab dính dùng nền `--pg-bg` mờ nên không thành một dải tối riêng (lỗi 27/10: nền gradient + thanh tab nền đặc = “dòng strip đen” thừa).
- **Kính mờ (glass) chỉ dùng cho chip thông tin trong khung xem** (`.vk-save`, `.hu-chip`, `.ed-save`). Mọi nút / thanh tab / viên thuốc VER / nút sáng tối: nền đặc theo token, không blur.

- **Nút sáng / tối: 2 nút** (mặt trời, mặt trăng — người dùng 27/10, bỏ nút “theo máy”). Chưa bấm thì trang theo máy, nút của chế độ máy đang dùng sáng lên; bấm thì chọn hẳn và nhớ trên máy đó.
- **Bảng màu ấm như ứng dụng Claude** (người dùng 27/10, đỡ mỏi mắt; `MONO_CSS` trong `build_page.py`): sáng — nền #faf9f5, thẻ #ffffff, lõm #f3f1ea, kẻ #e8e5da / #d9d5c8, chữ #1f1e1d, phụ #5e5d57 / #8c8a82; tối — nền #262624, thẻ #30302e, lõm #1f1e1d, kẻ #3a3936 / #4a4844, chữ #f5f4ef, phụ #b5b3aa / #85837c. Không dùng xám lạnh / đen tuyền.
- **Bàn vẽ trên điện thoại:** 1 ngón = công cụ đang chọn (chọn, bút, cọ…); **2 ngón = chỉ phóng / kéo khung vẽ**, không bao giờ tạo khung chọn hay điểm bút (thao tác ngón 1 vừa bắt đầu bị huỷ sạch khi ngón 2 chạm).

## Chưa có font · Ủng hộ · Kinh nghiệm trống · Bản public (người dùng 27/10)

- **Chưa có font** (người dùng quên gửi font, `rN/` không có `A.woff2`): `build_page.py` tự sang chế độ `NOFONT` — mục Xem trước hiện khung nét đứt giống ô Nạp font mẫu (“Chưa có font cần Việt hoá · Gửi file font gốc (.ttf / .otf) vào khung chat để bắt đầu”), ẩn Chỉnh dấu / Bàn vẽ / viên thuốc VER, tên ở đầu trang = “Chưa có font”.
- **Tab Ủng hộ** (cuối thanh tab, `VK.donate_panel()`, số liệu ở `VK.DONATE`): **tiêu đề “Cảm ơn bạn đã dùng Việt Font Kit!” ở trên cùng** (người dùng đọc đầu tiên) → lời của tác giả (tool trong bộ công cụ tự dựng cho workflow edit video, đóng gói sẵn để tiết kiệm token · ủng hộ tuỳ hỷ · cảm ơn) → lưu ý phi thương mại / không thương mại hoá font chưa được cấp phép → liên hệ email → thẻ trắng (cả chế độ tối, để quét được) có mã QR (`tools/assets/donate-qr.jpg`), tên tài khoản, nút ngân hàng · số tài khoản bấm để chép. **Không** gắn kinh nghiệm với ủng hộ: kinh nghiệm miễn phí cho tất cả.
- **Kinh nghiệm trống** (chưa có file kinh nghiệm nào): tab hiện khung “Kinh nghiệm đang trống · Hãy bắt đầu Việt hoá để có kinh nghiệm”, không có số đếm.
- **Bản public**: CHỈ đóng gói khi người dùng yêu cầu xuất bản public. `python3 tools/make_public.py <kit> <thư mục ra>` → phiên bản riêng (giữ **1.0.0** tới khi người dùng công bố), **giữ đủ kinh nghiệm** (miễn phí), nhật ký / MANIFEST mới, bỏ file nội bộ. Bản đã gửi mà chưa công bố thì đóng gói lại vẫn 1.0.0 (cất bản cũ thành tên khác, không xoá).

## Xem trước · Văn mẫu (người dùng 27/10)

- Xem trước có 2 kiểu: **Văn mẫu** (mặc định) và **Bảng chữ** (ô Chữ mẫu như cũ). Văn mẫu = bố cục văn bản thật: dòng nhỏ đầu (viết hoa, giãn chữ) · **tiêu đề to** (3,2 em) · **tiêu đề phụ** (1,5 em) · **thân bài** (1 em, giãn dòng 1,65); cỡ chạy theo phóng (thân = px / 48 × 20).
- Bài mẫu: chỉ văn thơ **phạm vi công cộng** — Truyện Kiều (Nguyễn Du), Bánh trôi nước (Hồ Xuân Hương), ca dao. Nút **TIÊU ĐỀ HOA** viết hoa tiêu đề để soi dấu chồng chữ hoa. Kiểu xem / bài / tiêu đề hoa nhớ trên máy (localStorage).

## Chỉnh dấu · Đồng loạt (người dùng 27/10)

- Tab Chỉnh dấu có 2 chế độ (nút đầu mục): **Đồng loạt** (mặc định, vị trí / cỡ dấu) · **Chi tiết** (trước gọi “Thanh kéo chi tiết”, rồi “Chi tiết”: râu, dấu hỏi, **dáng nét** dấu). Ô góp ý chung cho cả hai.
- Đồng loạt: tab theo **loại dấu** (sắc, huyền, hỏi, ngã, nặng, mũ, trăng, mọi dấu; chấm đỏ = đã chỉnh) → dòng chữ thường + dòng chữ hoa có dấu đó (dấu đang chỉnh tô đỏ, viền nét đứt = vị trí cũ, vạch đỏ đứt = giới hạn dòng — chữ đậm vạch khi dấu vượt) → câu mẫu có nhiều dấu đó. Bên phải: thanh kéo + ô số **ngang · dọc · cỡ % · chữ hoa thêm dọc**; dấu thanh có thêm **khi chồng ngang / dọc**; “mọi dấu” = dọc + cỡ mọi dấu trên. Nút về 0 từng dấu / tất cả.
- Đơn vị font; dấu thanh chồng **đi theo** dấu mũ / trăng bên dưới. Lưu db `<DOC>/batch/p` (`{p:{kind:{dx,dy,sc,uy,sx,sy}}}`), dòng “Chỉnh đồng loạt — …” vào tóm tắt. Claude áp bằng `batch_apply.py` (cùng công thức). Test: `tools/t_batch.js`.

## Chú giải chung · thanh kéo một dòng (người dùng 27/10)

- **Chú giải chung** cho cả Đồng loạt và Chi tiết, nằm ngay dưới khung xem của chế độ đang mở, **một hàng**, bấm từng mục để bật / tắt (thay các nút “tô đỏ dấu đang chỉnh”, “line biên”): ô đỏ đặc = dấu đang chỉnh · ô **viền nét đứt cùng cỡ** = vị trí cũ (Đồng loạt) · vạch đỏ đứt = giới hạn dòng (Đồng loạt) · vạch cam = line biên (Chi tiết). Nhớ trên máy (`vk-lgd`).
- Bỏ nút **đường dóng dấu hỏi** (tắt), **kern sau râu** (luôn bật), **nút link** (mỗi thanh chỉnh riêng; bỏ qua link đã lưu).
- Thanh kéo cả 2 chế độ: **một dòng** tên ngắn (vd “ngang ← →”, “hoa ↓ ↑”, “chồng ↓ ↑”; giải thích ở tooltip) · thanh · ô số · nút lùi (Đồng loạt: về mặc định). Màu thanh = `--pg-txt` (không xanh dương mặc định). Bỏ nút chữ “Về 0 …”.

## Chỉnh dấu · Chi tiết (người dùng 27/10)

- **Không lặp thanh kéo của Đồng loạt**: bỏ thanh vị trí dấu thanh (ngang / dọc / chồng) và vị trí dấu nặng ở Chi tiết (vị trí cũ đã lưu không nạp lại).
- **Nhóm dấu (Râu ơ ư · Dấu hỏi · Dấu thanh · Dấu nặng) nằm TRÊN khung xem**, dạng chữ gạch chân giống tab loại dấu của Đồng loạt (`#hu11-grpbar`, CSS `.hu-grp` = `.vb-tabs`), không phải viên thuốc ở cột phải.
- Thanh **dáng nét** (db hornui `fontvn/<slug>-r1/horn/v1` trường `shape`): sắc đầu / đuôi %, huyền đầu / đuôi %, ngã trái / phải % (40–180, độ dày nét dọc trục dấu) · dấu nặng: cỡ × chấm i + **độ tròn %** (0–100). Công thức trang = `tools/mark_shape.py` (taper theo trục PCA 20 khúc; tròn = kéo điểm về vòng tròn bán kính trung bình). Áp vào font: `quick_vn` cấu hình `mark_shape` = `{acute:{h:sh,t:st}, grave:{h:fh,t:ft}, tilde:{h:xh,t:xt}, dot:{round:nr}}`.
- Đã bỏ (người dùng đánh “?”): chip kern ở Xem trước, “Số đo” ở Xem trước, khối “Góp ý vòng trước → VER mới” (trả lời góp ý trong chat), “· đơn vị font, 1024 = 1 em” ở tiêu đề thanh Đồng loạt, ô Chữ mẫu ở Chi tiết (ẩn, câu mẫu cố định).
- Bỏ khối **“So vị trí cũ · nét đứt = VER n”** ở Xem trước (người dùng 27/10). Cột phải Xem trước: **Font mẫu (nạp font mẫu) đầu tiên** → (line biên, chỉ ở Bảng chữ) → mô tả VER → **Tên font xuất cuối cùng** (CSS `order`), **không đường kẻ ngang** (tách nhóm bằng khoảng trống), không để hàng nút trống chiếm chỗ (`.vk-tg:not(:has(>:not([hidden])))`).
- Ô góp ý mỗi mục **luôn giữ**: Xem trước (`data-note="V"`), Chỉnh dấu (`R`, chung 2 chế độ), Bàn vẽ (`C`). Bỏ khối nào trong mục thì kiểm lại đủ 3 ô.
- Đổi tên chế độ **Nét dấu → Chi tiết** (người dùng 27/10). Ẩn luôn dòng số đo “Rộng thêm Ư … · kern …” và mục “Số đo chi tiết” dưới chú giải (phần tử vẫn còn, `hidden`, để script không lỗi).

## Bản Free · Xuất chỉnh sửa · tab Hướng dẫn (người dùng 27/10)

- `tools/vk_localdb.js` chạy đầu trang: thử db của artifact (đọc thử 1 doc, chờ tối đa 12 s — khung tự trả null sau 10 s; hết giờ chỉ chuyển sang lưu trên máy khi CHƯA nối được db) → được thì dùng như cũ (Pro / Max / Team, **không đổi gì, không hiện nút**); không được (Free, mở file ngoài claude.ai) → lưu `localStorage` khoá `vkdb:<đường dẫn>`, thêm class `vk-local` cho `<html>`, hiện nút **Xuất chỉnh sửa** (`.vk-exp`, cạnh nút VER trên thanh dính, thấy ở mọi mục). `build_page.py` đổi mọi `window.claude.use('db')` → `window.__vkDb()`.
- Bản lưu trên máy trả db **sau DOMContentLoaded** (trả sớm thì script đọc db chạy trước khi trang khai báo `__FV_EDDOC` → không nạp lại được).
- **Khung artifact chặn link tải file thường** (blob / data:) → xuất theo thứ tự: (1) capability **`downloads`** (`claude.use('downloads').save({filename, data})`, người xem xác nhận) — trang phải khai `capabilities: {assets:{}, db:{}, user:{}, downloads:true}` khi xuất bản; (2) mở ngoài claude.ai → link blob; (3) không có cả hai (bản Free trong chat) → **chép đoạn chữ** + hộp `#vk-expdlg` có sẵn đoạn chữ để chép tay (clipboard trong khung có thể bị chặn). `import_edits.py` đọc được cả file .json lẫn đoạn chữ dán.
- Nút xuất: tải `vfk-chinh-sua-<slug>-rN.json` ({kind:"vfk-edits", dock, font, kitver, docs:{đường dẫn: dữ liệu}}); tab Hướng dẫn có thêm “Chép đoạn chữ”. Không hiện số đếm (trang tự ghi tóm tắt lúc mở). Free ẩn nút + đính kèm (không có chỗ lưu file).
- **Tab Hướng dẫn** (sau Kinh nghiệm, **trước Nguồn** và Ủng hộ — người dùng 27/10; `data-sec="H"`): dòng trạng thái lưu · 5 bước (cài skill, bắt đầu, duyệt, gửi chỉnh sửa, chốt) · **Pro: chỉ 5 bước, không thẻ nào; Free: thêm thẻ Free** (`data-plan="local"`, `vk_localdb.js` ẩn khi không phải Free; bước 4 đổi chữ theo gói qua `data-dbmode`). Pro không thấy chữ nào về Free và ngược lại. Ngắn gọn, không lặp README.
- Test: `tools/t_free.js` (Free: lưu, tải lại giữ, xuất file; Pro giả lập: không nút, ghi vào db).

## Gọn thêm (người dùng 27/10)

- Đồng loạt: **bỏ dòng “N chữ có dấu … · kéo thanh bên cạnh, xem trước cập nhật ngay”** dưới hàng tab loại dấu (`.vb-info` ẩn).
- Bàn vẽ · Xem trong chữ: **bỏ nút kern** (luôn xem có kern); chip trạng thái lưu dời sang phải, chỗ nút kern cũ.
- Kinh nghiệm: **bỏ nút / bảng “Chữ nền”** — đó là công cụ chỉnh giao diện, không phải một phần giao diện. Giá trị chốt là mặc định trong `KN_JS` (`D={r:18,y:-6,s:230,o:9,f:60}`: cách mép phải 18 px · dọc −6 % · cỡ 230 px · đậm nhạt 9 % · mờ từ dưới 60 %). Cần chỉnh lại: `KN_TUNE = True` trong `vfk_ui.py`, chỉnh xong ghi số vào `D` rồi tắt lại. Không có thanh thì trang bỏ qua giá trị cũ lưu trên máy / db.
- Công cụ chỉnh giao diện (thanh tinh chỉnh vị trí, màu…) chỉ bật khi người dùng đang chỉnh; chốt xong thì ghi thành mặc định và gỡ khỏi trang.

## Vòng 2 `serif.regular.condensed.contrast.italic.ttf` (người dùng 27/10)

- **Xem trước · Bảng chữ: bỏ nút line biên** (giới hạn dòng đã có ở Chỉnh dấu · Đồng loạt).
- **Viên thuốc VER** đứng ngay sau thanh tab; xuống dòng thì bắt đầu từ trái.
- **Tên loại dấu viết hoa chữ đầu**: Dấu sắc, Dấu huyền… (tab Đồng loạt, giống nhóm Chi tiết).
- **Thẻ thanh kéo**: Chi tiết dùng đúng kiểu thẻ Đồng loạt (tiêu đề + chữ nhỏ trong thẻ, nhãn 1 dòng ≤ 86 px, tên đầy đủ ở tooltip, ô số 52 px không mũi tên, nút lùi 26 px); **đỉnh thẻ = đỉnh khung xem** (`vkAlign()`), không ngang hàng tab loại dấu.
- **Chi tiết vẽ nét thật** của chữ có râu khi chưa kéo thanh râu (giống Xem trước); tô đỏ dấu đang chỉnh bằng CSS, không dựng lại khung.
- **Thẻ Kinh nghiệm mở mượt**: không blur toàn màn hình, ép reflow trước khi chuyển, chỉ opacity + transform.
- Test: `node tools/t_shots.js trang.html thư_mục` · `node tools/t_chitiet_speed.js trang.html`.
- **Khung xem Đồng loạt = Chi tiết** (người dùng 27/10): cùng chiều cao TỐI THIỂU `--vk-pvh` (min-height — không cố định height, nội dung dài thì khung cao theo, không cắt chữ, 28/10) (clamp 340–540 px), cùng viền / nền / bo góc, cùng lưới 1fr + 300 px, khe 18; điện thoại: tab loại dấu + chú giải 1 dòng vuốt ngang → chuyển chế độ khung không nhảy. Kiểm: `rects` 2 chế độ ở 1280 / 820 / 390 phải trùng.
- **Bàn vẽ: thanh công cụ dọc ngang đỉnh KHUNG VẼ** (người dùng 28/10), không ngang hàng “Bản vẽ” (`vkAlign()` đặt margin-top = đỉnh `.ed-stage` − đỉnh `.ed-bar`; điện thoại thanh nằm ngang phía trên như cũ).
- **Bàn vẽ: bảng ký tự bên phải ngang đỉnh khung vẽ; khung vẽ thấp hơn bảng thì kéo dài khung vẽ cho bằng đáy bảng** (người dùng 28/10, `vkAlign()` đặt chiều cao `svg.ed-cv`, phát `resize` để bàn vẽ vẽ lại).
- **Thẻ thanh kéo: div, không fieldset / legend** (Safari iOS đè tiêu đề lên viền, 28/10). **Trục chữ ở Bàn vẽ đi qua tâm dấu đã đặt** (`axis_editor.py`).
- **Phóng (vkZoom): phần tử mang transform phải là phần tử bị THAY khi vẽ lại** (hoặc lớp bọc tạm `.vk-zw` như Xem trước) — giữ nguyên phần tử đã transform thì Safari iOS hiện lớp ảnh cũ chồng lên chữ mới (28/10).
- **Chữ trên chip lưu ngắn, dễ hiểu** (người dùng 28/10): chỉ có đang kết nối… · tự lưu · đang lưu… · đã lưu HH:MM · chưa lưu được — mở lại số / nét / góp ý lần trước vẫn hiện “tự lưu”. Không dùng “đã nạp số lần trước”, “đã khôi phục”, “sẵn sàng · tự lưu khi vẽ”.
- **Chip lưu một chỗ ở mọi tab** (người dùng 28/10): góc phải trên của khung xem, cách viền 10 px, chữ 12 px; Bàn vẽ đặt trong khung vẽ dưới thước. Một luật CSS chung trong `vfk_ui.py`, không đặt lại ở chỗ khác.
- **Phóng xong không được nhảy chữ**: khung vẽ lại khi thả tay phải neo điểm dưới con trỏ (`vkZoom` đã làm sẵn); khung mới thêm vào chỉ cần gọi `vkZoom`, thử bằng `tools/t_wheel.js`.
