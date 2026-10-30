const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const S = process.argv[3]; const errs = [];
  for (const [w, th] of [[1280, 'dark'], [390, 'light']]) { const c = await b.newContext({ viewport: { width: w, height: 1000 }, isMobile: w < 500, hasTouch: w < 500, colorScheme: th }); const p = await c.newPage();
    p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error' && !/googleapis|ERR_/.test(m.text())) errs.push(m.text()); });
    await p.goto('file://' + process.argv[2]); await p.waitForTimeout(900); await p.evaluate(() => window.__VK_SHOW('chinh')); await p.waitForTimeout(400);
    const st = await p.evaluate(() => ({ batchVisible: !document.getElementById('vk-batch').hidden, huHidden: document.querySelector('#p-chinh .hu11-wrap, #p-chinh .hu11') ? document.querySelector('#p-chinh .hu11-wrap, #p-chinh .hu11').closest('[hidden]') !== null : 'n/a', glyphs: document.querySelectorAll('.vb-rows svg').length, tabs: [...document.querySelectorAll('.vb-tabs button')].map(b => b.textContent).join('|') }));
    console.log(w, JSON.stringify(st));
    await p.evaluate(() => window.scrollTo(0, document.getElementById('p-chinh').getBoundingClientRect().top + scrollY - 60)); await p.waitForTimeout(200);
    await p.screenshot({ path: S + 'vb-' + w + '.png', fullPage: false });
    // kéo thanh dọc dấu sắc +60
    await p.evaluate(() => { const r = document.querySelector('.vb-ctl input[type=range][data-f="dy"]'); r.value = 60; r.dispatchEvent(new Event('input', { bubbles: true })); });
    await p.waitForTimeout(200);
    const after = await p.evaluate(() => ({ hi: document.querySelectorAll('.vb-rows path.hi').length, gh: document.querySelectorAll('.vb-rows path.gh').length, over: document.querySelectorAll('.vb-rows svg.over').length, dot: !!document.querySelector('.vb-tabs .dot'), sum: window.__bSummary() }));
    console.log(w, 'after dy+60', JSON.stringify(after));
    await p.screenshot({ path: S + 'vb2-' + w + '.png' });
    await p.click('.vb-tabs button[data-k="circ"]'); await p.waitForTimeout(200);
    await p.evaluate(() => { const r = document.querySelector('.vb-ctl input[type=range][data-f="dy"]'); r.value = 40; r.dispatchEvent(new Event('input', { bubbles: true })); }); await p.waitForTimeout(200);
    await p.screenshot({ path: S + 'vb3-' + w + '.png' });
    // chuyển sang thanh kéo chi tiết rồi về
    await p.click('.vk-cmode button[data-v="fine"]'); await p.waitForTimeout(200);
    console.log(w, 'fine mode', await p.evaluate(() => [document.getElementById('vk-batch').hidden, !!document.querySelector('#hu11-view') && !document.querySelector('#hu11-view').closest('[hidden]')]));
    await c.close(); }
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
