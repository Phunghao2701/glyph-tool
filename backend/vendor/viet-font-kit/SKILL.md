---
name: "viet-font-kit"
description: "Việt hoá font chữ (.otf/.ttf thiếu ậ ặ ơ ư…): dựng đủ chữ Việt từ chính bộ phận của font, duyệt từng VER trên trang artifact có khung kéo và bàn vẽ, chỉ xuất file khi người dùng chốt VER."
---

# Việt Font Kit — Việt hoá font chữ

> build by @nhatmotion

Người dùng đưa một font Latin (thường có sẵn â ô á… nhưng thiếu hỏi, nặng, ă, ơ, ư, đ). Việc của skill:

- thêm đủ **134 chữ Việt có dấu + đ Đ**;
- cho người dùng **duyệt trên một trang artifact** (cùng URL qua mọi vòng) trước khi xuất;
- nhận nét vẽ mẫu / số kéo trên trang rồi **dựng lại cho hợp nét font**;
- bảo đảm font gõ đúng trong **Word, Excel, Canva**, không chỉ đẹp trong Photopea / AE.

Thứ tự: phân tích file → **dựng VER đầu + trang duyệt ngay** (kèm câu hỏi phạm vi, font mẫu) → đọc lựa chọn + góp ý → dựng lại (cùng URL) → **người dùng chốt VER** → xuất + kiểm tra cuối.

Đọc kèm:
- `quy-tac/kho-chuan.md`: luật đặt dấu mặc định, có nguồn.
- `quy-tac/trang-duyet-artifact.md`: cách dựng trang duyệt và hợp đồng artifact.
- `loi-thuong-gap.md`: lỗi đã gặp và cách sửa. **Đọc trước khi dựng.**
- `loi-font/`: lỗi kỹ thuật của file font hay gặp khi Việt hoá (vd dấu chồng chữ hoa vượt dòng → Word cắt đỉnh). Không phải kinh nghiệm theo loại font, không hiện ở mục Kinh nghiệm.
- `kinh-nghiem-viet-hoa/`: kinh nghiệm theo loại font. Chọn file trùng nhiều tag nhất với font mới.

## Nguyên tắc chung (bắt buộc)

- **Không gửi file font nào chưa qua `tools/kiemword.py` (in `KIỂM WORD: ĐẠT`)** — lỗi Word cắt dấu chồng chữ hoa đã lọt ra người dùng (27/10).

0. **Người dùng gửi font yêu cầu Việt hoá → luôn render trang artifact để duyệt từng VER**, ngay trong lượt đầu. Trang có ít nhất một VER dựng theo luật mặc định, mỗi VER một tab gõ thử. **Không hiện VER 0 (font gốc) trên viên thuốc VER** (người dùng 27/10: bỏ luật show VER 0) — so với font gốc thì dùng Nạp font mẫu.
   - **Vòng đầu luôn dựng 3 VER (người dùng 26/10):** VER 1A = dấu thanh **bên phải** dấu mũ / trăng (cách font hay làm), VER 1B = dấu thanh **chồng trên đỉnh** dấu mũ, **VER 1C = VER 1A nhưng dấu hỏi vẽ lại từ NỬA TRÊN dấu `?`** (vòm + cổ, bỏ đuôi cong dưới — không lấy nguyên phần móc của dấu `?`). Để sớm thấy điểm mạnh của font, chốt hướng dấu chồng và hướng dấu hỏi trước khi chỉnh chi tiết. (`config.json` `stack_place` "right" / "top"; đường dự phòng `quick_vn.py --cfg {"stack_place":"top"}` / `{"hook_src":"half"}`.)
   - **Từ vòng 2: VER người dùng thích / VER sửa trước đó + VER hiện tại** (mở sẵn VER hiện tại), không có VER 0. Thêm VER khác chỉ khi đang so phương án. Không trả lời chỉ bằng chữ hay ảnh. Câu hỏi về phạm vi / font mẫu hỏi kèm, không chặn việc dựng trang.
1. **Không tự xuất file font khi người dùng chưa chốt VER.** Trong các vòng duyệt, font chỉ nằm trên trang (woff2 nhúng). Chỉ xuất khi người dùng nói rõ chốt VER nào, hoặc tự xin file.
2. **Luật đặt dấu là tham khảo, không áp cứng.** Luôn dựng phương án cho người dùng chọn.
   - **Mỗi VER mới phải khác đủ để thấy** ở cỡ gõ thử (48–72 px). Đổi nhỏ (vd chỉ đầu giọt dấu hỏi) thì nói rõ trong “Điểm mới” và cho chữ mẫu to, hoặc đưa thêm một hướng khác hẳn để so.
3. **Người dùng thích bản nào thì giữ dáng bản đó**, chỉ chỉnh nhẹ quanh nó.
   - **Chỉ sửa đúng chữ trong yêu cầu (người dùng 27/10).** Một số / luật áp chung (vd `stack_dx` cho mọi dấu chồng) có thể lan sang chữ không được nhắc (ắ Ắ trên dấu trăng). Trước khi đưa VER mới lên trang: `tools/glyphdiff.py VER_cũ.ttf VER_mới.ttf --expect "<chữ trong yêu cầu>"` → chữ đổi NGOÀI yêu cầu thì **hỏi người dùng**: áp đều cho cả nhóm, hay chỉ sửa chữ được nhắc. Chưa hỏi được thì giữ nguyên các chữ đó như VER cũ và ghi rõ trong “Điểm mới”. Thay đổi chung người dùng đã yêu cầu (vd “dấu sắc dài thêm” → mọi á é ó…) thì ghi số chữ bị ảnh hưởng vào “Điểm mới”.
