# Lỗi thường gặp khi Việt hoá font

> build by @nhatmotion

Mỗi lỗi ghi theo: **Triệu chứng → Nguyên nhân → Cách sửa → Cách kiểm**. Gặp lỗi lạ thì **đo trước, kết luận sau**. Đừng sửa theo phỏng đoán.

---

## A · Lỗi trong file font

### A1 · Word chừa khoảng trống sau mọi chữ có dấu (lỗi tự gây ra)
- **Triệu chứng:** Photopea / AE đẹp. Word có khoảng trống sau mỗi chữ có dấu, chữ trơn thì bình thường.
- **Nguyên nhân:** font CFF (.otf) lưu độ rộng trong charstring dưới dạng **độ lệch so với `nominalWidthX`**. Script dựng glyph ghi thẳng độ rộng (`T2CharStringPen(width)`) nên độ rộng CFF lệch `hmtx`. Word đọc độ rộng từ CFF, còn HarfBuzz (Photopea, trình duyệt) đọc `hmtx`, nên chỉ Word sai.
- **Cách sửa:** `T2CharStringPen(width - nominalWidthX)` ở **mọi** script ghi glyph (vnfont, addons, place_hoi, horn5…).
- **Cách kiểm:** assert độ rộng CFF == `hmtx` cho mọi glyph trước khi lưu. `vnfont.py` tự assert, các script thêm sau cũng phải làm vậy.

### A2 · Đoán nhầm nguyên nhân là NFD (bài học chẩn đoán)
- **Chuyện đã xảy ra:** khi gặp lỗi A1, lần đầu đã đoán là do chuẩn Unicode tổ hợp (NFD, chữ + dấu rời) mà Word gõ ra, rồi đi sửa `ccmp` và dấu rời. Lỗi vẫn còn.
- **Bài học:** cùng một chữ, so độ rộng đọc từ CFF với `hmtx`, và so kết quả NFC với NFD bằng HarfBuzz. Con số chỉ ra đúng chỗ lệch. Phải có test tự động cho cả hai.
- **Cách kiểm NFD thật:** shape chuỗi NFC và NFD bằng `uharfbuzz`. Cùng advance và cùng glyph ghép thì `ccmp` ổn.

### A3 · Windows để trống lớn quanh i l j như font chữ đều
- **Nguyên nhân:** font gốc bật `post.isFixedPitch`, CFF `isFixedPitch` và PANOSE proportion = 9, dù là font tỉ lệ.
- **Cách sửa:** `vnfont.py` tự gỡ cả ba. Luôn kiểm ba cờ này đầu tiên.

### A4 · `linecheck` báo tràn ở u ù ú dù nhìn ổn
- **Nguyên nhân:** `OS/2.sxHeight` của font ghi sai, ví dụ thấp hơn x-height thật cả trăm đơn vị.
- **Cách sửa:** đo x-height thật từ chữ x / o. Bỏ qua cảnh báo giả, ghi rõ số đo trên trang.

### A5 · Thiếu đ Đ sau khi dựng
- **Nguyên nhân:** `vnfont.py` không dựng đ Đ.
- **Cách sửa:** `addons.py` + `addons.json`. Thanh ngang dày ≈ nét ngang chữ E. Đo vị trí và độ dài cho từng font. Copy cặp kern của d D.

### A6 · Dấu ngã trên ĩ Ĩ tràn ra ngoài chữ
- **Nguyên nhân:** chữ i hẹp hơn dấu ngã.
- **Cách sửa:** `addons.py` thu hẹp dấu ngã theo chiều ngang cho nằm trong advance.

### A7 · Dấu phẩy dính chữ tròn đứng trước (“cổ,”)
- **Nguyên nhân:** dấu phẩy chìa trái, chữ tròn chìa phải.
- **Cách sửa:** `"sb_fix": {"comma": <LSB dấu chấm của chính font>}`. Soi , ; : . ’ cạnh chữ tròn ngay vòng đầu.

### A8 · Dấu kép chữ hoa ló khỏi dòng trên
- **Nguyên nhân:** hộp dòng (hhea / typo / win) thấp hơn đỉnh dấu chồng chữ hoa.
- **Cách sửa:** `"vmetrics": "fit"`. Nói rõ dòng mặc định cao thêm bao nhiêu %. Dấu hỏi kép đặt bên phải dấu mũ cho đỉnh thấp hơn.

### A9 · Dấu thanh chồng đè dấu mũ (ố ấ ồ ẩ)
- **Cách sửa:** nâng cho có khe. Hỏi khe ≥ ~24, sắc / huyền `stack_gap_ag` ≥ ~18 (trên 1000 UPM). Luôn dựng cả option trên đỉnh và bên phải.

### A10 · Độ rộng chữ có râu sai, râu bị cắt hoặc thừa khoảng
- **Nguyên nhân:** bounds lấy từ pathops có thể phình ra hơn nét thật.
- **Cách sửa:** đo bằng `BoundsPen` trên nét đã ghép. Độ rộng = max(độ rộng gốc, mép phải râu + 10).

### A11 · Viền râu gợn sóng
- **Nguyên nhân:** độ dày râu nội suy qua nhiều mốc smoothstep.
- **Cách sửa:** dùng một hàm đơn điệu `thin + (head − thin)·u^p`.

### A12 · Gốc râu lòi vào lòng chữ U / O
- **Cách sửa:** cắt râu ở `x0 − clip` (vd 36) và chỉ hợp nhất phần ngoài. Râu chỉ chạm chữ gốc ở **một điểm**.

### A13 · Ư Ơ không song song (lỗi nặng)
- **Nguyên nhân:** mỗi chữ có tham số râu riêng, hoặc gốc râu Ơ đặt theo vai chữ O.
- **Cách sửa:** dùng cùng một dáng. Gốc râu Ơ đặt cùng độ cao gốc râu Ư.
- **Cách kiểm:** yMax Ư = Ơ, ư = ơ. Gõ “ƯƠ TƯƠNG ươ”.

### A14 · ư dày hơn Ư
- **Nguyên nhân:** tách thông số râu hoa / thường rồi chỉnh riêng từng cỡ.
- **Cách sửa:** một bộ thông số chung, chữ thường = hoa × `lc_ratio` × `lc_wratio`.

### A15 · Chữ sau ư ơ bị hở (ươ, ưa)
- **Nguyên nhân:** advance nới để chứa râu.
- **Cách sửa:** `autokern_horn.py` (kern chỉ khép, khe tối thiểu 50). Chỉ tác dụng ở app bật kern. Word thân văn bản cần bật kern trong style Normal.
- Không tự rút ngắn râu khi người dùng đã chốt số.

### A16 · Kern Latin gốc khác nhau giữa app
- **Nguyên nhân:** kern theo cặp không nhúng vào độ rộng được.
- **Cách xử lý:** không sửa được trong font. Nói rõ với người dùng, khuyên bật kern trong Word.

### A17 · Font mẫu .ttf làm hỏng script đo
- **Nguyên nhân:** glyph TrueType có `qCurveTo`.
- **Cách sửa:** dùng `flatpoly.glyph_poly()`: làm phẳng đường cong, ghép contour bằng XOR.

### A18 · Dấu hỏi trên ả lệch phải so với ẩ
- **Nguyên nhân:** `place_hoi.py` đặt dấu hỏi đơn theo tâm khung bao thân chữ. Chân phải của chữ a kéo khung bao sang phải, nên dấu bị lệch phải, còn dấu hỏi chồng trên ẩ đặt theo dấu mũ nên thuận mắt hơn.
- **Cách sửa:** `"dx_unit": {"a": -26}` trong `hoi_place.json` (đơn vị font, đo cho từng font): dời chân dấu hỏi ả về đúng chỗ chân dấu hỏi trên ẩ. Chỉ dời, **không đổi cỡ** dấu khi người dùng đã chốt cỡ.
- **Cách kiểm:** đo x chân dấu (điểm thấp nhất của dấu hỏi) trên ả và ẩ; so luôn ẻ / ể, ỏ / ổ. Chữ khác phải không đổi.

