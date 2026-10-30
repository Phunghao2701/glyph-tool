#!/usr/bin/env bash
# build_ver.sh SRC_NGHIENG.otf REF_DUNG_VN.otf VERDIR VERSION [NHÃN]
# Dựng một VER cho font NGHIÊNG từ bản đứng đã Việt hoá: build_italic → hornkern → stamp (version + watermark) → woff2.
# VERDIR cần cfg.json (xem mau-config/italic.json). Chỉ cần fontTools (không cần skia-pathops / shapely / harfbuzz).
set -e
N=$(cd "$(dirname "$0")" && pwd); SRC=$1; REF=$2; V=$3
OUT=$V/VFK-$(basename "${SRC%.*}").otf
python3 -I $N/build_italic.py "$SRC" "$REF" $V/A.otf $V/cfg.json $V/recipes.json | grep -v "^  "
python3 -I $N/hornkern.py $V/A.otf $OUT 50
python3 -I $N/../stamp.py $OUT $4 $5
python3 -I $N/../winfix.py $OUT
python3 - "$OUT" "$V/font.woff2" "$N/shim" <<'PY'
import sys; sys.path.insert(0, sys.argv[3])      # brotli qua libbrotli (ctypes) khi không cài được gói brotli
from fontTools.ttLib import TTFont
f = TTFont(sys.argv[1]); f.flavor = 'woff2'; f.save(sys.argv[2]); print('woff2', sys.argv[2])
PY
rm -f $V/A.otf
