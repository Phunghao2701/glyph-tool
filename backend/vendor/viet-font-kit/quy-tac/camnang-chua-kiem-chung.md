# Cẩm nang Việt hoá font — chưa kiểm chứng

> build by @nhatmotion

Gộp từ ba tài liệu Ryan gửi ngày 25/10/2026: “Quy tắc thiết kế dấu hỏi khi Việt hoá font”, “Cẩm nang quy tắc Việt hoá font chữ” bản 1 và bản 2. **Bản 2 của cẩm nang này**: đã tìm nguồn chuyên gia cho từng ý.

- **Mặc định: TẮT.** Người dùng mới chỉ dùng kho chuẩn `rules.json`, gồm nguồn chuyên môn có link và số đo trên chính font. Cẩm nang này chỉ được nạp khi người dùng tự bật cho dự án của họ.
- **Cách bật:** `use_packs(['packs/camnang-ryan.json'])` trong `content_rN.py`, hoặc `RULE_PACKS=tools/packs/camnang-ryan.json`. Khi bật, các ý hiện với ký hiệu (†).
- **Nguyên tắc:** ý nào tìm được nguồn chuyên gia thì chuyển sang kho chuẩn và trích nguồn đó. Ở đây chỉ còn những ý chưa tìm được.

## Còn chưa kiểm chứng (6 ý)

| # | Ý | Đã tìm ở đâu, kết quả |
|---|---|---|
| 1 | Dấu thanh chồng còn khoảng **75–85%** dấu đơn. | Google Fonts Guide chỉ nói dấu chồng “có thể nhỏ hơn”, không có tỉ lệ. Con số vẫn chưa kiểm chứng; phần “nhỏ hơn” đã vào kho chuẩn. |
| 2 | Khi thu nhỏ dấu chồng, **tăng nhẹ độ dày nét** để ở 10–12 pt vẫn đậm ngang dấu đơn. | Không thấy nguồn chuyên gia. Ngược lại, Google Fonts Guide dặn cụm dấu chồng **không được quá cao hoặc quá nặng**, nên cần cân hai ý khi chỉnh. |
| 3 | Dấu hỏi phải có **nét móc xuống rõ**, không dẹt tới mức giống sóng ngang của dấu ngã. | Donny Trương phân biệt hỏi / ngã theo thanh điệu, không bàn hình dáng dễ lẫn. Chỉ thấy bàn ở diễn đàn TypeDrawers (không tính là nguồn chuyên gia). |
| 4 | Ở **10–12 pt**, dấu hỏi trong ổ ể ở vẫn phải tách riêng, không bết thành khối. | Không thấy nguồn chuyên gia nêu cỡ chữ cụ thể. |
| 5 | Đặt dấu thanh **lệch phải dấu mũ giúp hạ đỉnh cụm dấu**, ít đụng dòng trên. | Glyphs chỉ nói dấu chồng có thể vượt rất cao và phải chỉnh thông số dọc; Donny Trương nói lệch phải cho nhất quán, không nói nó làm thấp đỉnh. Chưa có số đo kiểm chứng trên nhiều font. |
| 6 | Font **serif / editorial** hay lệch phải; **geometric / sans** hay chính giữa đỉnh. | Bảng khảo sát của Donny Trương (Type Recommendations) có cả hai kiểu ở cả serif lẫn sans, không thấy kết luận theo nhóm font. |

## Đã tìm được nguồn chuyên gia → chuyển sang kho chuẩn

| Ý trong cẩm nang | Nguồn |
|---|---|
| Dấu chồng nhỏ hơn dấu đơn (không có tỉ lệ) | Google Fonts Guide — Diacritics: “Smaller shapes than the stand-alone marks can be used to ensure visual balance, especially in capital letters.” |
| Dấu sắc / huyền: đáy hẹp hơn đỉnh | Donny Trương — Diacritical Details: “On both accents, their bottoms are narrower than their tops.” |
| Dấu chữ hoa là glyph riêng | Google Fonts Guide — Diacritics: “a separate set of `.case` marks should be created … typically wider, shorter, and flatter.” |
| Dấu đơn căn theo trục / tâm chữ | Google Fonts Guide — Diacritics: tâm thị giác thường khác tâm hình học; dấu phải trông cách chữ như nhau. |

## Đã bỏ vì nguồn chuyên môn đã có từ trước

| Ý trong tài liệu | Nguồn |
|---|---|
| Không lấy nguyên “?” thu nhỏ; dấu hỏi nhỏ hơn, chân cụt | Donny Trương — Diacritical Details, Tone Marks |
| Dấu hỏi kép chính giữa đỉnh / lệch phải cho tự nhiên | Donny Trương — Design Challenges, Type Recommendations; Glyphs — Advanced diacritics |
| ở ử: dấu hỏi né râu | Donny Trương — Tone Marks |
| Chữ hoa: dấu dẹt / thấp / sát hơn nhưng không chạm | Donny Trương — Design Challenges; Google Fonts Guide |
| Dấu mũ, dấu trăng, râu ơ ư, dấu ngã, dấu nặng | Donny Trương — Diacritical Details, Design Challenges |
| Dấu kép không đâm dòng trên; độ đậm dấu; không va chữ | Donny Trương — Design Challenges; Glyphs — Vietnamese double accents |

## Nguồn

- Donny Trương — [Diacritical Details](https://vietnamesetypography.com/diacritical-details/) · [Tone Marks](https://vietnamesetypography.com/tone-marks/) · [Design Challenges](https://vietnamesetypography.com/design-challenges/) · [Type Recommendations](https://vietnamesetypography.com/type-recommendations/)
- [Google Fonts Guide — Diacritics](https://googlefonts.github.io/gf-guide/diacritics.html)
- Rainer Erich Scheichelbauer (Glyphs) — [Localize your font: Vietnamese double accents](https://glyphsapp.com/learn/localize-your-font-vietnamese-double-accents) · [Advanced diacritics: multiple anchors](https://glyphsapp.com/learn/advanced-diacritics-multiple-anchors)


---
*build by @nhatmotion*
