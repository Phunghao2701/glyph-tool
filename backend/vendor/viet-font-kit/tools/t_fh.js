const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +process.argv[3]||1440, height: 1000 } });
  await p.addInitScript(()=>{try{localStorage.setItem('vk-cmode','fine')}catch(e){}}); await p.goto('file://' + process.argv[2]); await p.waitForTimeout(800);
  for (const [tab, sel] of [['xem','.vk-view'],['chinh','#hu11-view'],['ve','.ed-pvsc']]) {
    await p.click('#tab-'+tab); await p.waitForTimeout(400);
    const v = await p.$(sel); await v.scrollIntoViewIfNeeded(); const h0 = (await v.boundingBox()).height; const bb = await v.boundingBox();
    await p.mouse.move(bb.x+bb.width/2, bb.y+Math.min(bb.height/2,100)); for (let i=0;i<6;i++){ await p.mouse.wheel(0,-120); await p.waitForTimeout(30);} await p.waitForTimeout(400);
    const h1 = (await v.boundingBox()).height;
    for (let i=0;i<14;i++){ await p.mouse.wheel(0,150); await p.waitForTimeout(30);} await p.waitForTimeout(400);
    console.log(tab, 'h', Math.round(h0), '→ in', Math.round(h1), '→ out', Math.round((await v.boundingBox()).height));
  }
  await b.close();
})();