### A19 · Dấu nặng ị Ị lệch trục ở font nghiêng (lỗi tự gây ra)
- **Triệu chứng:** ị Ị (và vài chữ khác) có dấu nặng lệch trái so với nét đứng; dấu trên và dấu dưới không cùng một đường.
- **Nguyên nhân:** đặt dấu theo **trục riêng từng chữ** lấy từ dấu mũ có sẵn (î û…). Ở font nghiêng thật (không phải xiên máy), nhà thiết kế đặt dấu mũ lệch thân tới −52 (û) / −40 (î) / +49 (Ê), và góc khai trong `post.italicAngle` (15°) khác góc nét thật (13,9°).
- **Cách sửa:** **một trục chuẩn cho cả font** (`tools/nghieng/build_italic.py`, `"axis": "body"`):
  1. Góc trục = trung vị góc tâm các nét đứng thẳng (l ı I H T E b p), không tin `italicAngle`.
  2. Trục mỗi chữ = tâm khối dải 20–80 % chiều cao trong không gian dựng thẳng (i I: tâm nét đứng) + hiệu chỉnh thị giác của chính chữ đó lấy từ bản đứng đã chốt (vd a +21, E −15).
  3. Độ lệch theo **loại dấu** là một số cho cả font (hỏi +18 / hoa +16, còn lại 0); dấu nặng cũng trên trục (trừ ỵ: dời phải tới khi cách đuôi ≥ 40, và ị — xem dưới).
  - **ị (chữ thường có chấm):** KHÔNG ép dấu nặng vào trục chung. Đo thân i trước (tâm nét đứng ở dải giữa) → so với tâm chấm i trên đầu → trục của chính chữ i là đường qua 2 tâm đó → dấu nặng đặt trên đường này ở độ cao của dấu nặng (chấm i lệch trái thân bao nhiêu thì dấu nặng cân lại sang phải). Ví dụ: thân 141, chấm i 117 → dấu nặng 165. `"i_dot_axis": "tittle"`. Ị (không chấm) giữ trục chung — đã được duyệt.
  4. Dựng lại cả chữ Việt có sẵn (á à â ã é …) cho cùng trục.
- **Cách kiểm:** `tools/nghieng/axisproof.py` vẽ chữ + đường trục đỏ; soi `ịỊạẠọỌụỤ ỉỈ ảẢ`.
- **Ghi chú:** người dùng chưa chắc một trục cho cả font là đúng tuyệt đối, nhưng muốn thử vì font đồng bộ mới đẹp. Luôn để một VER đối chiếu.

### A20 · Khe dấu huyền – dấu mũ khác nhau giữa ề và ồ (lỗi tự gây ra)
- **Triệu chứng:** cùng một cặp dấu (mũ + huyền) mà khe ở ề hẹp (26) còn ồ rộng (42); ầ lại khác nữa.
- **Nguyên nhân:** chép quan hệ dấu theo **từng chữ** của bản mẫu (bản mẫu cũng lệch: ề 45, ồ 67), cộng thêm luật "giữ dấu trong advance" đẩy dấu thanh vào trong ở chữ hẹp (e hẹp hơn a, o).
- **Cách sửa:** dấu mũ / trăng + dấu thanh là **một khối cố định**: đo vị trí dấu thanh so với dấu mũ trên a / A, rồi đặt y hệt trên mọi chữ cùng cỡ (`"even_stack": true`). Khe các chữ bằng nhau đến từng đơn vị.
- **Đổi lại:** chữ hẹp (e, o) có dấu chìa khỏi advance bên phải (ề 44, ồ 26). Ghi số này lên trang để người dùng chọn: giữ khe đều hay co vào advance.
- **Cách kiểm:** `measure.py` in cột `stack` (khe nhỏ nhất giữa 2 dấu) — mọi chữ cùng cặp dấu, cùng cỡ phải bằng nhau.

### A26 · Dấu chồng tự đặt khác hẳn cách xếp dấu của font gốc (người dùng: “tôn trọng vị trí dấu font gốc, ví dụ Ầ”)
- **Nguyên nhân:** font gốc có anchor GPOS `mark` / `mkmk`; gõ tổ hợp (A + ̂ + ̀) trình duyệt xếp dấu huyền TRÊN dấu mũ đúng khe nhà thiết kế định. Kit lại tự đặt dấu chồng bên phải, co 0,78.
- **Cách sửa:** luật `src-marks` (xét dấu font gốc trước) + `anchor_marks.py`. Phân tích mục 1 phải in danh sách lookup GPOS (mark / mkmk có không).
- **Cách kiểm:** so VER mới với VER 0 gõ kiểu tổ hợp trên trang: dấu có sẵn trong font gốc phải trùng vị trí.

### A24 · Khe dấu mũ – dấu thanh chồng bên phải không đều (Ồ 46, còn lại 19)
- **Nguyên nhân:** `vnfont.py` chỉ NÂNG dấu thanh tới khi đủ khe; chữ rộng (O) đặt sẵn đã dư khe nên giữ nguyên.
- **Cách sửa:** sau khi nâng, HẠ từng 2 đơn vị tới khi vừa đủ khe (không thấp hơn 30 % cao dấu mũ). Khe đều tới ±1 trên mọi chữ, cả hoa lẫn thường.
- **Cách kiểm:** đo khe nhỏ nhất dấu mũ ↔ dấu thanh trên ầ ề ồ ấ ế ố ẩ ể ổ + hoa.

### A27 · Dấu chữ hoa không đều (Ứ thấp, Ủ cao, Ở sát) — người dùng 26/10
- **Nguyên nhân:** chép vị trí dấu từ chữ ghép sẵn của font gốc, mà font viết tay đặt rất lệch (khe dấu chữ hoa từ −36 ở Ú tới +96 ở Ã); dấu hỏi chữ hoa lại đặt theo đáy dấu sắc trên A (cao hơn U 132).
- **Cách sửa:** `quick_vn.py` `uc_sync` (mặc định): mọi dấu trên chữ hoa đặt cùng khe tới đỉnh chính chữ đó, trên trục phần mực 1/4 trên; đồng bộ luôn chữ ghép sẵn của font (sửa offset component). Ghi danh sách chữ gốc bị dời lên trang.
- **Cách kiểm:** đo khe (đáy dấu − đỉnh chữ) mọi chữ hoa có dấu: bằng nhau; soi `ÁÀẢÃ ÚỦỨỬỞ ÔỔỚ`.

### A28 · Dấu hỏi dày bằng dấu ngã thì lòng móc bị lấp
- **Nguyên nhân:** tăng bề dày nét mà giữ cỡ dấu → lòng móc khép lại, thành cục.
- **Cách sửa:** dày = thân dấu ngã (phân vị 75, bỏ cục mực ở chỗ bẻ nét), cao ≥ 4,4 × dày, ngang × 1,2. Dấu hỏi khi chồng giữ nguyên độ dày.

### A29 · Dấu hỏi lấy nguyên thân dấu `?` ra dáng số 2 / chữ z
- **Nguyên nhân:** dấu `?` viết tay có đuôi cong ở chân; khung xương đi hết thân nên dấu hỏi mang cả đuôi.
- **Cách sửa:** luôn có 1 VER dấu hỏi vẽ từ **nửa trên** dấu `?` (`quick_vn.py` `"hook_src": "half"`, `hook_half` 0,5).
- **Kèm:** gai mảnh lòi ra khi khớp đường cong mảnh nhỏ (dấu bị đặt lệch vì khung bao phình) → so khung bao đường cong với đa giác, lệch > 1,5 đv thì giữ đa giác.

### A30 · Word cắt đỉnh dấu chồng chữ hoa (win thấp hơn mực) — người dùng bổ sung 26/10
- **Nguyên nhân:** win được nâng theo khung lúc dựng bước đầu; bước sau (anchor_marks, đổi khe / cỡ dấu) đẩy dấu chồng cao hơn mà không ai nâng lại win. Trang duyệt (trình duyệt) không cắt theo win nên không thấy.
- **Cách sửa:** `tools/winfix.py` chạy CUỐI `build.sh` / `build_ver.sh` (cả bản .ttf): win ≥ mực thật, không đụng typo / hhea. Ghi đúng chữ cao nhất ĐO ĐƯỢC lên trang + `test-tieng-viet.txt`, không đoán.
- **Cách kiểm:** `winfix.py FONT --check` (mã 1 = lỗi). Chi tiết, giải phẫu dấu chồng, 3 bộ số dọc: `loi-font/dau-chong-chu-hoa-vuot-dong.md`.

