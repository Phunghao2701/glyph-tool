# Kho luật chuẩn đặt dấu tiếng Việt

> build by @nhatmotion

Bản đọc của `tools/rules.json` — **mặc định cho mọi người dùng**. Chỉ gồm nguồn chuyên môn có link (*) và lựa chọn / đo kiểm trên chính font (#). Kiến thức chưa kiểm chứng nằm ở `camnang-chua-kiem-chung.md`, mặc định tắt.

Cập nhật: 2026-10-26 (bản 8 — thêm `hook-weight-tilde`: dấu hỏi dày nhất = dấu ngã)

Luật là **tham khảo, không áp cứng**: luôn dựng phương án (VER) cho người dùng chọn trước.

## Luật

| Luật | Áp dụng khi | Nội dung | Nguồn |
|---|---|---|---|
| `axis` | mọi chữ | Font đứng (không nghiêng) → trục đặt dấu là đường thẳng đứng qua tâm thân chữ; chỉ font nghiêng mới nghiêng trục. Không chắc thì hỏi lại. | (#1) |
| `src-marks` | mọi chữ | XÉT DẤU FONT GỐC TRƯỚC: font gốc có anchor dấu (GPOS mark / mkmk) thì mọi chữ Việt xếp dấu đúng như font gốc xếp chuỗi tổ hợp — dấu chồng nằm theo anchor mkmk (thường trên đỉnh dấu mũ / trăng), khe và cỡ dấu như font gốc; dấu font thiếu (hỏi, nặng) mượn anchor dấu trên / dưới, khe bằng dấu sắc / dấu phẩy dưới gốc. Font có dấu sẵn mà không có anchor: giữ nguyên dáng, cỡ, vị trí dấu gốc, dấu mới đặt theo đáy / khe dấu gốc. Chỉ tự đặt dấu (luật mặc định) khi font không có gì để bám. | (#1) |
| `acute-grave` | sắc hoặc huyền | Dấu sắc lệch nhẹ sang phải tâm chữ, dấu huyền lệch nhẹ sang trái; hai dấu cùng dáng, soi gương nhau, phần đáy hẹp hơn phần đỉnh; không rộng quá chữ gốc. | (*1) |
| `hook-shape` | hỏi | Dấu hỏi giống dấu hỏi chấm bỏ chấm nhưng nhỏ hơn, chân cụt; khi đi với dấu khác phải tách rõ khỏi dấu đó. | (*1) (*2) |
| `hook-from-g` | hỏi | Chữ g có tai hình giọt thì dấu hỏi vẽ theo giọt đó: đầu dấu hỏi là giọt thuôn dần lấy bầu, cổ và độ dài từ tai g của chính font (thu theo cỡ dấu), phần còn lại theo nét thanh–đậm của font. Không nén dấu ? để làm dấu hỏi. | (#1) |
| `hook-weight-tilde` | hỏi | Dấu hỏi dày nhất (bầu giọt, đo bằng vòng tròn lớn nhất lọt trong nét) bằng chỗ dày nhất của dấu ngã font gốc, ở mọi cỡ: dấu đơn, chữ hoa, dấu chồng. Dấu co nhỏ (chồng / chữ hoa) thì tăng độ đậm bù lại, không để mảnh đi (tools/hook_fit.py). | (#1) |
| `optical-center` | sắc hoặc huyền hoặc hỏi hoặc ngã hoặc mũ hoặc trăng hoặc nặng | Đặt dấu theo tâm thị giác của chữ — tâm thị giác thường khác tâm hình học; các dấu cần trông cách chữ một khoảng như nhau. | (*6) |
| `stack-adjust` | mũ hoặc trăng hoặc râu ơ ư + sắc hoặc huyền hoặc hỏi hoặc ngã | Khi hai dấu đi cùng nhau, dạng dấu được phép chỉnh lại cho hài hoà, và dấu thanh phải tách rõ khỏi dấu phụ. | (*1) (*2) |
| `stack-smaller` | mũ hoặc trăng + sắc hoặc huyền hoặc hỏi hoặc ngã | Dấu chồng có thể nhỏ hơn dấu đứng một mình để cân thị giác, nhất là trên chữ hoa; khoảng cách giữa các dấu thường sát và phải nhất quán trong cả font; không để cụm dấu quá cao hoặc quá nặng. | (*6) |
| `stack-pos` | mũ + sắc hoặc huyền hoặc hỏi | Dấu thanh đặt bên phải dấu mũ là nhất quán và phổ biến nhất; đặt trên đỉnh cũng được tuỳ font. Cách làm thường gặp: sắc / huyền / hỏi dựa vào điểm neo phụ cạnh dấu mũ, dấu ngã đặt giữa trên dấu mũ. | (*3) (*4) (*8) |
| `stack-top` | mũ + hỏi | Dấu hỏi kép đặt trên đỉnh dấu mũ (khe vd 40) hoặc bên phải dấu mũ (khe tối thiểu với ^ vd 24, tự nâng cho đủ); sắc / huyền chồng bên phải cách ^ ít nhất 18 để khỏi dính ở ố ấ ồ. Dựng cả hai để người dùng chọn. | (#1) |
| `stack-right-height` | mũ + sắc hoặc huyền hoặc hỏi | Dấu hỏi kép lệch phải dấu mũ thường cho đỉnh cụm dấu thấp hơn đặt trên đỉnh — đo lại trên font đang làm. | (#2) |
| `stack-unit` | mũ hoặc trăng + sắc hoặc huyền hoặc hỏi hoặc ngã | Khoảng cách giữa chữ gốc, dấu phụ và dấu thanh đều và tỉ lệ; dấu mũ khi chồng trên chữ thường đặt sát chữ hơn dấu mũ đứng một mình. | (*1) (*3) |
| `circ` | mũ | Dấu mũ hình chevron, đỉnh dày, hai chân mảnh; thường đối xứng; không rộng hơn chữ gốc. | (*1) |
| `breve` | trăng | Dấu trăng cong mềm, không nhọn như caron; đáy dày hơn hai đầu; không dính vào chữ. | (*1) |
| `horn` | râu ơ ư | Râu mọc từ góc trên bên phải chữ o / u; trên u có thể gắn ở đỉnh hoặc thấp hơn trên thân; râu ơ và ư cùng dáng, cùng độ cao vì hay đi liền (ươ). | (*1) (*3) |
| `horn-space` | râu ơ ư | Râu dài tạo khoảng hở trước chữ sau (Ư T); rút ngắn râu tốt hơn là kern cho hai chữ chồng lên nhau. | (*3) |
| `horn-box` | râu ơ ư | Word thân văn bản và Excel không kern, nên phần râu nằm ngoài 2 biên advance sẽ chạm chữ sau. Đo trên font này: bản 1.003 tràn 71 (ơ) / 119 (ư). | (*5) (#2) |
| `horn-hook` | râu ơ ư + sắc hoặc huyền hoặc hỏi hoặc ngã | Dấu thanh trên ơ ư phải tách rõ khỏi râu; dấu dịch trái / nâng lên nhưng đuôi vẫn trên trục chữ. | (*2) (#1) |
| `tilde` | ngã | Dấu ngã đối xứng vì gốc từ chữ N; hai đầu nhỏ hơn đoạn uốn giữa. Font có sẵn dấu ngã đẹp thì giữ. | (*1) |
| `dot` | nặng | Dấu nặng căn giữa dưới chữ, bằng dấu chấm câu / chấm chữ i hoặc nhỏ hơn dấu chấm câu; ỵ dịch sang phải tránh nét đuôi. | (*1) |
| `caps` | sắc hoặc huyền hoặc hỏi hoặc ngã hoặc mũ hoặc trăng + chữ hoa | Chữ hoa có dấu: giảm cỡ hoặc góc của dấu, đặt sát chữ hơn nhưng không chạm — dính dấu vào chữ hoa làm giảm khả năng đọc. Nên có bộ dấu riêng cho chữ hoa (.case): thường rộng hơn, thấp hơn, dẹt hơn dấu chữ thường, để tốn ít chiều cao và không va dòng trên. | (*3) (*6) |
| `leading` | mũ hoặc trăng hoặc râu ơ ư + sắc hoặc huyền hoặc hỏi hoặc ngã + chữ hoa | Chữ hoa có dấu chồng có thể vượt rất cao trên chiều cao chữ hoa; cần chỉnh thông số dọc của font để tránh bị cắt (clipping), vd nâng line biên trên bằng dấu cao nhất. | (*3) (*7) (#1) |
| `i-marks` | chữ gốc i I + sắc hoặc huyền hoặc hỏi hoặc ngã | i có dấu bỏ chấm; dấu chìa nhẹ ra hai bên vẫn được miễn còn rõ. | (*3) |
| `weight` | sắc hoặc huyền hoặc hỏi hoặc ngã hoặc nặng hoặc mũ hoặc trăng hoặc râu ơ ư | Dấu mang nghĩa nên phải đủ đậm, cân với thân chữ; dấu quá mảnh hoặc lệch cỡ làm yếu cả đoạn văn. | (*3) |
| `no-collide` | sắc hoặc huyền hoặc hỏi hoặc ngã hoặc mũ hoặc trăng | Dấu không được va chữ bên cạnh. Word thân văn bản / Excel không kern nên mực của dấu cần nằm trong 2 biên advance. | (*3) (*5) (#2) |
| `punct-space` | mọi chữ | Dấu câu chìa trái (LSB âm) cạnh chữ tròn chìa phải (RSB âm) sẽ dính chữ, nhất là dấu phẩy sau o ơ ổ. Đặt khoảng chừa trái của phẩy bằng dấu chấm của chính font. | (#1) (#2) |

## Nguồn

### * Nguồn chuyên môn — kiểm chứng được

- (*1) [Donny Trương — Vietnamese Typography (Việt Type, 2nd ed.): Diacritical Details](https://vietnamesetypography.com/diacritical-details/)
- (*2) [Donny Trương — Vietnamese Typography: Tone Marks](https://vietnamesetypography.com/tone-marks/)
- (*3) [Donny Trương — Vietnamese Typography: Design Challenges](https://vietnamesetypography.com/design-challenges/)
- (*4) [Donny Trương — Vietnamese Typography: Type Recommendations (khảo sát cách đặt dấu chồng của nhiều font)](https://vietnamesetypography.com/type-recommendations/)
- (*5) [Office Watch — Kerning settings in Microsoft Word and Office](https://office-watch.com/2018/kerning-settings-in-microsoft-office/)
- (*6) [Google Fonts Guide — Diacritics (Stacked diacritics; Design considerations)](https://googlefonts.github.io/gf-guide/diacritics.html)
- (*7) [Rainer Erich Scheichelbauer — Localize your font: Vietnamese double accents (Glyphs, 2018)](https://glyphsapp.com/learn/localize-your-font-vietnamese-double-accents)
- (*8) [Rainer Erich Scheichelbauer — Advanced diacritics: multiple anchors (Glyphs, 2012, cập nhật 2022)](https://glyphsapp.com/learn/advanced-diacritics-multiple-anchors)

### # Lựa chọn và đo kiểm của chính font này

- (#1) Lựa chọn người dùng duyệt trên trang duyệt của chính font đang Việt hoá
- (#2) Đo kiểm trên chính font này: render có / không kern, đo độ rộng dòng và phần mực tràn khỏi 2 biên advance (linecheck.py)

> Nhóm (#) ghi lựa chọn người dùng duyệt và số đo trên chính font đang làm.


---
*build by @nhatmotion*
