# Kinh nghiệm Việt hoá: Sans đậm bo tròn

> build by @nhatmotion

**Đặc điểm nổi bật:** chữ không chân, rất đậm, đầu nét bo tròn, xếp sát nhau tới mức chữ tràn ra ngoài khung của mình.

**Mã loại:** `sans.heavy.rounded.tight`

**Tag:** `#display` `#sans` `#heavy` `#rounded-soft` `#monoline` `#organic-outline` `#large-x-height` `#tight-spacing` `#negative-sidebearings` `#kern-dependent` `#short-vmetrics` `#cff-otf` `#upright` `#latin1-accents-only` `#stylistic-sets`

**Thẻ:** Sans đậm bo tròn | Gỡ cờ monospace sai (isFixedPitch, PANOSE) · Độ rộng CFF trừ nominalWidthX (Word) · Dấu chồng bên phải: nâng cho có khe
**Chữ nền:** sans-tron | 700

> Dùng file này khi font mới trùng nhiều tag ở trên: chữ tiêu đề, thumbnail, logo, phụ đề vui; đậm, tròn, nét đều, xếp sát. Với font serif mảnh, font chữ thân (text) hoặc font nghiêng, nhiều kinh nghiệm dưới đây **không áp dụng** (xem mục 6). Số liệu trong file là ví dụ đo trên một font mẫu 1000 UPM của loại này — gặp font khác phải đo lại.

---

## 1 · Hồ sơ điển hình của loại font

| Đặc điểm | Thường gặp (số đo ví dụ) | Ý nghĩa khi Việt hoá |
|---|---|---|
| Định dạng | CFF (.otf), 1000 UPM, vài trăm glyph | Ghi độ rộng CFF phải trừ `nominalWidthX` (mục 3.2; chi tiết lỗi ở `loi-thuong-gap.md` A1–A2) |
| Giấy phép | font thương mại bán lẻ, `fsType = 4`, metadata sơ sài | Nhắc người dùng về giấy phép trước khi sửa |
| Độ đậm | nét đứng ~120–135 / 1000 UPM, dù `usWeightClass` có thể ghi 400 | Dấu mới phải dày ~90–100 mới cân; lấy theo độ dày dấu ngã của font |
| Tương phản | gần như không (monoline), đầu nét tròn, viền hơi gợn như vẽ tay | Dấu sinh bằng nét bút đều + bo tròn hợp hơn dấu cắt sắc |
| Tỉ lệ | x-height ~75% chữ hoa (rất cao) | Ít chỗ cho dấu trên chữ thường; dấu chồng dễ đụng dòng trên |
| Khoảng cách chữ | hầu hết chữ Latin có mực tràn ra ngoài 2 biên advance (vd o −14 / +13, dấu phẩy chìa trái −15) | Font cố ý xếp sát, sống nhờ kern → mọi thứ thêm vào dễ “dính” trong app không kern |
| Kern | vài trăm cặp, có cặp rất sâu (vd T + a ≈ −180) | Word thân văn bản / Excel không kern → khác Photopea rõ |
| Thông số dọc | ascender 750, descender −250, line gap 100 | Hộp dòng thấp → dấu kép chữ hoa ló khỏi dòng |
| Trục | đứng (`italicAngle 0`) | Trục đặt dấu thẳng đứng |
| Chữ có dấu sẵn | chỉ bộ Latin-1 (à á â ã ä…), thiếu ả ạ ă ơ ư và dấu chồng | Mũ / sắc / huyền / ngã lấy từ font; hỏi, nặng, trăng, râu phải sinh mới |
| Bộ chữ thay thế | `calt salt ss01 ss02`, hàng trăm glyph `.ss` | Chữ thay thế thường không có bản Việt — chỉ Việt hoá bộ chính, nói rõ với người dùng |

## 2 · Dấu hiệu nhận ra loại font này

Có từ 4 dấu hiệu trở lên thì đọc kỹ mục 3:

