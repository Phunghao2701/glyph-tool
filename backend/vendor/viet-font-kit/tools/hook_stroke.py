"""Dấu hỏi VẼ LẠI theo kết cấu nét của font (không nén dấu ? — nén làm đổi tỉ lệ thanh / đậm):
đường tâm hình móc (đầu giọt bên trái → vòm → thân chéo → chân cụt), bề dày đổi theo hướng nét như font serif trục đứng:
nét chạy dọc = đậm (`thick`), chạy ngang = mảnh (`thin`); đầu là GIỌT thuôn dần (`ball` → `neck` trên quãng `tear_len`,
mũ `tear_p`) như tai chữ g; chân cụt cắt phẳng.
LUẬT (người dùng 26/10): chữ g có tai giọt → dấu hỏi vẽ theo giọt đó (độ dày, độ bầu). "from_g": đo tai g của chính font
(bầu = vòng tròn nội tiếp lớn nhất, cổ = chỗ mảnh nhất, quãng thuôn = chiều dài tai) rồi nhân "ear_scale".
usage: hook_stroke.py OUT.json cfg.json [FONT]     → contours local (đáy-giữa = 0,0) cho config "marks": {"hook": …}
       hook_stroke.py --measure-g FONT              → in số đo tai g
cfg: {"h":165, "thick":37, "thin":11, "ball":46, "neck":15, "tear_len":70, "tear_p":1.0, "foot":22, "stress":1.8, "cut":8,
      "scale":1.0, "grow":0, "from_g": true, "ear_scale":0.62, "path":[[x,y], …]}
  path = đường tâm: điểm đầu + từng bộ 3 điểm (2 tay nắm + điểm cuối) của các đoạn cong bậc 3.
  "profile": [[t, w], …] = bề dày theo chiều dài nét học từ font mẫu (hook_from_ref.py), "wscale" nhân thêm.
  "mode": "taper" = ĐẬM ĐẦU THUÔN DẦN VỀ ĐUÔI: ball (đầu) → foot (đuôi) theo chiều dài nét, mũ "taper_p", "stress_mix" 0–1 pha thanh–đậm.
  Cùng công thức với thanh kéo “Dấu hỏi” ở mục B (slider_ui.html) → số kéo trên trang dùng thẳng ở đây.
build by @nhatmotion"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import marks as MK
from shapely.geometry import box
from shapely.affinity import scale as sscale, translate

def measure_g(font):
    """tai chữ g: phần nét trên x-height bên phải thân g. → bầu (D), cổ (mảnh nhất), dài tai"""
    import numpy as np, shapely, qhook
    from scipy import ndimage
    from skimage.morphology import skeletonize
    from fontTools.ttLib import TTFont
    from fontTools.pens.recordingPen import RecordingPen
    f = TTFont(font); gs = f.getGlyphSet(); cm = f.getBestCmap()
    r = RecordingPen(); gs[cm[ord("g")]].draw(r); cs, cur = [], []
    for o, a in r.value:
        cur.append((o, a))
        if o in ("closePath", "endPath"): cs.append(cur); cur = []
    g = qhook.to_poly(cs); x0, y0, x1, y1 = g.bounds
    xh = getattr(f["OS/2"], "sxHeight", 0) or 500
    ear = g.intersection(box((x0 + x1) / 2, xh - 10, x1 + 10, y1 + 10))
    if ear.is_empty: return None
    ex0, ey0, ex1, ey1 = ear.bounds
    xs = np.arange(ex0, ex1, 1.0); ys = np.arange(ey0, ey1, 1.0); X, Y = np.meshgrid(xs, ys)
    m = shapely.contains_xy(ear, X, Y); d = ndimage.distance_transform_edt(m)
    sk = skeletonize(m); rr, cc = np.nonzero(sk); w = 2 * d[rr, cc]
    D = float(2 * d.max()); bi = np.unravel_index(d.argmax(), d.shape); bx, by = xs[bi[1]], ys[bi[0]]
    ok = (ys[rr] > ey0 + 12) & (w > 12)                          # bỏ vệt mảnh giả ở mép cắt
    if not ok.any(): return {"ball": round(D), "neck": round(D / 3), "len": round(D * 1.6)}
    neck = float(w[ok].min()); far = np.argmax(np.hypot(xs[cc[ok]] - bx, ys[rr[ok]] - by))
    L = float(np.hypot(xs[cc[ok]][far] - bx, ys[rr[ok]][far] - by)) * 1.15 + D / 2
    return {"ball": round(D), "neck": round(neck), "len": round(L)}

if sys.argv[1] == "--measure-g":
    print(json.dumps(measure_g(sys.argv[2]))); sys.exit(0)

OUT, CFG = sys.argv[1], json.load(open(sys.argv[2]))
FONT = sys.argv[3] if len(sys.argv) > 3 else CFG.get("font")
if CFG.get("from_g") and FONT:
    G = measure_g(FONT)
    if G:
        es = CFG.get("ear_scale", 0.62)
        CFG.setdefault("ball", round(G["ball"] * es)); CFG.setdefault("neck", round(G["neck"] * es)); CFG.setdefault("tear_len", round(G["len"] * es))
        print("tai g: bầu %d · cổ %d · dài %d → × %.2f" % (G["ball"], G["neck"], G["len"], es))

def hook_geom(C):
    P = C["path"]; thick, thin, ball, foot = C.get("thick", 37), C.get("thin", 11), C.get("ball", 46), C.get("foot", 22)
    neck = C.get("neck", thin); tl = C.get("tear_len", 60); tp = C.get("tear_p", 1.0); stress = C.get("stress", 1.8)
    pts = []
    for i in range(1, len(P), 3):
        seg = MK.bez(tuple(P[i - 1]), tuple(P[i]), tuple(P[i + 1]), tuple(P[i + 2]), 40)
        pts += seg if not pts else seg[1:]
    n = len(pts) - 1; ws = []; s = 0
    S = sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, n + 1)) or 1
    for i, p in enumerate(pts):
        if i: s += math.hypot(p[0] - pts[i - 1][0], p[1] - pts[i - 1][1])
        a, b = pts[max(0, i - 1)], pts[min(n, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
        if C.get("profile"):   # bề dày học từ font mẫu (hook_from_ref.py): nội suy theo chiều dài nét, × "wscale"
            pr = C["profile"]; t_ = s / S; j = 0
            while j < len(pr) - 2 and pr[j + 1][0] < t_: j += 1
            (ta, wa), (tb, wb) = pr[j], pr[j + 1]
            w = (wa + (wb - wa) * max(0.0, min(1.0, (t_ - ta) / ((tb - ta) or 1)))) * C.get("wscale", 1.0)
            w *= 1 + (C.get("ball_k", 1.0) - 1) * max(0.0, 1 - t_ / 0.15)          # bầu giọt ×
            w *= 1 + (C.get("foot_k", 1.0) - 1) * max(0.0, (t_ - 0.85) / 0.15)    # chân ×
            ws.append(w); continue
        if C.get("mode") == "taper":
            # “đậm đầu thuôn dần về đuôi”: bề dày giảm đều từ đầu (ball) tới đuôi (foot) theo chiều dài nét, mũ taper_p;
            # stress_mix > 0 pha thêm chút thanh–đậm theo hướng nét
            w = ball + (foot - ball) * (s / S) ** C.get("taper_p", 1.0)
            mx_ = C.get("stress_mix", 0.0)
            if mx_: w *= (1 - mx_) + mx_ * (0.55 + 0.45 * abs(dy / L))
            ws.append(w); continue
        w = thin + (thick - thin) * abs(dy / L) ** stress          # trục đứng: nét dọc đậm, nét ngang mảnh
        if s < tl: w = max(w, ball + (neck - ball) * (s / tl) ** tp)   # đầu giọt thuôn như tai g
        t = i / n
        if t > 0.85: w = w + (foot - w) * ((t - 0.85) / 0.15)        # chân cụt
        ws.append(w)
    g = MK.vstroke(pts, ws)
    x0, y0, x1, y1 = g.bounds
    g = g.intersection(box(-999, y0 + C.get("cut", 8), 999, 999))
    if C.get("grow"): g = g.buffer(C["grow"], join_style="round")
    x0, y0, x1, y1 = g.bounds
    k = C.get("h", 165) / (y1 - y0) * C.get("scale", 1.0)
    g = sscale(g, k, k, origin=(0, 0)); x0, y0, x1, y1 = g.bounds
    return translate(g, -(x0 + x1) / 2, -y0), k

g, k = hook_geom(CFG)
cs = MK.poly_to_contours(g, simplify=0.35)
json.dump([[[o, [[round(v, 1) for v in p] for p in a]] for o, a in c] for c in cs], open(OUT, "w"))
json.dump({kk: CFG[kk] for kk in ("h", "thick", "thin", "ball", "neck", "tear_len", "tear_p", "foot", "stress", "cut", "path", "mode", "taper_p", "stress_mix", "profile", "wscale", "ball_k", "foot_k") if kk in CFG},
          open(os.path.splitext(OUT)[0] + ".params.json", "w"))
print("hook_stroke", [round(v) for v in g.bounds], "đậm %.0f · mảnh %.0f · giọt %.0f → cổ %.0f (× %.2f)" % (
      CFG.get("thick", 37) * k, CFG.get("thin", 11) * k, CFG.get("ball", 46) * k, CFG.get("neck", CFG.get("thin", 11)) * k, k))
