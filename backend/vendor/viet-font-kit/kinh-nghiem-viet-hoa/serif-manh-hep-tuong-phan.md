# Kinh nghiệm Việt hoá: Serif mảnh hẹp tương phản (display, .ttf)

> build by @nhatmotion

**Đặc điểm nổi bật:** serif chữ tiêu đề, độ đậm thường (Regular), dáng hẹp, tương phản thanh–đậm rõ (thân ~70, nét ngang ~25 trên 1000 UPM), đầu giọt ở a r ? g. Font Google (OFL), TrueType có hinting, GPOS có `mark` / `mkmk`, có sẵn dấu Latin mở rộng và đ Đ.

**Mã loại:** `serif.regular.condensed.contrast.ttf`

**Tag:** `#display` `#serif` `#regular` `#condensed` `#high-contrast` `#ball-terminals` `#ttf` `#hinted` `#ofl` `#gpos-mark` `#has-dcroat` `#upright` `#has-italic`

**Thẻ:** Serif mảnh hẹp tương phản | Dấu hỏi vẽ lại thanh–đậm, không nén từ ? · Khe dấu chồng đều 30 với nét mảnh · Giữ dấu gốc: không dẹt dấu mũ chữ hoa
**Chữ nền:** didone | 400

> Số liệu là ví dụ đo trên một font loại này. Đo lại trên font mới.

## 1 · Hồ sơ điển hình

| Đặc điểm | Ví dụ | Ý nghĩa |
|---|---|---|
| Định dạng | .ttf, 377 glyph, ttfautohint | `build.sh` tự đổi .ttf ↔ .otf; chữ gốc giữ hinting |
| GPOS | kern 4000+ cặp, `mark` / `mkmk` | Script chỉ đụng PairPos (lỗi A21) |
| Dấu có sẵn | á à ã â ă é ê í ó ô õ ú ý + đ Đ, dấu tổ hợp 0300 0301 0302 0303 0306 | Chỉ thiếu 96 chữ; dùng lại dấu tổ hợp sẵn, thêm 0309 0323 031B |
| Vị trí dấu gốc | đáy dấu sắc thường 583, hoa 793 (x-height 510, cap 720) | Luật `src-marks`: dấu mới bám theo vị trí này |
| Dòng | hhea 990 / −310 | Dấu kép chữ hoa cao tới ~1100; người dùng thường giữ dòng gốc, winAscent nâng để Word không cắt |

## 2 · Vấn đề hay gặp và cách xử lý

- **Dấu hỏi nén từ `?` bị chê "đổi kết cấu"**: thu nhỏ `?` rồi nở đều làm nét ngang dày lên, mất tương phản. Vẽ lại bằng `hook_stroke.py`: dọc 35 / ngang 11 / giọt 36 (≈ tỉ lệ thân 70 / ngang 25 của font), chân cụt cắt phẳng. Dấu hỏi chồng = cùng dáng × 0,84, nở 2.
- **Dấu huyền chồng sát dấu mũ (ề)**: khe 18 là quá chật với nét mảnh; người dùng chọn khe đều 30 cho mọi chữ (lỗi A24 với chữ rộng).
- **Tôn trọng dấu gốc**: không dẹt dấu mũ chữ hoa khi chồng (`caps_stack_flat: 1.0`), đáy dấu hỏi = đáy dấu sắc gốc (`gap_src`). Đổi lại đỉnh cao nhất tăng ~17 đơn vị.
- **Râu thanh đậm**: người dùng tự kéo ở B ra cổ 20, đầu 70, vươn 80, cao 60, giữ mảnh tới 0,5 → râu có cổ thật mảnh và đầu giọt rõ, hợp tương phản của font. Vươn 80 làm Ư +47, ư +41; kern sau râu khép −41 / −47.
- **Bàn vẽ hiện râu cũ chồng thân**: recipe giữa chừng — đã sửa bằng đồng bộ recipe trong `export_editor.py`.

## 2b · Diễn biến các VER