4. **Tên VER theo vòng duyệt (người dùng 27/10):** vòng N chỉ có 1 bản → **VER N**; vòng N có nhiều bản → **VER NA, NB, NC…** (vd vòng 1: VER 1A dấu chồng bên phải · 1B trên đỉnh · 1C dấu hỏi nửa trên dấu ?). Version font = **1.00N** (số vòng), chữ cái vào nhãn name 5: `stamp.py FONT 1.00N NA` → “Version 1.00N NA; VFK”. Cùng tên ở viên thuốc, “So vị trí cũ”, bảng góp ý, thư mục `rN/vers/VER NA/`, woff2 `vNa.woff2` (family `FV-vNa`). Mỗi lượt góp ý mới = vòng mới. VER 0 = font gốc.
5. **Dựng dấu từ bộ phận của chính font** (dấu `?`, giọt chữ g / r, chấm chữ i), không vẽ hình học rời.
   - **Xét dấu font gốc TRƯỚC** (luật `src-marks`): phân tích GPOS `mark` / `mkmk` ngay mục 1. Có anchor → `config.json` `"anchor_marks": {}` để `build.sh` gọi `tools/anchor_marks.py`: mọi chữ Việt xếp dấu y như HarfBuzz xếp chuỗi tổ hợp trên font gốc (dấu chồng theo anchor mkmk, khe + cỡ gốc; hỏi / nặng mượn anchor). Soi VER 0 bằng cách gõ tổ hợp (A + ̂ + ̀) trên trang: trình duyệt tự xếp theo anchor.
   - **Tôn trọng dấu font gốc** khi không có anchor: font có sẵn sắc / huyền / ngã / mũ / trăng thì giữ nguyên dáng, cỡ, vị trí; dấu mới đặt theo dấu gốc (`hoi_place.json` `"gap_src": true` = đáy dấu hỏi bằng đáy dấu sắc gốc; `config.json` `"caps_stack_flat": 1.0` = dấu mũ chữ hoa khi chồng không dẹt).
   - **Dấu hỏi theo tai giọt chữ g** (luật `hook-from-g`): `hook_stroke.py` với `"from_g": true` tự đo tai g (bầu, cổ, độ dài) × `ear_scale`; `--measure-g FONT` để xem số. Mục B có nhóm thanh **Dấu hỏi** cùng công thức (cần `horn5.json` `"hook_params"` trỏ tới `<hook>.params.json`).
   - Hai kiểu dựng dấu hỏi trong `hook_stroke.py`: thanh–đậm theo hướng nét (mặc định) và **`"mode": "taper"` — đậm đầu thuôn dần về đuôi** (đầu `ball` → đuôi `foot`, `taper_p`, `stress_mix` pha thanh–đậm). Người dùng không thấy khác biệt thì đưa hướng khác hẳn, không chỉnh nhỏ.
   - **Dấu hỏi không nén từ `?`** khi font tương phản rõ: nén rồi nở đều làm đổi tỉ lệ thanh / đậm. Vẽ lại bằng `tools/hook_stroke.py` (đường tâm + bề dày theo hướng nét: dọc đậm, ngang mảnh, đầu giọt, chân cụt), mẫu `mau-config/hook_stroke.json`.
6. **Thêm dấu phải hạn chế đổi spacing.** Mỗi VER báo số chữ đổi độ rộng và mức tăng.
7. **Hở spacing do râu thì xử lý bằng kern trước** (`autokern_horn.py`), giữ số râu người dùng đã chốt. Chỉ rút ngắn râu khi người dùng đồng ý.
8. **Đo trước khi kết luận nguyên nhân lỗi.** Xem `loi-thuong-gap.md`: đã từng đoán nhầm lỗi độ rộng CFF là do NFD.
9. **Hỏi font mẫu đã Việt hoá cùng tính chất.** Không có thì tự đề xuất 2–3 font Google Fonts cùng nhóm.
10. Mọi chỗ đặt dấu trả lời được **“vì sao”** bằng luật kèm nguồn. Tách nguồn chuyên môn (có link) khỏi kiến thức chưa kiểm chứng.
11. Không ghi tên font cụ thể vào kinh nghiệm chung. Kinh nghiệm viết theo **loại font** + tag.
12. **Sửa kit thì bump phiên bản** (`quy-tac/phien-ban-kit.md`): cấu trúc → MINOR, kinh nghiệm → PATCH. Chạy `tools/bump_kit.py <kit> auto "ghi chú"` trước khi gửi zip; không ghi đè zip cũ.

## 0 · Chuẩn bị

**Máy chặn pypi (không có skia-pathops / shapely / uharfbuzz)** — font đứng .ttf nét đều / viết tay: dùng đường dự phòng `tools/quick_vn.py SRC.ttf OUT.ttf --recipes recipes.json --horn horn5.json` (chỉ fontTools + numpy + Pillow + scikit-image; dấu lấy từ chính font, dấu hỏi vẽ lại từ khung xương dấu ?, râu theo công thức horn5, hợp nét bằng raster rồi dò viền), sau đó `stamp.py` rồi `winfix.py`. Dữ liệu trang: `nghieng/export_hornui_italic.py VN.otf SRC.otf horn5.json hornui.json 0` (font đứng: góc 0; đổi .ttf → .otf bằng `ttf2otf.py` trước) + `export_editor.py`. Nói rõ với người dùng đây là bản dựng nhanh. Cuối đường này: `winfix.py` → **`kiemword.py --fix`** (không có build.sh gọi hộ).

Giải nén gói vào `scratchpad/kit/` rồi làm việc trong `scratchpad/kit/tools`. File người dùng để thư mục riêng `src/`, font mẫu để `ref/`.

```bash
pip install --break-system-packages fonttools skia-pathops shapely brotli opentype-sanitizer uharfbuzz scikit-image scipy pillow
# Playwright có sẵn trong môi trường cloud: require('playwright'); đừng npm i trong thư mục tools
```

