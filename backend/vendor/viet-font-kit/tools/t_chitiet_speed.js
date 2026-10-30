const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:900}});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(1500);
await p.evaluate(()=>window.__VK_SHOW('chinh'));await p.waitForTimeout(500);
await p.evaluate(()=>{[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Chi tiết').click()});await p.waitForTimeout(800);
async function timed(label, fn){ await p.evaluate(()=>{window.__t0=performance.now();}); await fn(); const dt=await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r(performance.now()-window.__t0))))); console.log(label, Math.round(dt),'ms'); }
for (const g of await p.$$('#hu11-grpbar button, .hu-grp button')) {
  const name=(await g.textContent()).trim(); if(!(await g.isVisible())) continue;
  await timed('group '+name, ()=>g.click());
  const rows=await p.$$('#hu11-ctl .hu-row'); let n=0;
  for (const r of rows){ if(!(await r.isVisible())) continue; const lab=(await r.textContent()).trim().slice(0,18); await timed('  row '+lab, ()=>r.click({position:{x:5,y:5}})); if(++n>=3) break; }
}
await b.close();})();
