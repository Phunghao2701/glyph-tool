// iPhone thật hơn: ngón 1 trong khung, ngón 2 có thể rơi NGOÀI khung; touchstart từng ngón, kèm gesture* không clientX
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const c = await b.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, colorScheme: 'dark' }); const p = await c.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + process.argv[2]); await p.waitForTimeout(900);
  for (const [sel, tab] of [['.vk-view', 'xem'], ['#hu11-view', 'chinh'], ['.ed-pvsc', 've'], ['#on-view', 'xem']]) for (const outside of [false, true]) {
    await p.evaluate(t => window.__VK_SHOW(t), tab); await p.waitForTimeout(300);
    const r = await p.evaluate(async ([sel, outside]) => {
      const fr = document.querySelector(sel); fr.scrollIntoView({ block: 'center' }); await new Promise(r => setTimeout(r, 120));
      const R = fr.getBoundingClientRect(), cx = R.left + R.width / 2, cy = R.top + Math.min(R.height / 2, 30);
      const y2 = outside ? R.bottom + 30 : cy; const out = document.elementFromPoint(cx + 40, Math.min(y2, innerHeight - 2)) || document.body;
      const T = (x, y, id, tg) => new Touch({ identifier: id, target: tg, clientX: x, clientY: y });
      const ev = (tg, type, ts, ch) => tg.dispatchEvent(new TouchEvent(type, { touches: ts, targetTouches: ts.filter(t => t.target === tg), changedTouches: ch, bubbles: true, cancelable: true, composed: true }));
      const ge = (type, scale) => { const e = new Event(type, { bubbles: true, cancelable: true }); Object.defineProperty(e, 'scale', { value: scale }); fr.dispatchEvent(e); };
      const c0 = fr.firstElementChild; const w0 = c0.getBoundingClientRect().width;
      const a0 = T(cx - 30, cy, 1, fr), b0 = T(cx + 30, y2, 2, outside ? out : fr);
      ev(fr, 'touchstart', [a0], [a0]); ev(outside ? out : fr, 'touchstart', [a0, b0], [b0]); ge('gesturestart', 1);
      let mid = ''; for (let i = 1; i <= 6; i++) { const d = i * 15; const a = T(cx - 30 - d, cy - d * 0.3, 1, fr), bb = T(cx + 30 + d, y2 + d * 0.3, 2, outside ? out : fr); ev(fr, 'touchmove', [a, bb], [a, bb]); ge('gesturechange', 1 + i * 0.3); await new Promise(r => requestAnimationFrame(r)); mid = (fr.firstElementChild.style.transform || '').replace(/translate\([^)]*\) /, ''); }
      ev(fr, 'touchend', [], [a0, b0]); ge('gestureend', 2.8); await new Promise(r => setTimeout(r, 250));
      const w1 = fr.firstElementChild.getBoundingClientRect().width;
      return { mid, grow: +(w1 / w0).toFixed(2), visible: w1 > 0 };
    }, [sel, outside]);
    console.log(sel, outside ? 'ngón 2 ngoài khung' : 'cả 2 trong khung', JSON.stringify(r));
  }
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
