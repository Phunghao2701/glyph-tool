// thử bản chốt: gõ thử có zoom/kern, trục thẳng, mục (*) trích nguồn khi chọn chữ ổ, zoom “Xem trong chữ”: node itest5.js page.html outprefix
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error' && !/ERR_TUNNEL|fonts\.g/.test(m.text())) errs.push(m.text()); });
  await pg.goto('file://' + process.argv[2]); await pg.waitForTimeout(800);
  const out = {};
  const sp = pg.locator('#sp1'); const fs0 = await sp.locator('.sptx').first().evaluate(e => getComputedStyle(e).fontSize);
  await sp.locator('[data-z="-"]').click(); await sp.locator('[data-z="-"]').click();
  out.spec = [fs0, await sp.locator('.sptx').first().evaluate(e => getComputedStyle(e).fontSize)];
  await sp.locator('[data-z="k"]').click(); out.kern = await sp.locator('.sptx').first().evaluate(e => getComputedStyle(e).fontKerning);
  out.fontOk = await pg.evaluate(() => document.fonts.check('32px "Font VN"', 'ổ') && document.fonts.check('32px "FV-v1003"', 'ổ'));
  await sp.screenshot({ path: process.argv[3] + 'spec.png' });
  await pg.fill('#ed-find', 'ổ'); await pg.waitForTimeout(200); await pg.locator('.ed-list .ed-chip').first().click(); await pg.waitForTimeout(300);
  out.axis = await pg.locator('#ed-axis text').allTextContents();
  out.why = (await pg.locator('.ed-why').innerText()).slice(0, 900);
  const pv = pg.locator('.ed-zoom'); await pv.locator('select').selectOption('16'); await pg.waitForTimeout(100);
  out.pvW = await pg.locator('.ed-pv svg').evaluate(e => e.style.width);
  await pv.locator('select').selectOption('0');
  const ed = pg.locator('#ed'); await ed.scrollIntoViewIfNeeded();
  await ed.screenshot({ path: process.argv[3] + 'ed.png' });
  await pg.locator('.sec[data-sec="N"]').screenshot({ path: process.argv[3] + 'src.png' });
  await pg.setViewportSize({ width: 390, height: 800 }); await pg.waitForTimeout(300);
  out.mobileSW = await pg.evaluate(() => document.documentElement.scrollWidth);
  out.errs = errs; console.log(JSON.stringify(out, null, 1)); await b.close();
})();