### A25 · `linecheck.py` lỗi NaN với font .ttf
- **Nguyên nhân:** đọc thẳng `qCurveTo`. **Cách sửa:** đổi đường cong bậc 2 sang bậc 3 trước khi đo.

### A21 · `addons.py` lỗi `AttributeError: PairSet` (font có GPOS mark / mkmk)
- **Nguyên nhân:** vòng lặp kern đi qua mọi lookup GPOS; lookup MarkBase / MarkMark cũng có `Format == 1` nhưng không có `PairSet`.
- **Cách sửa:** chỉ xử lý lookup PairPos (`LookupType == 2`, kể cả bọc Extension). Đã sửa trong `addons.py`, `nghieng/build_italic.py`, `nghieng/hornkern.py`. Font có sẵn đ Đ thì `addons.py` không đụng kern của chúng.

### A22 · Font .ttf: chữ ghép (composite) bị ngược chiều contour sau khi đổi sang CFF
- **Triệu chứng:** kiểm chiều contour báo sai ở Á À Â… (glyph composite), chữ mới ghép từ thân â ê ô cũng sai theo.
- **Nguyên nhân:** `ReverseContourPen` chuyển thẳng `addComponent` xuống pen bên trong nên phần component không bị đảo.
- **Cách sửa:** `ttf2otf.py` tách composite bằng `DecomposingRecordingPen` trước khi đảo chiều.
- **Cách kiểm:** chỉ còn đúng các glyph vốn đã chồng nét trong font gốc (vd ç ş) báo sai chiều.

### A23 · `export_preview.py` không tìm thấy chấm chữ i
- **Nguyên nhân:** lọc chấm i bằng số cứng (y > 640) theo font cao; font x-height thấp có chấm i ở 605–710.
- **Cách sửa:** chấm i = contour nằm trên đỉnh thân i (đo trên chính font).

---

### A31 · Cờ bảng mã tiếng Việt (code page 1258) — nên có, nhưng KHÔNG phải nguyên nhân lỗi `serif.regular.condensed.contrast.ttf` VN (xem A32)
- **Ghi chú 27/10:** sửa cờ này trước (bản 1.015) mà Word vẫn lỗi → nguyên nhân thật là USE_TYPO_METRICS (A32). Vẫn giữ cờ cho đúng chuẩn.
- **Triệu chứng (giả định ban đầu):** Word gõ bằng bàn phím tiếng Việt thì chữ có dấu bị đổi sang font khác.
- **Nguyên nhân:** OS/2 `ulCodePageRange1` thiếu **bit 8 = Vietnamese (1258)**. Word đọc bit này để biết font có hỗ trợ tiếng Việt hay không ([MS-OE376: “Bit 8 in csb0 is defined as the Vietnamese code page”](https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oe376/53c33204-2806-48a2-8800-5fc488580734)). Chữ, nét, hinting đều đúng.
- **Cách sửa:** `winfix.py FONT` tự bật bit 8 + dải Unicode 1, 2, 6, 29 khi font đủ chữ Việt. Gửi bản sửa thì tăng `head.fontRevision` + name ID 3 / 5. Người dùng: gỡ bản cũ → tắt hẳn Word → cài bản mới → mở lại (Word nhớ font theo tên trong phiên chạy).
- **Cách kiểm:** `winfix.py FONT --check` phải ✓ cả dòng “cờ tiếng Việt” lẫn dòng win trước khi xuất.

### A32 · Word cắt dấu thanh trên dấu mũ / trăng chữ hoa: gõ “NGUYỄN” ra “NGUYÊN”, Ấ mất sắc (người dùng 27/10, `serif.regular.condensed.contrast.ttf` VN)
- **Triệu chứng:** Premiere, web, Canva hiện đủ dấu. Word mất dấu thanh của đúng 16 chữ ẤẦẨẪ ẮẰẲẴ ẾỀỂỄ ỐỒỔỖ (dấu nằm trên dấu mũ / trăng của chữ hoa). Ậ Ặ Ệ Ộ (dấu nặng dưới) vẫn đủ. Font khác (Shadows) gõ ở Word bình thường.
- **Cùng họ lỗi** `loi-font/dau-chong-chu-hoa-vuot-dong.md` (dấu chồng chữ hoa vượt dòng) — lần trước chỉ nâng win, sót bit 7.
- **Nguyên nhân:** OS/2 `fsSelection` bit 7 **USE_TYPO_METRICS** bật → Word lấy đỉnh / đáy dòng từ typo (990) thay vì win (1180) → phần mực vượt typo bị cắt. **Lỗi của kit:** `vnfont.py` tự bật bit này (“giữ khoảng dòng”) trong khi chỉ nâng win. `hand.marker.monoline.ttf-legacy` không dính vì đi đường `quick_vn` (bit tắt, typo = hhea = win = 1298).
- **Cách sửa:** tắt bit 7 khi typo thấp hơn mực (Word chuyển sang win đã nâng). Đã sửa `vnfont.py` (không bật nữa, font gốc có bật thì tắt) + `winfix.py` (tự tắt, `--check` báo ✗ kèm danh sách chữ bị cắt). Tác động: Word trên Windows dòng mặc định cao hơn (dùng win); Mac / web / Premiere giữ nguyên.
- **Cách kiểm:** `winfix.py FONT --check` phải ✓ dòng USE_TYPO_METRICS; `hintcheck.py FONT` 0 lỗi (lỗi 0x86 ở .notdef ª º ™ − của `serif.regular.condensed.contrast.ttf` VN: bỏ lệnh hinting glyph đó). Trong GSUB không để một nhóm ngôn ngữ khai cùng tính năng 2 lần (vnfont thêm `ccmp` thứ hai → gộp).

### A33 · Hợp nét râu (union) thất bại — ra 326 contour (font nghiêng .ttf, máy không có pathops)
- **Triệu chứng:** `build_it.py` báo `horn union failed u 326`; Ư ra 2 contour.
- **Nguyên nhân (đo được, không phải đoán):** tách đoạn râu bằng cách so contour ư (bản đứng VN) với contour u trơn, lấy mẫu viền u bằng hàm làm phẳng **chỉ lấy điểm đầu của đoạn thẳng** → cả thân thẳng của u bị coi là “xa viền” → gần như CẢ contour bị nhận là râu → râu và thân có cạnh **trùng nhau** → phép hợp nét chia nhỏ vô hạn, nối loạn. Không phải do vector râu chui vào thịt chữ.
- **Cách sửa:** lấy mẫu viền DÀY đều theo độ dài (`geom.dense`, ≤ 1,5 đv, cả đoạn thẳng); ngưỡng “xa” 8 đv (cu2qu làm lệch 1–3 đv); râu = **cụm** đoạn xa lớn nhất (cho hở ≤ 3 đoạn), không phải “mọi đoạn xa”.
- **Cách kiểm:** debug vẽ hình kín của râu (đỏ) trên thân (đen) trước khi hợp nét; số contour sau hợp nét = số contour chữ trơn.

