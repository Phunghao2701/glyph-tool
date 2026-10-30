(function(){
var picks = {}, notes = {};
document.querySelectorAll('.picks[data-key] .pick[aria-pressed="true"]').forEach(function(b){ picks[b.closest('.picks').dataset.key] = b.dataset.v; });
function esc(t){ return String(t).replace(/[&<>"]/g, function(c){ return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
function fmtT(s){ s = Math.max(0, s || 0); var m = Math.floor(s / 60), x = s - m * 60; return m + ':' + (x < 10 ? '0' : '') + x.toFixed(2); }
var SVGNS = 'http://www.w3.org/2000/svg';
var ANN = {};
var ANN_COLORS = ['#ff3b5c', '#ffd60a', '#22c55e', '#38bdf8'];
var TI = {
  hand:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3l14 7-6 1.6L10.4 18z"/></svg>',
  cmt:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12a8 8 0 1 1 3.3 6.5L4 20l1.2-3.6A7.9 7.9 0 0 1 4 12z"/><path d="M9 10.5h6M9 13.5h4"/></svg>',
  pen:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4z"/><path d="M14.5 5.5l3 3"/></svg>',
  erase: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 19.5 3.6 14.6a1.6 1.6 0 0 1 0-2.3l8.7-8.7a1.6 1.6 0 0 1 2.3 0l5 5a1.6 1.6 0 0 1 0 2.3l-8.8 8.6z"/><path d="M8.5 19.5H20M9 9l6 6"/></svg>',
  rect:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="4" y="5.5" width="16" height="13" rx="1.5"/></svg>',
  ellipse:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="8"/></svg>',
  ok:    '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.5" fill="#16a34a"/><path d="M7.5 12.4l3 3 6-6.2" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  no:    '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.5" fill="#e11d48"/><path d="M8.6 8.6l6.8 6.8M15.4 8.6l-6.8 6.8" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></svg>',
  undo:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 7 4.5 11.5 9 16"/><path d="M5 11.5h9.5a5 5 0 0 1 0 10H12"/></svg>',
  redo:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M15 7l4.5 4.5L15 16"/><path d="M19 11.5H9.5a5 5 0 0 0 0 10H12"/></svg>',
  trash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/></svg>',
  caret: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10l5 5 5-5"/></svg>',
  txt:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 6V4.5h14V6"/><path d="M12 4.5v15"/><path d="M9 19.5h6"/></svg>',
  fill:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><rect x="4.5" y="4.5" width="15" height="15" rx="2.5" fill="currentColor" fill-opacity=".35"/></svg>',
  close: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  draw:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4z"/><path d="M14.5 5.5l3 3"/></svg>',
  line:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M5 19 19 5"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 19 19 5"/><path d="M10 5h9v9"/></svg>',
  like:  '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.5" fill="#2563eb"/><g transform="translate(6.2 5.6) scale(.48)" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z"/></g></svg>',
  dislike:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.5" fill="#ea580c"/><g transform="translate(6.2 7.2) scale(.48)" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88Z"/></g></svg>'
};
var STICKERS = ['ok', 'no', 'like', 'dislike'];
/* (vòng 3) Bố cục bàn vẽ theo trang duyệt motion: mặc định THU GỌN thành một nút
   "Vẽ góp ý" trên dòng tên khung (khung HIỆN TẠI / ĐỀ XUẤT nằm cạnh nhau cùng cỡ);
   bấm mới mở thanh công cụ DỌC bên trái khung (màn hẹp: xếp ngang trên khung).
   Phím: V tay · C ghim · B bút · E tẩy · R chữ nhật · O tròn · T chữ · Ctrl+Z / Ctrl+Shift+Z / Ctrl+Y · Esc thu gọn. */
/* (vòng 4) Ryan: nhóm hình · nhóm sticker (+ like / dislike) · nhóm độ dày · màu tự do · bút tự mượt + tự thẳng. */
var SHAPES = [['rect', 'Chữ nhật', 'R'], ['ellipse', 'Tròn', 'O'], ['line', 'Đường thẳng', 'L'], ['arrow', 'Mũi tên', 'A']];
var STK = [['ok', 'Dấu OK'], ['no', 'Dấu NOT OK'], ['like', 'Like'], ['dislike', 'Dislike']];
var SIZES = [[2, 'Mảnh'], [3.5, 'Vừa'], [6, 'Dày'], [9, 'Rất dày']];
var SWATCH = ['#ff3b5c', '#ffd60a', '#22c55e', '#38bdf8', '#c47bff', '#ffffff'];
function annInit(fig){
  var spec = fig.dataset.ann, fr = fig.querySelector('.cv');
  var W = +fr.getAttribute('width'), H = +fr.getAttribute('height');
  var st = ANN[spec] = { items: [], hist: [], fut: [], tool: 'hand', shape: 'rect', sticker: 'ok', fill: false, color: SWATCH[0], sw: 3.5, fr: fr, W: W, H: H, spec: spec, open: false };
  var cap = fig.querySelector('figcaption');
  var pill = document.createElement('button'); pill.type = 'button'; pill.className = 'ann-pill'; pill.setAttribute('aria-expanded', 'false');
  pill.innerHTML = TI.draw + '<span>Vẽ góp ý</span><b class="ann-n" hidden></b>';
  cap.classList.add('has-pill'); cap.appendChild(pill);
  var bar = document.createElement('div'); bar.className = 'annbar'; bar.setAttribute('role', 'toolbar'); bar.setAttribute('aria-label', 'Công cụ vẽ góp ý'); bar.hidden = true;
  function tb(t, title, key, ico){ return '<button type="button" class="ann-b" data-t="' + t + '" aria-pressed="false" title="' + title + (key ? ' (' + key + ')' : '') + '" aria-label="' + title + '">' + (ico || TI[t]) + '</button>'; }
  bar.innerHTML =
    tb('hand', 'Tay — bấm vào panel như thường', 'V') + tb('cmt', 'Ghim comment', 'C') + tb('pen', 'Bút — tự mượt, vẽ gần thẳng thì thành đường thẳng', 'B') + tb('erase', 'Tẩy (bấm / kéo qua nét)', 'E') +
    '<button type="button" class="ann-b ann-grp" data-t="shape" data-grp="shape" aria-pressed="false" aria-haspopup="true" title="Hình (R O L A)" aria-label="Hình">' + TI.rect + '<i class="ann-crt"></i></button>' +
    tb('txt', 'Gõ chữ', 'T') +
    '<button type="button" class="ann-b ann-grp" data-t="sticker" data-grp="sticker" aria-pressed="false" aria-haspopup="true" title="Sticker (S)" aria-label="Sticker">' + TI.ok + '<i class="ann-crt"></i></button>' +
    '<span class="ann-sep"></span>' +
    '<button type="button" class="ann-b ann-grp" data-grp="color" aria-haspopup="true" title="Màu" aria-label="Màu"><span class="ann-dot"></span><i class="ann-crt"></i></button>' +
    '<button type="button" class="ann-b ann-grp" data-grp="size" aria-haspopup="true" title="Độ dày nét" aria-label="Độ dày nét"><span class="ann-ln"></span><i class="ann-crt"></i></button>' +
    '<span class="ann-sep"></span>' +
    '<button type="button" class="ann-b" data-act="undo" title="Hoàn tác (Ctrl+Z)" aria-label="Hoàn tác">' + TI.undo + '</button>' +
    '<button type="button" class="ann-b" data-act="redo" title="Làm lại (Ctrl+Shift+Z)" aria-label="Làm lại">' + TI.redo + '</button>' +
    '<button type="button" class="ann-b" data-act="clear" title="Xoá hết nét trên khung này" aria-label="Xoá hết">' + TI.trash + '</button>' +
    '<button type="button" class="ann-b ann-x" data-act="close" title="Thu gọn (Esc)" aria-label="Thu gọn">' + TI.close + '</button>' +
    '<div class="ann-fly" hidden></div>';
  var sc = fr.parentNode;
  var row = document.createElement('div'); row.className = 'ann-row';
  sc.parentNode.insertBefore(row, sc); row.appendChild(bar); row.appendChild(sc);
  var wrap = document.createElement('div'); wrap.className = 'annwrap';
  fr.parentNode.insertBefore(wrap, fr); wrap.appendChild(fr);
  var svg = document.createElementNS(SVGNS, 'svg'); svg.setAttribute('class', 'annsvg'); svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H); svg.setAttribute('preserveAspectRatio', 'none');
  wrap.appendChild(svg);
  var conf = document.createElement('div'); conf.className = 'ann-confirm'; conf.hidden = true;
  conf.innerHTML = 'Xoá hết nét trên khung này? <button type="button" data-act="clear-yes">Xoá</button><button type="button" data-act="clear-no">Thôi</button>';
  row.parentNode.insertBefore(conf, row.nextSibling);
  var list = document.createElement('ol'); list.className = 'anncmts'; fig.appendChild(list);
  st.svg = svg; st.wrap = wrap; st.bar = bar; st.list = list; st.pill = pill; st.conf = conf; st.row = row; st.fly = bar.querySelector('.ann-fly');
  pill.addEventListener('click', function(){ annOpen(st, !st.open); });
  /* (vòng 6) Ryan: bàn vẽ mở sẵn khi vào trang; công cụ mặc định = Tay để panel vẫn bấm được */
  setTimeout(function(){ paintBar(st); annOpen(st, true); }, 0);
  function onBtn(e){
    var b = e.target.closest('button'); if (!b) return;
    if (b.closest('.ann-fly')) return onFly(st, b);
    if (b.dataset.grp) { var was = st.flyFor === b.dataset.grp && !st.fly.hidden; if (b.dataset.t) setTool(st, b.dataset.t); if (was) closeFly(st); else openFly(st, b); return; }
    if (b.dataset.t) { closeFly(st); return setTool(st, b.dataset.t); }
    closeFly(st);
    if (b.dataset.act === 'undo') return annUndo(st);
    if (b.dataset.act === 'redo') return annRedo(st);
    if (b.dataset.act === 'close') return annOpen(st, false);
    if (b.dataset.act === 'clear') { conf.hidden = false; return; }
    if (b.dataset.act === 'clear-no') { conf.hidden = true; return; }
    if (b.dataset.act === 'clear-yes') { conf.hidden = true; if (st.items.length) { annPush(st); st.items = []; annCommit(st); } }
  }
  bar.addEventListener('click', onBtn); conf.addEventListener('click', onBtn);
  st.fly.addEventListener('input', function(e){ if (e.target.type === 'color') { st.color = e.target.value; paintBar(st); } });
  document.addEventListener('pointerdown', function(e){ if (!st.fly.hidden && !bar.contains(e.target)) closeFly(st); }, true);
  wrap.addEventListener('pointerenter', function(){ ANN._hover = st; });
  fig.addEventListener('pointerleave', function(){ if (ANN._hover === st) ANN._hover = null; });
  wrap.dataset.tool = 'hand';
  paintBar(st);
  bindDraw(st);
  annRender(st);
}
/* the bar always shows the CURRENT shape / sticker / colour / size on its group buttons */
function paintBar(st){
  var b = st.bar;
  b.querySelector('[data-grp="shape"]').firstChild.outerHTML = TI[st.shape];
  b.querySelector('[data-grp="sticker"]').firstChild.outerHTML = TI[st.sticker];
  b.querySelector('.ann-dot').style.background = st.color;
  var ln = b.querySelector('.ann-ln'); ln.style.height = Math.max(1.5, st.sw * 0.8) + 'px'; ln.style.background = st.color;
  b.querySelectorAll('[data-t]').forEach(function(x){ x.setAttribute('aria-pressed', String(x.dataset.t === st.tool || (x.dataset.t === 'shape' && SHAPES.some(function(s){ return s[0] === st.tool; })) || (x.dataset.t === 'sticker' && STICKERS.indexOf(st.tool) >= 0))); });
}
function openFly(st, btn){
  var g = btn.dataset.grp, f = st.fly, h = '';
  if (g === 'shape') h = SHAPES.map(function(s){ return '<button type="button" data-shape="' + s[0] + '" aria-pressed="' + (st.shape === s[0]) + '">' + TI[s[0]] + '<span>' + s[1] + '</span><kbd>' + s[2] + '</kbd></button>'; }).join('') +
    '<label class="ann-fill"><input type="checkbox"' + (st.fill ? ' checked' : '') + '> Tô nền (chữ nhật · tròn)</label>';
  if (g === 'sticker') h = STK.map(function(s){ return '<button type="button" data-stk="' + s[0] + '" aria-pressed="' + (st.sticker === s[0]) + '">' + TI[s[0]] + '<span>' + s[1] + '</span></button>'; }).join('');
  if (g === 'size') h = SIZES.map(function(z){ return '<button type="button" data-sz="' + z[0] + '" aria-pressed="' + (st.sw === z[0]) + '"><i style="height:' + Math.max(1.5, z[0] * 0.8) + 'px"></i><span>' + z[1] + '</span></button>'; }).join('');
  if (g === 'color') h = '<div class="ann-sw">' + SWATCH.map(function(c){ return '<button type="button" class="ann-c" data-col="' + c + '" style="--c:' + c + '" aria-pressed="' + (st.color.toLowerCase() === c) + '" aria-label="Màu ' + c + '"></button>'; }).join('') + '</div>' +
    '<label class="ann-free"><input type="color" value="' + st.color + '"> Màu khác…</label>';
  f.innerHTML = h; f.dataset.grp = g; f.hidden = false; st.flyFor = g;
  var vertical = getComputedStyle(st.bar).flexDirection === 'column';
  if (vertical) { f.style.left = 'calc(100% + 6px)'; f.style.top = btn.offsetTop + 'px'; }
  else { f.style.left = Math.max(0, btn.offsetLeft) + 'px'; f.style.top = 'calc(100% + 6px)'; }
  var fl = f.querySelector('.ann-fill input'); if (fl) fl.addEventListener('change', function(){ st.fill = fl.checked; });
}
function closeFly(st){ if (st.fly) { st.fly.hidden = true; st.flyFor = null; } }
function onFly(st, b){
  if (b.dataset.shape) { st.shape = b.dataset.shape; setTool(st, st.shape); closeFly(st); }
  else if (b.dataset.stk) { st.sticker = b.dataset.stk; setTool(st, st.sticker); closeFly(st); }
  else if (b.dataset.sz) { st.sw = +b.dataset.sz; paintBar(st); closeFly(st); }
  else if (b.dataset.col) { st.color = b.dataset.col; paintBar(st); closeFly(st); }
}
function annOpen(st, open){
  st.open = open; st.bar.hidden = !open; st.pill.setAttribute('aria-expanded', String(open));
  st.pill.classList.toggle('is-open', open); st.row.classList.toggle('is-open', open);
  st.wrap.dataset.tool = open ? toolCursor(st.tool) : 'hand';
  if (!open) { closePop(st); closeText(st, true); closeFly(st); st.conf.hidden = true; }
}
function toolCursor(t){ return (SHAPES.some(function(s){ return s[0] === t; }) || STICKERS.indexOf(t) >= 0) ? 'shape' : t; }
function setTool(st, t){
  closeText(st, true);
  if (t === 'shape') t = st.shape; if (t === 'sticker') t = st.sticker;
  st.tool = t;
  paintBar(st);
  st.wrap.dataset.tool = st.open ? toolCursor(t) : 'hand';
  closePop(st);
}
/* Pen: smooth (RDP simplify + Chaikin), or snap to a straight line when the stroke is nearly straight. */
function rdp(pts, eps){
  if (pts.length < 3) return pts.slice();
  var a = pts[0], b = pts[pts.length - 1], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, mi = 0, md = 0;
  for (var i = 1; i < pts.length - 1; i++) { var d = Math.abs(dy * pts[i][0] - dx * pts[i][1] + b[0] * a[1] - b[1] * a[0]) / L; if (d > md) { md = d; mi = i; } }
  if (md <= eps) return [a, b];
  return rdp(pts.slice(0, mi + 1), eps).slice(0, -1).concat(rdp(pts.slice(mi), eps));
}
function chaikin(pts, n){
  for (var k = 0; k < n; k++) {
    if (pts.length < 3) return pts;
    var out = [pts[0]];
    for (var i = 0; i < pts.length - 1; i++) { var p = pts[i], q = pts[i + 1]; out.push([p[0] * .75 + q[0] * .25, p[1] * .75 + q[1] * .25], [p[0] * .25 + q[0] * .75, p[1] * .25 + q[1] * .75]); }
    out.push(pts[pts.length - 1]); pts = out;
  }
  return pts;
}
function finishPen(d){
  var p = d.pts, a = p[0], b = p[p.length - 1], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
  var md = 0; for (var i = 1; i < p.length - 1; i++) md = Math.max(md, Math.abs((b[1] - a[1]) * p[i][0] - (b[0] - a[0]) * p[i][1] + b[0] * a[1] - b[1] * a[0]) / (L || 1));
  var path = 0; for (var j = 1; j < p.length; j++) path += Math.hypot(p[j][0] - p[j - 1][0], p[j][1] - p[j - 1][1]);
  if (L > 24 && md <= Math.max(3, L * 0.05) && path <= L * 1.12) return { t: 'line', x1: a[0], y1: a[1], x2: b[0], y2: b[1], c: d.c, sw: d.sw, auto: 1 };
  d.pts = chaikin(rdp(p, 1.2), 2).map(function(q){ return [Math.round(q[0] * 10) / 10, Math.round(q[1] * 10) / 10]; });
  return d;
}
/* T — a floating editable box at the click point. Enter = keep, Shift+Enter = new line, Esc = drop. */
function openText(st, p){
  closeText(st, true);
  var r = st.svg.getBoundingClientRect(), sx = r.width / st.W;
  var box = document.createElement('div'); box.className = 'ann-txt'; box.contentEditable = 'true';
  box.style.left = (p[0] * sx) + 'px'; box.style.top = (p[1] * sx - 10) + 'px'; box.style.color = st.color;
  box.style.fontSize = Math.round(11 + st.sw * 1.6) + 'px';
  st.wrap.appendChild(box); st.txt = { box: box, p: p };
  box.focus(); setTimeout(function(){ if (document.activeElement !== box) box.focus(); }, 10);
  box.addEventListener('keydown', function(e){
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); closeText(st, true); }
    else if (e.key === 'Escape') { e.preventDefault(); closeText(st, false); }
    e.stopPropagation();
  });
  box.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
}
function closeText(st, keep){
  var t = st.txt; if (!t) return; st.txt = null;
  var text = (t.box.innerText || '').replace(/ /g, ' ').trim();
  t.box.remove();
  if (keep && text) { annPush(st); st.items.push({ t: 'txt', x: t.p[0], y: t.p[1], text: text, c: st.color, fs: Math.round(11 + st.sw * 1.6) }); annCommit(st); }
}
function pt(st, e){ var r = st.svg.getBoundingClientRect(); return [Math.round((e.clientX - r.left) * st.W / r.width * 10) / 10, Math.round((e.clientY - r.top) * st.H / r.height * 10) / 10]; }
function annPush(st){ st.hist.push(JSON.stringify(st.items)); if (st.hist.length > 80) st.hist.shift(); st.fut = []; }
function annUndo(st){ if (!st.hist.length) return; st.fut.push(JSON.stringify(st.items)); st.items = JSON.parse(st.hist.pop()); annCommit(st); }
function annRedo(st){ if (!st.fut.length) return; st.hist.push(JSON.stringify(st.items)); st.items = JSON.parse(st.fut.pop()); annCommit(st); }
function annCommit(st){ annRender(st); annSave(st); render(); }
function el(tag, attrs){ var e = document.createElementNS(SVGNS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); return e; }
function shapeEl(it){
  var g, sw = it.sw || 2.5;
  if (it.t === 'pen') g = el('path', { d: 'M' + it.pts.map(function(p){ return p[0] + ' ' + p[1]; }).join(' L'), fill: 'none', stroke: it.c, 'stroke-width': it.sw || 3, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
  else if (it.t === 'rect') g = el('rect', { x: it.x, y: it.y, width: it.w, height: it.h, rx: 3, fill: it.f ? it.c : 'none', 'fill-opacity': it.f ? 0.28 : 0, stroke: it.c, 'stroke-width': sw });
  else if (it.t === 'ellipse') g = el('ellipse', { cx: it.x + it.w / 2, cy: it.y + it.h / 2, rx: Math.abs(it.w / 2), ry: Math.abs(it.h / 2), fill: it.f ? it.c : 'none', 'fill-opacity': it.f ? 0.28 : 0, stroke: it.c, 'stroke-width': sw });
  else if (it.t === 'line' || it.t === 'arrow') {
    g = el('g', {});
    g.appendChild(el('line', { x1: it.x1, y1: it.y1, x2: it.x2, y2: it.y2, stroke: it.c, 'stroke-width': sw, 'stroke-linecap': 'round' }));
    if (it.t === 'arrow') { var ang = Math.atan2(it.y2 - it.y1, it.x2 - it.x1), hl = 8 + sw * 2.2, aw = 0.5;
      g.appendChild(el('path', { d: 'M' + (it.x2 - hl * Math.cos(ang - aw)) + ' ' + (it.y2 - hl * Math.sin(ang - aw)) + ' L' + it.x2 + ' ' + it.y2 + ' L' + (it.x2 - hl * Math.cos(ang + aw)) + ' ' + (it.y2 - hl * Math.sin(ang + aw)), fill: 'none', stroke: it.c, 'stroke-width': sw, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })); }
  }
  else if (STICKERS.indexOf(it.t) >= 0) {
    g = el('g', { transform: 'translate(' + (it.x - 17) + ' ' + (it.y - 17) + ') scale(1.4167)' });
    g.innerHTML = TI[it.t].replace(/^<svg[^>]*>|<\/svg>$/g, '');
    g.insertBefore(el('circle', { cx: 12, cy: 12, r: 11, fill: '#fff', 'fill-opacity': 0.9 }), g.firstChild);
  } else if (it.t === 'txt') {
    g = el('text', { x: it.x, y: it.y, 'font-size': it.fs || 16, 'font-weight': 700, fill: it.c, stroke: '#0c0912', 'stroke-width': 3, 'paint-order': 'stroke', 'stroke-linejoin': 'round', 'font-family': 'Be Vietnam Pro, sans-serif' });
    String(it.text || '').split('\n').forEach(function(line, k){ var ts = el('tspan', { x: it.x, dy: k ? '1.25em' : '0' }); ts.textContent = line; g.appendChild(ts); });
  } else if (it.t === 'cmt') {
    g = el('g', { transform: 'translate(' + it.x + ' ' + it.y + ')', class: 'ann-pin' + (it.text ? '' : ' empty') });
    g.appendChild(el('path', { d: 'M-5 -6 L0 0 L5 -6 Z', fill: '#8b3fe0', stroke: '#fff', 'stroke-width': 1.4, 'stroke-linejoin': 'round' }));
    g.appendChild(el('circle', { cx: 0, cy: -16, r: 11, fill: '#8b3fe0', stroke: '#fff', 'stroke-width': 1.8 }));
    var tx = el('text', { x: 0, y: -12, 'text-anchor': 'middle', 'font-size': 11.5, 'font-weight': 700, fill: '#fff', 'font-family': 'Be Vietnam Pro, sans-serif' });
    tx.textContent = it.n; g.appendChild(tx);
  }
  return g;
}
function annRender(st){
  var svg = st.svg; while (svg.firstChild) svg.removeChild(svg.firstChild);
  st.items.forEach(function(it, i){ var g = shapeEl(it); if (!g) return; g.setAttribute('data-i', i); svg.appendChild(g); });
  if (st.draft) { var d = shapeEl(st.draft); if (d) { d.setAttribute('opacity', 0.85); svg.appendChild(d); } }
  var cm = st.items.filter(function(x){ return x.t === 'cmt'; });
  st.list.innerHTML = cm.map(function(c){ return '<li data-n="' + c.n + '"><b>' + c.n + '</b><span>' + (c.text ? esc(c.text) : '<i>(chưa gõ)</i>') + '</span></li>'; }).join('');
  st.list.hidden = !cm.length;
  st.bar.querySelector('[data-act="undo"]').disabled = !st.hist.length; st.bar.querySelector('[data-act="redo"]').disabled = !st.fut.length;
  var nb = st.pill.querySelector('.ann-n'); nb.hidden = !st.items.length; nb.textContent = st.items.length;
}
function nextN(st){ return st.items.reduce(function(m, x){ return x.t === 'cmt' ? Math.max(m, x.n) : m; }, 0) + 1; }
function closePop(st){ var p = st.wrap.querySelector('.ann-pop'); if (p) p.remove(); }
function openPop(st, idx){
  closePop(st);
  var it = st.items[idx]; if (!it) return;
  var pop = document.createElement('div'); pop.className = 'ann-pop';
  var r = st.svg.getBoundingClientRect(), sx = r.width / st.W;
  pop.style.left = Math.min(Math.max(it.x * sx + 14, 4), r.width - 234) + 'px'; pop.style.top = Math.max(it.y * sx - 8, 4) + 'px';
  pop.innerHTML = '<div class="ann-pop-h">Comment #' + it.n + '</div><textarea placeholder="Gõ góp ý cho chỗ này…"></textarea><div class="ann-pop-f"><button type="button" data-a="del">Xoá</button><button type="button" data-a="ok">Lưu</button></div>';
  st.wrap.appendChild(pop);
  var ta = pop.querySelector('textarea'); ta.value = it.text || ''; ta.focus(); setTimeout(function(){ ta.focus(); }, 20);
  var before = it.text || '';
  function saveText(){ var v = ta.value.trim(); if (v !== before) { annPush(st); st.items[idx].text = v; before = v; annCommit(st); } }
  pop.addEventListener('click', function(e){
    var b = e.target.closest('button'); if (!b) return;
    if (b.dataset.a === 'ok') { saveText(); closePop(st); }
    if (b.dataset.a === 'del') { annPush(st); st.items.splice(idx, 1); closePop(st); annCommit(st); }
  });
  ta.addEventListener('keydown', function(e){
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); saveText(); closePop(st); }
    if (e.key === 'Escape') { e.preventDefault(); closePop(st); }
  });
  pop.addEventListener('pointerdown', function(e){ e.stopPropagation(); });
}
function hitIndex(st, e){ var t = document.elementFromPoint(e.clientX, e.clientY); if (!t) return -1; var g = t.closest ? t.closest('[data-i]') : null; return g && st.svg.contains(g) ? +g.getAttribute('data-i') : -1; }
function bindDraw(st){
  var svg = st.svg, drag = null;
  svg.addEventListener('pointerdown', function(e){
    if (!st.open || st.tool === 'hand') return;
    e.preventDefault(); closePop(st);
    var p = pt(st, e);
    if (st.tool === 'cmt') {
      var hit = hitIndex(st, e);
      if (hit >= 0 && st.items[hit].t === 'cmt') { openPop(st, hit); return; }
      annPush(st); st.items.push({ t: 'cmt', x: p[0], y: p[1], n: nextN(st), text: '' }); annCommit(st);
      openPop(st, st.items.length - 1); return;
    }
    if (st.tool === 'erase') { drag = { erase: true, pushed: false }; eraseAt(e); svg.setPointerCapture(e.pointerId); return; }
    if (STICKERS.indexOf(st.tool) >= 0) { annPush(st); st.items.push({ t: st.tool, x: p[0], y: p[1] }); annCommit(st); return; }
    if (st.tool === 'txt') { openText(st, p); return; }
    svg.setPointerCapture(e.pointerId);
    if (st.tool === 'pen') st.draft = { t: 'pen', pts: [p], c: st.color, sw: st.sw };
    else if (st.tool === 'line' || st.tool === 'arrow') st.draft = { t: st.tool, x1: p[0], y1: p[1], x2: p[0], y2: p[1], c: st.color, sw: st.sw };
    else st.draft = { t: st.tool, x: p[0], y: p[1], w: 0, h: 0, c: st.color, f: st.fill, sw: st.sw, x0: p[0], y0: p[1] };
    drag = { start: p };
    annRender(st);
  });
  svg.addEventListener('pointermove', function(e){
    if (!drag) return;
    if (drag.erase) { eraseAt(e); return; }
    var p = pt(st, e), d = st.draft; if (!d) return;
    if (d.t === 'pen') { var l = d.pts[d.pts.length - 1]; if (Math.hypot(p[0] - l[0], p[1] - l[1]) >= 1.5) d.pts.push(p); }
    else if (d.t === 'line' || d.t === 'arrow') { d.x2 = p[0]; d.y2 = p[1]; }
    else { d.x = Math.min(d.x0, p[0]); d.y = Math.min(d.y0, p[1]); d.w = Math.abs(p[0] - d.x0); d.h = Math.abs(p[1] - d.y0); }
    annRender(st);
  });
  function end(){
    if (!drag) return;
    var d = st.draft; st.draft = null;
    if (!drag.erase && d) { var ok = d.t === 'pen' ? d.pts.length > 1 : (d.t === 'line' || d.t === 'arrow') ? Math.hypot(d.x2 - d.x1, d.y2 - d.y1) > 6 : (d.w > 4 && d.h > 4); if (ok) { if (d.t === 'pen') d = finishPen(d); delete d.x0; delete d.y0; annPush(st); st.items.push(d); } annCommit(st); }
    else if (drag.erase && drag.pushed) annCommit(st);
    drag = null;
  }
  svg.addEventListener('pointerup', end); svg.addEventListener('pointercancel', end);
  function eraseAt(e){ var i = hitIndex(st, e); if (i < 0) return; if (!drag.pushed) { annPush(st); drag.pushed = true; } st.items.splice(i, 1); annRender(st); }
  svg.addEventListener('click', function(e){
    if (st.open && st.tool !== 'hand') return;
    var g = e.target.closest && e.target.closest('.ann-pin'); if (!g) return;
    var g2 = g.closest('[data-i]'); if (g2) openPop(st, +g2.getAttribute('data-i'));
  });
}
document.addEventListener('click', function(e){
  var li = e.target.closest && e.target.closest('.anncmts li'); if (!li) return;
  var fig = li.closest('figure[data-ann]'), st = ANN[fig.dataset.ann]; if (!st) return;
  var n = +li.dataset.n, idx = st.items.findIndex(function(x){ return x.t === 'cmt' && x.n === n; }); if (idx >= 0) openPop(st, idx);
});
document.addEventListener('keydown', function(e){
  var st = ANN._hover; if (!st || !st.open) return;
  var a = document.activeElement;
  if (a && (/TEXTAREA|INPUT/.test(a.tagName) || a.isContentEditable)) return;
  var k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && (k === 'z' || k === 'y')) { e.preventDefault(); if (k === 'y' || e.shiftKey) annRedo(st); else annUndo(st); return; }
  if (e.ctrlKey || e.metaKey || e.altKey) return;
  if (k === 'escape') { if (st.fly && !st.fly.hidden) closeFly(st); else annOpen(st, false); return; }
  var map = { v: 'hand', c: 'cmt', b: 'pen', e: 'erase', t: 'txt' }, shp = { r: 'rect', o: 'ellipse', l: 'line', a: 'arrow' };
  if (shp[k]) { e.preventDefault(); st.shape = shp[k]; setTool(st, shp[k]); return; }
  if (k === 's') { e.preventDefault(); setTool(st, st.sticker); return; }
  if (map[k]) { e.preventDefault(); setTool(st, map[k]); }
});
var annTimers = {};
function annSave(st){
  if (!db) return;
  clearTimeout(annTimers[st.spec]); setStatus('đang lưu…');
  annTimers[st.spec] = setTimeout(function(){
    db.doc(ANNDOC + st.spec).set({ spec: st.spec, w: st.W, h: st.H, items: st.items, updatedAt: new Date().toISOString() })
      .then(function(){ setStatus('<b>đã lưu</b> · ' + new Date().toLocaleTimeString('vi-VN')); })
      .catch(function(e){ setStatus('lưu nét vẽ lỗi (' + ((e && e.code) || 'không rõ') + ')'); });
  }, 700);
}
function annLoad(){
  Object.keys(ANN).forEach(function(k){
    if (k === '_hover') return;
    db.doc(ANNDOC + k).get().then(function(s){
      if (!s.exists) return;
      var v = s.data() || {}; ANN[k].items = Array.isArray(v.items) ? v.items : []; ANN[k].hist = []; ANN[k].fut = [];
      annRender(ANN[k]); render();
    }).catch(function(){});
  });
}


/* ---------- ghi chú + đính kèm ---------- */
var att = {}, assets = null, assetsTried = false, AUDIO_URL = {};
function getAssets(){
  if (assetsTried) return Promise.resolve(assets);
  assetsTried = true;
  if (!(window.claude && window.claude.use)) return Promise.resolve(null);
  return Promise.resolve().then(function(){ return window.claude.use('assets'); }).then(function(a){ assets = a; return a; }).catch(function(){ return null; });
}
function fmtSize(b){ return b > 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB'; }
function uid(){ return 'a' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
var RAW_TYPES = { 'image/png': 1, 'image/jpeg': 1, 'image/gif': 1, 'image/webp': 1, 'video/mp4': 1, 'video/webm': 1, 'application/pdf': 1, 'text/plain': 1, 'text/markdown': 1, 'application/json': 1, 'text/csv': 1 };
function typeOf(f){
  var t = (f.type || '').split(';')[0], n = (f.name || '').toLowerCase();
  if (!t) { if (/\.md$/.test(n)) t = 'text/markdown'; else if (/\.txt$/.test(n)) t = 'text/plain'; else if (/\.json$/.test(n)) t = 'application/json'; else if (/\.csv$/.test(n)) t = 'text/csv'; else if (/\.wav$/.test(n)) t = 'audio/wav'; else if (/\.mp3$/.test(n)) t = 'audio/mpeg'; else if (/\.m4a$/.test(n)) t = 'audio/mp4'; }
  if (/\.md$/.test(n)) t = 'text/markdown';
  return t || 'application/octet-stream';
}
function b64Chunks(buf, size){
  var u = new Uint8Array(buf), out = [], cur = '', STEP = 3 * 8192;
  for (var i = 0; i < u.length; i += STEP) { cur += btoa(String.fromCharCode.apply(null, u.subarray(i, i + STEP))); if (cur.length >= size) { out.push(cur); cur = ''; } }
  if (cur) out.push(cur);
  return out;
}
function setAttStatus(sec, t){ var el = document.querySelector('.notewrap[data-note="' + sec + '"] .attst'); if (el) el.textContent = t; }
function addFiles(sec, files){
  files = Array.prototype.slice.call(files || []); if (!files.length) return;
  getAssets().then(function(a){
    if (!a) { setAttStatus(sec, 'Trang không lưu được file ở chế độ xem này — gửi file trong chat giúp mình.'); return; }
    var chain = Promise.resolve();
    files.forEach(function(f){
      chain = chain.then(function(){
        var t = typeOf(f), kind = /^image\//.test(t) ? 'img' : /^audio\//.test(t) ? 'audio' : /^video\//.test(t) ? 'video' : 'file';
        var it = { id: uid(), kind: kind, name: f.name || ('dán ' + new Date().toLocaleTimeString('vi-VN')), type: t, size: f.size, note: '', marks: [], ids: [], enc: 'raw' };
        AUDIO_URL[it.id] = URL.createObjectURL(f);
        setAttStatus(sec, 'Đang tải lên ' + it.name + ' (' + fmtSize(f.size) + ')…');
        var up;
        if (RAW_TYPES[t]) up = a.upload(f, { type: t }).then(function(r){ it.ids = [r.id]; });
        else up = f.arrayBuffer().then(function(buf){
          it.enc = 'b64';
          var parts = b64Chunks(buf, 14 * 1024 * 1024), k = 0, p = Promise.resolve();
          parts.forEach(function(s){ p = p.then(function(){ k++; setAttStatus(sec, 'Đang tải lên ' + it.name + ' · phần ' + k + '/' + parts.length + '…'); return a.upload(new Blob([s], { type: 'text/plain' }), { type: 'text/plain' }).then(function(r){ it.ids.push(r.id); }); }); });
          return p;
        });
        return up.then(function(){ (att[sec] = att[sec] || []).push(it); renderAtt(sec); render(); save(); setAttStatus(sec, 'Đã lưu ' + it.name); })
          .catch(function(e){ setAttStatus(sec, 'Không tải lên được ' + it.name + ' (' + ((e && e.code) || 'lỗi') + ')'); });
      });
    });
  });
}
function loadAudio(it){
  if (AUDIO_URL[it.id]) return Promise.resolve(AUDIO_URL[it.id]);
  if (it.enc !== 'b64') { AUDIO_URL[it.id] = '/_blob/' + it.ids[0]; return Promise.resolve(AUDIO_URL[it.id]); }
  return Promise.all(it.ids.map(function(id){ return fetch('/_blob/' + id).then(function(r){ return r.text(); }); })).then(function(parts){
    var bytes = [];
    parts.forEach(function(s){ var bin = atob(s.trim()), u = new Uint8Array(bin.length); for (var i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); bytes.push(u); });
    var url = URL.createObjectURL(new Blob(bytes, { type: it.type })); AUDIO_URL[it.id] = url; return url;
  });
}
function renderAtt(sec){
  var box = document.querySelector('.notewrap[data-note="' + sec + '"] .attl'); if (!box) return;
  var list = att[sec] || []; box.innerHTML = '';
  list.forEach(function(it, idx){
    var row = document.createElement('div'); row.className = 'att-it att-' + it.kind;
    var head = document.createElement('div'); head.className = 'att-h';
    head.innerHTML = '<b></b><span class="mini"></span><button type="button" class="btnx att-del">Xoá</button>';
    head.querySelector('b').textContent = (it.kind === 'img' ? 'Ảnh · ' : it.kind === 'audio' ? 'Âm thanh · ' : it.kind === 'video' ? 'Video · ' : 'File · ') + it.name;
    head.querySelector('.mini').textContent = fmtSize(it.size || 0);
    row.appendChild(head);
    if (it.kind === 'img' && it.ids[0]) { var im = document.createElement('img'); im.src = AUDIO_URL[it.id] || ('/_blob/' + it.ids[0]); im.alt = it.name; im.className = 'att-img'; row.appendChild(im); }
    if (it.kind === 'audio' || it.kind === 'video') {
      var pl = document.createElement(it.kind === 'video' ? 'video' : 'audio'); pl.controls = true; pl.preload = 'metadata'; pl.className = 'att-player';
      var holder = document.createElement('div');
      if (AUDIO_URL[it.id] || it.enc !== 'b64') { loadAudio(it).then(function(u){ pl.src = u; }); holder.appendChild(pl); }
      else { var lb = document.createElement('button'); lb.type = 'button'; lb.className = 'btnx'; lb.textContent = 'Nạp để nghe'; lb.addEventListener('click', function(){ lb.textContent = 'đang nạp…'; loadAudio(it).then(function(u){ pl.src = u; holder.innerHTML = ''; holder.appendChild(pl); }).catch(function(){ lb.textContent = 'nạp lỗi — thử lại'; }); }); holder.appendChild(lb); }
      row.appendChild(holder);
      var mb = document.createElement('button'); mb.type = 'button'; mb.className = 'btnx pri att-mark'; mb.textContent = 'Ghi chú tại giây này';
      mb.addEventListener('click', function(){ var t = Math.round((pl.currentTime || 0) * 100) / 100; it.marks.push({ t: t, note: '' }); it.marks.sort(function(a, b){ return a.t - b.t; }); renderAtt(sec); render(); save(); });
      row.appendChild(mb);
      var ol = document.createElement('ol'); ol.className = 'att-mks';
      it.marks.forEach(function(m, mi){
        var li = document.createElement('li'); li.className = 'att-mk';
        li.innerHTML = '<b class="mono"></b><input type="text" placeholder="ghi chú tại giây này…"><button type="button" class="btnx">Nghe</button><button type="button" class="btnx">Xoá</button>';
        li.querySelector('b').textContent = fmtT(m.t);
        var inp = li.querySelector('input'); inp.value = m.note || '';
        inp.addEventListener('input', function(){ m.note = inp.value; render(); save(); });
        var bs = li.querySelectorAll('button');
        bs[0].addEventListener('click', function(){ if (pl.src) { pl.currentTime = Math.max(0, m.t - 1); pl.play(); } });
        bs[1].addEventListener('click', function(){ it.marks.splice(mi, 1); renderAtt(sec); render(); save(); });
        ol.appendChild(li);
      });
      row.appendChild(ol);
    }
    var note = document.createElement('input'); note.type = 'text'; note.className = 'att-note'; note.placeholder = it.kind === 'img' ? 'Ghi chú cho ảnh này…' : 'Ghi chú chung cho file này…'; note.value = it.note || '';
    note.addEventListener('input', function(){ it.note = note.value; render(); save(); });
    row.appendChild(note);
    var del = head.querySelector('.att-del');
    del.addEventListener('click', function(){
      if (del.dataset.sure !== '1') { del.dataset.sure = '1'; del.textContent = 'Bấm lần nữa để xoá'; return; }
      list.splice(idx, 1); renderAtt(sec); render(); save();
      if (assets) it.ids.forEach(function(id){ try { assets.delete(id).catch(function(){}); } catch (e) {} });
    });
    box.appendChild(row);
  });
}
function buildNote(w){
  var sec = w.dataset.note;
  w.innerHTML = '<div class="ntawrap"><textarea data-note="' + sec + '" placeholder="Feedback vòng 11…" rows="1"></textarea>' +
    '<div class="ntabar"><button type="button" class="ntaplus" title="Thêm ảnh / file" aria-label="Thêm ảnh hoặc file"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></button><div class="ntazone" role="button" tabindex="0" title="Bấm để chọn tệp"><span class="z-ic"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14"/></svg></span><span class="z-h"><b>Thả / dán ảnh, tài liệu, âm thanh</b> · hoặc bấm để chọn tệp</span><button type="button" class="ntazx" title="Thu lại" aria-label="Thu lại">✕</button></div><span class="attst"></span></div>' +
    '<input type="file" hidden multiple></div><div class="attl"></div>';
  var ta = w.querySelector('textarea'), wrap = w.querySelector('.ntawrap'), inp = w.querySelector('input[type=file]');
  function open(){ if (wrap.classList.contains('is-min')) { wrap.classList.remove('is-min'); } }
  function maybeClose(){ setTimeout(function(){ /* (18/10 vòng 2) ô ghi chú luôn mở sẵn — không gập lại */ }, 120); }
  w.__open = open;
  ta.addEventListener('focus', open);
  ta.addEventListener('blur', maybeClose);
  ta.addEventListener('input', function(){ notes[sec] = ta.value; render(); save(); });
  w.querySelector('.ntaplus').addEventListener('click', function(){ open(); wrap.classList.add('is-zone'); });
  var zone = w.querySelector('.ntazone');
  zone.addEventListener('click', function(e){ if (e.target.closest('.ntazx')) { wrap.classList.remove('is-zone'); maybeClose(); return; } inp.click(); });
  zone.addEventListener('keydown', function(e){ if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); inp.click(); } });
  inp.addEventListener('change', function(){ addFiles(sec, inp.files); inp.value = ''; });
  ['dragenter', 'dragover'].forEach(function(ev){ w.addEventListener(ev, function(e){ e.preventDefault(); open(); wrap.classList.add('is-over'); }); });
  ['dragleave', 'drop'].forEach(function(ev){ w.addEventListener(ev, function(e){ e.preventDefault(); wrap.classList.remove('is-over'); }); });
  w.addEventListener('drop', function(e){ if (e.dataTransfer && e.dataTransfer.files) addFiles(sec, e.dataTransfer.files); });
  w.addEventListener('paste', function(e){
    var fs = [], items = (e.clipboardData && e.clipboardData.items) || [];
    for (var i = 0; i < items.length; i++) if (items[i].kind === 'file') { var fl = items[i].getAsFile(); if (fl) fs.push(fl); }
    if (fs.length) { e.preventDefault(); open(); addFiles(sec, fs); }
  });
}
/* ---------- picks ---------- */
var PKH = [], PKF = [];   // Ctrl+Z cho lựa chọn quyết định (qua __UB)
function pickTo(st, v){ if (v == null){ var g = document.querySelector('.picks[data-key="' + st.k + '"]'); if (g) g.querySelectorAll('.pick').forEach(function(x){ x.setAttribute('aria-pressed', 'false'); }); delete picks[st.k]; } else selectPick(st.k, v); render(); save(); }
if (window.__UB) __UB.reg('picks', function(){ var st = PKH.pop(); if (st){ PKF.push(st); pickTo(st, st.from); } }, function(){ var st = PKF.pop(); if (st){ PKH.push(st); pickTo(st, st.to); } });
function selectPick(k, v){
  var g = document.querySelector('.picks[data-key="' + k + '"]'); if (!g) return;
  g.querySelectorAll('.pick').forEach(function(x){ x.setAttribute('aria-pressed', String(x.dataset.v === v)); });
  picks[k] = v;
}
document.querySelectorAll('.picks[data-key]').forEach(function(group){
  group.addEventListener('click', function(e){
    var b = e.target.closest('.pick'); if (!b || b.disabled) return;
    var prev = picks[group.dataset.key];
    group.querySelectorAll('.pick').forEach(function(x){ x.setAttribute('aria-pressed', String(x === b)); });
    picks[group.dataset.key] = b.dataset.v;
    if (prev !== b.dataset.v && window.__UB){ PKH.push({k: group.dataset.key, from: prev, to: b.dataset.v}); PKF.length = 0; __UB.note('picks'); }
    render(); save();
  });
});

document.querySelectorAll('.sec-tog').forEach(function(b){ b.addEventListener('click', function(){ var s = b.closest('.sec'); var c = s.classList.toggle('is-collapsed'); b.setAttribute('aria-expanded', String(!c)); }); });

/* ---------- summary + db ---------- */
function labelOf(v){ var b = document.querySelector('.pick[data-v="' + v + '"]'); if (!b) return ''; var t = b.cloneNode(true); t.querySelectorAll('b:first-child,.rec,.warnline').forEach(function(x){ x.remove(); }); return t.textContent.replace(/\s+/g, ' ').trim(); }
function summary(){
  var L = ['VibeEdit · dev_99.37 · vòng 11', ''];
  if (window.__FV_VER) L.push('Đang xem: ' + window.__FV_VER), L.push('');
  'ABCDEFGH'.split('').forEach(function(s){
    var sec = document.querySelector('.sec[data-sec="' + s + '"]'); if (!sec) return;
    sec.querySelectorAll('.picks[data-key]').forEach(function(g){ var k = g.dataset.key; L.push(picks[k] ? picks[k] + ' · ' + labelOf(picks[k]) : k + ' · (chưa chọn)'); });
    if (notes[s] && notes[s].trim()) L.push('Ghi chú ' + s + ': ' + notes[s].trim());
    (att[s] || []).forEach(function(it){
      L.push('Đính kèm ' + s + ': ' + it.name + ' [' + it.kind + ', ' + it.ids.length + ' asset' + (it.enc === 'b64' ? ', base64' : '') + ']' + (it.note ? ' — ' + it.note : ''));
      it.marks.forEach(function(m){ L.push('  ' + fmtT(m.t) + ' ' + (m.note || '(chưa gõ)')); });
    });
    Object.keys(ANN).forEach(function(k){
      if (k === '_hover') return;
      var st = ANN[k]; if (!st.wrap || st.wrap.closest('.sec').dataset.sec !== s || !st.items.length) return;
      var c = { pen: 0, line: 0, arrow: 0, rect: 0, ellipse: 0, ok: 0, no: 0, like: 0, dislike: 0, txt: 0 };
      st.items.forEach(function(x){ if (c[x.t] != null) c[x.t]++; });
      var parts = Object.keys(c).filter(function(t){ return c[t]; }).map(function(t){ return c[t] + ' ' + ({ pen: 'nét bút', line: 'đường thẳng', arrow: 'mũi tên', rect: 'chữ nhật', ellipse: 'tròn', ok: 'dấu OK', no: 'dấu NOT OK', like: 'like', dislike: 'dislike', txt: 'chữ' })[t]; });
      L.push('Canvas ' + k + (parts.length ? ': ' + parts.join(', ') : ''));
      st.items.filter(function(x){ return x.t === 'cmt' || x.t === 'txt'; }).forEach(function(x){ L.push('  ' + (x.t === 'cmt' ? '#' + x.n : 'chữ') + ' (' + Math.round(x.x) + ',' + Math.round(x.y) + ') ' + (x.text || '(chưa gõ)')); });
    });
    if (L[L.length - 1] !== '') L.push('');
  });
  return L.join('\n').trim();
}
function render(){ var s = summary(); document.getElementById('sum').textContent = s; document.getElementById('fallback').value = s; }
var DOC = 'review/dev99-37', ANNDOC = 'review/dev99-37/ann1/', db = null, timer = null, statusEl = document.getElementById('status'), loaded = false;
function setStatus(h){ if (statusEl) statusEl.innerHTML = h; }   // trang “chưa có font” không có chip trạng thái
window.__save = function(){ render(); save(); };
function save(){
  if (!db || !loaded) return;
  clearTimeout(timer); setStatus('đang lưu…');
  timer = setTimeout(function(){
    db.doc(DOC).set({ picks: picks, notesR11: notes, attR11: att, round: 11, summary: summary(), updatedAt: new Date().toISOString() })
      .then(function(){ setStatus('<b>đã lưu</b> · ' + new Date().toLocaleTimeString('vi-VN')); })
      .catch(function(e){ setStatus('lưu lỗi (' + ((e && e.code) || 'không rõ') + ') — chép khối Tổng hợp gửi Claude'); showFallback(); });
  }, 600);
}
function showFallback(){ document.getElementById('fallback').style.display = 'block'; }
document.querySelectorAll('.notewrap[data-note]').forEach(buildNote);
document.querySelectorAll('figure[data-ann]').forEach(annInit);
render();
var useP = (window.claude && window.claude.use) ? Promise.resolve().then(function(){ return window.claude.use('db'); }) : Promise.resolve(null);
useP.then(function(d){
  db = d;
  if (!db) { setStatus('không kết nối được nơi lưu — lựa chọn chỉ nằm trên trang này; chép khối Tổng hợp gửi Claude'); showFallback(); return; }
  annLoad();
  return db.doc(DOC).get().then(function(snap){
    if (snap.exists) {
      var v = snap.data() || {};
      Object.keys(v.picks || {}).forEach(function(k){ var g = document.querySelector('.picks[data-key="' + k + '"]'); var b = g && g.querySelector('.pick[data-v="' + v.picks[k] + '"]'); if (g && b && !g.closest('.dec-done') && !b.classList.contains('cut')) selectPick(k, v.picks[k]); });
      var n = v.notesR11 || {};
      Object.keys(n).forEach(function(k){ notes[k] = n[k]; var ta = document.querySelector('.notewrap[data-note="' + k + '"]  textarea'); if (ta) ta.value = n[k]; var nw = document.querySelector('.notewrap[data-note="' + k + '"]'); if (nw && nw.__open && n[k]) nw.__open(); });
      att = v.attR11 || {}; Object.keys(att).forEach(function(k){ renderAtt(k); var nw = document.querySelector('.notewrap[data-note="' + k + '"]'); if (nw && nw.__open && att[k] && att[k].length) nw.__open(); });
      setStatus('<b>đã nạp lựa chọn cũ</b> · tự lưu khi bấm');
    } else setStatus('<b>sẵn sàng</b> · tự lưu khi bấm');
    loaded = true; render();
  });
}).catch(function(){ setStatus('nơi lưu lỗi — chép khối Tổng hợp gửi Claude'); showFallback(); });
window.__ve37 = { ANN: ANN, picks: picks };

})();