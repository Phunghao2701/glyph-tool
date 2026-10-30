// chụp computed style mọi phần tử trong .vk ở từng tab, sáng + tối → JSON (so trước / sau khi tách CSS)
const { chromium } = require('playwright'); const fs = require('fs');
const P = ['display','position','box-sizing','width','height','margin-top','margin-right','margin-bottom','margin-left','padding-top','padding-right','padding-bottom','padding-left','border-top-width','border-top-style','border-top-color','border-left-width','border-radius','background-color','background-image','color','font-family','font-size','font-weight','font-style','line-height','letter-spacing','text-transform','text-align','text-decoration-line','white-space','opacity','gap','flex-direction','grid-template-columns','overflow-x','overflow-y','cursor','box-shadow','list-style-type','vertical-align','border-collapse','fill','stroke','backdrop-filter','z-index','transform'];
(async () => {
  const b = await chromium.launch(); const res = {};
  for (const theme of ['light', 'dark']) for (const w of [1280, 390]) {
    const p = await b.newPage({ viewport: { width: w, height: 900 }, colorScheme: theme });
    await p.goto('file://' + process.argv[2]); await p.waitForTimeout(900);
    for (const tab of ['xem', 'chinh', 've', 'kn', 'nguon']) {
      await p.evaluate(t => window.__VK_SHOW ? window.__VK_SHOW(t) : document.querySelector('#tab-' + t).click(), tab); await p.waitForTimeout(350);
      if (tab === 'kn') await p.evaluate(() => { const d = document.querySelector('.kn-card, details'); if (d && d.tagName === 'DETAILS') d.open = true; });
      Object.assign(res, await p.evaluate(([P, key]) => {
        const o = {}; const els = [...document.querySelectorAll('.vk *')].filter(e => e.getClientRects().length && !e.closest('svg g, #hu11-view svg *, .ed-cv *'));
        const path = e => { const a = []; while (e && e !== document.body) { const s = e.parentElement ? [...e.parentElement.children].indexOf(e) : 0; a.unshift(e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (typeof e.className === 'string' && e.className ? '.' + e.className.trim().split(/\s+/)[0] : '') + ':' + s); e = e.parentElement; } return a.join('>'); };
        for (const e of els) { const c = getComputedStyle(e); o[key + ' ' + path(e)] = P.map(k => c.getPropertyValue(k)).join('|'); }
        return o;
      }, [P, theme + w + ' ' + tab]));
    }
    await p.close();
  }
  fs.writeFileSync(process.argv[3], JSON.stringify(res)); console.log('snap', Object.keys(res).length); await b.close();
})();
