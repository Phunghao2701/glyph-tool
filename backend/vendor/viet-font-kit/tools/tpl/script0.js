(function(){
var f=document.getElementById('pg-frame'), st=document.getElementById('pg-st'); if(!f) return;
var S={w:'760',m:'bottom',tab:'repeats',pl:'c',an:'a',eg:'4'};
function press(g,a,val){ document.querySelectorAll('#'+g+' button').forEach(function(b){ b.setAttribute('aria-pressed', b.getAttribute(a)===val?'true':'false'); }); }
function size(w){ f.style.width=w+'px'; f.style.height=(w>=560?720:760)+'px'; }
function reload(){ st.textContent='đang tải panel…'; f.style.transition='none'; size(+S.w); f.src='pg/src/index.html?v=11&cc=0&tp=a&mode='+S.m+'&tab='+S.tab+'&pl='+S.pl+'&an='+S.an+'&eg='+S.eg; }
function live(g,a,key){ document.querySelectorAll('#'+g+' button').forEach(function(b){ b.addEventListener('click',function(){ S[key]=b.getAttribute(a); press(g,a,S[key]); var o={}; o[key]=S[key]; try{ f.contentWindow.postMessage(o,'*'); }catch(e){} }); }); }
live('pg-pl','data-pl','pl'); live('pg-an','data-an','an'); live('pg-eg','data-eg','eg');
function bind(g,a,key){ document.querySelectorAll('#'+g+' button').forEach(function(b){ b.addEventListener('click',function(){ S[key]=b.getAttribute(a); press(g,a,S[key]); reload(); }); }); }
bind('pg-w','data-w','w'); bind('pg-m','data-m','m');
document.getElementById('pg-anim').addEventListener('click',function(){ var to=(parseInt(f.style.width,10)>=560)?392:760; f.style.transition='width .9s cubic-bezier(.32,.72,0,1)'; f.style.height='760px'; f.style.width=to+'px'; S.w=String(to); press('pg-w','data-w',S.w); });
window.addEventListener('message',function(e){ if(e.source!==f.contentWindow||!e.data) return; if(e.data.pgTab) S.tab=e.data.pgTab; if(e.data.pgReady) st.textContent='Panel sẵn sàng · thanh '+(S.m==='side'?'dọc':'ngang'); });
setTimeout(function(){ if(/đang tải/.test(st.textContent)) st.textContent='Panel chưa tải xong — nếu khung trống, tải lại trang.'; },9000);
})();