### A37 · Cắt thân chữ để ghép râu (bỏ đuôi serif Ư) — người dùng: “còn tệ hơn cách cũ” (27/10)
- **Luật chốt:** râu là **HÌNH RIÊNG**, gốc **đâm sâu vào thịt chữ** (~0,45 thân, 31–34 đv trên 1000 UPM); **thân chữ giữ nguyên** (không cắt serif, không luật cứng sửa nét). Font tĩnh: hợp nét (union) thân + râu; lỗ nhỏ khép giữa râu và serif thì lấp. Bàn vẽ / Chi tiết: râu là hình rời (`horn*`), gốc nằm trong thân.
- **Râu chép từ bản đứng:** đầu, cổ, đuôi (chỗ nhập thân) giữ đúng đường cong + độ dày của bản đứng, chỉ nghiêng theo trục.
- **Đuôi râu (phần chìm trong thân) — người dùng hỏi “đã soi đuôi vector của móc Regular chưa?”:** font Regular VN đã GỘP râu vào thân nên phần đuôi chìm không còn trong file; phải dựng lại theo cách kit vẽ râu (horn5: đường tâm đi tiếp vào thân với nét mảnh của cổ, cắt bằng đường song song trục cách gốc `clip` 36). Đừng chụm thành nêm (VER 4) — ở bàn vẽ nhìn như gai. `build_it.py`: 2 mép cổ kéo dài theo tiếp tuyến, cắt song song trục (`horn_clip` 36, thường × 0,9). Nếu đuôi theo cổ để hở túi với serif (Ư) thì font gộp bằng nêm gốc, bàn vẽ vẫn giữ đuôi theo cổ (phần chìm, không thấy).
- Thay cho cách A34 bên dưới (cắt ghép theo giao, bỏ đuôi serif) — chỉ dùng A34 khi người dùng muốn bỏ serif.

### A34 · Ư: râu dính ở mép đuôi serif — mấu nhỏ, gai, hoặc lỗ hổng (người dùng 27/10: “để phần râu đè lên phần thịt tip Ư”)
- **Triệu chứng:** (1) hợp nét giữ đuôi serif phải → mấu nhỏ lòi dưới chân râu, hoặc mép dưới râu + đuôi serif + thân **khép thành lỗ** (union ra 2 contour); (2) cắt ghép theo **điểm gần nhất** → gai / cắt mất thân khi râu dời.
- **Nguyên nhân:** chân râu của bản đứng đặt đúng mép serif; sang bản nghiêng, serif và thân lệch vài đơn vị → chân râu chỉ CHẠM thịt chữ ở một mép mỏng, chưa đè lên.
- **Cách sửa:** `splice()` cắt ghép theo **giao điểm thật** (giao đầu tiên dọc râu = rời mép trên serif, giao cuối = mép dưới râu nhập mép phải thân) → bỏ hẳn đuôi serif dưới râu (như bản đứng); **dời râu vào trong** (`horn_shift` U ≈ −18 đv) để chân râu đè lên phần thịt của đuôi serif / đầu thân. Giữ đỉnh Ư = Ơ (chỉ dời ngang).
- **Cách kiểm:** vẽ phóng to vùng nối (x ±150 quanh mép phải thân, y từ cap − 160 tới đỉnh râu); 1 contour; không còn mấu dưới chân râu.

### A35 · Dấu đặt sát nhau — cỡ nhỏ dính thành cục (người dùng 27/10)
- **Triệu chứng:** ờ (khe dấu huyền ↔ râu 35), ỡ (29), Ỡ (40); dấu bên phải dấu mũ (VER 1A) 21.
- **Nguyên nhân:** luật cũ chỉ đòi khe ≥ 28 với râu; dấu bên phải đặt sát cho gọn.
- **Cách sửa:** khe tối thiểu ≈ **0,75 nét dấu** (nét dấu sắc / huyền đo bằng đường tròn nội tiếp; font serif mảnh 1000 UPM: 75 → khe 55). Dấu thanh ↔ râu: dời trái ≤ 40 rồi nâng (`horn_tone_gap`); dấu bên phải dấu mũ: đẩy CHÉO lên-phải (không đẩy ngang — chữ hẹp sẽ đè sang chữ sau).
- **Cách kiểm:** `tools/nghieng/tt/measure_gaps.py FONT` — cột mark-mark và mark-body, mọi số ≥ khe tối thiểu.

### A36 · Chữ dựng mới bị dời trái khi gõ — lsb ≠ xMin (font .ttf, lỗi tự gây ra 27/10)
- **Triệu chứng:** chữ Việt dựng mới đứng lệch trái 13–40 đv so với chữ gốc (ẢÃ sát nhau); `export_editor.py` báo “đồng bộ lại 96” dù recipe đúng; kern sau râu tính sai.
- **Nguyên nhân:** ghi glyph TrueType mới với `hmtx = (advance, 0)`. FreeType, Chrome, Word đặt chữ theo lsb: lsb ≠ xMin thì cả chữ dời đi (xMin − lsb). fontTools `getGlyphSet()` cũng dời theo nên mọi phép đo sau đó lệch cùng chiều — Pillow / trình duyệt hiện “đẹp” nên không ai thấy.
- **Cách sửa:** `hmtx[name] = (advance, glyf[name].xMin)` sau `recalcBounds`; công cụ `tools/fixlsb.py FONT` sửa font đã dựng. `kiemword.py` có mục 8 “lsb = xMin” (`--fix` tự gọi fixlsb).
- **Cách kiểm:** `fixlsb.py FONT --check` → 0; `export_editor.py` “đồng bộ lại 0”.

## B · Lỗi trên trang duyệt (artifact)

