// Đo độ mượt khi lăn chuột để phóng ở Xem trước / Đồng loạt / Chi tiết (máy tính).
// node t_wheel.js review.html  → mỗi khung: khung hình dài nhất, số khung > 50 ms, tổng thời gian việc dài (long task)
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + process.argv[2]); await p.waitForTimeout(1500);
  async function run(name, sel, prep) {
    await prep(); await p.waitForTimeout(500);
    const box = await p.evaluate(s => { const e = document.querySelector(s); e.scrollIntoView({ block: 'center' }); const r = e.getBoundingClientRect(); return [r.left + r.width / 2, r.top + Math.min(120, r.height / 2)]; }, sel);
    await p.mouse.move(box[0], box[1]);
    await p.evaluate(() => { window.__fr = []; window.__lt = 0; let t = performance.now(); window.__on = true;
      (function f(n) { window.__fr.push(n - t); t = n; if (window.__on) requestAnimationFrame(f); })(t);
      try { new PerformanceObserver(l => l.getEntries().forEach(e => window.__lt += e.duration)).observe({ type: 'longtask' }); } catch (_) {} });
    // con lăn chuột thật: từng nấc 100 px, nấc cách nhau 30–220 ms (lăn nhanh rồi chậm), cả phóng lẫn thu
    const gaps = [30, 30, 40, 60, 90, 120, 160, 220, 180, 120, 60, 30, 30, 40, 200, 220, 160, 90, 40, 30];
    for (let i = 0; i < gaps.length; i++) { await p.mouse.wheel(0, i < 10 ? -100 : 100); await p.waitForTimeout(gaps[i]); }
    await p.waitForTimeout(600);
    const r = await p.evaluate(() => { window.__on = false; const f = window.__fr.slice(2); return { max: Math.round(Math.max(...f)), n50: f.filter(x => x > 50).length, frames: f.length, long: Math.round(window.__lt) }; });
    console.log(name.padEnd(10), JSON.stringify(r));
  }
  await run('xem', '.vk-view', () => p.evaluate(() => window.__VK_SHOW('xem')));
  await run('dongloat', '.vb-zf', () => p.evaluate(() => { window.__VK_SHOW('chinh'); const x = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Đồng loạt'); if (x) x.click(); }));
  await run('chitiet', '#hu11-view', () => p.evaluate(() => { const x = [...document.querySelectorAll('button')].find(b => b.textContent.trim() === 'Chi tiết'); if (x) x.click(); }));
  console.log('lỗi', errs); await b.close(); })();
