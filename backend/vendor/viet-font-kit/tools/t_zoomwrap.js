// test phóng (người dùng 27/10): Xem trước · Văn mẫu phóng mà số dòng mỗi khối không đổi; Đồng loạt phóng được, khung giữ cỡ. usage: node t_zoomwrap.js TRANG.html THU_MUC_ANH
const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const E=[];const S=process.argv[3];
for(const w of [1280,390]){const c=await b.newContext({viewport:{width:w,height:900},colorScheme:'dark',isMobile:w<500,hasTouch:w<500});const p=await c.newPage();p.on('pageerror',e=>E.push(e.message));
await p.addInitScript(()=>{try{localStorage.setItem('vk-pvmode','van');localStorage.setItem('vk-cmode','batch')}catch(e){}});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(1000);
const lines=()=>p.evaluate(()=>{const out=[];document.querySelectorAll('#p-xem .vk-sp>div').forEach(d=>{const r=document.createRange();r.selectNodeContents(d);const tops=new Set([...r.getClientRects()].map(x=>Math.round(x.top)));out.push(tops.size);});return out.join(',')+' w'+document.querySelector('.vk-panes').offsetWidth;});
console.log(w,'xem before',await lines());
const zoom=async(sel,k)=>{const r=await p.$eval(sel,e=>{const b=e.getBoundingClientRect();return [b.left+b.width/2,b.top+60];});await p.evaluate(([sel,x,y,k])=>{const el=document.querySelector(sel);for(let i=0;i<6;i++)el.dispatchEvent(new WheelEvent('wheel',{deltaY:-Math.log(k)/0.0022/6,clientX:x,clientY:y,bubbles:true,cancelable:true}));},[sel,r[0],r[1],k]);await p.waitForTimeout(400);};
await zoom('#p-xem .vk-view',2);console.log(w,'xem zoom×2',await lines());
await zoom('#p-xem .vk-view',1.6);console.log(w,'xem zoom×3.2',await lines());
await p.screenshot({path:S+'/zx'+w+'.png'});
await p.evaluate(()=>window.__VK_SHOW('chinh'));await p.waitForTimeout(500);
const bi=()=>p.evaluate(()=>{const rows=[...document.querySelectorAll('.vb-row')].map(r=>new Set([...r.children].map(x=>Math.round(x.getBoundingClientRect().top))).size);const s=document.querySelector('.vb-sent');const st=new Set([...s.children].map(x=>Math.round(x.getBoundingClientRect().top))).size;const g=document.querySelector('.vb-g');return 'rows '+rows+' sent '+st+' glyphW '+g.getAttribute('width')+' zoomable '+document.querySelector('.vb-zf').classList.contains('vk-zoomable')+' h '+document.querySelector('.vb-zf').offsetHeight;});
console.log(w,'batch before',await bi());
await zoom('.vb-zf',2);console.log(w,'batch ×2',await bi());
await p.screenshot({path:S+'/zb'+w+'.png'});
await c.close();}
console.log(E);await b.close();})();
