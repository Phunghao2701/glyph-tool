"""Dữ liệu cho thanh kéo râu (horn5): nét chữ gốc U O u o, advance, đỉnh U u, x gốc râu U u,
bảng mép phải O o theo y (để kéo Ơ lên / xuống). usage: export_horn5.py horn5.json out.json"""
import sys, os, json
CFGP, OUT = sys.argv[1], sys.argv[2]
CFG0 = json.load(open(CFGP))
sys.argv = [sys.argv[0], CFG0["src"], "x", CFGP]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "horn5.py")).read()
exec(compile(src[:src.index("HORNS = {}")], "horn5", "exec"))
from fontTools.pens.svgPathPen import SVGPathPen
data = {"all": CFG.get("all") or CFG["uc"], "lc_ratio": CFG.get("lc_ratio", 0.9), "lc_wratio": CFG.get("lc_wratio", CFG.get("lc_ratio", 0.9)), "g": {}}
for L in "UOuo":
    n = scm[ord(L)]; body = path_of(sgs, n); sp = SVGPathPen(sgs); sgs[n].draw(sp)
    g = {"d": sp.getCommands(), "w": sgs[n].width}
    top = path_of(sgs, scm[ord("U" if L.isupper() else "u")]).bounds[3]
    if L in "uU":
        g["x0"] = round(ox(body, top - 60), 1); g["top"] = top
        B = body.bounds; g["oy"] = [int(B[1] + (B[3] - B[1]) * 0.35), int(B[3]) - 1]   # mép phải theo y: kéo gốc râu Ư lên / xuống
        g["ox"] = [round(ox(body, y), 1) for y in range(g["oy"][0], g["oy"][1] + 1)]
    else:
        B = body.bounds; g["oy"] = [int(B[1] + (B[3] - B[1]) * 0.5), int(B[3]) - 1]
        g["ox"] = [round(ox(body, y), 1) for y in range(g["oy"][0], g["oy"][1] + 1)]
    data["g"][L] = g
if CFG0.get("hook_params") and os.path.exists(CFG0["hook_params"]):   # thanh kéo “Dấu hỏi” (cùng công thức hook_stroke.py)
    data["hook"] = json.load(open(CFG0["hook_params"]))
json.dump(data, open(OUT, "w"))
print("export_horn5 ok")
