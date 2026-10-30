# Kinh nghiệm Việt hoá theo loại font

> build by @nhatmotion

Mỗi file là kinh nghiệm của **một loại font**, không ghi tên font cụ thể — gọi bằng **mã loại** (tag nối bằng dấu chấm: nhóm.độ-đậm.bề-ngang.nét.kiểu), đọc mã là biết tính chất font. Bắt đầu font mới:

1. Phân tích font (SKILL.md mục 1), liệt kê tag của font mới.
2. Chọn file trùng nhiều tag nhất, đọc mục “Vấn đề hay gặp” và “Khi KHÔNG áp dụng”.
3. Số liệu trong file là ví dụ. **Đo lại trên font mới**, chỉ giữ cách làm.
4. Làm xong một font loại mới, viết thêm file cùng khuôn (dòng `**Thẻ:** tên ngắn | ý 1 · ý 2 · ý 3` = nội dung thẻ thu gọn ở trang duyệt, mỗi ý ≤ ~45 ký tự; dòng `**Chữ nền:** <kiểu: didone · serif-dam · sans-tron · viet-tay> | <độ đậm> [| italic]` = chữ “a” mờ to sau thẻ (kiểu mới thì thêm vào `CHU_NEN` trong `tools/vfk_ui.py`); dòng `**Mã loại:**` = tag nối bằng dấu chấm): đặc điểm, tag, hồ sơ, dấu hiệu, vấn đề và cách xử lý, quy trình, sai lầm, khi không áp dụng.

| Mã loại | File | Loại font | Tag chính |
|---|---|---|---|
| `sans.heavy.rounded.tight` | `sans-dam-bo-tron.md` | Sans đậm bo tròn, xếp sát | `#sans` `#heavy` `#rounded-soft` `#monoline` `#tight-spacing` `#kern-dependent` |
| `serif.heavy.condensed.contrast.ball` | `serif-dam-cao-hep.md` | Serif đậm cao hẹp, tương phản, đầu giọt | `#serif` `#heavy` `#condensed` `#extra-tall` `#high-contrast` `#ball-terminals` |
| `serif.heavy.condensed.contrast.ball.italic` | `serif-dam-cao-hep-nghieng.md` | Bản nghiêng thật của loại trên, có bản đứng VN làm mẫu | `#serif` `#heavy` `#italic` `#true-italic` `#has-upright-vn-ref` |
| `serif.regular.condensed.contrast.ttf` | `serif-manh-hep-tuong-phan.md` | Serif display độ đậm thường, hẹp, tương phản rõ, .ttf có hinting | `#serif` `#regular` `#condensed` `#high-contrast` `#ttf` `#gpos-mark` |
| `serif.regular.condensed.contrast.italic.ttf` | `serif-manh-hep-tuong-phan-nghieng.md` | Bản nghiêng thật của loại trên (.ttf, anchor nghiêng sẵn), có bản đứng VN làm mẫu — đã chốt VER 6 | `#serif` `#regular` `#condensed` `#high-contrast` `#italic` `#ttf` `#has-upright-vn-ref` |
| `hand.marker.monoline.ttf-legacy` | `viet-tay-net-deu.md` | Viết tay nét đều (bút dạ), .ttf cũ không GPOS / kern — đã chốt VER 10 | `#handwriting` `#monoline` `#marker` `#ttf` `#no-gpos` `#no-kern` |

Lỗi kỹ thuật dùng chung cho mọi loại (độ rộng CFF, NFD, cờ monospace…) ở `../loi-thuong-gap.md`.

---
*build by @nhatmotion*
