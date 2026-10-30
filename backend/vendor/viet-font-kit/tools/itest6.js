// thử trang VER: đổi ver, zoom, line biên, mục (*)(†)(#) của ổ, mục nguồn: node itest6.js page.html outprefix
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1300, height: 950 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_TUNNEL|fonts\.g/.test(m.text())) errs.push(m.text()); });
  await pg.goto('file://' + process.argv[2]); await pg.waitForTimeout(900);
  const v = pg.locator('#vv'), out = {};
  out.tag0 = await v.locator('.vtag').textContent();
  const w = {};
  for (const t of (process.env.VERS || 'VER 3,VER 4,VER 5B,VER 5').split(',')) { await v.locator('.vtab[data-tag="' + t + '"]').click(); await pg.waitForTimeout(150); w[t] = [await v.locator('.vtag').textContent(), await v.locator('.sptx').evaluate(e => e.style.fontFamily), await v.locator('.spw').textContent()]; }
  out.vers = w;
  await v.locator('[data-z="l"]').click(); await v.locator('[data-z="-"]').click();
  await v.screenshot({ path: process.argv[3] + 'v.png' });
  await pg.fill('#ed-find', 'ổ'); await pg.waitForTimeout(200); await pg.locator('.ed-list .ed-chip').first().click(); await pg.waitForTimeout(300);
  out.groups = await pg.locator('.ed-whyg').allTextContents();
  await pg.evaluate(() => document.querySelectorAll('details').forEach(d => d.open = true));
  await pg.locator('.ed-why').screenshot({ path: process.argv[3] + 'why.png' });
  await pg.locator('.sec[data-sec="N"]').screenshot({ path: process.argv[3] + 'n.png' });
  await pg.setViewportSize({ width: 390, height: 800 }); await pg.waitForTimeout(300);
  out.mobileSW = await pg.evaluate(() => document.documentElement.scrollWidth);
  out.errs = errs; console.log(JSON.stringify(out, null, 1)); await b.close();
})();
