const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const c = await b.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, deviceScaleFactor:2 }); const p = await c.newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + process.argv[2]); await p.waitForTimeout(1200);
  await p.evaluate(() => window.__VK_SHOW('xem')); await p.waitForTimeout(400);
  const info=await p.evaluate(()=>{const fr=document.querySelector('.vk-view');return [...fr.children].map(e=>e.className+':'+e.children.length).join(' | ')+' || panes children: '+[...fr.firstElementChild.children].map(e=>e.className).join(',')});
  console.log(info);
  for (const step of ['mid','after']){}
  const r = await p.evaluate(async () => {
      const fr = document.querySelector('.vk-view'); fr.scrollIntoView({ block: 'center' }); await new Promise(r => setTimeout(r, 150));
      const R = fr.getBoundingClientRect(), cx = R.left + R.width / 2, cy = R.top + 120;
      const T = (x, y, id) => new Touch({ identifier: id, target: fr, clientX: x, clientY: y });
      const ev = (type, ts, ch) => fr.dispatchEvent(new TouchEvent(type, { touches: ts, targetTouches: ts, changedTouches: ch, bubbles: true, cancelable: true, composed: true }));
      const ge = (type, scale) => { const e = new Event(type, { bubbles: true, cancelable: true }); Object.defineProperty(e, 'scale', { value: scale }); fr.dispatchEvent(e); };
      const a0 = T(cx - 30, cy, 1), b0 = T(cx + 30, cy, 2);
      ev('touchstart', [a0], [a0]); ev('touchstart', [a0, b0], [b0]); ge('gesturestart', 1);
      for (let i = 1; i <= 6; i++) { const d = i * 15; const a = T(cx - 30 - d, cy, 1), bb = T(cx + 30 + d, cy, 2); ev('touchmove', [a, bb], [a, bb]); ge('gesturechange', 1 + i * 0.3); await new Promise(r => requestAnimationFrame(r)); }
      window.__mid = (fr.querySelector('.vk-zw')||{style:{}}).style.transform;
      return R.top; });
  await p.waitForTimeout(50); await p.screenshot({ path: process.argv[3] + '/pinch_mid.png' });
  await p.evaluate(async () => { const fr = document.querySelector('.vk-view');
      const T = (x, y, id) => new Touch({ identifier: id, target: fr, clientX: x, clientY: y });
      fr.dispatchEvent(new TouchEvent('touchend', { touches: [], targetTouches: [], changedTouches: [T(10,10,1),T(20,20,2)], bubbles: true, cancelable: true }));
      const e = new Event('gestureend', { bubbles: true, cancelable: true }); Object.defineProperty(e, 'scale', { value: 2.8 }); fr.dispatchEvent(e); });
  await p.waitForTimeout(400); await p.screenshot({ path: process.argv[3] + '/pinch_after.png' });
  console.log('mid', await p.evaluate(()=>window.__mid), 'after', await p.evaluate(()=>{const fr=document.querySelector('.vk-view');return [fr.querySelectorAll('.vk-zw').length, fr.querySelectorAll('.vk-spec').length, fr.firstElementChild.style.width]}), errs);
  await b.close(); })();