Chạy Python bằng `python3 -I`, truyền đường dẫn file người dùng làm tham số, không chạy từ trong thư mục chứa file tải về.

## 1 · Phân tích font (luôn làm trước)

- **Thiếu ký tự nào**: dùng `getBestCmap`; `mplsheet.py` vẽ bảng glyph.
- **Giấy phép**: xem `OS/2.fsType` và name ID 0 / 13. Font thương mại thì nhắc một câu.
- **Định dạng**: CFF (.otf) thì ghi độ rộng phải trừ `nominalWidthX` (mục 3). **TrueType (.ttf)**: chuỗi dựng chỉ ghi CFF, nên `build.sh` tự đổi `SRC.ttf → SRC.otf` (`ttf2otf.py`: tách composite, đảo chiều contour) rồi cuối cùng trả thêm `VFK-<Font>.ttf` (`otf2ttf.py`: chữ không đổi dùng lại nguyên glyph gốc có hinting, chữ mới đổi sang bậc 2). `horn5.json` `"src"` trỏ tới `SRC.otf`. Hỏi người dùng muốn xuất .ttf, .otf hay cả hai.
- **GPOS có mark / mkmk** (font Google hay có): đây là cách xếp dấu của chính nhà thiết kế → dùng `anchor_marks.py` (luật `src-marks`). Script kern chỉ đụng lookup PairPos; dấu tổ hợp có sẵn (U+0300…) được dùng lại, chỉ thêm dấu thiếu (hỏi, nặng, móc).
- **Cờ monospace sai**: `post.isFixedPitch`, CFF `isFixedPitch`, PANOSE proportion 9. `vnfont.py` tự gỡ.
- **Thông số OS/2 sai**: ví dụ `sxHeight` ghi thấp hơn thật làm `linecheck` báo tràn giả. Đo x-height thật từ chữ x / o.
- **Font đứng hay nghiêng**: `vnfont.py` in `text axis …°`; dưới 1° là đứng. Không chắc thì hỏi.
- **Font nghiêng .ttf có anchor mark / mkmk + bản đứng VN**: `tools/nghieng/tt/build_it.py` — dấu có sẵn theo anchor nghiêng, hỏi / nặng / râu chép từng chữ bản đứng rồi nghiêng quanh anchor; Ư cắt theo giao, râu đè lên thịt serif (A34).
- **Font nghiêng**: tính **một trục chuẩn cho cả font** (góc đo từ nét đứng, không tin `italicAngle`); mọi dấu trên / dưới nằm trên trục đó (lỗi A19, `kinh-nghiem-viet-hoa/serif-dam-cao-hep-nghieng.md`). Có bản đứng đã Việt hoá thì dùng `tools/nghieng/build_ver.sh`.
- **Môi trường trước khi cài gói**: xem `loi-thuong-gap.md` mục D; gói bị chặn thì không thử lại, dùng công cụ có sẵn.
- **Chữ có dấu sẵn**: có sai dấu không (cần `"rebuild"`), rộng / hẹp khác chữ trơn không (`match_base_spacing`).
- **Dấu thanh chồng** đặt trên đỉnh hay bên phải dấu mũ trong font gốc.
- **Độ dày dấu ngã, `calt` / alternates, số cặp kern** (GPOS PairPos).
- **Dấu câu chìa trái** (, ; : . ’) cạnh chữ tròn có dính không. Nếu dính, sửa bằng `"sb_fix"`.
- **Tràn ngang / dọc**: chạy `linecheck.py FONT`, soi ở cỡ nhỏ 10–24 px.

## 2 · Hỏi (kèm trang duyệt đầu tiên, không chờ trả lời mới dựng)

- Phạm vi: 134 chữ hay toàn bộ, kể cả chữ thay thế.
- Ký tự người dùng muốn tự vẽ (giao việc).
- **Font mẫu tham khảo** (luôn hỏi): 1–3 font cùng nhóm, đã có tiếng Việt chuẩn. Nếu người dùng không có, tự tìm trên Google Fonts (OFL) theo **mã loại** của font đang làm (cùng nhóm, độ đậm, bề ngang, tương phản, đứng / nghiêng), lọc thêm “Vietnamese”; đề xuất 1–3 họ rồi hỏi.
- **Không ghi tên font cụ thể trong kit** (người dùng 28/10): font người dùng Việt hoá (nhất là font trả phí) chỉ gọi bằng **mã loại** = tag nối bằng dấu chấm, vd `serif.regular.condensed.contrast.italic.ttf`, `sans.heavy.rounded.tight`, `hand.marker.monoline.ttf-legacy` — đọc mã là biết tính chất font. Mã ghi ở dòng `**Mã loại:**` của file kinh nghiệm, bảng `kinh-nghiem-viet-hoa/README.md`; CHANGELOG / lỗi / quy tắc cũng dùng mã. Tên font chỉ còn ở phần giao diện trang (chữ UI) và bảng chữ nền trong `vfk_ui.py`.
- Tải font Google: `curl -sSL -o ref/X.ttf "https://raw.githubusercontent.com/google/fonts/main/ofl/<thư mục>/<file>.ttf"`. Variable font thì dùng `fontTools.varLib.instancer` để ra đúng độ đậm.
- Soi font mẫu: ả ẩ ở ư Ư ơ Ơ ố ồ ỗ ặ đ Đ, và ? g. Đo bằng `markpos.py` (HarfBuzz) và `flatpoly.py` (font TrueType có qCurveTo).
- **Font mẫu đã Việt hoá CÙNG KIỂU (đứng / nghiêng) là chuẩn cao nhất cho dấu hỏi:** `hook_from_ref.py MẪU.otf SRC.otf cfg.json ả` học khung xương + phân bố thanh–đậm của dấu hỏi font mẫu, dựng lại với bề dày × (thân mới / thân mẫu) và cao theo tỉ lệ x-height; `hook_stroke.py` dựng từ `"profile"` (B có thanh: cỡ, độ đậm ×, bầu giọt ×, chân ×). Cỡ chữ hoa / dấu chồng lấy theo font mẫu: `anchor_marks` `hook_uc`, `hook_stack`, `hook_uc_stack_flat`. Font đứng thì không lấy font mẫu nghiêng.
- **Vẽ lại dấu hỏi theo font mẫu:** `hookref.py` đo dấu hỏi của font mẫu và VER (cao / x-height, rộng / cao, đậm / thân, bầu / thân) → chỉnh `path` + số của `hook_stroke.py`, đưa 2 kiểu để chọn. Trang có khối “Dấu hỏi font mẫu” gõ font mẫu (subset woff2, chỉ vài chữ) cạnh các VER.
- **Chỉ học dáng và tỉ lệ, không chép nét** font mẫu, vì giấy phép khác nhau.

