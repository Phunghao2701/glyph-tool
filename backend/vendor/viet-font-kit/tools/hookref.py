"""Đo + vẽ so dấu hỏi của các font (font mẫu và VER): tỉ lệ so x-height, rộng / cao, nét đậm / mảnh, bầu giọt, so với thân chữ l.
usage: hookref.py TOOLS_DIR OUT.png '[{"t":"nhãn","f":"font","ch":"ả"}, …]'   → in JSON số đo, ảnh silhouette chuẩn hoá cao 165
Dùng khi người dùng đưa font mẫu để vẽ lại dấu hỏi: học tỉ lệ, không chép nét.
build by @nhatmotion"""
import sys, json
sys.path.insert(0, sys.argv[1])
import qhook
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.basePen import BasePen
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.geometry import box
import numpy as np, shapely
from scipy import ndimage
from skimage.morphology import skeletonize
items=json.loads(sys.argv[3]); out=sys.argv[2]
def cubic(gs,g):
    class Cub(BasePen):
        def __init__(s): super().__init__(gs); s.v=[]
        def _moveTo(s,p): s.v.append(("moveTo",(p,)))
        def _lineTo(s,p): s.v.append(("lineTo",(p,)))
        def _curveToOne(s,a,b,c): s.v.append(("curveTo",(a,b,c)))
        def _closePath(s): s.v.append(("closePath",()))
        def _endPath(s): s.v.append(("closePath",()))
    p=Cub(); gs[g].draw(p); cs=[];cur=[]
    for o,a in p.v:
        cur.append((o,a))
        if o=="closePath": cs.append(cur);cur=[]
    return cs
fig,axs=plt.subplots(1,len(items),figsize=(4*len(items),4.6))
res={}
for ax,it in zip(axs,items):
    f=TTFont(it["f"]); gs=f.getGlyphSet(); cm=f.getBestCmap()
    xh=f["OS/2"].sxHeight; 
    xb=qhook.to_poly(cubic(gs,cm[ord("x")])).bounds; xh=xb[3]
    stem=qhook.to_poly(cubic(gs,cm[ord("l")])); sb=stem.bounds; sw=stem.intersection(box(-999,(sb[1]+sb[3])/2-.5,9999,(sb[1]+sb[3])/2+.5)).bounds; stemw=sw[2]-sw[0]
    P=qhook.to_poly(cubic(gs,cm[ord(it["ch"])]))
    hk=P.intersection(box(-999,xh+20,9999,2000))
    b=hk.bounds; h=b[3]-b[1]; w=b[2]-b[0]
    xs=np.arange(b[0],b[2],1.0); ys=np.arange(b[1],b[3],1.0); X,Y=np.meshgrid(xs,ys); m=shapely.contains_xy(hk,X,Y); d=ndimage.distance_transform_edt(m); sk=skeletonize(m); ww=2*d[sk]
    res[it["t"]]=dict(xh=round(xh),stem=round(stemw),h=round(h),w=round(w),h_xh=round(h/xh,3),w_h=round(w/h,3),thick=round(float(np.percentile(ww,90))),thin=round(float(np.percentile(ww,10))),ball=round(float(2*d.max())),gap=round(b[1]-xh),
                      thick_stem=round(float(np.percentile(ww,90))/stemw,3), ball_stem=round(float(2*d.max())/stemw,3))
    for g in getattr(hk,"geoms",[hk]):
        x,y=g.exterior.xy; ax.fill(np.array(x)-(b[0]+b[2])/2,(np.array(y)-b[1])/h*165,color="k")
        for i in g.interiors: x,y=i.xy; ax.fill(np.array(x)-(b[0]+b[2])/2,(np.array(y)-b[1])/h*165,color="w")
    ax.set_aspect("equal"); ax.set_xlim(-110,110); ax.set_ylim(-10,180); ax.set_title(it["t"]); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig(out,dpi=60)
print(json.dumps(res,ensure_ascii=False,indent=0))
