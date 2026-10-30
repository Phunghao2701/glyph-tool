"""hook_fit.py KIT_TOOLS VERDIR ĐÍCH — dấu hỏi dày nhất = ĐÍCH (vd. chỗ dày nhất dấu ngã, đo bằng vòng tròn nội tiếp lớn nhất).
Tạo marks hook / hook_uc / hook_s / hook_s_uc trong VERDIR/config.json: cùng dáng, độ đậm (wscale) bù cho hệ số co của anchor_marks
(hook_uc, hook_stack, hook_uc_stack_flat) để dấu chồng / chữ hoa vẫn dày bằng dấu ngã. Ghi hook_cfg.json, hook_single.json(+params, wcomp).
build by @nhatmotion"""
# tìm wscale cho từng biến thể dấu hỏi để chỗ dày nhất (sau khi anchor_marks co giãn) = đích
import sys,json,subprocess,os,numpy as np,shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.affinity import scale as ssc
from scipy import ndimage
T,V,TARGET=sys.argv[1],sys.argv[2],float(sys.argv[3])
cfg=json.load(open(V+'/hook_cfg.json'));C=json.load(open(V+'/config.json'));AC=C['anchor_marks']
def poly(cs):
    import math
    rings=[]
    for c in cs:
        pts=[];cur=None
        for o,a in c:
            if o=='moveTo':cur=a[0];pts=[cur]
            elif o=='lineTo':cur=a[0];pts.append(cur)
            elif o=='curveTo':
                p0=cur
                for k in range(1,11):
                    t=k/10;u=1-t;pts.append([u**3*p0[i]+3*u*u*t*a[0][i]+3*u*t*t*a[1][i]+t**3*a[2][i] for i in (0,1)])
                cur=a[2]
        if len(pts)>2:rings.append(Polygon(pts).buffer(0))
    # chẵn-lẻ: dấu hỏi 1 contour
    return unary_union(rings)
def maxw(P):
    x0,y0,x1,y1=P.bounds;xs=np.arange(x0-2,x1+2,.5);ys=np.arange(y0-2,y1+2,.5);X,Y=np.meshgrid(xs,ys)
    return ndimage.distance_transform_edt(shapely.contains_xy(P,X,Y)).max()
def gen(ws,out):
    c=dict(cfg);c['wscale']=ws;json.dump(c,open('/tmp/_hc.json','w'))
    subprocess.run(['python3','-I',T+'/hook_stroke.py',out,'/tmp/_hc.json'],check=True,capture_output=True)
    return json.load(open(out))
res={}
cases={'hook':(1,1),'hook_uc':(AC['hook_uc'],AC['hook_uc']),'hook_s':(AC['hook_stack'],AC['hook_stack']),
       'hook_s_uc':(AC['hook_stack']*AC['hook_uc'],AC['hook_stack']*AC['hook_uc']*AC['hook_uc_stack_flat'])}
for key,(sx,sy) in cases.items():
    lo,hi=0.8,3.0
    for _ in range(18):
        m=(lo+hi)/2;cs=gen(m,V+'/_'+key+'.json');w=maxw(ssc(poly(cs),sx,sy,origin=(0,0)))
        if w<TARGET:lo=m
        else:hi=m
    ws=round((lo+hi)/2,3);cs=gen(ws,V+'/hook_'+key+'.json' if key!='hook' else V+'/hook_single.json')
    w=maxw(ssc(poly(cs),sx,sy,origin=(0,0)));res[key]=(ws,round(w,1))
    C['marks'][key]=cs
    if os.path.exists(V+'/_'+key+'.json'):os.remove(V+'/_'+key+'.json')
AC['stack_hook']='hook_s';json.dump(C,open(V+'/config.json','w'),ensure_ascii=False)
cfg['wscale']=res['hook'][0];json.dump(cfg,open(V+'/hook_cfg.json','w'),ensure_ascii=False)
gen(res['hook'][0],V+'/hook_single.json')
pp=V+'/hook_single.params.json';q=json.load(open(pp));q['wcomp']=True;q['wmax']=TARGET;json.dump(q,open(pp,'w'))
print(res)
