/* Việt Font Kit — lưu dự phòng cho Claude bản FREE (người dùng 27/10).
   Bản Pro / Max / Team: artifact có chỗ lưu (db) → dùng như cũ, không đổi gì.
   Bản Free: artifact KHÔNG có chỗ lưu → mọi get / set chuyển sang localStorage của trình duyệt (khoá "vkdb:<đường dẫn>"),
   trang thêm nút "Xuất chỉnh sửa" (.vk-exp) → tải file vfk-chinh-sua-<font>.json / chép đoạn chữ để gửi vào chat.
   Claude đọc file đó bằng tools/import_edits.py (cùng cấu trúc như đọc db).
   build_page.py chèn file này ĐẦU trang và đổi mọi window.claude.use('db') → window.__vkDb().
   build by @nhatmotion */
(function(){
var PFX = 'vkdb:', MODE = null, P = null, TMO = 12000;   // khung artifact tự trả null sau 10 s nếu không có chỗ lưu → chờ 12 s là đủ
function ls(){ try { var s = window.localStorage; s.setItem('vkdb:__t', '1'); s.removeItem('vkdb:__t'); return s; } catch (e) { return null; } }
var MEM = {};   // không có localStorage (cửa sổ ẩn danh…) → giữ trong bộ nhớ, vẫn xuất được
function rd(k){ var s = ls(); if (s) { try { var v = s.getItem(PFX + k); return v == null ? undefined : JSON.parse(v); } catch (e) { return undefined; } } return MEM[k]; }
function wr(k, v){ var s = ls(), j = JSON.stringify(v); if (s) { try { s.setItem(PFX + k, j); return; } catch (e) { /* đầy bộ nhớ → giữ tạm trong bộ nhớ */ } } MEM[k] = JSON.parse(j); }
function keys(){ var s = ls(), out = Object.keys(MEM); if (s) for (var i = 0; i < s.length; i++) { var k = s.key(i); if (k && k.indexOf(PFX) === 0 && k !== PFX + '__t') out.push(k.slice(PFX.length)); } return out.filter(function(k, i, a){ return a.indexOf(k) === i; }); }
function snap(path, v){ var id = path.split('/').pop(); return { id: id, exists: v !== undefined, data: function(){ return v === undefined ? undefined : JSON.parse(JSON.stringify(v)); } }; }
var LOCAL = {
  local: true,
  doc: function(path){ path = String(path).replace(/\/+$/, ''); return {
    get: function(){ return Promise.resolve(snap(path, rd(path))); },
    set: function(data){ wr(path, data); bump(); return Promise.resolve(); } }; },
  collection: function(path){ path = String(path).replace(/\/+$/, ''); return {
    get: function(){ var docs = keys().filter(function(k){ return k.indexOf(path + '/') === 0 && k.slice(path.length + 1).indexOf('/') < 0; })
      .map(function(k){ return snap(k, rd(k)); }); return Promise.resolve({ docs: docs, size: docs.length, empty: !docs.length, forEach: function(f){ docs.forEach(f); } }); } }; }
};
function realUse(){ var c = window.claude; return c && c.use && c.use !== shimUse ? c.use : (c && c.__vkRealUse) || null; }
function useLocal(){ MODE = 'local'; try { document.documentElement.classList.add('vk-local'); } catch (e) {} ui(); return LOCAL; }
window.__vkDb = function(){
  if (P) return P;
  P = new Promise(function(res){
    var done = false;
    // trả db sau khi trang đọc xong (DOMContentLoaded): bản lưu trên máy sẵn sàng ngay, nếu trả sớm thì script đọc db chạy trước khi
    // trang khai báo đường dẫn (window.__FV_EDDOC…) → không nạp được (lỗi 27/10: tải lại trang, thanh Đồng loạt về 0)
    function ok(d){ if (done) return; done = true; if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function(){ res(d); }); else res(d); }
    // CHỈ chuyển sang lưu trên máy khi CHƯA quyết (lỗi 27/10: hết giờ chờ vẫn gọi useLocal() dù db Pro đã nối → nút Xuất chỉnh sửa hiện ra sau ~8 s ở bản Pro)
    function local(){ if (!done) ok(useLocal()); }
    var u = realUse(); if (!u) { local(); return; }
    setTimeout(local, TMO);
    Promise.resolve().then(function(){ return u.call(window.claude, 'db'); }).then(function(d){
      if (!d || !d.doc) { local(); return; }
      return Promise.resolve(d.doc('fontvn/vk-ui').get()).then(function(){ if (done) return; MODE = 'cloud'; ok(d); });   // thử đọc 1 lần: Free thường lỗi ở đây
    }).catch(local);
  });
  return P;
};
window.__vkDbMode = function(){ return MODE; };
function shimUse(name){ if (name === 'db') return window.__vkDb(); return Promise.reject(new Error('không có ' + name + ' (Claude bản Free)')); }
if (!window.claude) window.claude = {};
if (!window.claude.use) window.claude.use = shimUse; else window.claude.__vkRealUse = window.claude.use;

/* ---- xuất chỉnh sửa ---- */
function dump(){ var docs = {}; keys().sort().forEach(function(k){ var v = rd(k); if (v !== undefined) docs[k] = v; });
  return { kit: 'viet-font-kit', kind: 'vfk-edits', dock: window.__VK_DOCK || '', font: window.__VK_FONT || '', kitver: window.__VK_KITVER || '', exportedAt: new Date().toISOString(), docs: docs }; }
function count(){ var n = 0; keys().forEach(function(k){ if (k !== 'fontvn/vk-ui') n++; }); return n; }
function slug(){ return (window.__VK_DOCK || 'font').split('/').pop().replace(/[^a-z0-9-]+/gi, '-'); }
function bump(){ /* không hiện số: trang tự ghi 1 bản tóm tắt lúc mở nên số đếm dễ gây hiểu nhầm */ }
/* Xuất: (1) có quyền tải file của khung artifact (capability downloads) → hỏi người xem lưu file .json;
   (2) mở trang ngoài claude.ai (không có khung) → tải bằng link blob; (3) còn lại (bản Free trong chat: khung chặn tải file)
   → chép đoạn chữ + hiện hộp có sẵn đoạn chữ để tự chép (clipboard trong khung có thể bị chặn). */
function hasHost(){ var c = window.claude; return !!(c && (c.__vkRealUse || (c.use && c.use !== shimUse))); }
function useReal(n){ var u = realUse(); if (!u) return Promise.resolve(null); return Promise.resolve().then(function(){ return u.call(window.claude, n); }).catch(function(){ return null; }); }
window.__vkExport = function(how){
  var d = dump(), name = 'vfk-chinh-sua-' + slug() + '.json', body = JSON.stringify(d, null, 1);
  var t = 'Chỉnh sửa Việt Font Kit (bản Free) — ' + name + '\n' + JSON.stringify(d);
  if (how === 'copy') { copyFlow(t); return; }
  useReal('downloads').then(function(dl){
    if (dl && dl.save) return dl.save({ filename: name, data: body }).then(function(){ say('Đã lưu ' + name + ' — gửi file này vào chat với Claude'); }, function(e){
      var c = e && e.code; if (c === 'declined') { say('Đã huỷ lưu file. Có thể bấm “Chép đoạn chữ” rồi dán vào chat.'); return; }
      if (c === 'rate_limited') { say('Đang có hộp lưu file mở — đợi chút rồi bấm lại.'); return; } copyFlow(t); });
    if (!hasHost()) { try { var b = new Blob([body], { type: 'application/json' }), a = document.createElement('a');
      a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click(); setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); }, 1500);
      say('Đã tải ' + name + ' — gửi file này vào chat với Claude'); return; } catch (e) {} }
    copyFlow(t); }); };
