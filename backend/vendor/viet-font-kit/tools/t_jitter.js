const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();
for (const w of [1280,1000,390]){const p=await b.newPage({viewport:{width:w,height:900}});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(1500);
await p.evaluate(()=>window.__VK_GO('ve','ở'));await p.waitForTimeout(1500);
const r=await p.evaluate(()=>new Promise(res=>{const cv=document.querySelector('.ed-stage svg.ed-cv'),sd=document.querySelector('.ed-side'),eb=document.querySelector('.ed-bar');let n=0;
 const mo=new MutationObserver(m=>{n+=m.length});[cv,sd,eb].forEach(e=>mo.observe(e,{attributes:true,attributeFilter:['style']}));
 const hs=[];let k=0;const t=setInterval(()=>{hs.push(Math.round(cv.getBoundingClientRect().height));if(++k>=20){clearInterval(t);mo.disconnect();
  const f=s=>{const b=document.querySelector(s).getBoundingClientRect();return [Math.round(b.top),Math.round(b.bottom)]};
  res({styleChanges:n,heights:[...new Set(hs)],bar:f('.ed-bar'),stage:f('.ed-stage'),side:f('.ed-side')});}},150);}));
// also scroll + resize stress
await p.mouse.wheel(0,400);await p.waitForTimeout(300);
console.log(w,JSON.stringify(r));await p.close();}
await b.close();})();
