const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const S = process.argv[3]; const errs = [];
  // máy tính
  let p = await b.newPage({ viewport: { width: 1280, height: 900 }, colorScheme: 'dark' }); p.on('pageerror', e => errs.push(e.message));
  await p.addInitScript(()=>{try{localStorage.setItem('vk-cmode','fine')}catch(e){}}); await p.goto('file://' + process.argv[2]); await p.waitForTimeout(800); await p.evaluate(() => window.__VK_SHOW('chinh')); await p.waitForTimeout(300);
  const c = await p.$('#hu11-view .hu-c[data-ch="Ở"]'); await c.scrollIntoViewIfNeeded(); const bb = await c.boundingBox();
  await p.mouse.move(bb.x + bb.width / 2, bb.y + bb.height / 2); await p.waitForTimeout(150);
  const hv = await p.$eval('#hu11-view .hu-c[data-ch="Ở"] rect', r => getComputedStyle(r).stroke + ' | ' + getComputedStyle(r).fill);
  await (await p.$('.hu11-vwrap')).screenshot({ path: S + 'hu-hover.png' });
  await p.mouse.click(bb.x + bb.width / 2, bb.y + bb.height / 2); await p.waitForTimeout(400);
  const t1 = await p.evaluate(() => window.__VK_TAB);
  await p.mouse.dblclick(bb.x + bb.width / 2, bb.y + bb.height / 2); await p.waitForTimeout(500);
  console.log('desktop hover', hv, '| 1 click →', t1, '| dblclick →', await p.evaluate(() => window.__VK_TAB), await p.evaluate(() => document.querySelector('.ed-title, .ed-gname, #ed-name') && (document.querySelector('.ed-title, .ed-gname, #ed-name').textContent || '').slice(0, 30)));
  await p.close();
  // điện thoại
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true, colorScheme: 'dark' }); p = await ctx.newPage(); p.on('pageerror', e => errs.push(e.message));
  await p.addInitScript(()=>{try{localStorage.setItem('vk-cmode','fine')}catch(e){}}); await p.goto('file://' + process.argv[2]); await p.waitForTimeout(800); await p.evaluate(() => window.__VK_SHOW('chinh')); await p.waitForTimeout(300);
  const tap = (ch) => p.evaluate(async ch => { const c = document.querySelector('#hu11-view .hu-c[data-ch="' + ch + '"]'); c.scrollIntoView({ block: 'center' }); await new Promise(r => setTimeout(r, 80));
    const r = c.querySelector('rect').getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2, tg = c.querySelector('rect');
    const T = new Touch({ identifier: 1, target: tg, clientX: x, clientY: y });
    tg.dispatchEvent(new TouchEvent('touchstart', { touches: [T], targetTouches: [T], changedTouches: [T], bubbles: true, cancelable: true }));
    tg.dispatchEvent(new TouchEvent('touchend', { touches: [], targetTouches: [], changedTouches: [T], bubbles: true, cancelable: true }));
    await new Promise(r => setTimeout(r, 120)); return [window.__VK_TAB, !!document.querySelector('.hu-c.sel'), document.getElementById('hu11-tip').hidden ? '' : document.getElementById('hu11-tip').textContent]; }, ch);
  console.log('phone tap1', JSON.stringify(await tap('Ở')));
  await (await p.$('.hu11-vwrap')).screenshot({ path: S + 'hu-tap.png' });
  console.log('phone tap other', JSON.stringify(await tap('Ơ')));
  console.log('phone tap again', JSON.stringify(await tap('Ơ')));
  // chụm 2 ngón trên chữ → không chọn, không nhảy tab
  await p.evaluate(() => window.__VK_SHOW('chinh')); await p.waitForTimeout(300);
  const pz = await p.evaluate(async () => { const c = document.querySelector('#hu11-view .hu-c[data-ch="Ở"]'); c.scrollIntoView({ block: 'center' }); await new Promise(r => setTimeout(r, 80)); const tg = c.querySelector('rect'), r = tg.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
    const T = (id, dx) => new Touch({ identifier: id, target: tg, clientX: x + dx, clientY: y });
    const ev = (ty, ts, ch) => tg.dispatchEvent(new TouchEvent(ty, { touches: ts, targetTouches: ts, changedTouches: ch, bubbles: true, cancelable: true }));
    ev('touchstart', [T(1, 0)], [T(1, 0)]); ev('touchstart', [T(1, 0), T(2, 40)], [T(2, 40)]);
    for (let i = 1; i < 5; i++) { ev('touchmove', [T(1, -i * 10), T(2, 40 + i * 10)], [T(1, -i * 10), T(2, 40 + i * 10)]); await new Promise(r => requestAnimationFrame(r)); }
    ev('touchend', [T(1, -40)], [T(2, 80)]); ev('touchend', [], [T(1, -40)]); await new Promise(r => setTimeout(r, 250));
    return [window.__VK_TAB, !!document.querySelector('.hu-c.sel')]; });
  console.log('phone pinch on glyph', JSON.stringify(pz));
  console.log('errors', JSON.stringify(errs)); await b.close(); })();
