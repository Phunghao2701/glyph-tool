const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1440, height: 1000 } }); const errs=[]; p.on('pageerror', e => errs.push(e.message));
  await p.addInitScript(()=>{try{localStorage.setItem('vk-cmode','fine')}catch(e){}}); await p.goto('file://' + process.argv[2]); await p.waitForTimeout(1000);
  const v = await p.$('.vk-view'); const vb = await v.boundingBox();
  await p.mouse.dblclick(vb.x+300, vb.y+200); await p.waitForTimeout(500);
  console.log('dblclick font', await p.evaluate(() => getComputedStyle(document.querySelector('.vk-tx, .vk-sp')).fontSize), await v.evaluate(e => [Math.round(e.scrollLeft), Math.round(e.scrollTop)]));
  await p.mouse.move(vb.x+500, vb.y+300); await p.mouse.down(); await p.mouse.move(vb.x+300, vb.y+200, {steps:8}); await p.mouse.up();
  console.log('drag scroll', await v.evaluate(e => [Math.round(e.scrollLeft), Math.round(e.scrollTop)]));
  await p.click('#tab-chinh'); await p.waitForTimeout(300); const h = await (await p.$('#hu11-view')).boundingBox();
  await p.mouse.move(h.x+600, h.y+150); await p.mouse.down(); await p.mouse.move(h.x+300, h.y+150, {steps:8}); await p.mouse.up(); await p.waitForTimeout(300);
  console.log('chinh drag → tab still', await p.evaluate(() => window.__VK_TAB), await p.evaluate(() => document.getElementById('hu11-view').scrollLeft));
  await p.click('#hu11-view g[data-ch="Ở"]', { force: true }).catch(()=>{}); await p.waitForTimeout(500); console.log('click glyph → tab', await p.evaluate(() => window.__VK_TAB), JSON.stringify(errs));
  await b.close();
})();
