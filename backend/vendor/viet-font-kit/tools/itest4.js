// thử snap + chế độ thành phần + trục chữ: node itest4.js page.html out.png
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1400, height: 1000 } });
  const errs = []; pg.on('pageerror', e => errs.push(e.message)); pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await pg.goto('file://' + process.argv[2]); await pg.waitForTimeout(800);
  const ed = pg.locator('#ed'); await ed.scrollIntoViewIfNeeded();
  // mở chữ ở
  await pg.fill('#ed-find', 'ở'); await pg.waitForTimeout(200); await pg.locator('.ed-list .ed-chip').first().click(); await pg.waitForTimeout(300);
  const out = {};
  out.axis = await pg.locator('#ed-axis text').allTextContents();
  await pg.locator('[data-tool="comp"]').click();
  const cxs = await pg.locator('#ed-comp .ed-cxd').count(); out.components = cxs;
  // bấm vào tâm thành phần nhỏ nhất ở trên cao (dấu hỏi) — lấy toạ độ màn hình các tâm
  const pts = await pg.$$eval('#ed-comp .ed-cxd', els => els.map(e => { const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }));
  pts.sort((a, b) => a[1] - b[1]); const top = pts[0];
  // bấm hơi lệch tâm để trúng mực
  await pg.mouse.move(top[0], top[1] - 2); await pg.mouse.down();
  out.info1 = (await pg.locator('.ed-info').innerText()).split('\n').slice(0, 3).join(' | ');
  await pg.mouse.move(top[0] + 30, top[1] - 2, { steps: 6 }); await pg.mouse.move(top[0] + 5, top[1] + 1, { steps: 6 });
  out.guides = await pg.locator('#ed-snapg text').allTextContents();
  await pg.screenshot({ path: process.argv[3], clip: await ed.boundingBox().then(r => ({ x: r.x, y: r.y, width: r.width, height: Math.min(r.height, 900) })) });
  await pg.mouse.up();
  out.info2 = (await pg.locator('.ed-info').innerText()).split('\n').slice(0, 3).join(' | ');
  // undo, snap toggle
  await pg.keyboard.press('Control+z');
  await pg.locator('[data-opt="snap"]').click(); out.snapAfterClick = await pg.locator('[data-opt="snap"]').getAttribute('aria-pressed');
  // node drag with snap in select mode on glyph 'a'
  await pg.locator('[data-opt="snap"]').click();
  await pg.locator('[data-tool="select"]').click();
  const nd = await pg.$$eval('#ed-nodes .ed-n', els => els.slice(0, 3).map(e => { const r = e.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }));
  if (nd.length) { await pg.mouse.move(nd[0][0], nd[0][1]); await pg.mouse.down(); await pg.mouse.move(nd[0][0] + 13, nd[0][1] + 9, { steps: 5 }); out.nodeGuides = await pg.locator('#ed-snapg text').allTextContents(); await pg.mouse.up(); }
  out.errs = errs;
  console.log(JSON.stringify(out, null, 1)); await b.close();
})();
