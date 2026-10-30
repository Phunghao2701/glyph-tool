import sys, unicodedata; sys.path.insert(0,'/home/claude/scripts')
from geom import *; import numpy as np
from fontTools.ttLib import TTFont
from scipy.ndimage import distance_transform_edt
from PIL import Image, ImageDraw
f=TTFont(sys.argv[1]); cm=f.getBestCmap()
def P(c): return np.array(dense(c,1.5))
def md(a,b):
    A=np.vstack([P(c) for c in a]); B=np.vstack([P(c) for c in b])
    return float(np.sqrt(((A[:,None]-B[None])**2).sum(-1)).min())
def thick(c,res=4):
    p=P(c); x0,y0=p.min(0)-4; x1,y1=p.max(0)+4
    im=Image.new('L',(int((x1-x0)*res),int((y1-y0)*res)),0); ImageDraw.Draw(im).polygon([((x-x0)*res,(y1-y)*res) for x,y in p],fill=255)
    return 2*distance_transform_edt(np.array(im)>0).max()/res
for g in ['acutecomb','gravecomb','tildecomb','uni0302','uni0306','uni0309']:
    if g in f.getGlyphOrder(): print(g,'nét dày %.0f'%thick(tt_contours(f,g)[0]))
res={}
for b in 'aăâeêoôơuưAĂÂEÊOÔƠUƯ':
    for t in '̀́̉̃':
        ch=unicodedata.normalize('NFC',b+t); cs=tt_contours(f,cm[ord(ch)])
        top=bbox_pts(tt_contours(f,cm[ord(unicodedata.normalize('NFD',ch)[0])])[0])[3]
        up=sorted([c for c in cs if bbox_pts(c)[1]>top-5],key=lambda c:bbox_pts(c)[1])
        body=[c for c in cs if bbox_pts(c)[1]<=top-5]
        if len(up)==2: res[ch]=('mark-mark',md([up[0]],[up[1]]))
        elif len(up)==1: res[ch]=('mark-body',md(up,body))
for k in ['mark-mark','mark-body']:
    print(k,' '.join('%s%.0f'%(c,v[1]) for c,v in res.items() if v[0]==k))