## 3 · Luật kỹ thuật font

**CFF (.otf):**
- Ghi glyph bằng `T2CharStringPen(width - nominalWidthX)`.
- Trước khi lưu, assert độ rộng CFF == `hmtx` cho mọi glyph.

**Bounds:** dùng `BoundsPen` trên nét đã ghép. Bounds của pathops có thể phình ra, làm sai độ rộng.

**Dấu tổ hợp:** 8 dấu rời rộng 0, `ccmp` chèn đầu LookupList. Dấu móc rời U+031B dùng `ccmp` để ghép thành ơ ư dựng sẵn.

**Kern sau râu** (`autokern_horn.py IN OUT 50`):
- Thêm lookup PairPos riêng vào feature kern.
- Thân chữ đứng sau ư ơ đặt như sau u o.
- Râu cách chữ sau ít nhất max(khe gốc, 50).
- Chỉ khép, không nới.

**Thông số dọc:** `"vmetrics": "fit"` khi dấu kép chữ hoa ló khỏi dòng. Nói rõ dòng cao thêm bao nhiêu %.

**Word / Excel / Canva:**
- Word chỉ kern khi bật Font → Advanced → *Kerning for fonts*. Word 365 bật cho Heading, tắt cho Normal. Excel không kern.
- Phần nào chìa ra ngoài 2 biên advance sẽ chạm chữ bên cạnh trong các app không kern.

## 4 · Dựng phương án (VER)

Quy trình một VER: `tools/build.sh SRC.otf final/VER-NA 1.00N NA` (vòng N, bản A; vòng 1 bản thì bỏ nhãn) (SRC.ttf cũng được, xem mục 1). Mẫu config ở `tools/mau-config/`, mọi số trong đó **phải đo lại** cho font mới.

```
vnfont.py   → dựng 134 chữ, dấu tổ hợp, ccmp, sửa cờ
addons.py   → đ Đ (thanh ngang ≈ nét ngang chữ E), thu hẹp ngã trên ĩ Ĩ
place_hoi.py→ dấu hỏi đơn: khe đều theo hoa / thường, tâm lệch phải 3–4 %
horn5.py    → râu ơ ư (kệ + thanh đậm), dấu thanh né râu
autokern_horn.py → kern sau râu
sortfeat.py → sắp lại FeatureList · stamp.py → version, tên “VFK - <tên gốc>”, watermark VFK · ots
```

**Dấu hỏi:**
- Font tương phản (serif thanh–đậm): vẽ lại bằng `hook_stroke.py`, đo `thick` / `thin` theo thân / nét ngang chữ rồi nhân tỉ lệ cỡ dấu. Font nét đều: lấy từ dấu `?` của font (`hoi.py`): bỏ chấm, cắt cuống, thu nhỏ, kéo rộng ~1.25, nở nét 4–7 đơn vị cho khỏi nhạt.
- Dấu hỏi chồng nở dày hơn dấu đơn.
- Đo lòng móc (`qhook.counter_d`) để soi ở cỡ nhỏ.
- Font đứng mà dấu hỏi nằm đúng tâm hình sẽ **trông lệch trái**, vì đầu móc nặng bên trái. Dời phải 3–4 % bề rộng thân.

**Font .ttf: lsb = xMin** cho glyph dựng mới (A36, `tools/fixlsb.py`, kiemword mục 8). **Khe dấu tối thiểu (người dùng 27/10): ≈ 0,75 nét dấu** (dấu ↔ dấu chồng, dấu thanh ↔ râu) — cỡ nhỏ khỏi dính; kiểm bằng `tools/nghieng/tt/measure_gaps.py` (A35).

**Dấu thanh chồng:** luôn dựng đủ hai option. Trộn được từng dấu: `quick_vn` `{"stack_place": "top", "stack_right": ["acute"]}` = chồng trên đỉnh, riêng dấu sắc bên phải dấu mũ. Lệch nhẹ thay vì ra hẳn bên phải: `{"stack_dx": {"acute": 40}}` (đơn vị font, so với giữa dấu mũ), từng chữ: `{"stack_dx_ch": {"ổ": 25}}` (người dùng 27/10: sắc ra hẳn bên phải là “quá lệch xa về bên phải dưới”). **Người dùng tự vẽ vài chữ trên Bàn vẽ rồi bảo “áp dụng cho toàn bộ”** → đo vị trí dấu so với dấu mũ trong bản vẽ (góc trái-dưới dấu − mép phải / đỉnh dấu mũ) → `{"stack_rel": {"acute": [dx, dy], …}}` cho mọi chữ cùng dấu mũ; chữ hẹp chìa quá `stack_overhang` thì dời cả cụm trái (≤ `stack_shift_max` × bề ngang dấu mũ). Đọc bản vẽ: `ArtifactData list fontvn/<slug>-rN/glyphs out_dir=…`. Dấu hỏi khi chồng rộng ngang hơn dấu đơn (`quick_vn` `hook_s_xstretch` 1,35) cho rõ ở cỡ nhỏ (người dùng 27/10). Khe dấu thanh ↔ dấu mũ / trăng ≈ 1 nét dấu (`quick_vn` `stack_gap_k` 0,95): khe 0,55 nét nhìn xa như dính (người dùng 27/10).
- Trên đỉnh dấu mũ: `stack_place:"top"`, `gap`.
- Bên phải dấu mũ: `stack_place:"right"`, `gap_right`.
- Không được chạm ^. Sắc / huyền chồng bên phải cần khe `stack_gap_ag` ≥ ~18.