function copyFlow(t){
  function done(ok){ say(ok ? 'Đã chép — dán vào chat với Claude' : 'Chép đoạn chữ trong hộp rồi dán vào chat với Claude'); dlg(t, ok); }
  var ok = false; try { ok = fallbackCopy(t); } catch (e) {}
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(function(){ done(true); }, function(){ done(ok); }); else done(ok); }
function fallbackCopy(t){ var x = document.createElement('textarea'), r = false; x.value = t; x.setAttribute('readonly', ''); x.style.cssText = 'position:fixed;left:-9999px;top:0'; document.body.appendChild(x); x.select(); try { r = document.execCommand('copy'); } catch (e) {} x.remove(); return r; }
function dlg(t, ok){ var o = document.getElementById('vk-expdlg');
  if (!o) { o = document.createElement('div'); o.id = 'vk-expdlg'; o.setAttribute('role', 'dialog'); o.setAttribute('aria-modal', 'true'); o.setAttribute('aria-label', 'Chỉnh sửa để gửi Claude');
    o.innerHTML = '<div class="vk-xd"><div class="vk-xd-h"><b></b><button type="button" class="vk-xd-x" aria-label="Đóng">×</button></div>'
      + '<p class="vk-xd-p">Dán toàn bộ đoạn này vào chat với Claude (bản Free). Chưa chép được thì bấm vào ô → chọn hết → chép.</p>'
      + '<textarea class="vk-xd-ta" readonly spellcheck="false"></textarea><div class="vk-xd-b"><button type="button" class="vk-xd-c">Chép lại</button><button type="button" class="vk-xd-x2">Xong</button></div></div>';
    document.body.appendChild(o);
    var close = function(){ o.hidden = true; }; o.addEventListener('click', function(e){ if (e.target === o || e.target.closest('.vk-xd-x,.vk-xd-x2')) close(); });
    document.addEventListener('keydown', function(e){ if (e.key === 'Escape' && !o.hidden) close(); });
    o.querySelector('.vk-xd-ta').addEventListener('focus', function(e){ e.target.select(); });
    o.querySelector('.vk-xd-c').addEventListener('click', function(){ var ta = o.querySelector('.vk-xd-ta'); ta.focus(); ta.select(); var r = false; try { r = document.execCommand('copy'); } catch (e) {}
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(ta.value).then(function(){ o.querySelector('b').textContent = 'Đã chép ✓'; }, function(){ o.querySelector('b').textContent = r ? 'Đã chép ✓' : 'Chọn hết rồi chép tay'; });
      else o.querySelector('b').textContent = r ? 'Đã chép ✓' : 'Chọn hết rồi chép tay'; }); }
  o.querySelector('b').textContent = ok ? 'Đã chép ✓' : 'Chép đoạn chữ này';
  o.querySelector('.vk-xd-ta').value = t; o.hidden = false; }
function say(m){ document.querySelectorAll('.vk-exp-msg').forEach(function(e){ e.textContent = m; e.hidden = false; clearTimeout(e.__t); e.__t = setTimeout(function(){ e.hidden = true; }, 6000); }); }
function ui(){ if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', ui); return; }
  document.querySelectorAll('.vk-exp,[data-vkexp-show]').forEach(function(b){ b.hidden = false; }); bump();
  mode(); }
/* tab Hướng dẫn: chỉ hiện chữ / thẻ đúng gói đang dùng (Pro: không nhắc Free, Free: không nhắc Pro — người dùng 27/10) */
function mode(){ if (!MODE) return; document.querySelectorAll('[data-dbmode]').forEach(function(e){ var v = e.getAttribute('data-' + MODE); if (v) e.textContent = v; });
  document.querySelectorAll('[data-plan]').forEach(function(e){ e.hidden = e.getAttribute('data-plan') !== MODE; }); }
document.addEventListener('click', function(e){ var b = e.target.closest && e.target.closest('[data-vkexp]'); if (!b) return; e.preventDefault(); window.__vkExport(b.getAttribute('data-vkexp')); });
document.addEventListener('DOMContentLoaded', function(){ window.__vkDb().then(mode); });
})();
