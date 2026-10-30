"""cmpglyph.py OUT.png "label:font.otf:char" ... [--ryan path.json]  side-by-side outlines in font units"""
import sys, json
sys.path.insert(0, __import__('os').path.dirname(__file__))
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from fontTools.ttLib import TTFont
from mplsheet import gpath
def jpath(cs):
    v=[];c=[]
    for cont in cs:
        for op,pts in cont:
            if op=='M': v.append(pts[0]);c.append(Path.MOVETO)
            elif op=='L': v.append(pts[0]);c.append(Path.LINETO)
            elif op=='C': v+=pts;c+=[Path.CURVE4]*3
        v.append((0,0));c.append(Path.CLOSEPOLY)
    return Path(v,c)
items=sys.argv[2:]
fig,ax=plt.subplots(1,len(items),figsize=(4.2*len(items),5),dpi=80)
for a,it in zip(ax,items):
    lab,src,ch=it.split(':',2)
    a.set_aspect('equal'); a.set_xlim(-80,780); a.set_ylim(-120,920); a.set_title(lab); a.axis('off')
    for y in (0,488,640): a.axhline(y,color='#ccc',lw=.6)
    if src.endswith('.json'):
        d=json.load(open(src)); d=d.get('data',d); p=jpath(d['contours']); w=d.get('w',0)
    else:
        f=TTFont(src); gs=f.getGlyphSet(); n=f.getBestCmap()[ord(ch)]; p=gpath(gs,n); w=gs[n].width
    a.add_patch(PathPatch(p,fc='k',ec='none')); a.axvline(0,color='#9cf',lw=.6); a.axvline(w,color='#9cf',lw=.6)
fig.savefig(sys.argv[1])
