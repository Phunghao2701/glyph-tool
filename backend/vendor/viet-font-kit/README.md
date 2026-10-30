# Việt Font Kit

> Bộ kit Việt hoá font chữ · Nhật Motion's Space

> build by @nhatmotion

**Phiên bản:** xem file `VERSION` (số trong tên zip: `viet-font-kit-vX.Y.Z.zip`; bản trước khi đổi tên là `viet-hoa-font-kit-v1.x.zip`). Thay đổi từng bản: `CHANGELOG.md`.

Gói này có đủ quy trình, quy tắc, kinh nghiệm và công cụ để Việt hoá một **font mới** trong một **chat mới**.

## Mở chat mới

1. Đính kèm **file zip này** (bản có số phiên bản lớn nhất) và **file font** (.otf / .ttf) cần Việt hoá. Có font mẫu đã Việt hoá cùng kiểu thì đính kèm luôn.
2. Gửi lời nhắn mẫu:

> Giải nén file zip bộ kit (viet-font-kit-vX.Y.Z.zip). Đọc README.md, SKILL.md, loi-thuong-gap.md, quy-tac/kho-chuan.md, quy-tac/trang-duyet-artifact.md, rồi chọn file trong kinh-nghiem-viet-hoa/ trùng nhiều tag nhất với font này. Việt hoá font đính kèm: phân tích trước rồi dựng ngay trang duyệt artifact để mình duyệt từng VER (VER 1A dấu chồng bên phải + VER 1B dấu chồng trên đỉnh + VER 1C dấu hỏi từ nửa trên dấu ?), kèm câu hỏi phạm vi và font mẫu. Không xuất file font khi mình chưa chốt VER. Không dùng cẩm nang chưa kiểm chứng.

   - **Font nghiêng đã có bản đứng Việt hoá:** đính kèm cả hai, thêm vào lời nhắn: “font nghiêng, bản đứng đã Việt hoá là font mẫu — dùng tools/nghieng/ và đọc kinh-nghiem-viet-hoa/serif-dam-cao-hep-nghieng.md”.
   - **Font nghiêng .ttf có anchor mark / mkmk (font Google) + bản đứng VN:** dùng `tools/nghieng/tt/` (đọc README trong đó) và `kinh-nghiem-viet-hoa/serif-manh-hep-tuong-phan-nghieng.md`.
   - Máy làm việc có thể chặn pypi / npm: đọc `loi-thuong-gap.md` mục D trước khi cài gói.

3. Mỗi vòng: chọn và ghi góp ý trên trang (mỗi mục có ô góp ý, khung kéo tự lưu; Ctrl+Z hoàn tác mọi thao tác), rồi nhắn “có góp ý trong artifact”.
   - **Claude bản Free:** trang lưu trên trình duyệt; xong mỗi vòng bấm **Xuất chỉnh sửa** (cạnh nút VER, trên cùng) rồi gửi file `.json` vào chat (hoặc chép đoạn chữ rồi dán). Bản Pro / Max / Team tự lưu, không cần bước này. Cần bật *Settings → Capabilities → Create and edit files*. Tab **Hướng dẫn** trên trang tóm tắt lại các bước.
   - **Font đã Việt hoá từ trước gõ trong Word bị mất dấu** (vd “NGUYỄN” ra “NGUYÊN”): gửi file font và nhắn “kiểm Word” — Claude chạy `tools/kiemword.py` sửa rồi gửi lại bản mới.
4. Khi ưng: đặt tên ở ô “Tên font xuất” (mục Xem trước) rồi nhắn “chốt VER 4” (hoặc “chốt VER 3A” khi vòng có nhiều bản) để nhận file font.
5. Sau mỗi font, Claude ghi kinh nghiệm / sửa công cụ vào kit rồi **tự bump phiên bản** (`quy-tac/phien-ban-kit.md`) và gửi lại zip số mới. Giữ các zip cũ làm backup.

## Trong gói có gì

