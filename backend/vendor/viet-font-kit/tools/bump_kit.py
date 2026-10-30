"""Tự động đánh số phiên bản + đóng zip bộ kit (quy tắc: quy-tac/phien-ban-kit.md).
usage: bump_kit.py KIT_DIR auto|minor|patch|major "ghi chú" [--out DIR] [--dry-run]
       bump_kit.py KIT_DIR init [--out DIR]     # lần đầu: ghi MANIFEST cho số trong VERSION, đóng zip, không bump
- auto: so với MANIFEST.json → có file cấu trúc đổi = MINOR; chỉ file kinh nghiệm đổi = PATCH; không đổi = không bump.
- Zip ra: <tên thư mục kit>-vX.Y.Z.zip, vd viet-font-kit-v1.0.0.zip (trong zip là thư mục viet-font-kit/).
build by @nhatmotion"""
import sys, os, json, hashlib, datetime, zipfile, fnmatch

SELF = {"VERSION", "CHANGELOG.md", "MANIFEST.json"}
# file KINH NGHIỆM → PATCH; mọi file khác → MINOR (cấu trúc)
EXPERIENCE = ["kinh-nghiem-viet-hoa/*", "loi-thuong-gap.md", "quy-tac/camnang-chua-kiem-chung.md", "tools/packs/*"]
SKIP = ["*/__pycache__/*", "*.pyc", ".DS_Store", "*/.DS_Store"]

args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = {a.split("=")[0]: (a.split("=", 1)[1] if "=" in a else True) for a in sys.argv[1:] if a.startswith("--")}
if "--out" in sys.argv:
    i = sys.argv.index("--out"); opts["--out"] = sys.argv[i + 1]; args = [a for a in args if a != sys.argv[i + 1]]
if len(args) < 2: sys.exit(__doc__)
KIT, MODE = os.path.abspath(args[0]), args[1]
NOTE = args[2] if len(args) > 2 else ""
OUT = os.path.abspath(opts.get("--out", os.path.dirname(KIT)))
DRY = "--dry-run" in opts
NAME = os.path.basename(KIT.rstrip("/"))

def files():
    out = {}
    for root, _d, fs in os.walk(KIT):
        for fn in fs:
            p = os.path.relpath(os.path.join(root, fn), KIT).replace(os.sep, "/")
            if p in SELF or any(fnmatch.fnmatch(p, s) or fnmatch.fnmatch("/" + p, s) for s in SKIP): continue
            out[p] = hashlib.sha256(open(os.path.join(root, fn), "rb").read()).hexdigest()[:16]
    return dict(sorted(out.items()))

def kind(p): return "patch" if any(fnmatch.fnmatch(p, e) for e in EXPERIENCE) else "minor"

def zip_kit(ver):
    zp = os.path.join(OUT, "%s-v%s.zip" % (NAME, ver))
    if os.path.exists(zp): sys.exit("đã có %s — không ghi đè bản backup" % zp)
    os.makedirs(OUT, exist_ok=True)
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(list(files()) + [s for s in SELF if os.path.exists(os.path.join(KIT, s))]):
            z.write(os.path.join(KIT, p), NAME + "/" + p)
    return zp

vp = os.path.join(KIT, "VERSION"); mp = os.path.join(KIT, "MANIFEST.json"); cp = os.path.join(KIT, "CHANGELOG.md")
cur = open(vp).read().strip() if os.path.exists(vp) else "1.0.0"
now = files()

if MODE == "init":
    json.dump({"version": cur, "files": now}, open(mp, "w"), ensure_ascii=False, indent=1)
    if not os.path.exists(vp): open(vp, "w").write(cur + "\n")
    print("init", cur, "·", len(now), "file →", zip_kit(cur)); sys.exit(0)

old = json.load(open(mp))["files"] if os.path.exists(mp) else {}
added = [p for p in now if p not in old]; removed = [p for p in old if p not in now]
changed = [p for p in now if p in old and now[p] != old[p]]
touched = added + removed + changed
if MODE == "auto":
    if not touched: print("không có thay đổi — giữ", cur); sys.exit(0)
    level = "minor" if any(kind(p) == "minor" for p in touched) else "patch"
elif MODE in ("minor", "patch", "major"): level = MODE
else: sys.exit("MODE phải là auto / minor / patch / major / init")

M, m, pa = (int(x) for x in cur.split("."))
new = {"major": "%d.0.0" % (M + 1), "minor": "%d.%d.0" % (M, m + 1), "patch": "%d.%d.%d" % (M, m, pa + 1)}[level]
why = {"major": "làm lại toàn bộ", "minor": "cập nhật cấu trúc", "patch": "cập nhật kinh nghiệm"}[level]
lines = ["## %s · %s · %s (%s)" % (new, datetime.date.today().isoformat(), level.upper(), why), ""]
if NOTE: lines += [NOTE, ""]
for lab, xs in (("Thêm", added), ("Sửa", changed), ("Xoá", removed)):
    for p in xs: lines.append("- %s `%s`%s" % (lab, p, "  · kinh nghiệm" if kind(p) == "patch" else ""))
entry = "\n".join(lines) + "\n"
print("%s → %s (%s) · %d file đổi" % (cur, new, level, len(touched)))
print(entry)
if DRY: sys.exit(0)
head = "# Nhật ký thay đổi bộ kit\n\n> Quy tắc đánh số: `quy-tac/phien-ban-kit.md`. Bản mới nhất ở trên.\n\n"
body = open(cp).read() if os.path.exists(cp) else head
body = body[len(head):] if body.startswith(head) else body
open(cp, "w").write(head + entry + "\n" + body)
open(vp, "w").write(new + "\n")
json.dump({"version": new, "files": now}, open(mp, "w"), ensure_ascii=False, indent=1)
print("→", zip_kit(new))
