# Kinh nghiệm Việt hoá: Serif mảnh hẹp tương phản — bản NGHIÊNG (.ttf)

> build by @nhatmotion

**Đặc điểm nổi bật:** bản nghiêng thật (a một tầng, u nét vào nhọn) của serif tiêu đề mảnh, hẹp, tương phản rõ; Google Fonts (OFL), TrueType có hinting, GPOS có `mark` / `mkmk` đã nghiêng sẵn theo trục. Bản đứng đã Việt hoá (dấu hỏi học từ font mẫu, dày theo dấu ngã) làm chuẩn bộ dấu.

**Mã loại:** `serif.regular.condensed.contrast.italic.ttf`

**Tag:** `#display` `#serif` `#regular` `#condensed` `#high-contrast` `#italic` `#true-italic` `#ttf` `#hinted` `#ofl` `#gpos-mark` `#has-upright-vn-ref` `#has-dcroat`

**Thẻ:** Serif mảnh tương phản nghiêng | Dấu có sẵn theo anchor nghiêng · Hỏi / nặng / râu chép bản đứng rồi nghiêng · Râu đâm thịt chữ, không cắt nét · Khe dấu ≥ 0,75 nét dấu
**Chữ nền:** didone | 400 | italic

> Số liệu là ví dụ đo trên một font loại này (1000 UPM). Đo lại trên font mới.

## 1 · Hồ sơ điển hình

| Đặc điểm | Ví dụ | Ý nghĩa |
|---|---|---|
| Góc | `post.italicAngle` 13°, nét đứng đo được 13,02° | Font Google khai đúng; vẫn đo để chắc |
| Anchor | mark anchor dấu ở y 510, mkmk dấu mũ (328, 740) — đã nghiêng theo trục | Dấu có sẵn xếp bằng anchor là đúng ý nhà thiết kế, không cần tự dựng trục |
| Dấu có sẵn | á à ã â ă é ê í ó ô õ ú ý + đ Đ; thiếu 96 chữ (cả ĩ ũ) | Chỉ dựng 96 chữ + ơ ư Ơ Ư |
| Nét dấu | sắc / huyền 75, ngã 58, mũ 68 (đường tròn nội tiếp) | Khe tối thiểu ≈ 0,75 × 75 ≈ 55 |
| Chữ i | chấm i lệch trái trục thân ~28 (dựng thẳng) | ị: dấu nặng trên đường qua tâm thân + tâm chấm i |

## 2 · Cách làm chạy tốt (`tools/nghieng/tt/`, chỉ fontTools)

1. **Dấu có sẵn → anchor của chính bản nghiêng**, cộng đúng độ lệch / co giãn bản đứng VN đã áp so với anchor của nó (ĩ Ĩ dấu ngã hẹp 0,65 / 0,73).
2. **Dấu thiếu → chép từng chữ của bản đứng VN, nghiêng quanh anchor gắn dấu** (`p = A + (dx + dy·tan, dy)`): dấu hỏi giữ đủ 4 cỡ của bản đứng (thường / hoa / chồng / hoa chồng); dấu nặng dùng chấm i nghiêng ở tâm chép từ bản đứng.
3. **Râu:** cắt đoạn râu từ ơ ư Ơ Ư bản đứng, nghiêng quanh gốc, đặt theo mép phải thân nghiêng ở cùng độ cao, hợp nét (union tự viết, không cần pathops). Râu nằm gọn trong độ rộng chữ nghiêng → không phải nới advance.
4. **Râu = hình riêng đâm vào thịt chữ, thân giữ nguyên** (A37). **Ư dùng râu của Ơ** (`horn_from`): râu Ư của bản đứng được vẽ để thay serif nên sang bản nghiêng (giữ serif) bị sai dáng; râu Ơ đặt theo mép phải thân U cùng độ cao thì đỉnh Ư = Ơ và cổ râu phủ đuôi serif: gốc râu kéo dài vào trong nét 31–34 đv theo hướng chung, rồi gộp nét; Ư giữ nguyên serif phải (cách cắt serif ở VER 3 bị chê “tệ hơn”).
5. **Khe:** dấu thanh ↔ râu ≥ 55 — **chỉ NÂNG, không dời trái** (bản nghiêng: dời trái làm dấu lệch trục, người dùng thích dấu đúng trục như 1B); dấu chồng trên đỉnh theo mkmk đã ≥ 73.
5b. **lsb = xMin** cho mọi glyph TrueType dựng mới (A36).
6. **Vòng 1 ba hướng:** A dấu bên phải dấu mũ (co 0,85, khe ≥ 50, đẩy chéo lên-phải), B chồng đỉnh theo bản đứng, C dấu hỏi từ nửa trên `?` nghiêng (cắt ở cổ, nở nét bằng dấu hỏi bản đứng).

