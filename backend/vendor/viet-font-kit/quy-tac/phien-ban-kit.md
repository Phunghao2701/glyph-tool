# Quy tắc phiên bản Việt Font Kit

> build by @nhatmotion

Bộ kit (đổi tên từ `viet-hoa-font-kit` 1.11.0 thành **Việt Font Kit** 1.0.0 ngày 26/10) đánh số theo dạng **MAJOR.MINOR.PATCH** (vd `1.1.0`). Số hiện tại ghi ở file `VERSION` ở gốc kit. Mỗi bản đóng gói là một file zip riêng, **tên có số phiên bản**, để giữ làm backup và biết ngay bản nào mới:

```
viet-font-kit-v1.0.0.zip
viet-font-kit-v1.1.0.zip
viet-font-kit-v1.1.1.zip
```

Trong zip vẫn là một thư mục `viet-font-kit/` (không kèm số; tên zip lấy theo tên thư mục kit) để lời nhắn mẫu trong README dùng được cho mọi bản.

## Khi nào bump số nào

| Loại thay đổi | Bump | Ví dụ |
|---|---|---|
| **Cập nhật cấu trúc quan trọng** | MINOR: `1.0.0 → 1.1.0` (PATCH về 0) | Thêm / xoá / đổi tên script trong `tools/`; sửa logic script (cách dựng dấu, định dạng file đọc / ghi); đổi quy trình trong `SKILL.md`; thêm / sửa luật trong `quy-tac/` (trừ cẩm nang); đổi bố cục thư mục, mẫu trang duyệt (`tpl/`, `build_page.py`, `editor.js`, `slider_ui.html`), mẫu config, `README.md`, `test-tieng-viet.txt` |
| **Cập nhật kinh nghiệm** | PATCH: `1.1.0 → 1.1.1` | Thêm / sửa file trong `kinh-nghiem-viet-hoa/`; thêm mục vào `loi-thuong-gap.md`; cập nhật cẩm nang chưa kiểm chứng (`quy-tac/camnang-chua-kiem-chung.md`, `tools/packs/`) |
| Làm lại toàn bộ kit, bản cũ không dùng chung được | MAJOR: `1.x.x → 2.0.0` | **Chỉ khi người dùng yêu cầu rõ** |

- Một lần cập nhật có cả hai loại thì lấy mức **cao hơn** (cấu trúc + kinh nghiệm → MINOR).
- Không có file nào đổi thì **không bump**, không đóng zip mới.
- `VERSION`, `CHANGELOG.md`, `MANIFEST.json` là file của chính hệ thống phiên bản, không tính là thay đổi.

## Tự động bump (bắt buộc sau mỗi lần sửa kit)

Mỗi khi Claude sửa bất kỳ file nào trong kit (sửa script, thêm kinh nghiệm sau khi chốt một font…), **trước khi gửi kit cho người dùng** phải chạy:

```bash
python3 -I tools/bump_kit.py <thư mục kit> auto "Ghi chú ngắn: đổi gì, vì sao" --out <thư mục xuất zip>
```

Script sẽ:
1. So từng file với `MANIFEST.json` (mã băm của bản trước) → liệt kê file thêm / sửa / xoá.
2. Tự chọn mức theo bảng trên (`auto`), hoặc ép mức bằng `minor` / `patch` / `major` thay cho `auto`.
3. Ghi số mới vào `VERSION`, thêm mục vào đầu `CHANGELOG.md` (ngày, mức, ghi chú, danh sách file), cập nhật `MANIFEST.json`.
4. Đóng `viet-font-kit-vX.Y.Z.zip` vào thư mục `--out`.

Xem trước mà không ghi gì: thêm `--dry-run`.

Gửi người dùng **file zip có số phiên bản mới** và một dòng: bản mới số mấy, vì sao bump mức đó. Không ghi đè zip cũ.

---
*build by @nhatmotion*
