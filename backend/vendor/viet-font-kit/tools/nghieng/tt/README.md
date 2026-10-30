# Font NGHIÊNG TrueType (.ttf) từ bản ĐỨNG đã Việt hoá — chỉ cần fontTools

> build by @nhatmotion · dùng lần đầu cho serif mảnh tương phản (Google Fonts, có anchor mark / mkmk)

| File | Việc |
|---|---|
| `build_it.py SRC_IT.ttf REF_VN.ttf OUT.ttf cfg.json` | Dựng đủ chữ Việt + ơ ư Ơ Ư, ccmp ghép NFD, GPOS cho dấu rời, ghi `OUT.recipes.json` (bàn vẽ). |
| `half_hook.py SRC_IT.ttf REF_VN.ttf half.json` | Dấu hỏi từ nửa trên dấu `?` của bản nghiêng (VER C). |
| `axis_editor.py FONT editor.json GÓC [TOL]` | Trục chữ ở bàn vẽ: một góc cả font, một trục cả họ chữ (nhóm tâm dấu trùng nhau đông nhất). Chạy sau `export_editor.py`, cho MỌI VER. |
| `hook_tf.py` (+ cfg `"hook_tf": {"w","h","head","tail"}`) | Chỉnh dáng dấu hỏi chép từ bản đứng: bề ngang, chiều cao, dày đầu móc, dày đuôi móc (%). Cùng công thức nhóm “Dấu hỏi” ở Chi tiết → số kéo trên trang (db `hook`) chép thẳng vào cfg rồi dựng lại. |
| `fix_sax.py SRC_IT.ttf recipes.json…` | Sửa trục chữ ở bàn vẽ (`sax`) cho recipes cũ: trục qua anchor dấu trên của chữ gốc. |
| `measure_gaps.py FONT` | Khe dấu ↔ dấu (chồng) và dấu ↔ thân / râu từng chữ — kiểm “không sát”. |
| `union.py` · `geom.py` · `gposanc.py` | Hợp nét đường cong bậc 2 (không cần pathops), contour TrueType, đọc anchor GPOS. |

Luật đặt dấu (`build_it.py`):
- Dấu font nghiêng có sẵn → anchor mark / mkmk của chính font + độ lệch / co giãn bản đứng VN đã áp (ĩ Ĩ hẹp…).
- Dấu thiếu (hỏi, nặng, râu) → chép quan hệ từng chữ của bản đứng, nghiêng quanh anchor gắn dấu: `p = A_it + (dx + dy·tan, dy)`.
- Dấu nặng = chấm i nghiêng; ị theo trục thân i + chấm i; ỵ giữ khe bản đứng.
- Râu: tách đoạn râu bản đứng (lấy mẫu DÀY trên cả đoạn thẳng — xem lỗi A33), nghiêng quanh gốc, hợp nét vào thân; râu là HÌNH RIÊNG, gốc kéo dài vào trong nét (`horn_root` 34 đv, chữ thường × 0,9), thân giữ nguyên rồi union (A37). Bàn vẽ / Chi tiết nhận râu rời.
- Râu là hình RỜI trong dữ liệu trang (bàn vẽ, Chi tiết); font vẫn gộp nét. lsb = xMin (A36).
- Khe: dấu thanh ↔ râu ≥ `horn_tone_gap` (mặc định 28; serif mảnh dùng 55 ≈ 0,75 nét dấu), dời trái tối đa `horn_tone_left` (40; bản nghiêng dùng 0 = chỉ nâng), dấu thanh bên phải dấu mũ `right_mingap` (50) — A35.

cfg mẫu (bản chốt `serif.regular.condensed.contrast.italic.ttf`): `{"stack":"top","horn_tone_gap":55,"horn_tone_left":0,"horn_from":{"U":"O"}}` · bên phải: `{"stack":"right","right_scale":0.85,"right_mingap":50,…}` · hỏi nửa ?: `{"hook":"half","hook_half":"half.json",…}`.
Sau đó: `nghieng/hornkern.py` → `stamp.py` → `winfix.py` → `kiemword.py --fix`. Dữ liệu trang: `export_editor.py FONT OUT.recipes.json editor.json`, `TONE_GAP=55 nghieng/export_hornui_italic.py FONT SRC.ttf horn5.json hornui.json <góc>`, `export_batch.py`.
