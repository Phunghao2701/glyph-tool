import numpy as np
from matplotlib.path import Path
from scipy import ndimage
from skimage.morphology import skeletonize
from fontTools.pens.recordingPen import RecordingPen
def cs_path(cs):
    v=[];c=[]
    for cont in cs:
        for op,a in cont:
            if op=='moveTo': v.append(a[0]);c.append(Path.MOVETO)
            elif op=='lineTo': v.append(a[0]);c.append(Path.LINETO)
            elif op=='curveTo': v+=list(a);c+=[Path.CURVE4]*3
            elif op=='qCurveTo': v+=list(a);c+=[Path.CURVE3]*len(a)
            elif op=='closePath': v.append((0,0));c.append(Path.CLOSEPOLY)
    return Path(v,c)
def thick(cs):
    p=cs_path(cs); e=p.get_extents()
    xs=np.arange(e.x0-5,e.x1+5,1.0); ys=np.arange(e.y0-5,e.y1+5,1.0)
    X,Y=np.meshgrid(xs,ys); m=p.contains_points(np.c_[X.ravel(),Y.ravel()]).reshape(X.shape)
    d=ndimage.distance_transform_edt(m); sk=skeletonize(m); v=d[sk]*2
    return dict(med=round(float(np.median(v))), max=round(float(v.max())), w=round(e.width), h=round(e.height))
