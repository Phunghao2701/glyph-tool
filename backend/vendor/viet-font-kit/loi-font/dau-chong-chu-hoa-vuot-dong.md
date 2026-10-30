# Dấu chồng chữ hoa vượt khỏi dòng (Ấ Ầ Ế Ề Ố Ồ cao hơn ascender)

> build by @nhatmotion

**Lỗi font thường gặp khi Việt hoá** (không phải kinh nghiệm theo loại font — không hiện ở mục Kinh nghiệm của trang duyệt), áp dụng mọi loại font: **chữ hoa có hai dấu chồng** (mũ / trăng + dấu thanh) thường cao hơn ascender của font gốc. Hậu quả nằm ở **khoảng dòng** và **chỗ Word cắt mực**, không nằm ở nét chữ. Số liệu dưới đây đo trên một serif display hẹp (UPM 1000, chữ hoa 720, ascender 990 / descender −310). Font khác thì **đo lại**, chỉ giữ cách làm.

Tag: `#vmetrics` `#stacked-caps` `#word-clipping` `#gpos-mark` `#use-typo-metrics`

## 1 · Chuyện đã xảy ra

| Mốc | Đỉnh cao nhất | winAscent | Ghi chú |
|---|---|---|---|
| Font gốc | 990 | 990 | Font gốc không có chữ Việt nào cao hơn ascender. |
| Bước đầu dựng (`vnfont.py`, `vmetrics: keep`) | ≈ 1144 | 1144 | win được nâng theo khung **lúc đó**. typo / hhea giữ 990 / −310. |
| Sau `anchor_marks.py` (luật `src-marks`) | **1180** | 1144 ✗ | Dấu sắc / huyền trên mũ đặt theo anchor `mkmk` của font gốc nên cao hơn. win không ai cập nhật. |
| Lúc xuất (VER 14) | 1180 | **1180** ✓ | Đã thêm `tools/winfix.py` chạy cuối `build.sh`. |

Lỗi này nằm im **từ khi chuyển sang đặt dấu theo anchor tới tận lúc xuất**, vì trang duyệt dùng woff2 trên trình duyệt. Trình duyệt không cắt mực theo winAscent nên trên trang không thấy gì.

### 1b · Tái phát 27/10: đã nâng win mà Word VẪN cắt (`serif.regular.condensed.contrast.ttf` VN)

Người dùng gõ “NGUYỄN MINH NHẬT” ở Word ra “NGUYÊN”, Ấ mất sắc; Premiere / web vẫn đủ dấu. Font đã có win = 1180 ✓ — sửa ở bước 1 **chưa đủ**:

| Thông số | Giá trị | Word dùng? |
|---|---|---|
| win (OS/2 usWinAscent / Descent) | 1180 / 310 | **Không** — vì bit 7 bật |
| typo (OS/2 sTypo…) | 990 / −310 | **Có** → đỉnh dòng 990, cắt 16 chữ ẤẦẨẪ ẮẰẲẴ ẾỀỂỄ ỐỒỔỖ |
| fsSelection bit 7 USE_TYPO_METRICS | bật (do `vnfont.py`) | bắt Word dùng typo |

**Luật:** nâng win KHÔNG đủ. Hoặc tắt USE_TYPO_METRICS (Word dùng win), hoặc nâng typo + hhea cùng win (`vmetrics: fit`). `winfix.py` nay kiểm cả bit 7 (tự tắt khi typo thấp hơn mực, `--check` liệt kê chữ bị cắt); `vnfont.py` thôi bật bit 7. Chi tiết: `loi-thuong-gap.md` A32.

## 2 · Giải phẫu một chữ hoa dấu chồng (đo thật)

```
1180 ┬ đỉnh dấu sắc / huyền        ← Ấ Ầ Ế Ề Ố Ồ (cao nhất)
     │ dấu sắc / huyền  cao 157
1023 ┴ đáy dấu thanh
     │ khe 73 (khe dấu sắc gốc → anchor mkmk)
 950 ┬ đỉnh dấu mũ
     │ dấu mũ  cao 158
 792 ┴ đáy dấu mũ
     │ khe 72
 720 ─ đỉnh chữ hoa
```

Thứ tự đỉnh cao: Ấ Ầ Ế Ề Ố Ồ **1180** · Ắ Ằ 1170 · Ẩ Ể Ổ 1161 · Ẫ Ễ Ỗ 1158 · Ẳ 1151 · Ẵ 1148. Tổng cộng 16 chữ vượt ascender 990.

