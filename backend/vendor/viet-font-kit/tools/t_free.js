// test bản Free / Pro (người dùng 27/10). usage: node t_free.js TRANG.html THU_MUC_ANH
const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch();const S=process.argv[3]||require('os').tmpdir();const F='file://'+process.argv[2];
for (const mode of ['free','pro']){
 const c=await b.newContext({viewport:{width:1280,height:900},colorScheme:'dark',acceptDownloads:true});const p=await c.newPage();const E=[];p.on('pageerror',e=>E.push(e.message));
 if(mode==='pro') await c.addInitScript(()=>{const M={};window.__M=M;const snap=(k)=>({id:k.split('/').pop(),exists:k in M,data:()=>M[k]&&JSON.parse(JSON.stringify(M[k]))});
   const db={doc:k=>({get:async()=>snap(k),set:async v=>{M[k]=v;}}),collection:k=>({get:async()=>{const d=Object.keys(M).filter(x=>x.startsWith(k+'/')).map(snap);return {docs:d,forEach:f=>d.forEach(f),size:d.length,empty:!d.length};}})};
   window.claude={use:async n=>{if(n==='db')return db;throw new Error('no')}};});
 await p.goto(F);await p.waitForTimeout(1200);
 const st=()=>p.evaluate(()=>({mode:window.__vkDbMode(),exp:!document.querySelector('.vk-nav .vk-exp').hidden,n:document.querySelector('.vk-nav .vk-exp-n').textContent,local:document.documentElement.classList.contains('vk-local'),status:(document.getElementById('status')||{}).textContent}));
 console.log(mode,'load',JSON.stringify(await st()));
 // chỉnh: góp ý Xem trước + đồng loạt dy + tên font
 await p.fill('[data-note="V"] textarea','Thử góp ý bản '+mode);await p.waitForTimeout(100);
 await p.evaluate(()=>window.__VK_SHOW('chinh'));await p.waitForTimeout(300);
 await p.evaluate(()=>{const r=document.querySelector('.vb-ctl input[type=range][data-f="dy"]');r.value=40;r.dispatchEvent(new Event('input',{bubbles:true}));});
 await p.waitForTimeout(1600);
 console.log(mode,'after edit',JSON.stringify(await st()), 'vb', await p.textContent('#vb-status'));
 if(mode==='free'){
   console.log('ls keys', await p.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('vkdb:'))));
   await p.reload();await p.waitForTimeout(1300);
   console.log('reload', await p.evaluate(()=>[document.querySelector('[data-note="V"] textarea').value, document.querySelector('#vk-batch input[data-f="dy"]').value]));
   const [dl]=await Promise.all([p.waitForEvent('download'),p.click('.vk-nav .vk-exp')]);const fp=S+'/'+dl.suggestedFilename();await dl.saveAs(fp);console.log('download',dl.suggestedFilename(),require('fs').statSync(fp).size);
   const j=JSON.parse(require('fs').readFileSync(fp));console.log('docs',Object.keys(j.docs),j.dock,j.font,j.kitver);
   await p.evaluate(()=>window.__VK_SHOW('huongdan'));await p.waitForTimeout(300);
   console.log('guide',await p.evaluate(()=>[document.querySelector('.vk-gd-mode').textContent,!document.querySelector('.vk-gd-btns').hidden]));
   await (await p.$('#p-huongdan')).screenshot({path:S+'/guide.png'});
   await p.screenshot({path:S+'/navfree.png',clip:{x:0,y:280,width:1280,height:120}});
 } else {
   console.log('pro M keys', await p.evaluate(()=>Object.keys(window.__M)), 'ls', await p.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('vkdb:')).length));
   await p.evaluate(()=>window.__VK_SHOW('huongdan'));await p.waitForTimeout(200);
   console.log('guide',await p.evaluate(()=>[document.querySelector('.vk-gd-mode').textContent,!document.querySelector('.vk-gd-btns').hidden]));
   await p.waitForTimeout(13000);   // lỗi 27/10: hết giờ chờ (8 s) bản Pro vẫn hiện nút Xuất chỉnh sửa
   console.log('pro after 13s', JSON.stringify(await st()));
 }
 console.log(mode,'errors',E);await c.close();}
await b.close();})();
