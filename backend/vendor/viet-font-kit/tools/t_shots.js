const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const O=process.argv[3];
for (const [w,scheme] of [[1280,'dark'],[390,'light']]){
 const c=await b.newContext({viewport:{width:w,height:900},colorScheme:scheme});const p=await c.newPage();const E=[];p.on('pageerror',e=>E.push(e.message));
 await p.goto('file://'+process.argv[2]);await p.waitForTimeout(1500);
 await p.evaluate(()=>window.__VK_SHOW('chinh'));await p.waitForTimeout(500);
 await p.screenshot({path:`${O}/dl_${w}.png`});
 await p.evaluate(()=>{[...document.querySelectorAll('button')].find(b=>b.textContent.trim()==='Chi tiết').click()});await p.waitForTimeout(600);
 await p.screenshot({path:`${O}/ct_${w}.png`});
 await p.evaluate(()=>window.__VK_SHOW('kn'));await p.waitForTimeout(400);
 await p.evaluate(()=>window.__knOpen(0));
 const frames=[];for(let i=0;i<6;i++){await p.waitForTimeout(50);frames.push(await p.evaluate(()=>{const d=document.querySelector('.kn-dlg');return getComputedStyle(d).opacity+'/'+getComputedStyle(d).transform}));}
 console.log(w,'kn open frames',frames.join(' | '));
 await p.evaluate(()=>window.__knClose());await p.waitForTimeout(300);
 await p.evaluate(()=>window.__VK_SHOW('xem'));await p.waitForTimeout(400);
 const vb=p.locator('.vk-mseg button[data-v="chu"]'); await vb.click(); await p.waitForTimeout(300);
 console.log(w,'line biên button',await p.locator('[data-z="l"]').count(),'errors',E);
 await p.screenshot({path:`${O}/xem_${w}.png`});
 await c.close();}
await b.close();})();
