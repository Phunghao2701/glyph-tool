#!/usr/bin/env bash
# build.sh SRC.otf|SRC.ttf VERDIR VERSION [NHÃN] — dựng một VER: vnfont → addons (đ Đ, ĩ) → place_hoi → horn5 (râu) → autokern sau râu → sortfeat → stamp → ots
# VERDIR cần: config.json, recipes.json, addons.json, hook_single.json, hoi_place.json, horn5.json (xem SKILL.md mục 4)
# Font gốc .ttf: tự đổi sang SRC.otf (ttf2otf.py) để dựng, cuối cùng trả thêm VFK-<Font>.ttf (otf2ttf.py, giữ hinting chữ gốc).
# Tên font mặc định "VFK - <tên gốc>", watermark VFK (stamp.py; PREFIX="" giữ tên, MARK="" tắt watermark).
#   horn5.json "src" trỏ tới SRC.otf (bản đã đổi).
# Đặt tên khác (tên người dùng gõ ở ô “Tên font xuất”): FAMILY="Tên khác" bash build.sh … (stamp.py đặt cả family, full, PostScript)
# build by @nhatmotion
set -e
T=$(cd "$(dirname "$0")" && pwd); SRC=$1; V=$2; TTF=""
if [[ "$SRC" == *.ttf ]]; then TTF=$SRC; SRC=${SRC%.ttf}.otf; [ -f "$SRC" ] || python3 -I $T/ttf2otf.py "$TTF" "$SRC"; fi
OUT=$V/VFK-$(basename "${SRC%.*}").otf
python3 -I $T/vnfont.py $SRC $V/A.otf --config $V/config.json --recipes $V/recipes.json | tail -1
python3 -I $T/addons.py $V/A.otf $V/B.otf $V/addons.json >/dev/null
python3 -I $T/place_hoi.py $V/B.otf $V/C.otf $SRC $V/hook_single.json $V/hoi_place.json
if grep -q '"anchor_marks"' $V/config.json; then python3 -I $T/anchor_marks.py $V/C.otf $V/C.otf "${TTF:-$SRC}" $V/config.json; fi   # luật src-marks: dấu theo anchor font gốc
KIT=$T python3 -I $T/horn5.py $V/C.otf $OUT $V/horn5.json | grep -v "^horn5" || true
python3 -I $T/autokern_horn.py $OUT $OUT 50
python3 -I $T/sortfeat.py $OUT
python3 -I $T/stamp.py $OUT $3 $4
python3 -I $T/winfix.py $OUT   # LUÔN cuối cùng: win ≥ mực thật (Word cắt đỉnh dấu chồng) — loi-font/dau-chong-chu-hoa-vuot-dong.md
python3 -m ots $OUT && echo "OK: $OUT"
python3 -I $T/kiemword.py $OUT --fix   # CỔNG KIỂM WORD (27/10): CHƯA ĐẠT thì set -e dừng, không có file để gửi
if [ -n "$TTF" ]; then python3 -I $T/otf2ttf.py $OUT "$TTF" "$SRC" "${OUT%.otf}.ttf" && python3 -I $T/winfix.py "${OUT%.otf}.ttf" && python3 -m ots "${OUT%.otf}.ttf" && python3 -I $T/kiemword.py "${OUT%.otf}.ttf" --fix && echo "OK: ${OUT%.otf}.ttf"; fi