| Triệu chứng | Nguyên nhân | Cách sửa |
|---|---|---|
| Ô xám không chữ ở nền tối | Nút hard-code `background:#fff`, chữ kế thừa màu trắng | Dùng token `--pg-card` / `--pg-txt` |
| Thanh công cụ bàn vẽ đè lên danh sách dấu khi cuộn | Phần tử sticky nằm trực tiếp trong lưới cả khối, nên dính suốt chiều cao | Bọc thanh + khung vẽ vào `.ed-left`, sticky chỉ trong khối đó |
| Nút tắt trông như bị khoá | Nút tắt dùng gạch ngang | Tắt = xám mờ; bật = tô đặc đảo màu |
| Hai đoạn râu chồng nhau bị “khoét” | Nhiều subpath chồng trong một `<path>` (fill-rule) | Mỗi đĩa / tứ giác là một `<path>` riêng |
| Ký tự không hiện trong khung kéo (· … “ ”) | Bộ ký tự xuất thiếu dấu câu | Thêm vào charset của `export_preview.py` |
| Dấu trên chữ hoa bị cắt mất đầu | Khung SVG thấp | ASC / LH = 1300 / 1640 |
| Trang tràn ngang trên điện thoại | Cột lưới `1fr` co theo nội dung | `minmax(0, 1fr)` và `min-width: 0` |
| Style bàn vẽ hỏng | Trùng tên class (`.ed-why`) | Đặt tên riêng (`ed-whyd`) |
| Test báo lỗi ở phần thu gọn | Phần tử nằm trong `details` đóng | Mở hết `details` trước khi chụp / test |
| Tách dấu thanh làm chữ a đen kín lòng | So contour theo điểm đầu, lòng chữ a bị coi là dấu | So theo **khung bao ±3**. Riêng ì í ỉ ĩ Ĩ tách theo độ cao |
| Dời dấu sắc ở ấ Ấ kéo theo cả dấu mũ | Ở chữ dấu chồng, dấu mũ / trăng đã bị dời nên không trùng khung chữ bỏ dấu | Khi có nhiều contour lạ, giữ contour có tỉ lệ rộng / cao gần dấu thanh của á Á nhất (`tone_split.py`) |
| Nút ↺ reset cả khung | Thiết kế cũ | ↺ riêng từng thanh, lùi từng bước; hoàn tác nhiều bước cho cả khung |
| Thẻ quyết định lỗi | Nhãn dài quá 40 byte | Rút ngắn nhãn |
| Bàn vẽ hiện “đ” không có thanh ngang, “ị” mất chấm i | Dữ liệu bàn vẽ (recipes) lấy nét tĩnh từ **chữ gốc trơn** (d, ı) thay vì phần thân đã dựng của chính glyph | Nét tĩnh = đúng phần thân đã dựng; **kiểm tự động**: ghép recipe (nét tĩnh + dấu) phải ra đúng số contour và khung bao của glyph trong font, lệch thì dừng không publish |
| Bỏ mục B (khung kéo) vì thiếu thư viện | Script xuất dữ liệu khung kéo cần shapely | **Không được bỏ mục B.** Xuất dữ liệu bằng cách khác (`tools/nghieng/export_hornui_italic.py` chỉ cần fontTools); font nghiêng: dữ liệu ở không gian dựng thẳng + `D.slant` |
| Đổi VER ở mục A thì khung chữ giật (tab xuống dòng, chữ reflow, font nháy) khó so | Tab ngang + khung chữ tự xuống dòng | `verspec2()`: menu xổ bên trái, khung xem cố định bên phải, không reflow, nạp sẵn mọi font |
| Đổi vị trí dấu giữa 2 VER mà người dùng phải so 2 tab bằng mắt | Không có lớp “vị trí cũ” | Vẽ lớp nét đứt VER trước (bật / tắt) ở bàn vẽ, khung kéo, ảnh đo |
| Thanh đ Đ chồng lên thân (font tĩnh) | Ghép thanh là contour rời | Gộp nét: nối thanh vào cạnh nét đứng (`bar_splice` trong `build_italic.py`, không cần pathops). Kiểm: `overlapcheck.py` phải báo “không có”; ảnh trước / sau giống nhau 0 điểm ảnh. Font biến thiên thì giữ nét chồng ở master, chỉ gộp khi xuất bản tĩnh |
| Bàn vẽ / “Xem trong chữ” hiện râu cũ chồng lên thân (vệt dư), dấu hỏi lệch, vẽ xong không thấy đổi | Recipe của vnfont là bước giữa; place_hoi dời dấu hỏi, horn5 ghép râu mới vào thân sau đó | `export_editor.py` đồng bộ recipe với glyph thật (contour trên đỉnh / dưới chân = dấu, tính lại phép biến đổi; râu ghép vào nét tĩnh). Kiểm: dòng in “bỏ 0” |
| Danh sách nhóm bút bị khung vẽ che, bấm không được | Thanh công cụ `position: sticky` tạo lớp riêng, khung vẽ đứng sau trong DOM vẽ đè | `.ed-bar{z-index:6}`, danh sách `z-index:40` |
| Đồng bộ recipe gán nhầm dấu (dấu huyền nhận thành dấu mũ) khi dấu đã dời hẳn chỗ | Gán contour theo vị trí dự đoán | Gán theo **tỉ lệ khung so với dấu gốc chưa co** trước, vị trí sau (`export_editor.py`) |
| Dấu dựng bằng nhiều đĩa + tứ giác (dấu hỏi, râu) trông đậm hơn nét thật / có vệt trắng ngang | Nhiều path chồng → khử răng cưa cộng dồn; gộp 1 path thì Chrome để lộ vệt ở cạnh trùng | Một path, mọi mảnh cùng chiều (đĩa = đa giác 32 cạnh, không dùng cung 180° vì mơ hồ chiều) + viền 0,7 px cùng màu (`vector-effect: non-scaling-stroke`) |
| Đo tai g ra cổ 8 (sai) | Bộ xương lấy cả vệt mảnh ở mép cắt vùng tai | Bỏ điểm xương sát mép cắt và bề dày < 12 (`hook_stroke.py --measure-g`) |
| Khối “So vị trí cũ” ghi nhầm nút “VER 7” thành tên VER cũ | Mẫu dùng chữ “VER 7” làm nhãn VER cũ; thay chuỗi sau khi chèn nút → đè cả nút VER mới trùng tên | `mk_oldnew.py` đổi nhãn mẫu sang mã tạm trước khi chèn nút |
| Người dùng “chưa thấy thay đổi” ở VER mới | Chỉ đổi chi tiết nhỏ (đầu giọt) — ở cỡ gõ thử gần như không thấy | Đổi hướng rõ rệt, đưa 2 mức để so, chữ mẫu cỡ 72, “So vị trí cũ” mở sẵn |
| Lấy dấu hỏi từ font mẫu nghiêng cho font đứng (người dùng: “chưa xét italic ref”) | Font mẫu sai kiểu | Font đứng học từ font mẫu đứng; hỏi lại khi chỉ có bản nghiêng |
| `hook_from_ref.py` ra bầu giọt nhỏ / chân mỏng | Khung xương chạy lố ra mép bầu và mép cắt chân | Nối tâm bầu = vòng tròn nội tiếp lớn nhất nửa trái; giữ bề dày ở 88 % cho đoạn chân |
| Font .ttf: “Xem trong chữ” và khung vẽ ra glyph vỡ — lòng chữ A, o đặc, nét gãy (người dùng 26/10) | Recipe lấy contour TrueType: `qCurveTo` có NHIỀU điểm điều khiển liền nhau (điểm trên đường nằm ngầm ở giữa). Bàn vẽ chỉ hiểu `Q` một điểm điều khiển nên đọc sai | `export_editor.py` `conv()` tách mỗi `qCurveTo` thành từng đoạn `Q` (điểm giữa 2 điểm điều khiển), contour toàn điểm điều khiển thì mở bằng `M` ở điểm giữa. **Kiểm:** đếm `Q` trong editor.json phải toàn 2 điểm; chụp “Xem trong chữ” ở nền tối, so với chữ gõ bằng font thật |
| Bỏ sót góp ý trên trang (vòng 3–4, người dùng 27/10) | Chỉ đọc db khi người dùng nhắc “có fb” | Đầu MỖI lượt: `ArtifactData list fontvn` + `…-rN/glyphs` của vòng đang hiện, rồi mới làm |
| Nhóm thanh “Dấu hỏi” ở Chỉnh dấu biến mất | Đường dựng không xuất thông số dấu hỏi (`hook_params`) | `quick_vn.py` ghi `hook.params.json` (kiểu taper) + gắn vào `horn5.json`; `export_hornui_italic.py` đọc vào `hornui.json` |
| Bút vector không dời được điểm neo (người dùng 26/10) | Bấm điểm bằng bút = xoá điểm ngay (Illustrator), không có đường kéo | `editor.js`: bút bấm-kéo điểm = dời, bấm thả = xoá; giữ Ctrl / ⌘ khi cầm bút = công cụ chọn. Kiểm bằng Playwright: kéo điểm bằng bút, bằng bút + Ctrl, bấm thả = bớt 1 điểm |
| Chụm 2 ngón / lăn chuột phóng chữ bị khựng, “không ăn” (người dùng 27/10) | Dựng lại chữ (đổi font-size, vẽ lại SVG) ở MỖI lần ngón di chuyển; pointer events bị trình duyệt huỷ khi ngón thứ 2 chạm | Trong cử chỉ chỉ đổi CSS `transform` (GPU, rAF), nhả tay mới dựng lại ở cỡ thật + chỉnh scroll giữ điểm neo; chụm bằng touch events `passive:false`. Máy tính thêm bấm-kéo = kéo khung, bấm đúp = phóng (`vkZoom`) |
| Phóng chữ làm khung xem giãn cao / co lại (người dùng 27/10: “khung preview giữ giá trị mặc định”) | Khung cao theo nội dung (`height: auto`), chữ to thì khung to theo | `vkZoom` khoá chiều cao khung = cỡ mặc định ở cử chỉ đầu (`height` + `max-height` + `overflow: auto`); chữ phóng bên trong, kéo / cuộn để xem phần ngoài |
| Khung Chỉnh dấu nền trắng, chữ đen khi bật chế độ tối (người dùng 27/10) | `slider_ui.html` tô cứng `background:#fff`, `<g fill="#111">`, `stroke:#111` | Nền `var(--pg-card)`, chữ `fill="currentColor"` + `color: var(--pg-txt)`; soi mọi khung xem ở chế độ tối trước khi gửi |
| Thành phần mới “tự mặc” CSS của khung trang cũ (h1, code, .sec, .fbold font Inter…) (người dùng 27/10) | Trang ghép nhiều khối `<style>`; bộ chọn chung / cùng tên class của `tpl/styles.css` chạm cả thành phần Việt Font Kit | `@layer vk-legacy` cho CSS cũ + `tools/vk_own.css` (CSS riêng, `:where(.vk)`); so computed style trước / sau bằng `snap_css.js` + `cmp_snap.py` |
| Chế độ tối mà nền trang trắng, chữ trắng — mọi tab (người dùng 27/10, ngay sau khi tách CSS) | Khung artifact chèn `body{background:#fff;color:#000}` KHÔNG layer; luật `body{background:var(--pg-bg)}` đã bị đưa vào `@layer vk-legacy` nên thua. Thử trên file cục bộ (không có khung) không thấy lỗi | `tools/vk_base.css` (luật `:root/html/body`, không layer). Test luôn trên bản `HOST_OUT` giả lập khung artifact |
| Phóng xong bấm-kéo không xem được phần bị cắt (người dùng 27/10, Mac) | Bấm-kéo trên chữ = bôi đen; Safari tự cuộn theo vùng bôi đen, giành cuộn với tay kéo | `preventDefault` ở pointerdown (chuột, trừ ô nhập / nút) + `user-select:none` trên khung; thêm `gesture*` cho chụm touchpad Safari |
| Sửa lan sang chữ không được yêu cầu (người dùng 27/10: dấu sắc ắ Ắ đổi chỗ ở VER 8 rồi đổi lại ở VER 9) | `stack_dx {"acute": 40}` áp cho MỌI dấu sắc chồng, kể cả trên dấu trăng; VER sau bỏ số đó thì ắ Ắ lại về chỗ cũ — cả hai lần đều không hỏi | Chạy `tools/glyphdiff.py` giữa VER cũ / mới với `--expect` = chữ trong yêu cầu; chữ ngoài danh sách → hỏi người dùng trước. Luật theo nhóm dấu nên giới hạn bằng điều kiện (vd chỉ `bk == "circ"`) |
| Khung info (nút i) nhảy lên cao, xa nút (người dùng 27/10) | `.info-pop` `position:absolute` nhưng không cha nào định vị → neo vào `body`, `top:100%` = đáy trang tính ngược | `.h2row{position:relative}`, khung neo ngay dưới hàng tiêu đề (`left:0`, rộng ≤ 640). Thành phần nổi (popover) luôn có cha `position:relative` của chính nó |
| Chụm 2 ngón trên điện thoại không phóng được nữa (người dùng 27/10, sau khi thêm chụm touchpad Safari) | iPhone / iPad cũng phát `gesturestart/gesturechange` song song với touch events; handler gesture chốt lần phóng của touch rồi `begin(clientX undefined)` → toạ độ NaN, phóng hỏng | Đang chạm (`TT > 0`) thì gesture* chỉ `preventDefault` rồi bỏ qua; `begin` / `upd` từ chối số không hợp lệ. Test giả lập iPhone: touch 2 ngón + gesture* không clientX (`t_ios.js`) |
| Chụm 2 ngón ở Chỉnh dấu / Bàn vẽ lúc được lúc không (người dùng 27/10, điện thoại) | Nghe touchstart trên chính khung; khung nhỏ (Bàn vẽ ~70 px) → ngón thứ 2 rơi ra ngoài khung, khung không nhận sự kiện 2 ngón | Một bộ nghe touch cho CẢ TRANG (`vkTouch`, capture): chỉ cần 1 ngón nằm trong khung là phóng khung đó. Test `tools/t_ios.js` có ca ngón 2 ngoài khung |
| Chụm 2 ngón trên khung vẽ của Bàn vẽ thành khung chọn / chấm điểm bút (người dùng 27/10) | Bàn vẽ dùng pointer events: ngón 1 chạm là bắt đầu thao tác ngay, không biết ngón 2 sắp tới | `editor.js`: ngón 1 chạm → chụp trạng thái; ngón 2 chạm → huỷ thao tác ngón 1 (trả nét, lịch sử hoàn tác, vùng chọn, bút về như cũ) rồi phóng / kéo khung quanh điểm giữa 2 ngón; thả bớt ngón thì ngón còn lại không vẽ tiếp. Test `tools/t_edpinch.js` |
| Chụm 2 ngón ở Chỉnh dấu trúng một chữ → nhảy sang Bàn vẽ, phóng khựng (người dùng 27/10) | Bấm 1 lần vào chữ = mở Bàn vẽ; chạm trong lúc chụm cũng tính là bấm | Máy tính: bấm đúp mới mở; điện thoại: chạm chọn rồi chạm lần nữa; chạm nhiều ngón / vừa chụm / có kéo không tính. Khung bao dùng màu chữ của trang (nổi trên nền tối) |
| Xem trước · Văn mẫu: phóng lên thì chữ xuống dòng khác hẳn; khung Đồng loạt không phóng được (người dùng 27/10) | Phóng = đổi cỡ chữ thật, khối chữ vẫn rộng bằng khung → dòng ngắt lại; Đồng loạt chưa gắn `vkZoom` | `vkZoom(..., {wrap:true})` giữ bề rộng theo tỉ lệ + khoảng cách ngang `calc(*var(--vkz))`; khung mới nào có chữ cũng phải gắn `vkZoom` (khung cuộn riêng, chip trạng thái nằm ngoài) |
| Cột phải Xem trước (điện thoại) có khoảng trống + 2 đường kẻ giữa Tên font xuất và Font mẫu (người dùng 27/10) | Hàng nút kern / line biên vẫn chiếm chỗ (gap 16 px) dù cả 2 nút ẩn ở Văn mẫu; `.vk-out` kẻ dưới + `.vk-ref` kẻ trên | Ẩn hàng khi mọi nút con ẩn (`:has`), bỏ cả 2 đường kẻ (người dùng muốn không kẻ ngang). Ẩn nút nào thì xem hàng chứa nó có thành hàng trống không |
| Bản Pro: mới mở không có nút, ~8 s sau nút “Xuất chỉnh sửa” hiện ra (người dùng 27/10) | Hẹn giờ dự phòng gọi `ok(useLocal())` — `useLocal()` chạy (bật giao diện Free) TRƯỚC khi `ok` kiểm tra đã quyết chưa | Hẹn giờ / nhánh lỗi gọi `local()` = `if (!done) ok(useLocal())`. Test `t_free.js` chờ 13 s rồi kiểm tra Pro vẫn không có nút |
| Nút tải file trên trang artifact không làm gì (cảnh báo khi xuất bản) | Khung artifact không cho trang tải file bằng link blob / data: | Dùng capability `downloads` (`save({filename,data})`); không có thì chép đoạn chữ + hộp chép tay. Khai `downloads:true` trong capabilities |
| Bản Free: tải lại trang thì thanh Đồng loạt về 0 dù đã lưu (người dùng 27/10, lúc làm chế độ Free) | db lưu trên máy sẵn sàng ngay (microtask) → script Đồng loạt đọc db trước khi trang khai báo `window.__FV_EDDOC` → đường dẫn rỗng, bỏ qua | `vk_localdb.js` trả db sau `DOMContentLoaded`. Mọi db giả lập / dự phòng phải trả bất đồng bộ sau khi trang đọc xong |
| Ô nhập góp ý ở Xem trước biến mất sau khi bỏ một khối trong `VK.panel('xem', …)` (người dùng 27/10) | Sửa dòng biểu thức dài bằng `sed 's|….*$|…|'` → cắt luôn đuôi dòng `+ '<div class="notewrap" data-note="V"></div>' if not NOFONT else VK.nofont())` | Bỏ khối thì chỉ thay đúng đoạn đó, không xoá tới cuối dòng; sau mỗi lần sửa content_*.py đếm `data-note=` trong trang: phải đủ **V, R, C** |
| Chú giải (legend) biến mất ở Chỉnh dấu sau khi thêm `hidden` cho ô Chữ mẫu | `slider_panel` chèn LEGEND bằng regex khớp đúng chuỗi `<div class="hu11-txt">` — thêm thuộc tính là trượt, không báo lỗi | Regex khớp `<div class="hu11-txt"[ >]`; test `t_lgd.js` sau mọi sửa markup `slider_ui.html` |
| Khung kéo / bàn vẽ ở mục ẩn vẽ sai cỡ khi mở | Đo kích thước lúc mục đang `hidden` (rộng 0) | Ẩn mục SAU khi mọi script chạy (`TAIL_JS` cuối trang); mở mục thì phát `resize`, Bàn vẽ mở lần đầu bấm “vừa khung” |
| Khối có class `display:flex` vẫn hiện dù `hidden` | CSS class thắng thuộc tính `hidden` khi không có reset | `[hidden]{display:none!important}` trong CSS trang |
| `export_editor.py` lỗi `NoneType … glyphSet` với .ttf | Pen không có glyphSet nên không tách được chữ ghép (composite) | Pen nhận `gs` để tự tách composite |
| Chỉnh dấu · Chi tiết khác Xem trước: râu ơ ư khác dáng, có vệt cắt ở gốc (người dùng 27/10) | Chi tiết vẽ râu bằng CÔNG THỨC horn5 (bộ thông số mẫu) + cắt bằng clipPath, còn font thật có râu chép từ bản đứng | `export_hornui_italic.py` xuất nét thật chữ có râu (`rd`, `rm`, `rw`); `slider_ui.html` vẽ nét thật khi thanh râu chưa đổi (`hornDef()`), chỉ khi kéo thanh râu mới chuyển sang công thức |
| Bấm vào thanh / nhóm dấu ở Chi tiết phải chờ mới đổi màu (người dùng 27/10) | Mỗi lần đổi “dấu đang chỉnh” gọi `renderText()` dựng lại cả khung (~5 000 phần tử SVG) + báo Bàn vẽ dựng lại | Tô đỏ bằng class `hk-<loại>` + 1 thẻ `<style>` (`applyHL()`), không dựng lại; chỉ dựng khi số thay đổi. Đo bằng `tools/t_chitiet_speed.js` |
| Thẻ thanh kéo Đồng loạt nằm cao hơn khung xem (ngang hàng tab loại dấu); thẻ Chi tiết thấp hơn 10 px (người dùng 27/10) | Thẻ đặt cạnh cả khối (tab + khung) / hàng công cụ ẩn vẫn chiếm `gap` | `vkAlign()` (VK.JS) căn đỉnh thẻ = đỉnh khung xem khi 2 cột; hàng công cụ toàn ô ẩn thì `display:none`. Thẻ Chi tiết dùng cùng kiểu thẻ Đồng loạt (tiêu đề trong thẻ, nhãn 1 dòng, ô số 52 px không mũi tên) |
| Mở thẻ Kinh nghiệm bị giật (người dùng 27/10) | `backdrop-filter: blur` toàn màn hình dưới hộp thoại đục + thêm class trong cùng khung hình (không có trạng thái đầu) + thanh cuộn biến mất làm trang nhảy ngang | Bỏ blur, `void OV.offsetWidth` trước khi thêm `.in`, chỉ animate opacity + transform 0,22 s, `scrollbar-gutter: stable` |
| Viên thuốc VER xuống dòng thì nằm sát phải (người dùng 27/10) | `.vk-vers{margin-left:auto}` | Bỏ `margin-left:auto`, VER đứng ngay sau tab, xuống dòng thì bắt đầu từ trái |
| Publish trang lỗi “must be HTML (text/plain)” | `build_page.py` ghi trang mở bằng `<meta>`, không có `<!DOCTYPE html>` | `build_page.py` tự chèn DOCTYPE |
| `itest6.js` treo (chờ `#vv .vtag`) | Test của bố cục cũ (verspec2) | Bố cục Việt Font Kit dùng `tools/t_shots.js` (Chỉnh dấu 2 chế độ, mở thẻ Kinh nghiệm, nút line biên, lỗi trang) |
| Bàn vẽ / Chi tiết: râu ơ ư thành một khối dính thân, không tô đỏ được khi chọn nhóm Râu (người dùng 27/10) | Font gộp râu vào thân (đúng cho font tĩnh) nhưng dữ liệu trang lấy luôn nét đã gộp | `build_it.py` giữ bản tách: thân (Ư bỏ đuôi serif) + râu hình kín riêng (dấu `horn`, `horn_u`, `horn_O`, `horn_U`); `export_editor.py` chấp nhận thừa 1 contour / râu; `export_hornui_italic.py` (`RECIPES=`) xuất `rh` → Chi tiết vẽ râu riêng, tô đỏ được |
| Khung xem có thanh cuộn ngang / dọc dù đã kéo được kiểu Google Maps (người dùng 27/10) | Thanh cuộn mặc định | `.vk-zoomable{scrollbar-width:none}` + `::-webkit-scrollbar{display:none}` — vẫn cuộn / kéo được |
| Bàn vẽ: trục chữ (đường đứt chéo) lệch hẳn sang trái ở chữ dựng mới (người dùng 28/10) | `build_it.py` ghi `sax: [0, tan]` → trục đi qua gốc toạ độ x = 0 | `sax[0]` = x tại đường chân chữ của trục qua anchor dấu trên chữ gốc (`ax − ay·tan`); sửa file cũ bằng `tools/nghieng/tt/fix_sax.py SRC recipes.json` |
| Bàn vẽ giật khung liên tục (người dùng 28/10, ngay sau khi căn thanh công cụ / kéo dài khung vẽ) | `vkAlign()` đặt lề về 0 rồi đo lại, và công thức chiều cao khung vẽ tính từ chiều cao GỐC thay vì chiều cao HIỆN TẠI (`2·h0 − cur + lệch`) → lần sau co lại, lần sau nữa giãn ra; mỗi lần đổi lại phát `resize` + ResizeObserver gọi tiếp → vòng lặp không dừng | Tính từ lề / chiều cao đang có (`cur + (đáy bảng − đáy khung)`), chỉ ghi khi lệch > 1 px, không đặt lại 0. Test `jitter`: theo dõi style 3 s phải 0 thay đổi, chiều cao khung 1 giá trị |
| Đồng loạt (điện thoại): chữ bị cắt — hàng đầu bị đẩy khỏi khung, đầu dấu chồng ở câu mẫu bị cụt (người dùng 28/10) | (1) khung xem đặt `height` cố định chung với Chi tiết → nội dung dài hơn khung bị giấu (thanh cuộn đã ẩn nên không biết còn chữ); (2) SVG từng chữ ở câu mẫu `overflow:hidden`, viewBox chỉ tới ascender → phần dấu chồng vượt (tới ~1180) bị cắt | Dùng `min-height` chung (khung cao theo nội dung, không cắt); `.vb-g{overflow:visible}` + khoảng dòng câu mẫu chừa ~0,3 em. Test điện thoại: `scrollHeight == clientHeight` mọi tab loại dấu, chụp câu mẫu |
| Chi tiết (iPhone): tiêu đề thẻ thanh kéo nằm đè lên đường viền (người dùng 28/10) | `fieldset` + `legend`: Safari iOS vẽ legend lên viền dù `float` | Thẻ là `div.hu-card` + `div.hu-cardh`, không dùng fieldset / legend |
| Bàn vẽ: trục chữ của chữ có sẵn (â á ă…) không đi qua tâm dấu (người dùng 28/10) | Chữ có sẵn không có recipe → editor tự đoán trục theo hình chữ | `tools/nghieng/tt/axis_editor.py FONT editor.json GÓC`: trục nghiêng theo trục chuẩn đi qua TÂM DẤU đã đặt (dấu trên thấp nhất; chỉ có dấu nặng thì tâm dấu nặng), ghi `sax` cho cả recipes lẫn glyphs; `editor.js` dùng `glyphs[n].sax` |
| Xem trước (iPhone): phóng xong thấy 2 lớp chữ chồng nhau (cỡ cũ + cỡ mới), phóng tiếp bị khựng; Chỉnh dấu thì mượt (người dùng 28/10) | `vkZoom` transform đúng phần tử con đầu của khung. Chỉnh dấu: phần tử đó (svg) bị THAY hẳn khi vẽ lại → không còn lớp ảnh cũ. Xem trước: `.vk-panes` GIỮ NGUYÊN, chỉ ruột đổi → Safari iOS giữ lớp ảnh cũ của phần tử đã transform / will-change | Chế độ `wrap`: lúc bắt đầu phóng bọc ruột vào lớp tạm `.vk-zw`, transform lớp tạm; vẽ lại thay ruột thì lớp tạm mất theo (không thay thì tự gỡ). Test `pinch`: sau khi thả còn 0 `.vk-zw`, 1 bản chữ |
| Chip lưu ở Đồng loạt xám, chữ “chưa đổi”, khác chip Chi tiết; rồi nội dung 2 chip vẫn lệch nhau (người dùng 28/10) | Đồng loạt dùng class `vk-save` + chữ riêng; mỗi chế độ tự giữ trạng thái lưu riêng | Dùng chung `hu-status hu-chip` + `data-s`, và MỘT trạng thái cho cả tab: `window.__vkChip(chữ, ok/busy, lúc_nạp)` ghi cùng lúc vào `#vb-status` và `#hu11-status` (lúc nạp không hạ “đã lưu” về “tự lưu”). Bộ chữ (ngắn, dễ hiểu — người dùng 28/10 thấy “đã nạp số lần trước” khó hiểu): đang kết nối… → tự lưu (cả khi đã mở lại số / nét / góp ý lần trước — người dùng 28/10: chỉ cần “tự lưu”) → đang lưu… → đã lưu HH:MM · chưa lưu được |
| Câu mẫu thiếu dấu chồng chữ hoa | Câu mẫu chỉ có vài từ | Câu mẫu mặc định phải có đủ dãy: `ẦẤẨẪẬ ẰẮẲẴẶ ỀẾỂỄỆ ỒỐỔỖỘ ỜỚỞỠỢ ỪỨỬỮỰ ỲÝỶỸỴ ÌÍỈĨỊ` + chữ thường tương ứng + từ thật (NGƯỜI, TƯƠNG, “cổ,”) |

