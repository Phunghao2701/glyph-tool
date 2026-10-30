# Kinh nghiệm Việt hoá: Viết tay nét đều (marker / bút dạ)

> build by @nhatmotion · Nhật Motion's Space

**Đặc điểm nổi bật:** chữ viết tay bằng bút dạ, nét đều (gần như không tương phản), đầu nét tròn, chữ cao hẹp, nghiêng nhẹ theo tay nhưng font khai đứng. File .ttf cũ (Google Fonts thời 2010), không có GPOS / GSUB / kern.

**Mã loại:** `hand.marker.monoline.ttf-legacy`

**Tag:** `#handwriting` `#display` `#monoline` `#marker` `#rounded-soft` `#condensed` `#upright` `#ttf` `#hinting` `#no-gpos` `#no-kern` `#latin-ext-accents` `#ofl`

**Thẻ:** Viết tay nét đều | Dấu hỏi vẽ lại từ khung dấu ?, bỏ đuôi · Sắc / huyền dài ×1,45 so với dấu gốc · Dấu chồng bên phải dấu mũ, theo bản vẽ
**Chữ nền:** viet-tay | 400

> Trạng thái: **ĐÃ CHỐT VER 10** (1.010, vòng 10, 27/10/2026). Số liệu đo trên một font mẫu 1024 UPM của loại này, gặp font khác phải đo lại.

---

## 0 · Bản chốt (VER 10) — bắt đầu từ đây cho font cùng loại

`quick_vn.py` (đường dự phòng, máy chặn pypi) với cấu hình:

```json
{"stack_place": "top", "hook_weight": "acute_grave", "hook_src": "notail",
 "acute_len": 1.45, "grave_len": 1.45,
 "stack_rel": {"acute": [-92, -11], "grave": [-112, -41], "hook": [-130, -24]},
 "stack_dx_ch": {"ắ": 32, "Ắ": 32}}
```

| Phần | Chốt | Ghi chú |
|---|---|---|
| Dấu hỏi | vẽ lại từ khung xương dấu `?` **bỏ đuôi móc** (`notail`), dày theo sắc / huyền (đầu dày, thuôn về chân); khi chồng rộng ngang ×1,35 | dày bằng dấu ngã → thô; lấy nguyên dấu `?` → to bề ngang |
| Sắc / huyền | **dài ×1,45** so với dấu gốc, giữ đáy, giữ độ dày; sửa luôn glyph dấu gốc nên á é ó… cũng dài theo | ×1,3 vẫn bị chê ngắn |
| Dấu thanh trên dấu mũ (â ê ô, thường + hoa) | **bên phải dấu mũ, thấp, khe rộng (~100)** — số đo từ chữ người dùng tự vẽ (ấ ầ ẩ) | ra hẳn bên phải giữa dấu mũ (VER 7) bị chê “lệch xa về bên phải dưới”; trên đỉnh (VER 6, 8) cao dòng |
| Chữ hẹp ô Ô | dời cả cụm dấu sang trái ≤ 0,15 × bề ngang dấu mũ (ố −49, ổ −41) | để dấu không chìa xa khỏi chữ |
| Ngã trên dấu mũ, mọi dấu trên dấu trăng | trên đỉnh, giữa; sắc trên dấu trăng lệch phải +32 (ắ Ắ) | người dùng chọn riêng |
| Chữ hoa | dấu trên trục ink ¼ trên của chữ, khe chung (51) — đồng bộ cả chữ ghép sẵn của font | font gốc đặt dấu hoa lệch (Ú −36) |
| Dòng | đỉnh 1203 → 1298 (+6 % dòng), win = mực thật (winfix) | dấu chồng trên đỉnh từng đẩy lên 1335 |
| Không có | kern, GSUB / GPOS (ccmp) | gõ Unicode dựng sẵn; tổ hợp mượn dấu font dự phòng |

**Đường đi 10 vòng (để lần sau rút ngắn):** 1A–1C chọn hướng (chồng phải / đỉnh / hỏi nửa trên `?`) → 2–3 sửa chữ hoa lệch, dấu hỏi thô → 4–5 hỏi theo sắc / huyền, bỏ đuôi, khe dấu chồng rộng ≈ 1 nét → 6 hỏi chồng rộng ngang → 7–8 sắc / huyền dài, thử sắc chồng bên phải / lệch nhẹ → **9 người dùng tự vẽ ấ ầ ẩ → đo → áp đều** → 10 sửa riêng ắ Ắ. Bài học: với loại font này mời người dùng vẽ 2–3 chữ dấu chồng ngay vòng 2–3, đo rồi áp đều (`stack_rel`) — nhanh hơn thử số.

## 1 · Hồ sơ điển hình của loại font

