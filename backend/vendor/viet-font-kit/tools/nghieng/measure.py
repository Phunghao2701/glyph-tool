import sys, runpy, json, unicodedata
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from geo import mindist, slant, cb, bounds
src, ref, cfg = sys.argv[1:4]
sys.argv = ['x', src, ref, '/tmp/_m.otf', cfg]
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()): g = runpy.run_path(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'build_italic.py'))
T = g['T']; NEW = g['NEW']; out = {}
worst = []
for n, e in NEW.items():
    if n in ('dcroat', 'Dcroat'): continue
    cs = e['cs']; k = e['nstatic']; body = cs[:k]; marks = cs[k:]
    if 'horn' in e: body = cs[:k]
    ups = sorted([m for m in marks if cb(m)[1] > 0], key=lambda c: cb(c)[1])
    S = lambda x: slant(x, T)
    r = {}
    if ups: r['body'] = round(mindist(S(body), S([ups[0]])))
    if len(ups) > 1: r['stack'] = round(mindist(S([ups[0]]), S([ups[1]])))
    dn = [m for m in marks if cb(m)[3] < 0]
    if dn: r['dot'] = round(mindist(S(body), S(dn)))
    bu = bounds(cs); r['over_r'] = round(bu[2] - e['w']); r['over_l'] = round(-bu[0])
    r['ymax'] = round(bu[3])
    out[e['ch']] = r
for ch in sorted(out, key=lambda c: (c.isupper(), c)):
    print(ch, out[ch])