| Đường dẫn | Nội dung |
|---|---|
| `VERSION` · `CHANGELOG.md` · `MANIFEST.json` | Số phiên bản kit, nhật ký thay đổi, mã băm từng file (để tự biết file nào đổi). |
| `quy-tac/phien-ban-kit.md` | Quy tắc bump: cập nhật cấu trúc → MINOR (1.0.0 → 1.1.0), cập nhật kinh nghiệm → PATCH (1.1.0 → 1.1.1). |
| `tools/bump_kit.py` | Tự so file với MANIFEST, tự chọn mức bump, ghi CHANGELOG, đóng zip `viet-font-kit-vX.Y.Z.zip`. |
| `test-tieng-viet.txt` | Mẫu bản test tiếng Việt gửi kèm file font khi chốt VER (đổi `<Tên font>` và số VER): dấu chồng hoa / thường, đủ bảng chữ, câu soi, mục kiểm Word. |
| `SKILL.md` | Quy trình đầy đủ: phân tích → hỏi → dựng VER → trang duyệt → đọc góp ý → chốt → xuất. Có nguyên tắc bắt buộc và checklist. |
| `loi-thuong-gap.md` | Lỗi đã gặp và cách sửa: độ rộng CFF lệch `nominalWidthX` (lỗi tự gây ra), lần đoán nhầm do NFD, cờ monospace, OS/2 sai, râu không song song, lỗi trang ở nền tối… |
| `loi-font/` | **Lỗi kỹ thuật của file font** hay gặp khi Việt hoá, đúng mọi loại font (vd dấu chồng chữ hoa vượt dòng → Word cắt đỉnh, `tools/winfix.py`). Không hiện trên trang duyệt. |
| `kinh-nghiem-viet-hoa/` | Kinh nghiệm theo **loại font**, không ghi tên font: `sans-dam-bo-tron.md`, `serif-dam-cao-hep.md`, `serif-dam-cao-hep-nghieng.md`, `serif-manh-hep-tuong-phan.md`, `serif-manh-hep-tuong-phan-nghieng.md`, `viet-tay-net-deu.md`. `README.md` trong đó hướng dẫn chọn file và viết file mới. |
| `quy-tac/kho-chuan.md` | Luật đặt dấu mặc định có nguồn (Donny Trương, Office Watch…) + số đo trên font. Bản máy đọc: `tools/rules.json`. |
| `quy-tac/trang-duyet-artifact.md` | Quy tắc trang duyệt: hợp đồng artifact (token màu, sáng / tối, db), bố cục Việt Font Kit (thanh viên thuốc, xem trước → ô nhập → khung chỉnh, nạp font mẫu), nút bật / tắt, khung kéo, bàn vẽ, khoá db, kiểm tra. |
| `quy-tac/camnang-chua-kiem-chung.md` | Cẩm nang chưa kiểm chứng. **Mặc định tắt**, chỉ bật khi tự yêu cầu. |
| `tools/anchor_marks.py` | Xếp dấu theo anchor GPOS mark / mkmk của font gốc (luật `src-marks`: xét dấu font gốc trước). `build.sh` tự gọi khi `config.json` có `"anchor_marks"`. |
| `tools/hook_from_ref.py` | Học dáng + thanh–đậm dấu hỏi từ font mẫu đã Việt hoá, dựng theo độ đậm font mới (ra cfg cho `hook_stroke.py`). |
| `tools/hookref.py` | Đo + vẽ so dấu hỏi của font mẫu và các VER (tỉ lệ so x-height, thân chữ). |
| `tools/hook_stroke.py` | Vẽ lại dấu hỏi theo nét thanh–đậm của font, đầu giọt theo tai chữ g (`from_g`; không nén dấu ?). Mẫu: `mau-config/hook_stroke.json`. |
| `tools/ttf2otf.py` · `tools/otf2ttf.py` | Font gốc .ttf: đổi sang CFF để dựng, rồi trả về .ttf giữ hinting chữ gốc (`build.sh` tự gọi khi SRC là .ttf). |
| `tools/build.sh` | Dựng một VER (SRC .otf hoặc .ttf): vnfont → addons (đ Đ) → place_hoi → horn5 (râu) → kern sau râu → stamp (version + tên “VFK - <tên gốc>” + watermark VFK trong file font) → ots. |
| `tools/mau-config/` | Mẫu config.json, horn5.json, hoi_place.json, addons.json. Số mẫu, **phải đo lại** cho font mới. |
| `tools/content_template.py` · `tools/vfk_ui.py` | Mẫu trang duyệt **Việt Font Kit**: đầu trang Nhật Motion's Space / Việt Font Kit / tên phông; thanh viên thuốc Xem trước · Chỉnh dấu · Bàn vẽ · Nguồn + viên thuốc VER chung; ô Tên font xuất; nạp font mẫu so ngay (trên dưới / chồng lớp); trạng thái lưu dạng chip. |
| `tools/quick_vn.py` | Đường dựng **dự phòng** khi máy chặn pypi: chỉ fontTools + numpy + Pillow + scikit-image, cho font .ttf nét đều / viết tay. |
| `tools/slider_ui.html` | Khung kéo râu + dấu thanh + dấu nặng, hoàn tác nhiều bước. Hỗ trợ font nghiêng (`D.slant`, `D.guide`). |
| `tools/nghieng/tt/` | Font nghiêng **TrueType có anchor** từ bản đứng VN: `build_it.py` (dấu theo anchor nghiêng + chép hỏi / nặng / râu từ bản đứng, hợp nét không cần pathops), `half_hook.py`, `measure_gaps.py` (khe dấu). |
| `tools/nghieng/` | Việt hoá **font nghiêng** từ bản đứng đã Việt hoá, chỉ cần fontTools: `build_ver.sh` (build_italic → hornkern → stamp → woff2), `export_hornui_italic.py` (dữ liệu mục B), `axisproof.py` (vẽ trục chuẩn), `measure.py` (khe dấu), `proof.js` (ảnh soi), `shim/brotli.py`. Mẫu config: `mau-config/italic.json`. |
| `tools/t_shots.js` · `tools/t_chitiet_speed.js` | Test trang bố cục Việt Font Kit: chụp Chỉnh dấu 2 chế độ, mở thẻ Kinh nghiệm (đo từng khung hình), lỗi trang · đo thời gian bấm dấu ở Chi tiết. |
| `tools/` (còn lại) | Script font (`vnfont.py`, `hoi.py`, `place_hoi.py`, `horn5.py`, `autokern_horn.py`, `addons.py`, `tone_split.py`, `export_preview.py`, `linecheck.py`, `markpos.py`, `flatpoly.py`, `stamp.py`…), trang duyệt (`build_page.py`, `editor.js`, `tpl/`), test (`itest*.js`). |

