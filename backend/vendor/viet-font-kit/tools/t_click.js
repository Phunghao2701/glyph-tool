const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 1000 } }); const errs=[]; p.on('pageerror', e => errs.push(e.message));
  await p.addInitScript(()=>{try{localStorage.setItem('vk-cmode','fine')}catch(e){}}); await p.goto('file://' + process.argv[2]); await p.waitForTimeout(800);
  await p.click('#tab-chinh'); await p.waitForTimeout(400);
  await p.dblclick('#hu11-view g[data-ch="Ở"]', { force: true }).catch(async e => { errs.push('noỞ'); await p.click('#hu11-view rect.hu-hit >> nth=5'); });
  await p.waitForTimeout(900);
  console.log(await p.evaluate(() => [window.__VK_TAB, [...document.querySelectorAll('.ed-bc .bch')].map(x => x.textContent).join(','), document.querySelector('.ed-ttl') ? document.querySelector('.ed-ttl').textContent : '']), JSON.stringify(errs));
  await p.screenshot({ path: process.argv[3] });
  await b.close();
})();