1. Chữ đậm, đầu tròn, nét đều; dáng vui / mềm / “béo”.
2. Chạy `linecheck.py` thấy **hầu hết chữ Latin đã tràn biên** ngay trong font gốc.
3. Có vài trăm cặp kern với số âm lớn.
4. Hộp dòng (hhea) khoảng 750 / −250 hoặc thấp hơn.
5. Chỉ có dấu Latin-1, không có dấu Việt nào.
6. Cờ `isFixedPitch` hoặc PANOSE proportion = 9 dù font không phải chữ đều.
7. Font thương mại, metadata sơ sài (thiếu tác giả, giấy phép).

## 3 · Vấn đề hay gặp và cách xử lý

### 3.1 Metadata sai → Windows chừa trống quanh chữ
- **Triệu chứng:** Windows Font Viewer và Word để khoảng trống lớn quanh i, l, j như font chữ đều.
- **Nguyên nhân:** font gốc bật `post.isFixedPitch`, CFF `isFixedPitch`, PANOSE proportion 9 dù là font tỉ lệ.
- **Làm:** `vnfont.py` tự gỡ cả ba. Luôn kiểm ba cờ này đầu tiên.

### 3.2 Độ rộng CFF → Word chừa trống sau mọi chữ có dấu
- **Triệu chứng:** Photopea đẹp, còn Word có khoảng trống sau mỗi chữ có dấu.
- **Nguyên nhân:** charstring CFF lưu độ rộng dưới dạng **độ lệch so với `nominalWidthX`**. Word đọc CFF, còn HarfBuzz đọc `hmtx`.
- **Làm:** `T2CharStringPen(width − nominalWidthX)`, và tự kiểm CFF width == hmtx cho mọi glyph trước khi lưu. Tìm lỗi bằng số đo, đừng đoán (từng đoán nhầm nguyên nhân là chuẩn Unicode tổ hợp NFD).

### 3.3 Xếp sát + app không kern → dấu, râu, dấu câu dính chữ bên cạnh
- **Word thân văn bản (style Normal) và Excel không kern.** Word 365 chỉ bật kern sẵn cho Heading (Font → Advanced → Kerning for fonts). Với loại font này, mọi phần chìa ra ngoài 2 biên advance sẽ đè chữ bên cạnh trong các app đó.
- **Râu ơ ư** thường tràn khá nhiều (ví dụ 70 / 120). Luôn đưa 3 hướng cho người dùng chọn:
  - giữ độ rộng và dựa vào kern;
  - nới ơ ư cho râu nằm trong khung — Word không dính, nhưng dòng nhiều ơ ư dài thêm khoảng 4–7%;
  - **rút ngắn râu** (Donny Trương khuyên) và giữ độ rộng — râu vẫn tràn ít hơn (ví dụ còn 40 / 85).
- **Dấu chồng bên phải dấu mũ** (ấ ẩ ố…) mặc định đè lên mép phải dấu mũ. Phải nâng cho có khe: hỏi ≥ ~24, sắc / huyền ≥ ~18 trên 1000 UPM.
- **Dấu câu:** dấu phẩy chìa trái gặp chữ tròn chìa phải → “cổ,” dính. Sửa bằng `"sb_fix": {"comma": <LSB dấu chấm của chính font>}`. Kiểm , ; : . ’ đứng sau chữ tròn ngay từ đầu.
- **Kern Latin gốc** (T, V, Y…) không thể đồng bộ giữa các app, vì kern theo cặp không nhúng vào độ rộng được. Nói rõ với người dùng, khuyên bật kern trong style Normal của Word.

### 3.4 Hộp dòng thấp → dấu kép chữ hoa ló dòng trên
- Ascender ~750 trong khi dấu chồng chữ hoa cao tới ~1000–1035.
- Làm: `"vmetrics": "fit"` (hhea = typo = win = dấu cao nhất, line gap 0). Nói rõ dòng mặc định cao thêm khoảng 15%.
- Dấu hỏi kép đặt **bên phải** dấu mũ cho đỉnh thấp hơn đặt trên đỉnh (ví dụ 997 so với 1034).

