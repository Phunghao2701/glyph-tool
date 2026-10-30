# Kinh nghiệm Việt hoá: Serif đậm cao hẹp — bản NGHIÊNG (italic thật)

> build by @nhatmotion

**Đặc điểm nổi bật:** bản nghiêng của loại serif đậm cao hẹp (xem `serif-dam-cao-hep.md`), là chữ nghiêng **thật** (a một tầng, u có nét vào, y đuôi cong), không phải chữ đứng xiên máy. Thường đã có bản đứng Việt hoá làm mẫu.

**Mã loại:** `serif.heavy.condensed.contrast.ball.italic`

**Tag:** `#serif` `#heavy` `#condensed` `#extra-tall` `#italic` `#true-italic` `#has-upright-vn-ref` `#cff-otf` `#latin1-accents-only` `#wrong-os2-xheight` `#no-italic-bit`

**Thẻ:** Serif đậm cao hẹp nghiêng | Chép quan hệ dấu từ bản đứng đã chốt · Một trục chuẩn cho cả font · Đo độ rộng / kern trong không gian dựng thẳng
**Chữ nền:** serif-dam | 400 | italic

## 1 · Hồ sơ điển hình

| Đặc điểm | Thường gặp (số đo ví dụ) | Ý nghĩa |
|---|---|---|
| Góc khai `post.italicAngle` | 15° | **Không tin**: góc nét đứng đo được 13,9° |
| Dấu có sẵn (á â ã…) | đặt lệch thân từng chữ: û −52, î −40, Ê +49 | Không lấy dấu mũ có sẵn làm trục; dựng lại cả chữ có sẵn |
| x-height | thật 629, OS/2 ghi 548 | Đo lại |
| Cờ OS/2 | thiếu bit Italic | Bật bit 0 `fsSelection` + bit 1 `macStyle`, tên kiểu “Bold Italic” |
| Nét ngang E | mảnh hơn bản đứng nhiều (≈ 25 so với 45) | Thanh đ Đ mảnh theo E nghiêng (≈ 30), hỏi người dùng |

## 2 · Cách làm chạy tốt

1. **Lấy bản đứng đã chốt làm chuẩn quan hệ**: dấu hỏi, râu, khe dấu, cách chồng dấu chép từ bản đứng; dấu sắc / huyền / ngã / mũ / trăng lấy hình từ font nghiêng; dấu nặng = chấm chữ i nghiêng.
2. **Một trục chuẩn cho cả font** (lỗi A19): đo góc từ nét đứng → làm mọi phép đặt dấu trong không gian dựng thẳng `x' = x − y·tan(góc)` → nghiêng lại. Trục mỗi chữ = tâm khối dải 20–80 % (i I: tâm nét đứng) + hiệu chỉnh thị giác của chữ đó lấy từ bản đứng. Mỗi loại dấu một độ lệch cho cả font.
3. **Râu ơ ư**: nối vào contour (tách đường cong ở gốc râu), Ư thay chân serif phải như bản đứng; gốc Ơ nâng sao cho đỉnh Ơ = Ư, ơ = ư.
4. **Độ rộng / kern đo trong không gian dựng thẳng** (chữ bên cạnh cũng nghiêng cùng góc), kern sau râu chỉ khép.
5. **ỵ**: đuôi y cong sang trái dưới chân chữ → dấu nặng trên trục chạm đuôi; dời phải tới khi cách ≥ 40.
5b. **ị**: chấm i của chữ nghiêng thật nằm lệch trái thân (vd −24). Đo thân i → so chấm i → dấu nặng nằm trên đường qua tâm thân và tâm chấm i (cân lại sang phải). **Ị** không có chấm: giữ trục chung (đã duyệt).
5c. **Dấu chồng**: dấu mũ + dấu thanh là một khối giống hệt nhau trên a e o (lấy theo a / A); không để luật "giữ trong advance" bóp khe ở chữ hẹp.
6. **Dấu thanh trên ơ ư**: dời trái ≤ 40 rồi mới nâng, khe ≥ 28 với râu (ờ ỡ Ỡ hay vướng).

## 2b · Diễn biến các VER (một font mẫu loại này, 1000 UPM)

