// Chi tiết › Dấu hỏi: 4 thanh (bề ngang, cao, dày đầu, dày đuôi) đổi dáng nét thật. node t_hook.js review.html OUTDIR
const { chromium } = require('playwright');
(async () => { const b = await chromium.launch(); const p = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('file://' + process.argv[2]); await p.waitForTimeout(1500);
  await p.evaluate(() => { window.__VK_SHOW('chinh'); [...document.querySelectorAll('button')].find(x => x.textContent.trim() === 'Chi tiết').click(); });
  await p.waitForTimeout(500);
  const rows = await p.evaluate(() => { const g = document.querySelector('#hu11-grpbar [data-grp="hook"]'); if (!g) return 'NO GROUP'; g.click();
    const t = document.getElementById('hu11-text'); t.value = 'ả ở ẩ Ủ Ử ỷ'; t.dispatchEvent(new Event('input'));
    return [...document.querySelectorAll('#hu11-ctl .hu-card[data-grp="hook"] .hu-row span')].map(s => s.textContent).join(' | '); });
  console.log('thanh:', rows); await p.waitForTimeout(400);
  const shot = async n => { const v = await p.$('#hu11-view'); await v.screenshot({ path: process.argv[3] + '/' + n + '.png' }); };
  const dOf = () => p.evaluate(() => [...document.querySelectorAll('#hu11-view .hk-r path')].map(x => x.getAttribute('d')).join('').length);
  await shot('hook_0'); const d0 = await dOf();
  for (const [k, v] of [['w', 130], ['head', 160], ['tail', 70]]) await p.evaluate(([k, v]) => { const r = document.querySelector('#hu11-ctl input[type=range][data-g="hook"][data-k="' + k + '"]'); r.value = v; r.dispatchEvent(new Event('input', { bubbles: true })); r.dispatchEvent(new Event('change', { bubbles: true })); }, [k, v]);
  await p.waitForTimeout(400); await shot('hook_1');
  const d1 = await p.evaluate(() => [...document.querySelectorAll('#hu11-view .hk-r path')].map(x => x.getAttribute('d')));
  console.log('số dấu hỏi tô đỏ:', d1.length, 'đổi dáng:', d1.join('').length !== d0, 'tóm tắt:', await p.evaluate(() => (document.querySelector('#hu11-meas, .hu-meas') || {}).textContent || ''));
  console.log('lỗi', errs); await b.close(); })();
