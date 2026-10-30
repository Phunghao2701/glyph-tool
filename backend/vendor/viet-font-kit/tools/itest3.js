const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:1000}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.route(/googleapis|gstatic/, r=>r.abort());
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(1200);
// assignment
await p.evaluate(()=>document.querySelector('#asg').scrollIntoView());
await p.locator('.asg-c').nth(3).click(); await p.locator('.asg-c').nth(10).click();
console.log('mine pressed', await p.$$eval('.asg-c[aria-pressed="true"]',e=>e.map(x=>x.textContent).join(' ')));
await p.fill('#asg-type','ả ơ'); await p.click('#asg [data-a="add"]');
console.log('after type', await p.$$eval('.asg-c[aria-pressed="true"]',e=>e.length), await p.textContent('.asg-st'));
await p.click('[data-scope="full"]'); console.log('full cells', (await p.$$('.asg-c')).length);
await p.screenshot({path:process.argv[3]+'/shotK.png'});
// editor option toggles
await p.evaluate(()=>document.querySelector('#ed').scrollIntoView());
for (const o of ['lbox','axis']) await p.click('.ed-opt[data-opt="'+o+'"]');
console.log('opts', await p.$$eval('.ed-opt',e=>e.map(x=>x.dataset.opt+':'+x.getAttribute('aria-pressed')).join(' ')));
console.log('grid paths', await p.$$eval('#ed-grid path',e=>e.length), 'ruler ticks', await p.$$eval('.ed-rx text',e=>e.length), 'axis', await p.$$eval('#ed-axis line',e=>e.length), 'lbox', await p.$$eval('#ed-lbox rect',e=>e.length));
// open a horn glyph from 1.003-like overflow? choose i-family to see warning
await p.fill('#ed-find','ì'); await p.click('.ed-chip'); await p.waitForTimeout(200);
console.log('warn', await p.textContent('.ed-info'));
await p.screenshot({path:process.argv[3]+'/shotEd.png'});
await p.click('.ed-opt[data-opt="rulers"]'); console.log('rulers off', await p.$eval('.ed-rx',e=>getComputedStyle(e).display));
console.log('sum', (await p.textContent('#sum')).split('\n').filter(l=>/^K ·/.test(l)).join(' | '));
console.log('ERR',JSON.stringify(errs));
await b.close();})();