| VER | Thay đổi | Người dùng nói |
|---|---|---|
| 1 | Chép quan hệ dấu từ bản đứng, trục = dấu mũ có sẵn từng chữ, nghiêng 15° | ị Ị lệch trục dấu nặng; bàn vẽ đ thiếu thanh; thiếu mục B; câu mẫu ít dấu chồng |
| 2 | Như 1, sắc / huyền chồng trên đỉnh | (phương án đối chiếu) |
| 3 | **Một trục chuẩn** 13,9° đo từ nét đứng; dựng lại 30 chữ có sẵn | Ị duyệt; ị vẫn lệch (bị ép vào trục chung); khe ề ≠ ồ |
| 4 | Như 3, dấu chồng trên đỉnh | (đối chiếu) |
| 5 | ị theo trục thân + chấm i; dấu mũ + dấu thanh là khối cố định | — |
| 6 | Như 5, **mọi dấu thanh chồng trên đỉnh** | **Chốt**: nghiêng chồng đỉnh đẹp hơn, bản đứng giữ chồng ngang vì dễ đọc |
| 7 | Như 6 + **gộp nét** thanh đ Đ vào thân | **Chốt, xuất file** (bản biến thiên làm sau) |

## 2c · Hồ sơ bản chốt (VER 7)

- Trục chuẩn 13,9° (font khai 15°). Trục chữ = tâm khối dải 20–80 % + hiệu chỉnh từ bản đứng (a +21, E −15). Hỏi lệch phải +18 (hoa +16), dấu khác 0.
- ị: thân 141, chấm i 117 → dấu nặng 165 (dựng thẳng). ỵ: dấu nặng dời phải 144 khỏi đuôi.
- Dấu chồng trên đỉnh, khe đều: thường sắc 43 · huyền 51 · hỏi 40 · ngã 30; hoa sắc 29 · huyền 28 · hỏi 40 · ngã 30. Không dấu nào chìa khỏi advance.
- Dấu trăng + thanh (ắ ằ ẳ ẵ): cùng khe dọc 20 trên đỉnh trăng, tâm lệch theo bản đứng (+42 / +13 / +44 / +24) → khe nhỏ nhất 81 / 49 / 84 / 21. **Còn mở**: có thể canh giữa trên trục ở font sau.
- Râu: đỉnh ư = ơ = 754, Ư = Ơ = 972. Độ rộng ư +24, ơ +8, Ư +61; kern sau râu ươ −24, ƯƠ −61.
- Thanh đ Đ dày 30 (theo nét ngang E nghiêng), đã gộp nét. winAscent 1238 (dòng Word cao thêm ~8 %).
- Tên: họ riêng “… Italic VN”, kiểu Bold Italic, bật bit Italic.

## 2d · Người dùng loại việc này thường muốn

- Bản nghiêng và bản đứng **được phép khác cách chồng dấu** (nghiêng: trên đỉnh; đứng: bên phải) — mỗi file phải thống nhất bên trong. Trang có ô **trộn chữ đứng + nghiêng** để soi chỗ chuyển.
- Đồng bộ là trên hết: một trục, một khe cho mỗi loại dấu, ảnh đo có số để tự kiểm.
- Mỗi lần dời dấu: **lớp nét đứt vị trí cũ** bật / tắt được (quy tắc trang duyệt).
- Font tĩnh phải **gộp nét**; font biến thiên giữ nét chồng ở master.

## 3 · Sai lầm đã mắc

| Sai lầm | Bài học |
|---|---|
| Trục từng chữ lấy theo dấu mũ có sẵn → ị Ị lệch trục dấu nặng | Một trục chuẩn đo từ nét đứng, dấu trên và dưới cùng trục |
| Dùng góc `italicAngle` khai trong font | Đo góc thật của nét |
| Bàn vẽ lấy nét chữ gốc trơn → đ mất thanh, ị mất chấm | Nét tĩnh = phần thân đã dựng; kiểm recipe khớp glyph |
| Bỏ mục khung kéo vì thiếu shapely | Không được bỏ; xuất dữ liệu bằng fontTools, trang nghiêng lại bằng `D.slant` |
| Câu mẫu ít dấu chồng | Câu mẫu đủ dãy Ầ Ấ Ẩ Ẫ Ậ … cả hoa lẫn thường |
| ị đặt dấu nặng theo trục chung → vẫn lệch (chấm i lệch trái thân) | Trục chữ i = đường qua tâm thân và tâm chấm i |
| Khe huyền – mũ ở ề khác ồ (chép từng chữ của bản mẫu + co vào advance) | Dấu mũ + dấu thanh là một khối cố định, khe bằng nhau mọi chữ |

## 4 · Khi KHÔNG áp dụng

- **Chữ xiên máy (oblique)**: dấu có sẵn thường đã đúng trục; chỉ cần nghiêng dấu mới theo góc.
- **Không có bản đứng Việt hoá**: dùng quy trình chung trong SKILL.md, chỉ giữ ý “một trục chuẩn”.

---
*build by @nhatmotion*