## Lưu ý

- Kiểm giấy phép trước khi Việt hoá font thương mại.
- Luật trong kho là **tham khảo**; luôn có phương án để chọn.
- Kit không chứa nét của bất kỳ font nào. Dấu hỏi, chấm i, râu đều dựng lại từ font của bạn.
- Các VER cùng tên font: cài từng bản (gỡ bản cũ trước).
- File font xuất ra mặc định tên “VFK - <tên font gốc>” (file `VFK-<Font>.otf`) và có watermark “VFK” trong thông tin font (phiên bản + mô tả), không ảnh hưởng nét chữ.

---
*build by @nhatmotion*

## Ủng hộ · liên hệ

Đây là một tool nằm trong bộ công cụ mình tự dựng để tối ưu workflow edit video hằng ngày. Việc đóng gói sẵn thế này giúp tiết kiệm token hơn nhiều vì AI không cần phải build lại từ đầu mỗi lần dùng.

☕️ Nếu thấy Việt Font Kit hữu ích cho công việc của bạn, có thể ủng hộ mình chút ‘năng lượng’ qua chiếc ví bên dưới. Giá trị tùy hỷ — từ 2k cái kẹo đến ly cà phê đều là động lực lớn để mình ra thêm nhiều món mới. Cảm ơn mọi người rất nhiều! ✨

Công cụ dành cho mục đích phi thương mại — vui lòng không thương mại hoá những font chưa được cấp phép.

- Liên hệ: nhatmotion@gmail.com
- Ủng hộ: tab **Ủng hộ** trên trang duyệt (mã QR) · ACB 39798267 · NGUYEN MINH NHAT