**Râu ơ ư:**
- **Song song (lỗi nặng nếu sai):** Ư Ơ và ư ơ cùng dáng, cùng đỉnh. Kiểm yMax và ghi số lên trang.
- **Ghép:** râu chạm chữ gốc ở **một điểm**. Gốc râu cắt gọn trong nét (`clip`), không lòi vào lòng chữ, không sửa nét chữ gốc.
- **Ơ:** gốc râu đặt cùng độ cao gốc râu Ư, nhờ vậy cùng đỉnh mà không phải kéo dài râu.
- **Thanh đậm:** từ nét mảnh `thin` dày dần (mũ `p`, bắt đầu từ `t0`) thành đầu giọt `head`.
  - Dùng hàm thuôn đơn điệu. Nhiều mốc smoothstep làm viền gợn sóng.
  - Đầu râu dày ≈ nét đậm nhất của dấu hỏi, đo bằng đường tròn nội tiếp.
- **Một bộ thông số cho hoa và thường:** chữ thường = chữ hoa × `lc_ratio` (dáng) × `lc_wratio` (độ dày).
  - Tham khảo đo đạc: râu thường mảnh hơn hoặc bằng râu hoa, không bao giờ dày hơn.
  - Không chỉnh riêng từng cỡ: làm vậy từng ra ư dày hơn Ư.
- **Dấu thanh trên ơ ư:** dời trái ≤ 40 rồi mới nâng, giữ khe ≥ 28 với râu.

**Độ dày dấu hỏi:** dày nhất = dày nhất của dấu ngã font gốc, ở mọi cỡ (luật `hook-weight-tilde`). Font nét bút (sắc / huyền thuôn đầu–cuối): đưa thêm phương án **theo sắc / huyền** — đầu móc dày = chỗ dày nhất của sắc / huyền, thuôn về chân = chỗ mảnh của chúng (`quick_vn.py` `"hook_weight": "acute_grave"`; người dùng 26/10 thấy dày đều bằng dấu ngã còn nặng). Sau khi có `hook_cfg.json` + `anchor_marks` trong config: `python3 -I tools/hook_fit.py tools final/1.00n 60` (60 = số đo dấu ngã) → tạo marks hook / hook_uc / hook_s / hook_s_uc dày bù co giãn; thanh kéo B tự bù (`wcomp`).

**Dấu trên chữ hoa — đồng bộ (người dùng 26/10, “dấu bị thấp, sửa lại nhớ đồng bộ”):** mọi dấu trên chữ hoa cùng một khe tới đỉnh chữ và nằm trên trục chữ (giữa phần mực 1/4 trên: đỉnh A, giữa 2 càng U), **kể cả chữ có sẵn của font** khi font gốc đặt lệch (vd Ú gốc chìm −36 vào chữ). Khe = trung vị khe hợp lý của chữ ghép sẵn. Chân dấu hỏi chữ hoa nằm trên trục. Chạm râu (Ở Ớ) thì dời trái ≤ 40 rồi mới nâng. Mỗi VER đổi vị trí dấu phải có khối “So vị trí cũ” (`mk_oldnew.py` → `rN/oldnew.html`, tự chèn vào Xem trước).

**Dấu nặng:** dùng đúng contour chấm chữ i, cùng cỡ cho hoa và thường. Theo Donny Trương, dấu nặng bằng dấu chấm câu và chấm i; nếu khác thì phải nhỏ hơn dấu chấm câu.

**Luật song song cho dấu:** cùng loại dấu thì cùng khe tới đỉnh và cùng độ lệch tâm, ví dụ Ỷ Ủ Ả Ỏ thẳng hàng.

**Khi đưa nhiều mức:**
- Kèm số đo: độ rộng tăng, phần tràn, đỉnh cao nhất, khe dấu, lòng móc, lệch trục.
- Kèm câu soi: `ố ấ ồ Ố Ấ`, `ẩ ể ổ Ẩ`, `ở ử`, `“cổ,”`, `Người`, `ƯT`, `ƯƠ TƯƠNG ươ`.

## 5 · Trang duyệt

Xem đầy đủ trong `quy-tac/trang-duyet-artifact.md`. Tóm tắt:

**Mẫu và dữ liệu:**
- Mẫu nội dung: `tools/content_template.py` → chép thành `content_rN.py`.
- Lệnh dựng: `build_page.py tools/tpl rN r1/review.html content_rN.py`, luôn ghi cùng file để giữ cùng URL.
- Dữ liệu khung kéo (chạy trong thư mục có `src/`):
  ```bash
  KIT=tools python3 -I tools/export_horn5.py final/1.00n/horn5.json ui.json
  KIT=tools python3 -I tools/export_preview.py final/1.00n/VFK-<Font>.otf src/<Font>.otf ui.json pv.json
  python3 -I tools/tone_split.py final/1.00n/VFK-<Font>.otf pv.json rN/hornui.json
  ```
