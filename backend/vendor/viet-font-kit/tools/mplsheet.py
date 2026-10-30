import sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
class MP(BasePen):
    def __init__(s,gs): super().__init__(gs); s.v=[]; s.c=[]
    def _moveTo(s,p): s.v.append(p); s.c.append(Path.MOVETO)
    def _lineTo(s,p): s.v.append(p); s.c.append(Path.LINETO)
    def _curveToOne(s,a,b,c): s.v+= [a,b,c]; s.c+=[Path.CURVE4]*3
    def _qCurveToOne(s,a,b): s.v+=[a,b]; s.c+=[Path.CURVE3]*2
    def _closePath(s): s.v.append((0,0)); s.c.append(Path.CLOSEPOLY)
def gpath(gs,n,dx=0,dy=0):
    p=MP(gs); gs[n].draw(p)
    if not p.v: return None
    return Path([(x+dx,y+dy) for x,y in p.v], p.c)
if __name__=='__main__':
    f=TTFont(sys.argv[1]); gs=f.getGlyphSet()
    names=sys.argv[3].split(',') if len(sys.argv)>3 else f.getGlyphOrder()
    cols=int(sys.argv[4]) if len(sys.argv)>4 else 14
    rows=(len(names)+cols-1)//cols
    fig=plt.figure(figsize=(cols*1.3,rows*1.6),dpi=90); ax=fig.add_axes([0,0,1,1]); ax.set_xlim(0,cols*1100); ax.set_ylim(-rows*1300,0); ax.axis('off')
    for i,n in enumerate(names):
        ox=(i%cols)*1100+150; oy=-(i//cols)*1300-950
        ax.plot([ox,ox+gs[n].width],[oy,oy],color='#f88',lw=.6); ax.plot([ox,ox+gs[n].width],[oy+488,oy+488],color='#8cf',lw=.6); ax.plot([ox,ox+gs[n].width],[oy+640,oy+640],color='#cfc',lw=.6)
        pa=gpath(gs,n,ox,oy)
        if pa: ax.add_patch(PathPatch(pa,fc='k',ec='none'))
        ax.text(ox-100,oy-280,n[:20],fontsize=6,family='monospace')
    fig.savefig(sys.argv[2])