---

## C · Lỗi quy trình

| Sai lầm | Bài học |
|---|---|
| Đính kèm file font khi người dùng chưa chốt VER | Chỉ xuất khi người dùng nói rõ chốt VER nào |
| Kit chứa ví dụ của font khác loại, làm nhiễu kết quả | Kinh nghiệm viết theo **loại font** + tag, không trộn vào luật chung |
| Dựng dấu hỏi / râu bằng hình học | Người dùng thích dấu lấy từ bộ phận của chính font (?, giọt g) |
| Đề xuất thiết kế mới khi người dùng đã thích bản cũ | Giữ bản người dùng thích, chỉnh nhẹ |
| Đoán nguyên nhân rồi sửa lan man (A2) | Đo trước; viết test tự động cho chỗ nghi ngờ |
| Giải thích dài trên trang | Một câu, phần còn lại vào nút i |

---

## D · Lỗi môi trường (máy làm việc trên cloud)

| Triệu chứng | Nguyên nhân | Cách làm đúng |
|---|---|---|
| `pip install skia-pathops shapely uharfbuzz brotli opentype-sanitizer` lỗi liên tục; npm, cdnjs, jsdelivr cũng bị chặn | Proxy chỉ cho các host được phép; pypi.org / registry npm có thể bị tắt cho phiên | **Kiểm mạng trước khi cài** (`curl -sS "$HTTPS_PROXY/__agentproxy/status"`, xem `recentRelayFailures`). Bị chặn thì **không thử lại**, báo người dùng mở pypi.org ở Settings → Capabilities nếu thật cần pathops |
| Không có `brotli` → không ghi được woff2 | Thiếu gói Python | Dùng `tools/nghieng/shim/brotli.py` (ctypes gọi `libbrotlienc/dec` có sẵn trong máy) |
| Không có `ots` | Thiếu gói | Nạp font vào Chromium (Playwright có sẵn): Chrome chạy OTS, `document.fonts` báo `loaded` / `error` |
| Không có `uharfbuzz` | Thiếu gói | Đo NFC / NFD bằng Chromium (cùng HarfBuzz); kern lấy thẳng từ bảng GPOS (`tools/nghieng/hornkern.py`) |
| Không có `skia-pathops` / `shapely` | Thiếu gói | Râu: **nối thẳng vào contour** (tách đường cong tại gốc râu), không cần hợp nét. Khoảng cách / va chạm: `geo.mindist` (numpy + matplotlib.path). Chỉ thanh đ Đ còn chồng lên thân |
| Font đứng .ttf mà chuỗi vnfont → horn5 không chạy (thiếu pathops / shapely) | Gói bị chặn | `tools/quick_vn.py` (dấu từ chính font, dấu hỏi từ khung xương ?, râu horn5, hợp nét bằng raster + dò viền) → `stamp.py`; dữ liệu khung kéo bằng `nghieng/export_hornui_italic.py … 0` |
| `nghieng/geo.py contours` lỗi `lambda takes 2 positional arguments but 11 were given` với font .ttf | RecordingPen ghi `addComponent` (chữ ghép) và `qCurveTo` nhiều điểm / toàn điểm điều khiển (`None`) | `geo.contours` dùng BasePen: tự tách chữ ghép, tách `qCurveTo` thành từng đoạn |
| Lăn chuột phóng ở Xem trước / Đồng loạt bị giật, Chi tiết thì mượt (28/10) | Khi thả tay, chữ vẽ lại ở cỡ mới không trùng khít ảnh đã phóng bằng CSS (lề, khoảng, cỡ làm tròn không nhân theo tỉ lệ) → chữ nhảy mỗi lần vẽ lại; Chi tiết là một SVG nên vốn khớp | `vkZoom.commit` neo ký tự / phần tử dưới con trỏ (caretRangeFromPoint, rồi elementFromPoint), vẽ lại xong tìm lại theo cùng đường dẫn và cuộn bù → lệch ≤ 2 px. Đo bằng `tools/t_wheel.js` (khung hình) và so ảnh trước / sau khi thả (giữ `window.__vkzHold` = 1500 để chụp kịp) |
| Chip “tự lưu” mỗi tab một chỗ, một cỡ (28/10) | Mỗi khung tự đặt top / right / cỡ chữ riêng; Bàn vẽ để chip dưới khung “Xem trong chữ” | MỘT luật CSS cho `#status`, `#hu11-status`, `#vb-status`, `.ed-stage>.ed-save`: góc phải trên khung, cách viền 10 px, chữ 12 px; Bàn vẽ đặt trong khung vẽ, dưới thước 20 px |
| Trục chữ ở Bàn vẽ không đồng nhất: a ≠ â, á / à nhảy, u không nghiêng (28/10) | (1) mỗi chữ có dấu lấy trục qua tâm dấu RIÊNG → sắc / huyền lệch một bên, ¨ chỉ bắt 1 chấm, dấu nặng ụ ị theo thân; chữ gốc không có trục; (2) chữ không có trục thì editor.js tự nghiêng theo dáng (±8°) → u gần đứng; (3) sửa editor.json của bản gốc (r*/editor.json) mà quên `vers/<VER>/editor.json` → chọn VER khác thì trục cũ quay lại, trang còn phình thêm 1 MB (khác biệt mỗi VER) | `axis_editor.py`: một góc cho cả font; MỘT trục cho cả họ chữ (o ò ó … ô ơ… cùng trục) = nhóm ứng viên trùng nhau đông nhất (lệch ≤ 4 đv), chữ lạ vẫn nhận trục họ, in % trùng + danh sách lệch; editor.js: font nghiêng thì mọi chữ cùng góc font. Chạy cho MỌI VER (export_data.sh đã làm) |
| Chi tiết thiếu nhóm thanh “Dấu hỏi” ở font nghiêng (28/10) | Nhóm chỉ hiện khi có thông số dấu hỏi VẼ LẠI (`hook_stroke.py`, cần shapely); font nghiêng chép dấu hỏi có sẵn từ bản đứng nên không có số | `export_hornui_italic.py` ghi `hook_tf` → Chi tiết hiện 4 thanh chỉnh dáng nét thật (bề ngang, cao, dày đầu / đuôi móc; `hook_tf.py` cùng công thức); dấu hỏi trên ơ ư (nằm trong phần tĩnh của recipe) tách ra `rm` để tô đỏ / chỉnh được. Dựng: cfg `hook_tf` = số trong db |
| Có sẵn trong máy | | fontTools, numpy, scipy, scikit-image, matplotlib, Pillow, OpenCV, Playwright + Chromium; thư viện hệ thống libbrotli, libharfbuzz, libfreetype, libpotrace |

---
*build by @nhatmotion*