| VER | Thay đổi | Người dùng nói |
|---|---|---|
| 1 | Dấu chồng bên phải dấu mũ (khe 18), dấu hỏi nén từ `?`, râu cổ 24 / đầu 58 | Dấu hỏi đổi kết cấu; ề huyền sát ^; râu chưa thanh đậm; tôn trọng dấu font gốc |
| 2 | Như 1, dấu hỏi chồng trên đỉnh | (đối chiếu) |
| 3 | Dấu hỏi vẽ lại thanh–đậm, râu theo số kéo ở B, khe chồng đều 30, giữ dấu mũ hoa | “Tôn trọng vị trí + spacing dấu font gốc luôn, ví dụ Ầ” |
| 4 | **Mọi dấu theo anchor mark / mkmk của font gốc** (dấu chồng trên đỉnh, khe 73, cỡ nguyên) | Dấu hỏi tham khảo giọt chữ g (độ dày, độ bầu); cần thanh kéo riêng cho dấu hỏi |
| 5 | Dấu hỏi theo tai g: bầu 75 · cổ 23 · dài 145 × 0,62 → giọt 43 → cổ 13; thêm nhóm thanh Dấu hỏi ở B | “Chưa thấy thay đổi”; thử dấu hỏi đậm đầu thuôn dần về đuôi |
| 6 / 7 | Dấu hỏi `taper`: đầu 50 → đuôi 12 pha 35 % thanh–đậm (6) · đầu 52 → đuôi 12 thuôn đều (7) | “VER 5 vẫn ổn hơn”; vẽ lại theo font mẫu serif + mẫu didone Google |
| 8 / 9 | Dấu hỏi thanh–đậm theo tỉ lệ font mẫu: rộng / cao 0,95, bầu tròn 54, vòm 12, phải đậm 43, cao 172; chân đứng cụt (8, mẫu didone Google) / đuôi chéo (9, mẫu serif đậm đã Việt hoá) | Đưa font mẫu ĐỨNG đã Việt hoá (bản đứng VN `serif.heavy.condensed.contrast.ball` VER 12) — “mới chuẩn” |
| 10 / 11 | Dấu hỏi học trực tiếp từ font mẫu đứng (`hook_from_ref.py`): khung xương + thanh–đậm, bề dày × 0,578 (thân 68 / 118), cao 0,354 x-height; hoa × 0,94, chồng × 0,8, hoa chồng dẹt × 0,9. VER 11 đậm × 1,2 | — |
| 12 / 13 | Người dùng thích VER 11 nhưng “dấu chồng nhỏ quá, bầu giọt nhỏ” → giữ dáng, tăng `ball_k` (× 1,3 / × 1,45, chỉ 15 % đầu nét) và `hook_stack` (0,9 / 1,0). Bài học: dấu chồng × 0,8 là quá tay với serif mảnh — bắt đầu từ 0,9; bầu giọt học từ khung xương thường hụt, cộng thêm `ball_k` ≥ 1,3 | — |
| 14 | Người dùng chọn VER 12, rồi “chỗ dày nhất dấu hỏi = chỗ dày nhất dấu ngã”. Dấu ngã gốc dày 60; VER 12 dấu hỏi 52 / hoa 49 / chồng 47 / hoa chồng 41. `tools/hook_fit.py VERDIR 60` tìm độ đậm riêng mỗi cỡ (× 1,42 / 1,53 / 1,62 / 1,92) → marks hook / hook_uc / hook_s / hook_s_uc; anchor_marks tự dùng. Bài học: co dấu = co luôn độ dày → luôn bù độ đậm cho dấu chồng / chữ hoa | — |

**Bài học chính:** (1) font có anchor GPOS thì nhà thiết kế đã quyết vị trí dấu — đọc anchor trước khi tự đặt dấu (luật `src-marks`). Đổi lại dấu chồng chữ hoa cao (đỉnh ~1190 trên line 990). (4) Có font mẫu đã Việt hoá cùng kiểu (đứng) thì học thẳng dấu hỏi của nó — nhanh và đúng ý người dùng hơn mọi cách tự vẽ. (3) Đổi nhỏ không ai thấy — với dấu nhỏ, đưa hướng khác hẳn (thanh–đậm theo hướng nét ↔ đậm đầu thuôn đuôi giống dấu sắc gốc). (2) Font có tai giọt ở g → đầu dấu hỏi lấy từ đó (`hook-from-g`), người dùng nhìn ra ngay sự đồng bộ.

**Tỉ lệ dấu hỏi đo trên font mẫu serif tương phản** (ả): cao 0,35–0,44 x-height · rộng / cao 0,89–1,02 · nét đậm 0,50–0,66 thân chữ · bầu giọt 0,6–0,95 thân · vòm trên là nét mảnh, bầu tròn treo ở đầu trái. Dấu hỏi “hẹp như dấu ?” (rộng / cao ~0,8) trông lạc.

## 3 · Khi KHÔNG áp dụng

- Font nét đều / sans: dấu hỏi lấy từ `?` (`hoi.py`) vẫn ổn, không cần `hook_stroke.py`.
- Font không có dấu sẵn: `src-marks` không có gì để bám, dùng khe mặc định trong `hoi_place.json`.

---
*build by @nhatmotion*