| Đặc điểm | Thường gặp (số đo ví dụ) | Ý nghĩa khi Việt hoá |
|---|---|---|
| Định dạng | TrueType .ttf, 1024 UPM, ~350 glyph, có `fpgm` / `prep` (hinting) | Chuỗi dựng chính đổi sang CFF rồi trả .ttf (`ttf2otf` / `otf2ttf`); đường dự phòng `quick_vn.py` ghi thẳng .ttf, giữ nguyên glyph gốc có hinting |
| Chữ có dấu sẵn | á à â ã ä ă ĩ ũ Ð… là **chữ ghép (composite)** chữ gốc + glyph dấu riêng (´ ˋ ˆ ˜ ˘) | Vị trí dấu lấy thẳng từ offset của chữ ghép (luật `src-marks`), dấu mới đặt theo đó |
| Thiếu | 94 chữ: hỏi, nặng, dấu chồng, ơ ư, đ Đ | Hỏi, nặng, râu phải dựng mới; Đ chép Ð (U+00D0) |
| Độ đậm | nét thân ~46, nét dấu sắc ~58 (dấu đậm hơn thân) | Dấu hỏi dày ≈ 0,85 × thân (~39) mới cân; dày bằng dấu sắc thì thành cục |
| Dấu mũ | rất cao (276 / 1024, đáy 679 → đỉnh 955 ở chữ thường) | Dấu chồng ăn nhiều chiều cao: dòng trên phải nâng (dấu chồng bên phải +50, trên đỉnh +71 trên 1203) |
| Đặt dấu gốc | chữ thường: dấu cùng độ cao (dy = 0), u thấp nên khe rộng — người dùng thấy ổn, giữ. **Chữ hoa rất lệch** (khe −36 ở Ú chìm vào chữ, −12 À, +96 Ã) | Chữ hoa: đồng bộ một khe (51) + trục phần mực 1/4 trên, sửa cả chữ có sẵn (`uc_sync`); duyệt ở vòng 2 |
| Chữ i | í ì ĩ vẽ sẵn dạng contour (không ghép), dấu cao hơn các chữ khác ~120 | Dấu trên ỉ: đáy = đáy dấu sắc của í, tâm theo thân ı |
| Kern / spacing | không có kern, chữ xếp thoáng | Râu chỉ cần nới advance, không cần kern sau râu |
| Giấy phép | OFL, không khai Reserved Font Name | Đổi tên “VFK - <tên gốc>” được; nhớ kèm OFL khi gửi file |

## 2 · Dấu hiệu nhận ra loại font này

- Không có bảng GPOS / GSUB / kern; chữ có dấu là composite.
- `thickness()` của thân và của dấu sắc gần nhau, viền hơi run như nét bút thật.
- Dấu mũ / trăng / ngã to, nét đều, đầu tròn.

## 3 · Vấn đề hay gặp và cách xử lý

