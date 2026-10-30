const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const c = await b.newContext({ viewport: { width: 1280, height: 900 }, hasTouch: true }); const p = await c.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + process.argv[2]); await p.waitForTimeout(900); await p.evaluate(() => window.__VK_SHOW('ve')); await p.waitForTimeout(600);
  for (const tool of ['select', 'pen']) {
    if (tool === 'pen') { await p.click('.ed-pgb'); await p.click('.ed-pgi[data-tool="pen"]'); } else await p.click('[data-tool="select"]');
    const r = await p.evaluate(async () => {
      const svg = document.querySelector('svg.ed-cv'), R = svg.getBoundingClientRect(); const cnt = () => document.querySelectorAll('#ed-nodes .ed-n').length;
      const st0 = { nodes: cnt(), vb: svg.getAttribute('viewBox'), marq: !!document.querySelector('.ed-marq, rect.ed-mq') };
      const P = (type, id, x, y) => svg.dispatchEvent(new PointerEvent(type, { pointerId: id, pointerType: 'touch', clientX: x, clientY: y, bubbles: true, cancelable: true, isPrimary: id === 1, button: 0, buttons: type === 'pointerup' ? 0 : 1 }));
      const x0 = R.left + R.width * 0.75, y0 = R.top + R.height * 0.3;
      P('pointerdown', 1, x0, y0); P('pointermove', 1, x0 + 20, y0 + 15); await new Promise(r => setTimeout(r, 30));
      const mid1 = { nodes: cnt() };
      P('pointerdown', 2, x0 + 80, y0 + 60);
      for (let i = 1; i <= 5; i++) { P('pointermove', 1, x0 + 20 - i * 12, y0 + 15 - i * 9); P('pointermove', 2, x0 + 80 + i * 12, y0 + 60 + i * 9); await new Promise(r => setTimeout(r, 16)); }
      const during = window.__edPinchState();
      P('pointerup', 2, x0 + 140, y0 + 105); P('pointermove', 1, x0 - 80, y0 - 40); P('pointerup', 1, x0 - 80, y0 - 40); await new Promise(r => setTimeout(r, 50));
      return { st0, mid1, during: { n: during.n, pinch: during.pinch }, after: { nodes: cnt(), vb: svg.getAttribute('viewBox'), selMarq: document.querySelectorAll('.ed-sel, .ed-n.on').length } };
    });
    console.log(tool, JSON.stringify(r));
  }
  // 1 ngón vẫn vẽ / chọn bình thường
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
