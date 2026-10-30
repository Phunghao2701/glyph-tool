const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:420,height:900},deviceScaleFactor:2});
await p.goto('file://'+process.argv[2]);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
const els=await p.$$('.p');let i=0;for(const e of els){await e.screenshot({path:process.argv[3]+'/panel'+(i++)+'.png'});}
await b.close();})();