- **Dấu hỏi không phải thứ cao nhất.** Ẩ chỉ 1161: dấu hỏi chồng chữ hoa đã được làm dẹt × 0,9 (`hook_uc_stack_flat`). Làm dấu hỏi dày lên (luật `hook-weight-tilde`) cũng không đổi chiều cao, vì `hook_stroke.py` luôn đưa dấu về đúng cao `h`.
- **Thứ cao nhất là sắc / huyền trên mũ.** Hai dấu này lấy nguyên nét và anchor của font gốc. Muốn hạ thì phải can thiệp dấu gốc, mà như vậy là trái luật `src-marks`.

## 3 · Ba con số phải phân biệt

| Bảng | Ai dùng | Ảnh hưởng |
|---|---|---|
| `hhea` ascender / descender | macOS, iOS, phần lớn trình duyệt | Khoảng dòng mặc định |
| `OS/2` typo + cờ USE_TYPO_METRICS | Trình duyệt / DirectWrite khi cờ bật | Khoảng dòng mặc định |
| `OS/2` usWinAscent / usWinDescent | **Word, Excel, app GDI trên Windows** | Khoảng dòng **và vùng cắt mực**: mực vượt win bị cắt cụt |

“Giữ khoảng dòng gốc” (quyết định D3) chỉ giữ được trọn vẹn ở hhea / typo. Riêng win thì buộc phải ≥ đỉnh cao nhất, nếu không Word cắt đỉnh dấu. Cái giá là Word trên Windows có dòng mặc định cao hơn: (1180 + 310) / (990 + 310) ≈ **+15 %**.

## 4 · Cách làm cho font sau

1. **Vòng đầu:** đo đỉnh cao nhất của bản dựng (`linecheck.py`) và ghi luôn hệ quả cho Word vào thẻ quyết định khoảng dòng. Ví dụ: “Giữ dòng gốc: Mac / Canva / web y nguyên; Word Windows cao hơn ~15 %”.
2. **Mỗi lần đổi cách đặt dấu** (anchor, dấu chồng, cỡ dấu): đo lại đỉnh. Nếu đỉnh tăng hơn 10 đơn vị thì ghi vào “Điểm mới vòng N”.
3. **Lúc xuất:** `build.sh` tự chạy `winfix.py` (win ≥ khung thật, không đụng typo / hhea). Sau đó kiểm `linecheck.py`: dòng `win_asc` phải ≥ “cao nhất”.
4. **Câu báo người dùng** (vào `test-tieng-viet.txt`): ghi đúng chữ cao nhất **đo được**, đừng đoán. Lần này đã ghi nhầm “Ẩ, Ổ” và phải sửa thành “Ấ Ầ Ế Ề Ố Ồ”.
5. Người dùng muốn Word **không** cao dòng thêm thì đưa ra phương án VER rõ ràng để họ chọn. Đừng tự làm:
   - hạ khe mũ – dấu thanh trên chữ hoa (trái luật `src-marks`, phải hỏi);
   - làm dẹt cả dấu sắc / huyền chồng chữ hoa (`caps_stack_flat` < 1);
   - chấp nhận Word cắt đỉnh (không khuyên).

## 5 · Dấu hiệu nhận biết sớm

- Font gốc có GPOS `mkmk` và khe dấu sắc gốc lớn (≥ 60): dấu chồng chữ hoa chắc chắn vượt ascender khá xa.
- `linecheck.py` báo “vượt ascender typo/hhea … cao nhất X” mà `win_asc` < X (hoặc `winfix.py FONT --check` báo ✗): lỗi A30, phải sửa trước khi xuất.
- Trang duyệt (trình duyệt) **không** lộ lỗi cắt của Word. Chỉ đo số mới thấy.

## Khi KHÔNG áp dụng

- Font gốc đã có sẵn chữ Việt (ascender đã tính cho dấu chồng): giữ nguyên vmetrics gốc.
- Người dùng chọn “nới khoảng dòng” (vmetrics theo đỉnh): khi đó typo / hhea cũng tăng, win đi theo sẵn.

Liên quan: `../loi-thuong-gap.md` A30 (win thấp hơn đỉnh dấu) · `../kinh-nghiem-viet-hoa/serif-manh-hep-tuong-phan.md` (font gặp case này) · `../tools/winfix.py` (chỉ cần fontTools, in luôn chữ cao nhất đo được).

> Ghi chú khi nhập vào Việt Font Kit 1.4.0: bản gốc của file đánh số A27 / A28; trong kit này A27, A28 đã dùng cho lỗi khác nên lỗi win đổi thành **A30**. Mục “nhãn name 5” chưa có trong kit này.

---
*build by @nhatmotion*
