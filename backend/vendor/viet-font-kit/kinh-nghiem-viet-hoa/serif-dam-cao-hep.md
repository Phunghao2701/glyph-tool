# Kinh nghiệm Việt hoá: Serif đậm cao hẹp

> build by @nhatmotion

**Đặc điểm nổi bật:** chữ có chân, rất đậm, dáng cao và hẹp (condensed / extra tall), tương phản nét rõ. Đầu nét dạng giọt (tai chữ g, đầu chữ r tròn).

**Mã loại:** `serif.heavy.condensed.contrast.ball`

**Tag:** `#display` `#serif` `#heavy` `#condensed` `#extra-tall` `#high-contrast` `#ball-terminals` `#large-x-height` `#cff-otf` `#upright` `#latin1-accents-only` `#wrong-os2-xheight` `#commercial`

**Thẻ:** Serif đậm cao hẹp | Râu kệ + thanh đậm, Ơ cùng gốc râu Ư · Kern sau râu khép ươ ƯƠ · Dấu nặng bằng đúng chấm chữ i
**Chữ nền:** serif-dam | 400

> Dùng file này khi font mới trùng nhiều tag ở trên: chữ tiêu đề, poster, bìa, logo; serif đậm, hẹp, cao, có giọt. Với font sans tròn, font mảnh hoặc font chữ thân, nhiều kinh nghiệm dưới đây **không áp dụng** (xem mục 6). Số liệu là ví dụ đo trên một font mẫu 1000 UPM của loại này. Gặp font khác phải đo lại.

---

## 1 · Hồ sơ điển hình của loại font

| Đặc điểm | Thường gặp (số đo ví dụ) | Ý nghĩa khi Việt hoá |
|---|---|---|
| Định dạng | CFF (.otf), 1000 UPM, ~300 glyph | Ghi độ rộng CFF phải trừ `nominalWidthX` |
| Giấy phép | thương mại bán lẻ | Nhắc người dùng về giấy phép trước khi sửa |
| Tỉ lệ | chữ hoa ~700, x-height thật ~620, chữ rất hẹp (U ~550, u ~500) | Rất ít chỗ ngang cho râu và dấu; mỗi đơn vị rộng thêm đều thấy |
| Thông số OS/2 | `sxHeight` ghi sai (vd 465, thật ~620) | `linecheck` báo tràn giả ở u ù ú; đo x-height thật |
| Tương phản | nét đứng đậm, nét ngang / nối mảnh, đầu giọt tròn | Dấu phẳng nét đều trông lạc; râu cần **thanh đậm**: cổ mảnh, đầu giọt dày |
| Chữ có dấu sẵn | bộ Latin-1, thiếu ả ạ ă ơ ư đ và dấu chồng | Mũ / sắc / huyền / ngã lấy từ font; hỏi, nặng, trăng, râu, đ phải dựng |
| Trục | đứng | Trục đặt dấu thẳng đứng |

## 2 · Dấu hiệu nhận ra loại font này

Có từ 4 dấu hiệu trở lên thì đọc kỹ mục 3:

1. Có chân, đậm, dáng cao hẹp kiểu poster.
2. Chữ g có tai hình giọt, chữ r có đầu tròn.
3. Tương phản nét rõ ở cỡ lớn.
4. x-height đo được cao hơn nhiều so với số ghi trong OS/2.
5. Chỉ có dấu Latin-1.
6. Font thương mại, metadata sơ sài.

## 3 · Vấn đề hay gặp và cách xử lý

### 3.1 Dấu hỏi
- Dấu hỏi hình học trông lạc. **Lấy từ dấu `?` của font** (`hoi.py`): bỏ chấm, cắt cuống, thu nhỏ (cao ~200), kéo rộng ~1.25, nở nét 7 (dấu đơn) / 12 (dấu chồng) cho khỏi nhạt.
- Khe dấu–đỉnh thân phải **đều theo cỡ**, ví dụ thường 60, hoa 50. Đừng để Y U A lệch nhau vì bbox khác.
- Font đứng mà dấu hỏi đúng tâm hình sẽ **trông lệch trái**, vì đầu móc nặng. Dời phải 3–4 % bề rộng thân (`place_hoi.py`). Font mẫu cùng nhóm đo được +3…+6 %.
- Chữ hoa: dấu hỏi nhỏ lại khoảng 6 %.

### 3.2 Râu ơ ư: dáng
- Thử theo thứ tự, người dùng ưng dần:
  1. tai chữ g ghép bằng pathops: **thô** ở Ư, bị chê;
  2. dấu phẩy nghiêng phải: **nới spacing**, trên U nhìn như dấu chấm, bị chê;
  3. giọt đứng: ổn hơn nhưng chưa ra móc;
  4. **râu kệ + thanh đậm**: được chốt.