- Dữ liệu bàn vẽ: `export_editor.py` ra `rN/editor.json` — tự **đồng bộ recipe với nét thật** của font (sau place_hoi / horn5), in số chữ đồng bộ lại / bỏ; phải là “bỏ 0”.
- **Dữ liệu chỉnh đồng loạt** (tab Chỉnh dấu · Đồng loạt, người dùng 27/10): `export_batch.py VER.ttf rN/batch.json` — tách thân / từng dấu của mọi chữ Việt (mảnh y hệt chữ gốc = thân, mảnh trên đỉnh = dấu trên, dưới đường cơ sở = dấu nặng; 2 dấu trên: đáy thấp hơn = mũ / trăng). Không có file thì trang chỉ hiện Chi tiết.
- **Áp dáng nét dấu** (tab Chỉnh dấu · Chi tiết): đọc db hornui `fontvn/<slug>-r1/horn/v1` trường `shape` {sh,st,fh,ft,xh,xt,nr} → cấu hình `quick_vn` `mark_shape` = `{acute:{h:sh,t:st}, grave:{h:fh,t:ft}, tilde:{h:xh,t:xt}, dot:{round:nr}}` (100 / 0 = giữ nguyên; công thức chung `tools/mark_shape.py`). Vị trí dấu thì áp từ Đồng loạt (`batch_apply.py`).

**Các mục trên trang** (giao diện Việt Font Kit, chi tiết ở `quy-tac/trang-duyet-artifact.md` mục 2):
- Đầu trang giữ cấu trúc cũ: “Nhật Motion's Space” (tác giả, nhỏ trên cùng) → **“Việt Font Kit”** (tên lớn) + nhãn `ver x.y.z` (đọc từ `VERSION`) → “Đang Việt hoá” + tên phông viết bằng chính phông đó + nhãn vòng.
- **Thanh viên thuốc dính**: Xem trước · Chỉnh dấu · Bàn vẽ · Nguồn (kèm số đếm), không đánh A, B, C, **không có mục Tổng hợp** (tóm tắt vẫn tự lưu vào db). Bên phải: **viên thuốc VER chung** cho cả trang. Một mục hiện một lúc.
- **Xem trước:** khung xem → ô nhập chữ → khung chỉnh bên phải: **Tên font xuất** (mặc định “VFK - <tên gốc>”, hiện luôn tên PostScript + tên file, lưu db `fontvn/<slug>-rN/out/name`), cỡ, kern, line biên, **Nạp font mẫu** (hoặc thả file vào khung xem → so ngay, Trên dưới / Chồng lớp).
- **Chỉnh dấu:** khung xem → chữ mẫu ngay dưới (cột trái); cột phải: nút → thanh kéo. **Bấm một chữ trong khung xem → mở đúng chữ đó ở Bàn vẽ.**
- **Bàn vẽ:** khung vẽ + danh sách ký tự → chữ mẫu → “Xem trong chữ”.
- **Kinh nghiệm** (sau Bàn vẽ): mỗi file `kinh-nghiem-viet-hoa/*.md` là một thẻ ngắn (loại font, 1 câu đặc điểm, vài tag), bấm mở rộng đọc hết; thẻ của loại font đang làm có nhãn “đang dùng” (`KN_ACTIVE`). Không hiện `loi-font/`.
- **Trạng thái lưu** chỉ là chip nhỏ trong khung xem của từng mục (“tự lưu”, “đã lưu 22:51”, “chưa lưu được”), không viết câu dài.
- **Chỉnh dấu** = khung kéo (nhóm Râu / Dấu thanh / Dấu nặng; hoàn tác nhiều bước; gốc râu Ư ↓ ↑; nút link chỉ ở thanh link được). Kéo ở đây thì “Xem trong chữ” của Bàn vẽ đổi theo ngay.
- **Bàn vẽ** = bàn vẽ glyph, nhóm bút vector kiểu Illustrator, bản vẽ nhiều chữ kiểu artboard, chép / dán dấu (Ctrl+C / Ctrl+V).
- **Ctrl+Z / Ctrl+Shift+Z (Ctrl+Y)** hoàn tác / làm lại **mọi thao tác** trên trang theo đúng thứ tự qua `__UB` trong `build_page.py`.
- Dòng “Mới” (2–3 ý của vòng) đầu mục Xem trước; ý dựa vào nguồn gắn `cite('id')` → **[n]** bấm nhảy tới mục Nguồn.
- **Không có quyết định chọn VER** — người dùng chốt bằng “chốt VER 4” / “chốt VER 3A”.
- **Phóng to / thu nhỏ chữ: KHÔNG có nút** (người dùng 27/10, bỏ cả viên thuốc − +). Mọi khung xem (Xem trước, Chỉnh dấu, Xem trong chữ, So vị trí cũ): **máy tính lăn chuột = phóng tại chỗ con trỏ** (điểm dưới con trỏ đứng yên), **điện thoại chụm 2 ngón**; **bấm-kéo chuột = kéo khung, bấm đúp = phóng ×2 (Shift: thu)** — cảm giác như Google Maps (người dùng 27/10): trong lúc chụm / lăn chỉ đổi CSS transform (GPU), nhả tay mới dựng lại chữ ở cỡ thật cho nét sắc (`VK.JS` `vkZoom`, touch events, `touch-action: pan-x pan-y`). **CSS riêng cho thành phần** (người dùng 27/10): CSS cũ ở `@layer vk-legacy`, thành phần có `tools/vk_own.css` + CSS trong `vfk_ui.py`; sửa CSS xong luôn so `snap_css.js` / `cmp_snap.py` (xem `quy-tac/trang-duyet-artifact.md`). Khung xem không tô màu cứng (chế độ tối). **Luật `:root/html/body` để ngoài layer** (`tools/vk_base.css`) vì khung artifact chèn `body{background:#fff}`; test trên bản `HOST_OUT=…` giả lập khung. Kính mờ chỉ cho chip thông tin trong khung xem; trang một nền gradient nhẹ, không đường kẻ ngang; thẻ Kinh nghiệm bấm → lớp phủ có nút × (xem `quy-tac/trang-duyet-artifact.md`). **Khung xem giữ đúng cỡ mặc định khi phóng** (người dùng 27/10): lần chạm / lăn đầu khoá chiều cao khung, chữ phóng bên trong, kéo để xem phần ngoài khung. Mỗi mục có ô góp ý.
- **Không còn khối “So vị trí cũ” ở Xem trước** (người dùng 27/10: bỏ — so vị trí cũ đã có ở Chỉnh dấu · Đồng loạt, viền nét đứt). `mk_oldnew.py` vẫn dùng được khi cần ảnh so trong chat.