## 2b · Diễn biến các VER

| VER | Thay đổi | Người dùng nói |
|---|---|---|
| 1A / 1B / 1C | bên phải · chồng đỉnh theo Regular · hỏi nửa trên ? | Tránh đặt dấu sát nhau (cỡ nhỏ dính); râu Ư phải đè lên thịt tip serif; Chi tiết khác Xem trước |
| 2A / 2B / 2C | khe ≥ 55 / 56; râu Ư dời −18, cắt theo giao; Chi tiết vẽ nét thật | Thích 1B hơn (dấu thanh trên ơ ư đúng trục), nhưng luật khe của 2B tốt hơn; râu phải là hình rời ở bàn vẽ |
| 3 | Dáng 1B + khe ≥ 55 bằng cách NÂNG dấu (không dời trái, `horn_tone_left: 0`); sửa lsb = xMin (A36) | Cắt serif để ghép râu “còn tệ hơn cách cũ”; muốn râu là hình riêng đâm vào thịt chữ, chữ giữ nguyên; khung xem 2 chế độ cùng cỡ |
| 4 | Râu hình riêng, gốc đâm 31–34 đv vào thân, thân giữ nguyên, union | Hỏi đuôi râu dạng vector có tham khảo Regular không (đuôi nêm nhìn như gai ở bàn vẽ) |
| 5 | Đuôi râu đi tiếp theo cổ, cắt song song trục 32–36 đv (như horn5 của bản đứng) | Mọi râu ổn, riêng râu Ư sai → “dùng râu của Ơ” |
| 6 | Ư dùng râu Ơ (`horn_from: {U: O}`), gốc theo mép phải thân U cùng độ cao gốc Ơ | **Chốt, xuất .ttf** |

## 2c · Hồ sơ bản chốt (VER 6, 1.006)

- cfg `build_it.py`: `{"stack":"top","horn_tone_gap":55,"horn_tone_left":0,"horn_from":{"U":"O"}}` — dấu chồng trên đỉnh theo anchor mkmk của bản nghiêng; hỏi / nặng / râu chép từ bản đứng VN, nghiêng 13,02° (đo từ nét đứng = `italicAngle`).
- Khe: dấu chồng 73–104; dấu thanh ↔ râu ≥ 55 (ờ 56, ỡ 55, Ờ 58, Ỡ 55), chỉ nâng dấu, dấu luôn đúng trục.
- Râu: hình riêng chép bản đứng (đầu, cổ, đuôi nhập thân), đuôi chìm đi tiếp theo cổ, cắt song song trục 32–36 đv, gộp nét (union tự viết). Ư mượn râu Ơ, serif phải giữ nguyên, cổ râu phủ đuôi serif. Đỉnh ư = ơ = 600, Ư = Ơ = 817. Độ rộng không đổi (râu nằm trong advance chữ nghiêng); kern sau râu chỉ khép (ƯA −26, ơ. −30).
- Dấu nặng = chấm i nghiêng; ị theo trục thân i + chấm i; ỵ bên phải đuôi y (khe như bản đứng). ĩ Ĩ dấu ngã hẹp như bản đứng (0,65 / 0,73).
- Tên: cùng họ “VFK - <họ bản đứng>”, kiểu Italic (bit Italic giữ từ font gốc) → cặp đúng với bản Regular VN. win 1180 / 310 (Word cao dòng +15 %), USE_TYPO_METRICS tắt, code page 1258, lsb = xMin, hinting 0 lỗi, NFC = NFD trong Chromium.