- Dáng chốt: đường tâm như râu kệ (cổ rời đỉnh chân phải, chạy ngang rồi dựng lên; vươn ~60, cao ~80). Bề dày từ nét mảnh `thin` ~30, giữ mảnh tới t0 ~0.29, dày dần (mũ p ~2.15) thành đầu giọt `head` ~100.
- Gốc râu cắt gọn trong nét (`clip` 36), không lòi vào lòng U.
- **Ơ:** gốc râu đặt **cùng độ cao gốc râu Ư**, dời lên vai trên. Nhờ vậy cùng đỉnh mà cổ không phải dài ra.
- Lấy *cách vẽ* giọt chữ g, **không chép nét**. Không nguồn nào bắt râu phải theo giọt. Hài hoà là được, nhưng phải đọc rõ ở cỡ nhỏ (đầu râu không thành chấm).

### 3.3 Râu ơ ư: độ dày hoa / thường
- Đầu râu dày ≈ nét đậm nhất của dấu hỏi cùng cỡ (vd ~70 / 75). Đo bằng đường tròn nội tiếp (buffer âm tới khi rỗng).
- Người dùng có thể muốn dày hơn (vd đầu 100). Ưu tiên mắt người dùng, nêu số đo để họ biết.
- **Một bộ thông số**: chữ thường = hoa × 0.9 (dáng) × 1.07 (độ dày). Font mẫu cùng nhóm cho thấy râu thường mảnh bằng 0.82–0.97 râu hoa, không bao giờ dày hơn.
- Tách thông số hoa / thường từng làm ư dày hơn Ư.

### 3.4 Spacing quanh râu
- Chữ hẹp nên râu đẩy độ rộng lên rõ (vd Ư +63, ư +58, ơ +19, Ơ +0). Dòng nhiều ươ trông hở.
- **Kern sau râu** (`autokern_horn.py`, khe tối thiểu 50) khép lại, ví dụ ươ −58, ưa −58, ƯƠ −63, ƯA −63.
- Nói rõ: chỉ app bật kern mới thấy. Word thân văn bản cần bật kern trong style Normal.
- Không rút ngắn râu khi người dùng đã chốt số.

### 3.5 Dấu thanh trên ơ ư
- Dời trái ≤ 40 rồi mới nâng, giữ khe ≥ 28 với râu.
- Trên trang cho thanh kéo vị trí từng dấu (sắc / huyền / hỏi / ngã / nặng, chung hoa thường) để người dùng tự chỉnh.

### 3.6 Dấu nặng
- **Bằng đúng chấm chữ i** (vd 147×154), cùng cỡ hoa / thường.
- Bản nhỏ hơn chấm i bị người dùng chê.
- Dấu chấm câu của loại font này thường nhỏ hơn chấm i (vd 129×133). Donny Trương cho phép bằng chấm i.

### 3.7 đ Đ và ĩ
- Thanh ngang dày ≈ nét ngang chữ E (vd 52).
  - đ: đặt cao gần đỉnh cán, vắt qua cán.
  - Đ: đặt ở giữa chiều cao, bên trái thân.
- Dấu ngã trên ĩ Ĩ rộng hơn i: thu hẹp ngang.

## 4 · Quy trình chạy tốt với loại font này

1. Phân tích: CFF, OS/2 x-height, giấy phép, dấu sẵn có, giọt chữ g / r.
2. VER đầu: hai option dấu chồng (trên đỉnh / bên phải dấu mũ), dấu hỏi từ `?`.
3. Từ vòng 3–4 trở đi, đưa **khung kéo** cho người dùng tự kéo râu. Khung vẽ bằng nét font thật, ghép râu theo đúng công thức script dựng.
4. Dựng VER theo đúng số người dùng kéo, thêm kern sau râu.
5. Soi: `ƯƠ TƯƠNG ươ`, `người ươn ưa`, `ỦY BAN ỷ`, `ịạẹọụỵ`, `phố cổ,`, ở cỡ lớn lẫn 12–16 px, cả bật lẫn tắt kern.

## 5 · Sai lầm đã mắc và bài học

| Sai lầm | Bài học |
|---|---|
| Râu tai g ghép pathops, thô ở Ư | Dùng cách vẽ, không ghép nét |
| Râu nghiêng phải nới spacing | Râu ngắn, gọn trong khe; đo độ rộng tăng mỗi VER |
| Ư Ơ không song song | Một dáng, gốc Ơ cùng độ cao Ư; kiểm yMax |
| Thông số hoa / thường riêng → ư dày hơn Ư | Một bộ thông số + tỉ lệ |
| Dấu nặng nhỏ hơn chấm i | Dấu nặng = chấm i |
| Tin `sxHeight` của font | Đo x-height thật |
| Smoothstep nhiều mốc → viền gợn | Hàm thuôn đơn điệu |
| Bounds pathops → độ rộng sai | `BoundsPen` |

## 6 · Khi KHÔNG áp dụng

- **Sans tròn / monoline:** không có tương phản. Râu nét đều, bo tròn, kiểu kệ; xem `sans-dam-bo-tron.md`.
- **Serif mảnh / chữ thân:** dấu mảnh, khe khác hẳn. Chỉ giữ quy trình, không giữ số.
- **Font nghiêng:** trục đặt dấu nghiêng theo góc chữ, dấu sinh mới phải nghiêng theo.
- **Font rộng:** ít áp lực spacing hơn, có thể giữ advance không đổi.
- **TrueType (.ttf):** không có vấn đề `nominalWidthX`, nhưng phải kiểm `glyf` và hinting.

---
*build by @nhatmotion*