## 6 · Đọc góp ý và dựng lại

- **Claude bản FREE (người dùng 27/10)**: artifact bản Free không có chỗ lưu (db) → trang tự lưu trên trình duyệt (`tools/vk_localdb.js`, `build_page.py` chèn sẵn), hiện nút **“Xuất chỉnh sửa”** cạnh nút VER. Người dùng gửi file `vfk-chinh-sua-<font>-rN.json` (hoặc dán đoạn chữ bắt đầu “Chỉnh sửa Việt Font Kit (bản Free)”) → chạy `python3 tools/import_edits.py FILE OUT_DIR` → in tóm tắt + góp ý từng mục, ghi `OUT_DIR/db/<đường dẫn>.json` (như ArtifactData out_dir), `batch_params.json` (→ batch_apply.py), `mark_shape.json` (→ quick_vn). Đọc file này thay cho bước đọc db bên dưới. Người dùng dán đoạn chữ thay vì gửi file → lưu đoạn đó ra file .txt rồi chạy import_edits.py như file .json. Xuất bản trang duyệt luôn khai `capabilities: {assets:{}, db:{}, user:{}, downloads:true}` (nút xuất cần `downloads`). ArtifactData trả rỗng mà người dùng nói đã chỉnh → hỏi họ có đang dùng bản Free không, nhắc bấm Xuất chỉnh sửa. Ảnh / file minh hoạ bản Free gửi thẳng trong chat (nút + đính kèm bị ẩn). Bản Pro / Max / Team: không đổi gì.
- **MỖI LƯỢT người dùng nhắn (kể cả khi không nhắc “có fb”), nếu đã có trang duyệt: đọc db của vòng đang hiện TRƯỚC khi làm** — `ArtifactData list collection:"fontvn"` (ghi chú `notesRN`, tóm tắt) + `fontvn/<slug>-rN/glyphs` (nét vẽ, ghi chú từng chữ). Góp ý trên trang không phụ thuộc việc đã chốt VER hay chưa. Lỗi đã gặp 27/10: bỏ sót góp ý vòng 3–4 vì chỉ đọc khi người dùng nhắc.
- **Chỉnh đồng loạt**: đọc thêm `ArtifactData get collection:"fontvn/<slug>-rN/batch" doc_id:"p"` (thông số theo loại dấu: dx, dy, sc %, uy chữ hoa, sx / sy khi chồng; `all` = mọi dấu trên). Áp: `batch_apply.py VER.ttf p.json OUT.ttf` → `winfix.py` → `glyphdiff.py VER cũ OUT --expect <các chữ có dấu đó>` → VER mới (cùng công thức với trang: dấu thanh chồng đi theo dấu mũ / trăng).

- Khi người dùng nhắc trang (“có fb trong artifact”…), đọc bằng `ArtifactData list collection:"fontvn"`:
  - `picks` và `notesRN` của vòng mới nhất;
  - số khung kéo ở `…/horn/v1`;
  - nét vẽ ở `…/glyphs/…`.
- Ưu tiên điều người dùng nói trong chat hơn chip tự lưu.
- Nét người dùng vẽ thì đưa qua `cmpglyph.py`: lấy ý rồi dựng lại bằng nét đều của font.
- Ghi lại trên trang: góp ý cũ → lý do VER mới.

## 7 · Xuất (chỉ khi đã chốt VER)

- **CỔNG KIỂM WORD — BẮT BUỘC, không ngoại lệ (người dùng 27/10, sau lỗi `serif.regular.condensed.contrast.ttf` VN):** mọi file font trước khi gửi (VER thử, bản chốt, font người dùng nhờ sửa) chạy `python3 -I tools/kiemword.py FONT --fix` và **chỉ gửi khi in `KIỂM WORD: ĐẠT`**. Gom 7 lỗi đã gặp: đủ chữ, đỉnh dòng Word (USE_TYPO_METRICS — A32), win (A30), cờ tiếng Việt (A31), hinting, tính năng GSUB/GPOS khai trùng, độ rộng CFF (A1). `build.sh` tự gọi ở cuối; đường `quick_vn` / sửa tay thì tự chạy sau `winfix.py`. Premiere / web / trang duyệt hiện đúng KHÔNG có nghĩa Word đúng.
- **Người dùng gửi font đã Việt hoá (bằng kit cũ hoặc nơi khác) nhờ sửa lỗi Word:** `kiemword.py FONT` (đọc lỗi) → `kiemword.py FONT --fix` → `glyphdiff.py` bản cũ / bản sửa (không được đổi nét) → `stamp.py FONT <version+0.001>` (Windows nhận bản mới) → `kiemword.py` lại → gửi kèm cách cài: tắt hẳn Word → gỡ bản cũ → cài → mở lại.

