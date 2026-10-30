const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1280,height:1000}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.route(/googleapis|gstatic/, r=>r.abort());
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(1200);
await p.evaluate(()=>document.querySelector('#ed').scrollIntoView());
const stat=()=>p.evaluate(()=>document.querySelector('.ed-stat').textContent);
console.log('start',await stat());
// 1 drag a node
let n=await p.$('.ed-n'); let bb=await n.boundingBox();
await p.mouse.move(bb.x+bb.width/2,bb.y+bb.height/2); await p.mouse.down(); await p.mouse.move(bb.x+40,bb.y-20,{steps:5}); await p.mouse.up();
console.log('after drag',await stat());
// 2 pen
const st=await (await p.$('.ed-stage svg')).boundingBox();
await p.mouse.move(st.x+100,st.y+100); await p.keyboard.press('p');
await p.mouse.click(st.x+100,st.y+300); await p.mouse.click(st.x+160,st.y+320);
await p.mouse.move(st.x+200,st.y+260); await p.mouse.down(); await p.mouse.move(st.x+240,st.y+240,{steps:4}); await p.mouse.up();
const first=await p.$('.ed-n.first'); const fb=await first.boundingBox(); await p.mouse.click(fb.x+fb.width/2,fb.y+fb.height/2);
console.log('after pen',await stat());
// 3 brush
await p.keyboard.press('b'); await p.mouse.move(st.x+600,st.y+200); await p.mouse.down(); await p.mouse.move(st.x+650,st.y+260,{steps:8}); await p.mouse.move(st.x+700,st.y+240,{steps:8}); await p.mouse.up();
console.log('after brush',await stat());
await p.keyboard.press('v');
// undo once
await p.keyboard.press('Control+z'); console.log('after undo',await stat());
await p.keyboard.press('Control+Shift+z'); console.log('after redo',await stat());
// 4 picks
await p.click('.pick[data-v="'+(process.env.PICK||'A1b')+'"]'); const PK=process.env.PICK||'A1b'; console.log(PK+' pressed', await p.getAttribute('.pick[data-v="'+PK+'"]','aria-pressed'), await p.getAttribute('.pick[data-v="'+(process.env.PICK0||'A1a')+'"]','aria-pressed'));
// 5 choose another glyph
await p.click('.ed-tabs button[data-tab="vn"]'); await p.click('.ed-chip[title="uni1EDF"]').catch(async()=>{const c=await p.$$('.ed-chip'); await c[20].click();});
console.log('glyph', await p.evaluate(()=>document.querySelector('.ed-ttl').textContent));
await p.click('.ed-tabs button[data-tab="marks"]'); await p.click('.ed-chip[data-id="hook"]');
await p.waitForTimeout(300);
console.log('summary:', await p.evaluate(()=>document.getElementById('sum').textContent));
await p.screenshot({path:process.argv[3]});
console.log('ERR',JSON.stringify(errs));
await b.close();})();