0. **Vòng 6:** người dùng thấy VER 5 ổn hơn; dấu hỏi khi chồng (ẩ ẳ ể ổ) cần **rộng ngang hơn** dấu đơn cho rõ → ×1,35, giữ cao và độ dày. **Vòng 4 → 5 (góp ý trên trang):** dấu sắc / hỏi trông lệch trái → giữ chân dấu sắc ở chỗ cũ khi kéo dài (đừng đặt lại tâm), đặt **chân dấu hỏi** (cuối nét) trên trục thay vì tâm khung bao (dấu bỏ đuôi có chân lệch trái tâm ~27); dấu chồng sát dấu mũ → khe 32 → 55 (≈ 1 nét dấu), dòng cao thêm 23.
1. **Dấu hỏi — luôn đưa thêm 1 VER vẽ từ NỬA TRÊN dấu `?` (người dùng 26/10, áp dụng mọi font):** dấu hỏi tiếng Việt là phần móc trên của dấu `?`. Lấy nguyên thân dấu `?` (cả đuôi cong dưới) làm dấu hỏi thì ra dáng số 2 / chữ z. Cách làm: khung xương thân `?` → giữ từ đầu móc tới khi tụt quá nửa chiều cao (`hook_half` 0,5) → vẽ lại cùng độ dày, cao ≈ 1,4 × dấu sắc (197 trên 1024). Lưu ý: khớp đường cong cho mảnh nhỏ có thể bắn gai mảnh → `quick_vn` tự giữ đa giác khi khung bao lệch > 1,5.
2. **Dấu hỏi vòng 4 (đang duyệt):** người dùng thấy VER nửa trên `?` **to bề ngang quá**; muốn dáng VER cả thân `?` (theo sắc / huyền) nhưng **bỏ đuôi móc ở chân**. Cách làm: khung xương cả thân `?` → cắt ở điểm trái nhất trong 45 % dưới (đáy nét chéo), không giãn ngang (`quick_vn` `"hook_src": "notail"`). Thứ tự thử dấu hỏi nên đưa: cả thân `?` · bỏ đuôi móc · nửa trên `?`.
3. **Dấu sắc / huyền ngắn** (người dùng vòng 4: “độ dài dấu sắc ngắn quá”): font viết tay vẽ dấu sắc ngắn (cao 141 / 1024) — khi dấu hỏi đã cao 230+ thì sắc trông cụt. Kéo dài ×1,3 dọc trục dấu, giữ bề dày và đáy (`acute_len`, `grave_len`), sửa luôn glyph dấu của font để á é ó… có sẵn dài theo; kéo cả huyền cùng hệ số để 2 dấu vẫn soi gương nhau.
4. **Dấu hỏi:** không nén dấu `?` (nét thành mảnh, đầu to). Lấy **khung xương** của dấu `?` (bỏ chấm), vẽ lại bằng nét đều đầu tròn. **Dày = thân dấu ngã** (người dùng vòng 1: “chỉnh độ dày giống dấu ngã”; 57 trên 1024, phân vị 75 — phân vị 95 = 67 dính cục mực chỗ bẻ nét), cao 254 (≥ 4,4 × dày), ngang × 1,2 để lòng móc còn mở. Vòng 1 dùng 0,85 × thân (39) → người dùng thấy mảnh. Vòng 2 dày đều = dấu ngã (57): người dùng thấy ổn nhưng muốn thử **theo sắc / huyền** (nét bút thuôn): vòng 3 đầu móc 61 (chỗ dày nhất của sắc / huyền) thuôn về chân 44 (chỗ mảnh trung bình của sắc 53 và huyền 36). Cao 1,25 × dấu sắc thì quá nhỏ, nhìn như chữ z (đã thử).
5. **Dấu nặng:** đúng contour chấm chữ i, khe dưới chân = khe dấu sắc trên chữ a (~42). ỵ dời phải tránh đuôi; ị theo tâm thân ı.
6. **Râu ơ ư:** công thức horn5 (kệ + thanh đậm), `thin` ≈ 0,75 × thân, `head` ≈ 1,35 × thân; gốc cắt trong nét. Ở font viết tay râu đọc như một nét móc ngắn — để người dùng kéo ở mục Chỉnh dấu.
7. **Dấu chồng — luôn đưa 2 hướng ở vòng 1:** VER 1 dấu thanh bên phải dấu mũ (co 0,82, khe ≥ 0,55 × nét dấu ~32), VER 2 dấu thanh trên đỉnh (co 0,82). Dấu ngã và mọi dấu trên dấu trăng đặt giữa trên đỉnh ở cả hai.
8. **Đ đ:** Đ = chép Ð của font; đ = d + dấu gạch nối co lại, đặt giữa thân phải ở 74 % chiều cao, hợp nét bằng raster.
9. **Glyph vỡ trên bàn vẽ (lỗi trang):** contour .ttf có `qCurveTo` nhiều điểm → bàn vẽ đọc sai, lòng chữ đặc. Đã sửa ở `export_editor.py` (tách thành `Q` một điểm). Luôn chụp “Xem trong chữ” để kiểm khi font là .ttf.

## 4 · Quy trình đã dùng

1. Phân tích: cmap thiếu 94 chữ, không GPOS, composite có offset dấu, nét thân / nét dấu (`thickness`).
2. Máy chặn pypi → `tools/quick_vn.py` (fontTools + numpy + Pillow + scikit-image): VER 1 mặc định, VER 2 `--cfg {"stack_place":"top"}`.
3. `stamp.py` → “VFK - <tên gốc>”, watermark VFK.
4. Trang: `ttf2otf.py` cho bản dựng + font gốc → `nghieng/export_hornui_italic.py … 0` (khung kéo) + `export_editor.py` (bàn vẽ); VER 1 vào `r1/vers/VER 1/`.

## 5 · Sai lầm đã gặp

- Dấu hỏi quá nhỏ và quá đậm ở bản đầu (cao 1,25 × dấu sắc, dày = dấu sắc).
- Bàn vẽ hiện glyph vỡ vì không tách `qCurveTo` nhiều điểm của .ttf.
- Tự ghi số đo “rộng thêm” trước khi đo — luôn đo bằng hmtx rồi mới ghi lên trang.
- Dấu chữ hoa chép theo chữ ghép sẵn của font → Ứ thấp (chìm như Ú gốc), Ủ cao (đặt theo chữ A). Người dùng: “sửa lại nhớ đồng bộ”.

## 6 · Khi KHÔNG áp dụng

- Font viết tay có tương phản (bút lông, calligraphy): dấu hỏi phải theo thanh–đậm (`hook_stroke.py`), không dùng nét đều.
- Font có GPOS mark / mkmk: dùng `anchor_marks.py` (chuỗi dựng chính).
- Font nghiêng thật: một trục chuẩn cho cả font (`tools/nghieng/`).

---
*build by @nhatmotion*