- **Đọc tên font xuất người dùng đặt trên trang trước:** `ArtifactData get collection:"fontvn/<slug>-rN/out" doc_id:"name"` → `FAMILY="<name>"` cho `build.sh` / `stamp.py`. Không có thì dùng mặc định “VFK - <tên gốc>”.
- `build.sh` (đã gồm stamp + ots), rồi `linecheck.py`.
- **Tên font mặc định:** `stamp.py` đặt family “VFK - <tên font gốc>” (name 1 / 16 / 4), PostScript `VFK-<TenGoc>` (name 6), file `VFK-<Font>.otf` / `.ttf`. Đổi tiền tố bằng `PREFIX`, giữ tên đang có bằng `PREFIX=""`; `FAMILY="…"` trong `build.sh` ghi đè hẳn.
- **Watermark trong file font:** `stamp.py` tự ghi “VFK” vào name 5 (`Version 1.00n; VFK`, Windows hiện ở Properties → Details) và name 10 (mô tả: “Việt hoá bằng VFK · … (Việt Font Kit)”, macOS Font Book hiện). Không ghi tên người, không đụng bản quyền / tác giả gốc. Đổi chữ bằng biến `MARK`, tắt bằng `MARK=""`. Font OFL: tên gốc có “Reserved Font Name” thì hỏi người dùng trước khi giữ tên gốc trong tên mới.
- **`winfix.py` chạy cuối cùng** (build.sh tự gọi): win ≥ mực thật; ghi đúng chữ cao nhất nó in ra vào trang / `test-tieng-viet.txt` (lỗi A30, `loi-font/dau-chong-chu-hoa-vuot-dong.md`).
- Kiểm: CFF width == hmtx, đủ 134/134 + đ Đ, NFC và NFD, có / không kern, câu có dấu câu cạnh chữ tròn.
- Gửi file kèm `test-tieng-viet.txt` (mẫu ở gốc kit: đổi `<Tên font>` và số VER). Các VER cùng family nên cài từng bản: tắt app → gỡ bản cũ → cài bản mới.

## 8 · Cập nhật kit sau mỗi font

- Làm xong một font (đã chốt + xuất): ghi kinh nghiệm theo loại font vào `kinh-nghiem-viet-hoa/`, lỗi mới vào `loi-thuong-gap.md`; sửa script nếu có lỗi công cụ.
- Chạy `python3 -I tools/bump_kit.py <thư mục kit> auto "ghi chú" --out <thư mục xuất>`: tự so `MANIFEST.json`, chọn MINOR (cấu trúc) hay PATCH (kinh nghiệm), ghi `VERSION` + `CHANGELOG.md`, đóng `viet-hoa-font-kit-vX.Y.Z.zip`.
- Gửi người dùng zip số mới kèm một dòng: số mới và vì sao bump mức đó.

## Checklist

- [ ] **`kiemword.py` in `KIỂM WORD: ĐẠT` cho MỌI file font gửi đi** (.otf và .ttf).

- [ ] Phân tích từ file người dùng gửi lượt này? Đã rõ font đứng hay nghiêng? Đã kiểm cờ monospace, OS/2, dấu câu?
- [ ] Đã hỏi font mẫu, hoặc tự đề xuất font Google và soi dấu của nó?
- [ ] Mỗi quyết định có VER để chọn? Dấu chồng có đủ 2 option?
- [ ] Râu song song (yMax Ư = Ơ, ư = ơ)? Chỉ chạm chữ gốc một điểm?
- [ ] Spacing: số chữ đổi độ rộng, kern sau râu?
- [ ] Lượt đầu đã có trang duyệt với **VER 1A (dấu chồng bên phải) + VER 1B (dấu chồng trên đỉnh) + VER 1C (dấu hỏi từ nửa trên dấu ?)**? Tên VER đúng theo vòng (VER N / NA, NB)? Từ vòng 2 có VER trước + VER hiện tại, KHÔNG có VER 0?
- [ ] Trang “Việt Font Kit”: đầu trang tác giả / tên kit / tên phông, thanh viên thuốc (không A–E, không Tổng hợp), thứ tự từng mục đúng mục 5, ô Tên font xuất, nạp font mẫu so được ngay, trạng thái lưu dạng chip, ô góp ý từng mục, sáng / tối, Ctrl+Z cho mọi thao tác, không tràn 390 px, kiểm cả nền tối?
- [ ] Chưa chốt VER thì không gửi file font?
- [ ] Trang có đủ mục Chỉnh dấu (khung kéo)? Bàn vẽ đã kiểm recipe khớp glyph (đ có thanh, ị có chấm)? Font .ttf: “Xem trong chữ” không có lòng chữ đặc / nét gãy (lỗi B Q nhiều điểm)?
- [ ] Câu mẫu có đủ dãy dấu chồng chữ hoa + thường (Ầ Ấ Ẩ Ẫ Ậ …)?
- [ ] Font nghiêng: một trục chuẩn, đã soi `ịỊạẠọỌụỤ` bằng `axisproof.py`? ị đặt theo trục qua tâm thân + chấm i?
- [ ] VER đổi vị trí dấu: trang có lớp nét đứt vị trí cũ (bật / tắt)?
- [ ] Font tĩnh: không còn chồng nét (`tools/nghieng/overlapcheck.py`)?
- [ ] Dấu chồng cùng loại có khe bằng nhau trên mọi chữ (ầ = ề = ồ, Ấ = Ế = Ố)? Xem cột `stack` của `measure.py`.
- [ ] Xuất: đã đọc tên người dùng đặt (`…/out/name`)? ots 0, CFF width == hmtx, NFC + NFD, version = VER, tên “VFK - <tên gốc>”, có watermark VFK (name 5 + 10)?
- [ ] Có sửa kit? Đã chạy `bump_kit.py … auto` và gửi zip có số phiên bản mới?

---
*build by @nhatmotion*