## 2d · Người dùng loại việc này thường muốn

- Bộ dấu **theo bản đứng đã chốt** (không phải dấu tự vẽ lại); bản nghiêng được phép chồng dấu trên đỉnh như bản đứng.
- **Dấu đúng trục hơn là né bằng cách dời ngang**: cần khe thì nâng dấu.
- **Trục chữ nghiêng: MỘT góc cho cả font (13,02°, đo từ thân), MỘT trục cho cả họ chữ** (người dùng 28/10: “cùng 1 bộ nên cùng trục”). Mỗi chữ có dấu cho một ứng viên (đường nghiêng qua tâm dấu); nhóm ứng viên trùng nhau đông nhất (≤ 4 đv) là trục họ, gán cho mọi chữ trong họ kể cả chữ gốc và chữ sắc / huyền. Font này: a 86 %, e 73–80 %, o 63 %, u 50 %, y 43 %, i 38 % trùng; rơi ra ngoài: sắc / huyền (lệch một bên ~17–19 đv, đúng thiết kế), ¨ ő (chỉ bắt 1 chấm), dấu nặng ụ ị ỵ ẹ (đặt theo thân), ỡ Ỡ (ngã trên ơ lệch trái ~4–7 đv).
- **Không đặt dấu sát nhau** (≈ 0,75 nét dấu).
- **Không sửa nét chữ gốc để ghép râu** (cắt serif bị chê); râu là hình riêng đâm vào thịt chữ; chữ hoa có serif khác bản đứng thì mượn râu Ơ.
- Ở bàn vẽ râu phải là hình rời, đuôi vector giống râu bản đứng (không chụm thành gai).

## 3 · Sai lầm đã mắc

| Sai lầm | Bài học |
|---|---|
| Tách râu bằng mẫu viền thưa (đoạn thẳng chỉ lấy điểm đầu) → cả contour thành “râu”, union nổ | Lấy mẫu dày theo độ dài; râu = cụm đoạn xa lớn nhất (A33) |
| Ghép râu Ư bằng điểm gần nhất → gai / mất thân; rồi cắt serif để ghép (người dùng chê) | Râu là hình riêng đâm vào thịt chữ, thân giữ nguyên (A37) |
| Khe dấu thanh ↔ râu 29–35 | ≥ 0,75 nét dấu (A35) |
| Dấu bên phải đẩy ngang → đè sang chữ sau ở chữ hẹp | Đẩy chéo lên-phải |
| Trang: Chi tiết vẽ râu công thức horn5 cho font có râu chép từ bản đứng | Xuất nét thật (`rd`) và vẽ nét thật khi chưa kéo thanh râu |
| Ghi glyph .ttf mới với lsb = 0 → cả chữ dời trái khi gõ | lsb = xMin (A36), kiemword mục 8 |
| Đuôi râu chìm dựng thành nêm | Đuôi theo cổ, cắt song song trục (như horn5) |
| Dời dấu thanh trái để né râu | Chỉ nâng — dấu lệch trục bị chê |

## 4 · Khi KHÔNG áp dụng

- Không có bản đứng VN: dùng quy trình chung, giữ ý “anchor nghiêng trước”.
- Font nghiêng không có anchor mark / mkmk: xem `serif-dam-cao-hep-nghieng.md` (một trục chuẩn đo từ nét đứng).

---
*build by @nhatmotion*