### 3.5 Dấu hỏi trên font đậm, x-height cao
- Dấu hỏi lấy theo dáng “?” của font, nhưng nét đậm làm **lòng móc bị khít** (ví dụ chỉ 27 đơn vị), nên ở 12–16 px trông như dấu chấm.
- Nếu người dùng **đã thích một dấu hỏi** thì chỉ chỉnh nhẹ: kéo đầu nét trái ra xa thân và lên cao để mở lòng (ví dụ 27 → 33), không thay bằng thiết kế mới.
- Dấu hỏi kép: cỡ ~80%, nét ~90% — nét giảm ít hơn cỡ để không nhạt trên font đậm.
- ở ử: né râu **rất ít** (ví dụ 8 đơn vị). Né nhiều (ví dụ 30) làm dấu lệch khỏi trục rõ rệt.
- Chữ hoa: dấu hỏi dẹt ~10%.

### 3.6 Trục đặt dấu
- Font đứng → **trục thẳng đứng**. Vẽ trục nghiêng theo dáng từng chữ (vài độ) sẽ bị thấy sai. Chỉ font nghiêng mới nghiêng trục; không chắc thì hỏi.
- Đường giữa 2 biên advance **không phải** tâm thị giác. Với font tràn biên, hai đường lệch nhau vài đơn vị. Đặt dấu theo thân chữ và nói rõ con số.

### 3.7 Râu ơ ư cho font đậm, tròn
- Dáng hợp nhất là râu kiểu “kệ” (`horn.style: shelf`): cổ dày đi ngang từ đỉnh thân rồi ngóc lên đầu tròn như dấu phẩy. Nên mời người dùng vẽ mẫu rồi dựng lại cho đều nét.
- Râu ơ và ư phải cùng dáng, cùng độ cao (Donny Trương). Râu dài trên font đậm tạo khoảng hở lớn trước T / V, nên ưu tiên râu ngắn.

## 4 · Quy trình chạy tốt với loại font này

1. Phân tích file: cờ monospace, CFF, chữ Latin-1 có dấu sai (vd À mang dấu sắc), spacing âm, kern, hộp dòng.
2. Dựng bộ dấu từ dấu có sẵn (mũ, sắc, huyền, ngã) và sinh dấu mới dày theo dấu ngã.
3. Mỗi phương án là một **VER** riêng. Trang duyệt có tab VER chữ to, gõ thử zoom được, nút kern và line biên.
4. Soi ngay từ vòng đầu: `ố ấ ồ Ố Ấ`, `ẩ ể ổ Ẩ`, `ở ử`, `“cổ,”`, `Người`, `ƯT`. Soi cả cỡ lớn lẫn 12–16 px, cả bật lẫn tắt kern.
5. Đọc feedback trên trang mỗi vòng; bản sửa là VER mới.

## 5 · Sai lầm đã mắc và bài học

| Sai lầm | Bài học |
|---|---|
| Ghi sai độ rộng CFF, lại đoán nhầm do NFD | Đo trước khi kết luận; có test tự động CFF == hmtx |
| Đề xuất dấu hỏi mới khi người dùng thích bản cũ | Giữ cái người dùng thích, chỉnh nhẹ |
| Né râu quá nhiều, dấu lệch trục | Đo lệch trục trước khi chọn số |
| Vẽ trục nghiêng cho font đứng | Font đứng = trục thẳng |
| Dùng ảnh tĩnh để demo chữ | Mọi khung chữ gõ bằng font nhúng, zoom được |
| Trộn tài liệu chưa kiểm chứng với nguồn chuyên môn | Tách kho chuẩn và cẩm nang; tìm nguồn cho từng ý |
| Không soi ố ấ ồ và dấu phẩy sớm | Bộ chữ soi bắt buộc ở mục 4 |

## 6 · Khi KHÔNG áp dụng

- **Font serif / chữ mảnh / tương phản cao:** dấu mỏng, sắc / huyền nghiêng nhiều hơn; khe giữa các dấu và mọi số đo khác hẳn. Chỉ giữ quy trình, không giữ số.
- **Font nghiêng:** trục đặt dấu nghiêng theo góc chữ (`axis_slant`), dấu sinh mới phải nghiêng theo.
- **Font chữ thân (text) có spacing thoáng:** ít chữ tràn biên, nên vấn đề Word / kern nhẹ hơn nhiều; ưu tiên giữ spacing gốc.
- **Font TrueType (.ttf):** không có vấn đề CFF `nominalWidthX`, nhưng phải kiểm `glyf` và hinting khi thêm glyph.

---
*build by @nhatmotion*
