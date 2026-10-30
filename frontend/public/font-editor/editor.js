/* Bàn vẽ glyph — trình sửa vector kiểu FontLab cho trang duyệt Việt hoá font.
   Dữ liệu: FV = { upm, xh, cap, asc, desc, tildeW, glyphs{name:{u,w,c}}, marks{k:contours}, recipes{name:{u,w,s,m:[{m,t}]}} }
   contour = [[op, [[x,y],...]], ...]  op: M L C Q  (đơn vị font, y hướng lên)
   Lưu: db  <EDDOC>/<key>   key = "m-<mark>" | "g-<glyph>"
   Bản vẽ nhiều chữ (kiểu artboard): BOARDS = [glyph…], chữ đang sửa (BA) luôn ở gốc toạ độ, chữ khác xếp hai bên. */
(function(){
'use strict';
function tr(key, values){ return window.__FV_T ? window.__FV_T(key, values) : key; }
var FV = JSON.parse(document.getElementById('fv-data').textContent);
var EDDOC = window.__FV_EDDOC || 'fontvn/review-r1/glyphs';
var SVGNS = 'http://www.w3.org/2000/svg';
var U2N = {}; Object.keys(FV.glyphs).forEach(function(n){ U2N[FV.glyphs[n].u] = n; });
Object.keys(FV.recipes).forEach(function(n){ U2N[FV.recipes[n].u] = n; });
var MARKS = [
  ['hook', 'Dấu hỏi', 'ả', 'uni1EA3'], ['hook_s', 'Dấu hỏi (khi chồng)', 'ẩ', 'uni1EA9'], ['horn', 'Móc ơ ư', 'ơ', 'uni01A1'],
  ['dot', 'Dấu nặng', 'ạ', 'uni1EA1'], ['tilde', 'Dấu ngã', 'ĩ', 'uni0129'], ['acute', 'Dấu sắc', 'ớ', 'uni1EDB'],
  ['grave', 'Dấu huyền', 'ờ', 'uni1EDD'], ['circ', 'Dấu mũ', 'ậ', 'uni1EAD'], ['breve', 'Dấu trăng', 'ă', 'uni0103']
];
var MK = {}; MARKS.forEach(function(m){ MK[m[0]] = m; });
function markLabel(id){ return tr('markNames.' + ({ hook_s: 'hookStacked', circ: 'circumflex' }[id] || id)); }
var VN = 'aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữựyỳýỷỹỵđ';
var VNU = VN.toUpperCase();
var PENS = ['pen', 'addpt', 'delpt', 'convert'];   // nhóm bút vector

/* ---------- geometry ---------- */
function opsToNodes(cs){
  return cs.map(function(c){
    var nodes = [], i;
    for (i = 0; i < c.length; i++) {
      var op = c[i][0], p = c[i][1];
      if (op === 'M' || op === 'L') nodes.push({ x: p[0][0], y: p[0][1] });
      else if (op === 'C') { var last = nodes[nodes.length - 1]; last.ox = p[0][0]; last.oy = p[0][1]; nodes.push({ x: p[2][0], y: p[2][1], ix: p[1][0], iy: p[1][1] }); }
      else if (op === 'Q') { var l2 = nodes[nodes.length - 1]; var q = p[0], e = p[1];
        l2.ox = l2.x + 2 / 3 * (q[0] - l2.x); l2.oy = l2.y + 2 / 3 * (q[1] - l2.y);
        nodes.push({ x: e[0], y: e[1], ix: e[0] + 2 / 3 * (q[0] - e[0]), iy: e[1] + 2 / 3 * (q[1] - e[1]) }); }
    }
    if (nodes.length > 1) { var a = nodes[0], z = nodes[nodes.length - 1];
      if (Math.abs(a.x - z.x) < .01 && Math.abs(a.y - z.y) < .01) { if (z.ix != null) { a.ix = z.ix; a.iy = z.iy; } nodes.pop(); } }
    nodes.forEach(function(n){ n.sm = isSmooth(n); });
    return { closed: true, nodes: nodes };
  });
}
function isSmooth(n){
  if (n.ix == null || n.ox == null) return false;
  var ax = n.x - n.ix, ay = n.y - n.iy, bx = n.ox - n.x, by = n.oy - n.y;
  var la = Math.hypot(ax, ay), lb = Math.hypot(bx, by); if (!la || !lb) return false;
  return (ax * bx + ay * by) / (la * lb) > 0.995;
}
function nodesToOps(contours){
  return contours.filter(function(c){ return c.nodes.length > 1; }).map(function(c){
    var N = c.nodes, out = [['M', [[r1(N[0].x), r1(N[0].y)]]]], n = N.length, last = c.closed ? n : n - 1;
    for (var i = 0; i < last; i++) {
      var a = N[i], b = N[(i + 1) % n];
      if (a.ox != null || b.ix != null) out.push(['C', [[r1(a.ox != null ? a.ox : a.x), r1(a.ox != null ? a.oy : a.y)], [r1(b.ix != null ? b.ix : b.x), r1(b.ix != null ? b.iy : b.y)], [r1(b.x), r1(b.y)]]]);
      else out.push(['L', [[r1(b.x), r1(b.y)]]]);
    }
    return out;
  });
}
function r1(v){ return Math.round(v * 10) / 10; }
function opsToD(cs, T){
  var t = T || [1, 0, 0, 1, 0, 0];
  function P(p){ return r1(t[0] * p[0] + t[2] * p[1] + t[4]) + ' ' + r1(t[1] * p[0] + t[3] * p[1] + t[5]); }
  return cs.map(function(c){
    return c.map(function(s){ var op = s[0], p = s[1];
      if (op === 'M') return 'M' + P(p[0]); if (op === 'L') return 'L' + P(p[0]);
      if (op === 'C') return 'C' + P(p[0]) + ' ' + P(p[1]) + ' ' + P(p[2]); if (op === 'Q') return 'Q' + P(p[0]) + ' ' + P(p[1]); return ''; }).join('') + 'Z';
  }).join('');
}
function strokesToD(strokes, T){
  var t = T || [1, 0, 0, 1, 0, 0];
  return strokes.map(function(s){ return 'M' + s.pts.map(function(p){ return r1(t[0] * p[0] + t[2] * p[1] + t[4]) + ' ' + r1(t[1] * p[0] + t[3] * p[1] + t[5]); }).join(' L'); });
}
function inv(t){ var d = t[0] * t[3] - t[1] * t[2]; return [t[3] / d, -t[1] / d, -t[2] / d, t[0] / d, (t[2] * t[5] - t[3] * t[4]) / d, (t[1] * t[4] - t[0] * t[5]) / d]; }
function ap(t, x, y){ return [t[0] * x + t[2] * y + t[4], t[1] * x + t[3] * y + t[5]]; }
function rdp(pts, eps){
  if (pts.length < 3) return pts.slice();
  var a = pts[0], b = pts[pts.length - 1], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, mi = 0, md = 0;
  for (var i = 1; i < pts.length - 1; i++) { var d = Math.abs(dy * pts[i][0] - dx * pts[i][1] + b[0] * a[1] - b[1] * a[0]) / L; if (d > md) { md = d; mi = i; } }
  if (md <= eps) return [a, b];
  return rdp(pts.slice(0, mi + 1), eps).slice(0, -1).concat(rdp(pts.slice(mi), eps));
}

/* ---------- hình học thành phần: làm phẳng, diện tích, tâm khối, bao lồi, trục dáng chữ ---------- */
function flatC(c){
  var N = c.nodes, n = N.length, pts = [], last = c.closed ? n : n - 1;
  if (!n) return pts;
  for (var i = 0; i < last; i++) {
    var a = N[i], b = N[(i + 1) % n], cv = a.ox != null || b.ix != null;
    var c1x = a.ox != null ? a.ox : a.x, c1y = a.ox != null ? a.oy : a.y, c2x = b.ix != null ? b.ix : b.x, c2y = b.ix != null ? b.iy : b.y, st = cv ? 10 : 1;
    for (var k = 0; k < st; k++) { var t = k / st, m = 1 - t;
      pts.push([m * m * m * a.x + 3 * m * m * t * c1x + 3 * m * t * t * c2x + t * t * t * b.x, m * m * m * a.y + 3 * m * m * t * c1y + 3 * m * t * t * c2y + t * t * t * b.y]); }
  }
  if (!c.closed) pts.push([N[n - 1].x, N[n - 1].y]);
  return pts;
}
function polyAC(P){   // diện tích có dấu + tâm khối (shoelace)
  var A = 0, cx = 0, cy = 0;
  for (var i = 0, n = P.length; i < n; i++) { var p = P[i], q = P[(i + 1) % n], k = p[0] * q[1] - q[0] * p[1]; A += k; cx += (p[0] + q[0]) * k; cy += (p[1] + q[1]) * k; }
  A /= 2; if (Math.abs(A) < 1e-6) { var sx = 0, sy = 0; P.forEach(function(p){ sx += p[0]; sy += p[1]; }); return { A: 0, x: sx / (P.length || 1), y: sy / (P.length || 1) }; }
  return { A: A, x: cx / (6 * A), y: cy / (6 * A) };
}
function inPoly(P, x, y){ var o = false; for (var i = 0, j = P.length - 1; i < P.length; j = i++) { var a = P[i], b = P[j]; if ((a[1] > y) !== (b[1] > y) && x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]) o = !o; } return o; }
function bboxOf(P){ var x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9; P.forEach(function(p){ if (p[0] < x0) x0 = p[0]; if (p[0] > x1) x1 = p[0]; if (p[1] < y0) y0 = p[1]; if (p[1] > y1) y1 = p[1]; }); return [x0, y0, x1, y1]; }
/* gom contour thành "thành phần": 1 nét ngoài + các lỗ nằm trong nó (lòng chữ o, a…). Tâm = tâm khối (đã trừ lỗ). */
function components(contours){
  var F = contours.map(function(c){ var P = flatC(c), ac = P.length > 2 ? polyAC(P) : { A: 0, x: 0, y: 0 }; return { P: P, A: Math.abs(ac.A), x: ac.x, y: ac.y }; });
  var parent = F.map(function(f, i){
    var best = -1; if (!f.P.length) return -1;
    F.forEach(function(g, j){ if (j === i || g.A <= f.A || g.P.length < 3) return; if (inPoly(g.P, f.P[0][0], f.P[0][1]) && (best < 0 || g.A < F[best].A)) best = j; });
    return best;
  });
  function depth(i){ var d = 0; while (parent[i] >= 0 && d < 9) { i = parent[i]; d++; } return d; }
  var out = [];
  F.forEach(function(f, i){ if (depth(i) % 2 || f.P.length < 2) return;
    var ci = [i], A = f.A, mx = f.A * f.x, my = f.A * f.y;
    F.forEach(function(g, j){ if (parent[j] === i && depth(j) % 2) { ci.push(j); A -= g.A; mx -= g.A * g.x; my -= g.A * g.y; } });
    var bb = bboxOf(f.P);
    out.push({ ci: ci, outer: f.P, A: A, cx: A > 1 ? mx / A : (bb[0] + bb[2]) / 2, cy: A > 1 ? my / A : (bb[1] + bb[3]) / 2, bb: bb });
  });
  return out;
}
function hull(pts){
  var P = pts.slice().sort(function(a, b){ return a[0] - b[0] || a[1] - b[1]; }); if (P.length < 3) return P;
  function cr(o, a, b){ return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]); }
  var lo = [], up = [];
  P.forEach(function(p){ while (lo.length > 1 && cr(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); });
  for (var i = P.length - 1; i >= 0; i--) { var p = P[i]; while (up.length > 1 && cr(up[up.length - 2], up[up.length - 1], p) <= 0) up.pop(); up.push(p); }
  return lo.slice(0, -1).concat(up.slice(0, -1));
}
/* trục dáng chữ x = a + b·y: tâm các lát cắt ngang của bao lồi thân chữ (bỏ dấu), nghiêng tối đa ±8° — giống vnfont.shape_axis */
function shapeAxis(ops, topLine, upright){
  var pts = [];
  opsToNodes(ops).forEach(function(c){ var P = flatC(c); if (!P.length) return; var bb = bboxOf(P);
    if (bb[1] > topLine * 0.85 || bb[3] < -5) return;    // dấu trên / dấu nặng: không tính
    pts = pts.concat(P); });
  if (pts.length < 3) return null;
  var H = hull(pts), bb = bboxOf(H), ys = [], xs = [];
  for (var k = 0; k < 24; k++) {
    var y = bb[1] + (bb[3] - bb[1]) * (0.30 + 0.67 * k / 23), lo = 1e9, hi = -1e9;
    for (var i = 0; i < H.length; i++) { var a = H[i], b = H[(i + 1) % H.length];
      if ((a[1] - y) * (b[1] - y) <= 0 && a[1] !== b[1]) { var x = a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]); if (x < lo) lo = x; if (x > hi) hi = x; } }
    if (hi >= lo) { ys.push(y); xs.push((lo + hi) / 2); }
  }
  if (ys.length < 3) return { a: (bb[0] + bb[2]) / 2, b: 0 };
  var my = ys.reduce(function(s, v){ return s + v; }, 0) / ys.length, mx = xs.reduce(function(s, v){ return s + v; }, 0) / xs.length, sxy = 0, syy = 0;
  ys.forEach(function(y, i){ sxy += (y - my) * (xs[i] - mx); syy += (y - my) * (y - my); });
  if (upright) return { a: mx, b: 0 };     // font đứng → trục thẳng đứng qua tâm thân chữ
  /* font nghiêng: MỘT góc cho cả font (người dùng 28/10: “u không nghiêng”, trục phải đồng bộ cả bộ) — không tự nghiêng theo dáng từng chữ */
  var lim = Math.tan(8 * Math.PI / 180), bs = TANA ? TANA : (syy ? Math.max(-lim, Math.min(lim, sxy / syy)) : 0);
  return { a: mx - bs * my, b: bs };
}

/* ---------- edit state ---------- */
var ED = {};           // key -> {contours, strokes, w, note, touched, hist, fut}
function keyOf(sel){ return sel.kind === 'm' ? 'm-' + sel.id : 'g-' + sel.id; }
function sourceOps(sel){
  if (sel.kind === 'm') return FV.marks[sel.id] || [];
  var r = FV.recipes[sel.id];
  if (r) { var cs = r.s.slice(); r.m.forEach(function(mi){ cs = cs.concat(transformOps(markOps(mi.m), mi.t)); }); return cs; }
  return (FV.glyphs[sel.id] || { c: [] }).c;
}
function transformOps(cs, t){ return cs.map(function(c){ return c.map(function(s){ return [s[0], s[1].map(function(p){ return ap(t, p[0], p[1]).map(r1); })]; }); }); }
function markOps(m){ var e = ED['m-' + m]; return e && e.touched ? nodesToOps(e.contours) : (FV.marks[m] || []); }
function markStrokes(m){ var e = ED['m-' + m]; return e && e.touched ? e.strokes : []; }
function getEd(sel){
  var k = keyOf(sel);
  if (!ED[k]) {
    var w = sel.kind === 'm' ? 0 : ((FV.recipes[sel.id] || FV.glyphs[sel.id] || {}).w || 500);
    ED[k] = { contours: opsToNodes(sourceOps(sel)), strokes: [], w: w, note: '', touched: false, pendingSave: false, saveGen: 0, hist: [], fut: [] };
  }
  return ED[k];
}
function snap(e){ return JSON.stringify({ c: e.contours, s: e.strokes }); }
var EH = [], EF = [];   // thứ tự bước hoàn tác của MỌI chữ trên bàn vẽ (key), để Ctrl+Z quay đúng chữ vừa sửa
function push(){ var e = cur(); e.hist.push(snap(e)); if (e.hist.length > 120) e.hist.shift(); e.fut = []; EH.push(keyOf(sel)); EF = []; if (window.__UB) __UB.note('editor'); }
function unpush(){ var e = cur(); e.hist.pop(); EH.pop(); if (window.__UB && __UB.drop) __UB.drop('editor'); }   // bấm mà không kéo: bỏ bước rỗng
function commit(){ var e = cur(); e.touched = true; e.pendingSave = true; e.saveGen = (e.saveGen || 0) + 1; render(); if (window.__FV_BRIDGE && window.__FV_BRIDGE.dirty) window.__FV_BRIDGE.dirty(keyOf(sel)); schedSave(); }
function undo(){ if (!EH.length) return; var k = EH.pop(); goKey(k); var e = cur(); if (!e.hist.length) return; EF.push(k); if (window.__UB) __UB.undone('editor'); e.fut.push(snap(e)); var s = JSON.parse(e.hist.pop()); e.contours = s.c; e.strokes = s.s; sel.nodes = []; commit(); }
function redo(){ if (!EF.length) return; var k = EF.pop(); goKey(k); var e = cur(); if (!e.fut.length) return; EH.push(k); if (window.__UB) __UB.redone('editor'); e.hist.push(snap(e)); var s = JSON.parse(e.fut.pop()); e.contours = s.c; e.strokes = s.s; sel.nodes = []; commit(); }

/* ---------- DOM ---------- */
var root = document.getElementById('ed');
if (!root) return;
var svg = root.querySelector('.ed-stage svg.ed-cv'), world = svg.querySelector('#ed-world');
var RX = root.querySelector('.ed-rx'), RY = root.querySelector('.ed-ry'), stage = root.querySelector('.ed-stage');
['boards', 'grid', 'lbox', 'axis', 'advx'].forEach(function(id){ if (!svg.querySelector('#ed-' + id)) { var g = document.createElementNS(SVGNS, 'g'); g.setAttribute('id', 'ed-' + id); world.insertBefore(g, world.firstChild); } });
/* hàng tuỳ chọn hiển thị dưới canvas — bấm 1 lần bật, lần 2 tắt; nhớ theo trình duyệt */
['comp', 'snapg'].forEach(function(id){ if (!svg.querySelector('#ed-' + id)) { var g = document.createElementNS(SVGNS, 'g'); g.setAttribute('id', 'ed-' + id); world.appendChild(g); } });
var OPT = { grid: true, rulers: true, metrics: true, orig: true, adv: true, axis: true, nodes: true, lbox: false, snap: true };
try { var _o = JSON.parse(localStorage.getItem('fv-ed-opt') || 'null'); if (_o) Object.keys(OPT).forEach(function(k){ if (k in _o) OPT[k] = !!_o[k]; }); } catch (e) {}
var AX = (FV.axis || 0), TANA = Math.abs(AX) > 1 ? Math.tan(AX * Math.PI / 180) : 0;
var L = {}; ['boards', 'grid', 'lbox', 'axis', 'advx', 'metrics', 'ghost', 'ctx', 'orig', 'fill', 'strokes', 'handles', 'nodes', 'draft', 'marq', 'comp', 'snapg'].forEach(function(id){ L[id] = svg.querySelector('#ed-' + id); });
var info = root.querySelector('.ed-info'), listEl = root.querySelector('.ed-list'), noteEl = root.querySelector('#ed-note');
var brushW = root.querySelector('#ed-bw'), brushOut = root.querySelector('#ed-bwv');
var pvIn = root.querySelector('#ed-pvtext'), pvSvg = root.querySelector('.ed-pv svg');
/* mặc định mở chữ a */
var sel = U2N[97] ? { kind: 'g', id: U2N[97], nodes: [], stroke: -1, comp: -1 } : { kind: 'm', id: 'hook', nodes: [], stroke: -1, comp: -1 }, tool = 'select', pen = null, drag = null, vb = null;
function cur(){ return getEd(sel); }

/* view transform of the edited layer (marks are shown in place on a representative glyph) */
function repRecipe(){ return sel.kind === 'm' ? FV.recipes[MK[sel.id][3]] : null; }
function layerT(){
  if (sel.kind !== 'm') return [1, 0, 0, 1, 0, 0];
  var r = repRecipe(); if (!r) return [1, 0, 0, 1, 0, 0];
  var mi = r.m.filter(function(x){ return x.m === sel.id; })[0]; return mi ? mi.t : [1, 0, 0, 1, 0, 0];
}
function el(tag, a){ var e = document.createElementNS(SVGNS, tag); for (var k in a) e.setAttribute(k, a[k]); return e; }
function clear(g){ while (g.firstChild) g.removeChild(g.firstChild); }
function upp(){ var r = svg.getBoundingClientRect(); return vb.w / Math.max(1, r.width); }
function fit(){
  var r = sel.kind === 'm' ? repRecipe() : null, w = r ? r.w : cur().w || 600;
  var top = Math.max(FV.asc, FV.cap + 380), bot = Math.min(FV.desc, -220);
  var h = top - bot, ww = Math.max(w + 400, h * svgAspect());
  vb = { x: w / 2 - ww / 2, y: -top, w: ww, h: h * Math.max(1, ww / svgAspect() / h) };
  vb.y = -top - (vb.h - h) / 2; applyVB();
}
function svgAspect(){ var r = svg.getBoundingClientRect(); return (r.width || 600) / (r.height || 560); }
function applyVB(){ svg.setAttribute('viewBox', [vb.x, vb.y, vb.w, vb.h].map(r1).join(' ')); render(); }
function toWorld(e){ var p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; var q = p.matrixTransform(world.getScreenCTM().inverse()); return [q.x, q.y]; }
function toLocal(e){ var w = toWorld(e); return ap(inv(layerT()), w[0], w[1]); }

function render(){
  if (!vb) return;
  var e = cur(), T = layerT(), u = upp(), s = Math.hypot(T[0], T[1]) || 1, R = 5 * u / s;
  var lg = L.metrics; clear(lg);
  var w = sel.kind === 'm' ? (repRecipe() || {}).w || 600 : e.w;
  if (OPT.metrics) [[0, tr('baselineValue')], [FV.xh, tr('xHeightValue', { value: FV.xh })], [FV.cap, tr('capHeightValue', { value: FV.cap })], [FV.asc, tr('ascenderValue', { value: FV.asc })], [FV.desc, tr('descenderValue', { value: FV.desc })]].forEach(function(m){
    lg.appendChild(el('line', { x1: vb.x, x2: vb.x + vb.w, y1: m[0], y2: m[0], class: 'ed-ml' + (m[0] === 0 ? ' base' : '') , 'vector-effect': 'non-scaling-stroke' }));
    var t = el('text', { x: vb.x + 8 * u, y: -(m[0] + 4 * u), class: 'ed-mt', transform: 'scale(1,-1)', 'font-size': 11 * u }); t.textContent = m[1]; lg.appendChild(t);
  });
  drawGrid(u); drawLineBox(u); drawAxis(w, u); drawAdvance(w, u, e, T); drawBoards(u);
  drawRulers();
  clear(L.ctx); clear(L.ghost); clear(L.orig);
  if (sel.kind === 'm') {
    var r = repRecipe();
    if (r) {
      L.ctx.appendChild(el('path', { d: opsToD(r.s), class: 'ed-ctx' }));
      r.m.forEach(function(mi){ if (mi.m !== sel.id) { L.ctx.appendChild(el('path', { d: opsToD(markOps(mi.m), mi.t), class: 'ed-ctx' })); } });
    }
  }
  L.orig.setAttribute('transform', 'matrix(' + T.join(' ') + ')');
  L.orig.appendChild(el('path', { d: opsToD(sel.kind === 'm' ? (FV.marks[sel.id] || []) : sourceOpsPristine()), class: 'ed-orig', 'vector-effect': 'non-scaling-stroke' }));
  L.orig.style.display = OPT.orig ? '' : 'none';
  [L.fill, L.strokes, L.handles, L.nodes, L.draft].forEach(function(g){ g.setAttribute('transform', 'matrix(' + T.join(' ') + ')'); });
  clear(L.fill); clear(L.strokes); clear(L.handles); clear(L.nodes); clear(L.draft);
  var ops = nodesToOps(e.contours);
  L.fill.appendChild(el('path', { d: opsToD(ops), class: 'ed-fill', 'fill-rule': 'nonzero' }));
  e.contours.forEach(function(c, ci){
    if (!c.nodes.length) return;
    var single = nodesToOps([c]); if (single.length) L.fill.appendChild(el('path', { d: opsToD(single), class: 'ed-outline', 'data-c': ci, 'vector-effect': 'non-scaling-stroke' }));
  });
  e.strokes.forEach(function(st, si){ L.strokes.appendChild(el('path', { d: strokesToD([st])[0], class: 'ed-brush' + (sel.stroke === si ? ' is-sel' : ''), 'stroke-width': st.w, 'data-s': si })); });
  if (tool !== 'brush' && tool !== 'comp' && (OPT.nodes || PENS.indexOf(tool) >= 0)) e.contours.forEach(function(c, ci){
    c.nodes.forEach(function(n, ni){
      var on = sel.nodes.some(function(x){ return x[0] === ci && x[1] === ni; });
      var nearSel = on || sel.nodes.some(function(x){ return x[0] === ci && Math.abs(x[1] - ni) <= 1; });
      if (nearSel || c.nodes.length < 40) {
        if (n.ix != null && (on || nearSel)) { L.handles.appendChild(el('line', { x1: n.x, y1: n.y, x2: n.ix, y2: n.iy, class: 'ed-hl', 'vector-effect': 'non-scaling-stroke' })); L.handles.appendChild(el('circle', { cx: n.ix, cy: n.iy, r: R * 0.75, class: 'ed-h', 'data-c': ci, 'data-n': ni, 'data-h': 'i' })); }
        if (n.ox != null && (on || nearSel)) { L.handles.appendChild(el('line', { x1: n.x, y1: n.y, x2: n.ox, y2: n.oy, class: 'ed-hl', 'vector-effect': 'non-scaling-stroke' })); L.handles.appendChild(el('circle', { cx: n.ox, cy: n.oy, r: R * 0.75, class: 'ed-h', 'data-c': ci, 'data-n': ni, 'data-h': 'o' })); }
      }
      var cls = 'ed-n' + (n.sm ? ' sm' : '') + (on ? ' on' : '') + (pen && pen.c === ci && ni === 0 ? ' first' : '');
      if (n.sm) L.nodes.appendChild(el('circle', { cx: n.x, cy: n.y, r: R, class: cls, 'data-c': ci, 'data-n': ni }));
      else L.nodes.appendChild(el('rect', { x: n.x - R, y: n.y - R, width: 2 * R, height: 2 * R, class: cls, 'data-c': ci, 'data-n': ni }));
    });
  });
  if (pen && pen.hover && e.contours[pen.c]) {
    var nn = e.contours[pen.c].nodes, ln = nn[nn.length - 1];
    if (ln) L.draft.appendChild(el('path', { d: 'M' + ln.x + ' ' + ln.y + ' C' + (ln.ox != null ? ln.ox : ln.x) + ' ' + (ln.ox != null ? ln.oy : ln.y) + ' ' + pen.hover[0] + ' ' + pen.hover[1] + ' ' + pen.hover[0] + ' ' + pen.hover[1], class: 'ed-rubber', 'vector-effect': 'non-scaling-stroke' }));
  }
  if (drag && drag.brush) L.draft.appendChild(el('path', { d: 'M' + drag.pts.map(function(p){ return p[0] + ' ' + p[1]; }).join(' L'), class: 'ed-brush', 'stroke-width': +brushW.value }));
  drawComp(T, u); drawSnapGuides(u);
  clear(L.marq);
  if (drag && drag.marq) { var a = drag.marq; L.marq.appendChild(el('rect', { x: Math.min(a[0], a[2]), y: Math.min(a[1], a[3]), width: Math.abs(a[2] - a[0]), height: Math.abs(a[3] - a[1]), class: 'ed-marq', 'vector-effect': 'non-scaling-stroke' })); }
  renderInfo(); renderPreview(); renderList(); renderStrip();
  var ub = root.querySelector('[data-ed="undo"]'), rb = root.querySelector('[data-ed="redo"]'); if (ub) ub.disabled = !EH.length; if (rb) rb.disabled = !EF.length;
}
/* lưới mờ: bước nhỏ tự đổi theo độ phóng, nét đậm mỗi 5 bước */
function gridStep(u){ var st = [2, 5, 10, 20, 25, 50, 100, 200, 250, 500]; for (var i = 0; i < st.length; i++) if (st[i] / u >= 9) return st[i]; return 1000; }
function drawGrid(u){
  var g = L.grid; clear(g); if (!OPT.grid) return;
  var st = gridStep(u), x0 = Math.floor(vb.x / st) * st, x1 = vb.x + vb.w, y0 = Math.floor(-(vb.y + vb.h) / st) * st, y1 = -vb.y, d1 = '', d2 = '';
  for (var x = x0; x <= x1; x += st) { var M = Math.round(x / st) % 5 === 0; (M ? (d2 += 'M' + x + ' ' + y0 + 'V' + y1) : (d1 += 'M' + x + ' ' + y0 + 'V' + y1)); }
  for (var y = y0; y <= y1; y += st) { var M2 = Math.round(y / st) % 5 === 0; (M2 ? (d2 += 'M' + x0 + ' ' + y + 'H' + x1) : (d1 += 'M' + x0 + ' ' + y + 'H' + x1)); }
  g.appendChild(el('path', { d: d1, class: 'ed-gr', 'vector-effect': 'non-scaling-stroke' }));
  g.appendChild(el('path', { d: d2, class: 'ed-gr2', 'vector-effect': 'non-scaling-stroke' }));
}
/* line biên dọc: hộp dòng mà Canva / web / Word dùng (ascender–descender của font) */
function drawLineBox(u){
  var g = L.lbox; clear(g); if (!OPT.lbox) return;
  var a = FV.lbAsc != null ? FV.lbAsc : FV.asc, d = FV.lbDesc != null ? FV.lbDesc : FV.desc;
  g.appendChild(el('rect', { x: vb.x, y: d, width: vb.w, height: a - d, class: 'ed-lb' }));
  [[a, tr('lineBoxTop', { value: a })], [d, tr('lineBoxBottom', { value: d })]].forEach(function(m){
    g.appendChild(el('line', { x1: vb.x, x2: vb.x + vb.w, y1: m[0], y2: m[0], class: 'ed-lbl', 'vector-effect': 'non-scaling-stroke' }));
    var t = el('text', { x: vb.x + vb.w - 8 * u, y: -(m[0] + 4 * u), class: 'ed-mt lb', transform: 'scale(1,-1)', 'font-size': 11 * u, 'text-anchor': 'end' }); t.textContent = m[1]; g.appendChild(t);
  });
}
/* trục chữ: đứng hay nghiêng theo góc dò được từ font */
/* trục chữ: font nghiêng → cùng góc font cho mọi chữ, vị trí theo trục họ chữ (axis_editor.py) hoặc tâm thân chữ; + đường giữa hộp (giữa 2 biên advance) để so */
var AXC = {};
function glyphAxis(gid){
  var id = gid || (sel.kind === 'm' ? MK[sel.id][3] : sel.id), r = FV.recipes[id];
  if (AXC[id] !== undefined) return AXC[id];
  var gi = r || FV.glyphs[id]; if (!gi) return (AXC[id] = null);
  var up = !TANA;   // font đứng (góc dò < 1°) → mọi trục chữ thẳng đứng; chỉ font nghiêng mới vẽ trục chéo
  var sx = (r && r.sax) || (FV.glyphs[id] && FV.glyphs[id].sax);   // trục qua tâm dấu đã đặt (axis_editor.py), cả chữ có sẵn của font
  if (sx) return (AXC[id] = up ? { a: sx[0] + sx[1] * FV.xh * 0.6, b: 0 } : { a: sx[0], b: sx[1] });
  var ch = String.fromCodePoint(gi.u), top = ch !== ch.toLowerCase() ? FV.cap : FV.xh;
  return (AXC[id] = shapeAxis(r ? r.s : gi.c, top, up));
}
function axisX(y, w, gid){ var g = glyphAxis(gid); return g ? g.a + g.b * y : w / 2 + (y - FV.xh / 2) * TANA; }
function drawAxis(w, u){
  var g = L.axis; clear(g); if (!OPT.axis) return;
  var ya = FV.desc - 150, yb = FV.asc + 350, ga = glyphAxis();
  g.appendChild(el('line', { x1: w / 2, y1: ya, x2: w / 2, y2: yb, class: 'ed-boxc', 'vector-effect': 'non-scaling-stroke' }));
  var t0 = el('text', { x: w / 2 + 6 * u, y: -(ya + 20), class: 'ed-mt', transform: 'scale(1,-1)', 'font-size': 10.5 * u }); t0.textContent = tr('middleBox', { value: r1(w / 2) }); g.appendChild(t0);
  g.appendChild(el('line', { x1: axisX(ya, w), y1: ya, x2: axisX(yb, w), y2: yb, class: 'ed-ax', 'vector-effect': 'non-scaling-stroke' }));
  var deg = ga ? Math.atan(ga.b) * 180 / Math.PI : AX;
  var t = el('text', { x: axisX(yb - 40, w) + 8 * u, y: -(yb - 40), class: 'ed-mt ax', transform: 'scale(1,-1)', 'font-size': 11 * u });
  t.textContent = (Math.abs(deg) > 0.2 ? tr('slantedAxis', { angle: deg.toFixed(1) }) : tr('verticalAxis')) + ' · ' + tr('axisCoordinate', { value: r1(axisX(FV.xh, w)) }); g.appendChild(t);
}
/* ---------- snap: điểm / tâm thành phần dính vào lưới, đường chữ, 2 biên, giữa hộp, trục chữ, điểm khác ---------- */
function snapTargets(w, u){
  var X = [[0, tr('snapLeft')], [w, tr('snapRight')], [w / 2, tr('snapCenter')]], Y = [[0, tr('snapBaseline')], [FV.xh, tr('snapXHeight')], [FV.cap, tr('snapCap')], [FV.asc, tr('snapAscender')], [FV.desc, tr('snapDescender')]];
  return { X: X, Y: Y, grid: OPT.grid ? gridStep(u) : 0 };
}
function snapPt(pw, u, skip){   // pw: điểm thế giới; skip(ci,ni) → bỏ các điểm đang kéo
  var w = sel.kind === 'm' ? (repRecipe() || {}).w || 600 : cur().w, thr = 8 * u, T = layerT(), tg = snapTargets(w, u);
  var bx = null, by = null, dx = thr, dy = thr;
  function tx(v, lb, pen){ var d = Math.abs(v - pw[0]) + (pen || 0); if (d < dx) { dx = d; bx = [v, lb]; } }   // pen: đường phụ (điểm khác) ưu tiên thấp hơn trục / biên
  function ty(v, lb, pen){ var d = Math.abs(v - pw[1]) + (pen || 0); if (d < dy) { dy = d; by = [v, lb]; } }
  tg.X.forEach(function(t){ tx(t[0], t[1]); }); tg.Y.forEach(function(t){ ty(t[0], t[1]); });
  tx(axisX(pw[1], w), tr('snapAxis'));
  cur().contours.forEach(function(c, ci){ c.nodes.forEach(function(n, ni){ if (skip && skip(ci, ni)) return; var q = ap(T, n.x, n.y); tx(q[0], tr('snapVerticalPoint'), thr * 0.45); ty(q[1], tr('snapHorizontalPoint'), thr * 0.45); }); });
  if (tg.grid) { var gx = Math.round(pw[0] / tg.grid) * tg.grid, gy = Math.round(pw[1] / tg.grid) * tg.grid; if (!bx && Math.abs(gx - pw[0]) < thr * 0.6) bx = [gx, tr('snapGrid')]; if (!by && Math.abs(gy - pw[1]) < thr * 0.6) by = [gy, tr('snapGrid')]; }
  return { p: [bx ? bx[0] : pw[0], by ? by[0] : pw[1]], gx: bx, gy: by };
}
var GUIDES = null;
function drawSnapGuides(u){
  var g = L.snapg; clear(g); if (!GUIDES) return;
  if (GUIDES.gx) { g.appendChild(el('line', { x1: GUIDES.gx[0], x2: GUIDES.gx[0], y1: -(vb.y + vb.h), y2: -vb.y, class: 'ed-snapl', 'vector-effect': 'non-scaling-stroke' }));
    var t = el('text', { x: GUIDES.gx[0] + 5 * u, y: vb.y + 16 * u, class: 'ed-mt snap', transform: 'scale(1,-1)', 'font-size': 10.5 * u }); t.textContent = GUIDES.gx[1]; g.appendChild(t); }
  if (GUIDES.gy) { g.appendChild(el('line', { x1: vb.x, x2: vb.x + vb.w, y1: GUIDES.gy[0], y2: GUIDES.gy[0], class: 'ed-snapl', 'vector-effect': 'non-scaling-stroke' }));
    var t2 = el('text', { x: GUIDES.p[0] + 8 * u, y: -(GUIDES.gy[0] + 4 * u), class: 'ed-mt snap', transform: 'scale(1,-1)', 'font-size': 10.5 * u }); t2.textContent = GUIDES.gy[1]; g.appendChild(t2); }
  g.appendChild(el('circle', { cx: GUIDES.p[0], cy: GUIDES.p[1], r: 4 * u, class: 'ed-snapd' }));
}
/* ---------- chế độ thành phần: mỗi phần (thân, dấu, móc…) có tâm khối riêng ---------- */
function drawComp(T, u){
  var g = L.comp; clear(g); g.setAttribute('transform', 'matrix(' + T.join(' ') + ')');
  if (tool !== 'comp') return;
  var s = Math.hypot(T[0], T[1]) || 1, k = u / s, C = components(cur().contours);
  C.forEach(function(c, i){
    var on = i === sel.comp, R = (on ? 12 : 8) * k;
    if (on) g.appendChild(el('rect', { x: c.bb[0], y: c.bb[1], width: c.bb[2] - c.bb[0], height: c.bb[3] - c.bb[1], class: 'ed-cbb', 'vector-effect': 'non-scaling-stroke' }));
    g.appendChild(el('path', { d: 'M' + (c.cx - R) + ' ' + c.cy + 'H' + (c.cx + R) + 'M' + c.cx + ' ' + (c.cy - R) + 'V' + (c.cy + R), class: 'ed-cx' + (on ? ' on' : ''), 'vector-effect': 'non-scaling-stroke' }));
    g.appendChild(el('circle', { cx: c.cx, cy: c.cy, r: R * 0.42, class: 'ed-cxd' + (on ? ' on' : ''), 'vector-effect': 'non-scaling-stroke' }));
  });
}
/* 2 đường biên advance + tô đỏ phần mực tràn ra ngoài (Word/Excel/Canva không kern → chỗ này dính chữ bên cạnh) */
function inkBox(e, T){
  var xs = [], ys = [];
  function addOps(cs, t){ cs.forEach(function(c){ c.forEach(function(sg){ sg[1].forEach(function(p){ var q = t ? ap(t, p[0], p[1]) : p; xs.push(q[0]); ys.push(q[1]); }); }); }); }
  if (sel.kind === 'm') { var r = repRecipe(); if (r) { r.m.forEach(function(mi){ addOps(mi.m === sel.id ? nodesToOps(e.contours) : markOps(mi.m), mi.t); }); } }
  else {
    var gi = FV.recipes[sel.id] || FV.glyphs[sel.id], ch = gi ? String.fromCodePoint(gi.u) : '', topL = (ch && ch !== ch.toLowerCase() ? FV.cap : FV.xh) + 12;
    addOps(nodesToOps(e.contours), null);
    var keep = []; for (var i = 0; i < xs.length; i++) if (ys[i] > topL || ys[i] < -12) keep.push(i);   // marks only, not the body
    xs = keep.map(function(i){ return xs[i]; }); ys = keep.map(function(i){ return ys[i]; });
  }
  e.strokes.forEach(function(st){ st.pts.forEach(function(p){ var q = sel.kind === 'm' ? ap(T, p[0], p[1]) : p; xs.push(q[0] - st.w / 2, q[0] + st.w / 2); ys.push(q[1]); }); });
  if (!xs.length) return null;
  return [Math.min.apply(null, xs), Math.min.apply(null, ys), Math.max.apply(null, xs), Math.max.apply(null, ys)];
}
var OVER = null;
function drawAdvance(w, u, e, T){
  var g = L.advx; clear(g); OVER = null;
  if (!OPT.adv) return;
  [0, w].forEach(function(x){ g.appendChild(el('line', { x1: x, x2: x, y1: FV.desc - 300, y2: FV.asc + 500, class: 'ed-advl', 'vector-effect': 'non-scaling-stroke' })); });
  var b = inkBox(e, T); if (!b) return;
  var top = FV.xh + 12;   // only marks count: ink above x-height (lowercase) / below baseline
  var L0 = Math.max(0, -b[0]), R0 = Math.max(0, b[2] - w);
  OVER = { L: Math.round(L0), R: Math.round(R0) };
  if (L0 > 0) g.appendChild(el('rect', { x: b[0], y: b[1], width: L0, height: b[3] - b[1], class: 'ed-over' }));
  if (R0 > 0) g.appendChild(el('rect', { x: w, y: b[1], width: R0, height: b[3] - b[1], class: 'ed-over' }));
}
/* thước trên + trái, đơn vị font */
function drawRulers(){
  if (!RX || !RY) return;
  RX.style.display = RY.style.display = OPT.rulers ? '' : 'none';
  if (!OPT.rulers) return;
  var rr = svg.getBoundingClientRect(), W = rr.width, H = rr.height, u = vb.w / Math.max(1, W), st = gridStep(u) , major = st * 5;
  while (major / u < 60) major *= 2;
  var hx = '', tx = '', x0 = Math.floor(vb.x / st) * st;
  for (var x = x0; x <= vb.x + vb.w; x += st) { var sx = (x - vb.x) / u, M = Math.round(x) % major === 0; hx += 'M' + sx.toFixed(1) + ' ' + (M ? 6 : 13) + 'V20'; if (M) tx += '<text x="' + (sx + 3).toFixed(1) + '" y="10">' + Math.round(x) + '</text>'; }
  RX.setAttribute('viewBox', '0 0 ' + W + ' 20'); RX.innerHTML = '<path d="' + hx + '"/>' + tx;
  var hy = '', ty = '', ya = Math.floor(-(vb.y + vb.h) / st) * st;
  for (var y = ya; y <= -vb.y; y += st) { var sy = (-y - vb.y) / u, M2 = Math.round(y) % major === 0; hy += 'M' + (M2 ? 8 : 16) + ' ' + sy.toFixed(1) + 'H26'; if (M2) ty += '<text x="2" y="' + (sy - 3).toFixed(1) + '">' + Math.round(y) + '</text>'; }
  RY.setAttribute('viewBox', '0 0 26 ' + H); RY.innerHTML = '<path d="' + hy + '"/>' + ty;
}
var pristine = {};
function sourceOpsPristine(){ var k = keyOf(sel); if (!pristine[k]) { var r = FV.recipes[sel.id]; if (r) { var cs = r.s.slice(); r.m.forEach(function(mi){ cs = cs.concat(transformOps(FV.marks[mi.m] || [], mi.t)); }); pristine[k] = cs; } else pristine[k] = (FV.glyphs[sel.id] || { c: [] }).c; } return pristine[k]; }

/* ---------- vì sao đặt dấu như vậy (*) — luật + nguồn lấy từ kho tài liệu rules.json ---------- */
var RULES = (function(){ var e = document.getElementById('fv-rules'); try { return e ? JSON.parse(e.textContent) : null; } catch (er) { return null; } })();
var CMB = { '\u0300': 'grave', '\u0301': 'acute', '\u0302': 'circ', '\u0303': 'tilde', '\u0306': 'breve', '\u0309': 'hook', '\u031B': 'horn', '\u0323': 'dot' };
var MK2M = { hook: ['hook'], hook_s: ['circ', 'hook'], horn: ['horn'], dot: ['dot'], tilde: ['tilde'], acute: ['acute'], grave: ['grave'], circ: ['circ'], breve: ['breve'] };
function featOf(){
  if (sel.kind === 'm') return { base: '', marks: MK2M[sel.id] || [], caps: false, ch: MK[sel.id][2] };
  var gi = FV.recipes[sel.id] || FV.glyphs[sel.id]; if (!gi) return null;
  var ch = String.fromCodePoint(gi.u), d = ch.normalize('NFD'), base = d[0], ms = [];
  Array.from(d.slice(1)).forEach(function(c){ if (CMB[c]) ms.push(CMB[c]); });
  if (ch === 'đ' || ch === 'Đ') base = ch;
  return { base: base, marks: ms, caps: base !== base.toLowerCase(), ch: ch };
}
function ruleHits(f){
  if (!RULES || !f) return [];
  return RULES.rules.filter(function(r){ var w = r.when || {};
    if (w.base && w.base !== 'any' && (!f.base || w.base.indexOf(f.base) < 0)) return false;
    if (w.caps != null && w.caps !== f.caps) return false;
    if ((w.marks || []).some(function(g){ return !g.split('|').some(function(m){ return f.marks.indexOf(m) >= 0; }); })) return false;
    if ((w.not || []).some(function(m){ return f.marks.indexOf(m) >= 0; })) return false;
    if (w.base === 'any' && !(w.marks || []).length) return true;
    return (w.marks || []).length > 0 || (w.base && w.base !== 'any');
  });
}
function esc(t){ return String(t).replace(/[&<>"]/g, function(c){ return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
var whyEl = null;
function renderWhy(){
  if (!whyEl) { whyEl = document.createElement('div'); whyEl.className = 'ed-why'; info.parentNode.insertBefore(whyEl, info.nextSibling); }
  var f = featOf(), hits = ruleHits(f);
  if (!RULES) { whyEl.innerHTML = ''; return; }
  var SRC = {}, nums = {}, GR = RULES.groups || {}, cnt = {};
  ['expert', 'other', 'own'].forEach(function(g){ RULES.sources.forEach(function(s0){ if ((s0.group || 'expert') === g) { cnt[g] = (cnt[g] || 0) + 1; SRC[s0.id] = s0; nums[s0.id] = ((GR[g] || {}).sym || '*') + cnt[g]; } }); });
  function grp(r){ var gs = r.src.map(function(x){ return (SRC[x] || {}).group || 'expert'; }); return gs.indexOf('expert') >= 0 ? 'expert' : gs.indexOf('other') >= 0 ? 'other' : 'own'; }
  var m = measureMarks(), used = [];
  var h = '<div class="ed-whyh">' + (f && f.ch ? esc(tr('whyQuestion', { glyph: f.ch })) : tr('whyTitle') + '?') + '</div>';
  if (m) h += '<div class="ed-stat">' + m + '</div>';
  var HD = { expert: tr('expert'), other: tr('other'), own: tr('own') };
  ['expert', 'other', 'own'].forEach(function(g){
    var rs = hits.filter(function(r){ return grp(r) === g; }); if (!rs.length) return;
    h += '<div class="ed-whyg ' + g + '">' + HD[g] + '</div><ol class="ed-whyl">' + rs.map(function(r){
      return '<li>' + esc(r.text) + ' ' + r.src.map(function(sid){ if (used.indexOf(sid) < 0) used.push(sid); return '<sup title="' + esc((SRC[sid] || {}).title || sid) + '">(' + nums[sid] + ')</sup>'; }).join('') + '</li>'; }).join('') + '</ol>';
  });
  if (!hits.length) h += '<p class="ed-whyn">' + tr('noVietnameseMark') + '</p>';
  var ORD = { expert: 0, other: 1, own: 2 };
  used.sort(function(a, b){ return ORD[(SRC[a] || {}).group || 'expert'] - ORD[(SRC[b] || {}).group || 'expert'] || parseInt(nums[a].slice(1)) - parseInt(nums[b].slice(1)); });
  if (used.length) h += '<ul class="ed-whys">' + used.map(function(sid){ var s0 = SRC[sid] || { title: sid };
    return '<li><sup>(' + nums[sid] + ')</sup> ' + (s0.url ? '<a href="' + esc(s0.url) + '" target="_blank" rel="noopener">' + esc(s0.title) + '</a>' : esc(s0.title)) + '</li>'; }).join('') + '</ul>';
  h += '<p class="ed-whyn">' + esc(tr('sourceUpdated', { date: RULES.updated || '' })) + '</p>';
  whyEl.innerHTML = h;
}
/* đo vị trí các dấu trên chữ đang mở: lệch trục + khe với phần bên dưới */
function measureMarks(){
  var e = cur(), T = layerT(), w = sel.kind === 'm' ? (repRecipe() || {}).w || 600 : e.w;
  var C = components(e.contours).map(function(c){ var p = ap(T, c.cx, c.cy), b0 = ap(T, c.bb[0], c.bb[1]), b1 = ap(T, c.bb[2], c.bb[3]); return { cx: p[0], cy: p[1], y0: Math.min(b0[1], b1[1]), y1: Math.max(b0[1], b1[1]) }; });
  if (sel.kind === 'm') { var r = repRecipe(); if (!r) return ''; }
  var top = FV.xh * 0.9, ups = C.filter(function(c){ return c.y0 > top; }).sort(function(a, b){ return a.y0 - b.y0; });
  if (!ups.length) return '';
  var body = C.filter(function(c){ return c.y0 <= top; }), bodyTop = body.length ? Math.max.apply(null, body.map(function(c){ return c.y1; })) : 0, prevTop = bodyTop, out = [];
  ups.forEach(function(c, i){ out.push(tr('measureMark', { index: i + 1, offset: (Math.round(c.cx - axisX(c.cy, w)) >= 0 ? '+' : '') + Math.round(c.cx - axisX(c.cy, w)), gap: Math.round(c.y0 - prevTop) })); prevTop = c.y1; });
  return tr('measurePrefix') + out.join(' · ');
}
function renderInfo(){
  var e = cur(), t = '';
  var label = sel.kind === 'm' ? markLabel(sel.id) + ' <span>· ' + tr('markScope') + '</span>' : esc(tr('glyphLabel', { glyph: String.fromCodePoint((FV.recipes[sel.id] || FV.glyphs[sel.id]).u), id: sel.id, width: e.w }));
  t += '<div class="ed-ttl">' + label + '</div>';
  var np = e.contours.reduce(function(s, c){ return s + c.nodes.length; }, 0);
  t += '<div class="ed-stat">' + tr('counts', { paths: e.contours.length, nodes: np, strokes: e.strokes.length }) + (e.touched ? ' · <b>' + tr('edited') + '</b>' : '') + '</div>';
  if (sel.nodes.length === 1) { var n = e.contours[sel.nodes[0][0]].nodes[sel.nodes[0][1]];
    t += '<div class="ed-xy"><label>x <input id="ed-x" type="number" step="1" value="' + Math.round(n.x) + '"></label><label>y <input id="ed-y" type="number" step="1" value="' + Math.round(n.y) + '"></label><span>' + (n.sm ? tr('smoothPoint') : tr('cornerPoint')) + '</span></div>'; }
  else if (tool === 'comp' && sel.comp >= 0) { var C = components(e.contours)[sel.comp], T0 = layerT();
    if (C) { var cw = ap(T0, C.cx, C.cy), bw0 = ap(T0, (C.bb[0] + C.bb[2]) / 2, (C.bb[1] + C.bb[3]) / 2), wv = sel.kind === 'm' ? (repRecipe() || {}).w || 600 : e.w;
      t += '<div class="ed-stat">' + tr('componentStats', { index: sel.comp + 1, total: components(e.contours).length, cx: Math.round(cw[0]), cy: Math.round(cw[1]), bx: Math.round(bw0[0]), by: Math.round(bw0[1]), offset: Math.round(cw[0] - axisX(cw[1], wv)) }) + '</div>'; } }
  else if (tool === 'comp') t += '<div class="ed-stat">' + tr('componentHelp') + '</div>';
  else if (sel.nodes.length > 1) t += '<div class="ed-stat">' + tr('selectedNodes', { count: sel.nodes.length }) + '</div>';
  if (OVER && (OVER.L || OVER.R)) t += '<div class="ed-warn">' + tr('overflow', { left: OVER.L || 0, right: OVER.R || 0 }) + '</div>';
  else if (OVER) t += '<div class="ed-okl">' + tr('withinAdvance') + '</div>';
  info.innerHTML = t;
  var xi = info.querySelector('#ed-x'), yi = info.querySelector('#ed-y');
  if (xi) [xi, yi].forEach(function(inp){ inp.addEventListener('change', function(){ var n = e.contours[sel.nodes[0][0]].nodes[sel.nodes[0][1]]; push(); moveNode(n, (+xi.value) - n.x, (+yi.value) - n.y); commit(); }); });
  if (document.activeElement !== noteEl) noteEl.value = e.note || '';
  renderWhy();
}
function moveNode(n, dx, dy){ n.x += dx; n.y += dy; if (n.ix != null) { n.ix += dx; n.iy += dy; } if (n.ox != null) { n.ox += dx; n.oy += dy; } }

/* ---------- glyph list ---------- */
function chip(kind, id, ch, lbl){
  var k = (kind === 'm' ? 'm-' : 'g-') + id, e = ED[k];
  return '<button type="button" class="ed-chip' + (kind === 'm' ? ' mk' : '') + (sel.kind === kind && sel.id === id ? ' on' : '') + (e && e.touched ? ' dirty' : '') + (kind === 'g' && BOARDS.indexOf(id) >= 0 ? ' inb' : '') + '" data-k="' + kind + '" data-id="' + id + '" title="' + (lbl || id) + '"><b>' + ch + '</b>' + (lbl ? '<small>' + lbl + '</small>' : '') + '</button>';
}
var listTab = 'vn';   // thứ tự tab: 134 chữ Việt (mặc định) → Dấu → Chữ gốc
function renderList(){
  var q = (root.querySelector('#ed-find').value || '').trim(), h = '';
  if (q) {
    Array.from(q).forEach(function(c){ var n = U2N[c.codePointAt(0)]; if (n) h += chip('g', n, c); });
    if (!h) h = '<p class="mini">' + tr('noCharacter') + '</p>';
  } else if (listTab === 'marks') h = MARKS.map(function(m){ return chip('m', m[0], m[2], markLabel(m[0])); }).join('');
  else if (listTab === 'vn') h = Array.from(VN + VNU).map(function(c){ var n = U2N[c.codePointAt(0)]; return n ? chip('g', n, c) : ''; }).join('');
  else h = Array.from('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?').map(function(c){ var n = U2N[c.codePointAt(0)]; return n ? chip('g', n, c) : ''; }).join('');
  if (listEl.__h !== h) { listEl.innerHTML = h; listEl.__h = h; }
  root.querySelectorAll('.ed-tabs button').forEach(function(b){ b.setAttribute('aria-pressed', String(b.dataset.tab === listTab && !q)); });
}
root.querySelector('.ed-tabs').addEventListener('click', function(ev){ var b = ev.target.closest('button'); if (!b) return; listTab = b.dataset.tab; root.querySelector('#ed-find').value = ''; renderList(); });
root.querySelector('#ed-find').addEventListener('input', renderList);
listEl.addEventListener('click', function(ev){ var b = ev.target.closest('.ed-chip'); if (!b) return; choose(b.dataset.k, b.dataset.id, ev.shiftKey || ADD); });

/* ---------- bản vẽ nhiều chữ (kiểu artboard Illustrator) ----------
   Chữ đang sửa luôn ở gốc toạ độ; các chữ khác xếp cạnh theo thứ tự, cách nhau BGAP. Bấm vào chữ khác để sửa chữ đó. */
var BOARDS = sel.kind === 'g' ? [sel.id] : [], BA = 0, ADD = false, BMAX = 8, BGAP = Math.round((FV.upm || 1000) * 0.22), CLIP = null;
function boardW(id){ var e = ED['g-' + id]; return e ? e.w : ((FV.recipes[id] || FV.glyphs[id] || {}).w || 500); }
function boardX(){ var X = [], x = 0; BOARDS.forEach(function(id){ X.push(x); x += boardW(id) + BGAP; }); return X; }
function chOf(id){ var gi = FV.recipes[id] || FV.glyphs[id]; return gi ? String.fromCodePoint(gi.u) : id; }
function multi(){ return sel.kind === 'g' && BOARDS.length > 1; }
function activate(i, how){
  finishPen(); var fromG = sel.kind === 'g', X = boardX(), d = X[i] - X[BA];
  BA = i; sel = { kind: 'g', id: BOARDS[i], nodes: [], stroke: -1, comp: -1 }; getEd(sel);
  if (how === 'fit' || !fromG || !vb) fitAll(); else { vb.x -= d; applyVB(); }   // giữ nguyên chỗ nhìn, chỉ đổi chữ đang sửa
}
function choose(kind, id, add){
  if (kind === 'm') { finishPen(); sel = { kind: 'm', id: id, nodes: [], stroke: -1, comp: -1 }; getEd(sel); if (add) say2(tr('markOnItsOwn')); fit(); return; }
  var i = BOARDS.indexOf(id);
  if (i >= 0) return activate(i);
  if (add && BOARDS.length >= BMAX) { say2(tr('boardLimit', { count: BMAX })); return; }
  if (add && BOARDS.length) { BOARDS.push(id); return activate(BOARDS.length - 1, 'fit'); }
  var fromG = sel.kind === 'g';
  if (!BOARDS.length) { BOARDS = [id]; BA = 0; } else BOARDS[BA] = id;     // bấm thường = thay chữ đang sửa
  finishPen(); sel = { kind: 'g', id: id, nodes: [], stroke: -1, comp: -1 }; getEd(sel);
  if (BOARDS.length === 1 || !fromG) fitAll(); else render();
}
/* mở MỘT chữ từ nơi khác trên trang (bấm chữ ở khung xem Chỉnh dấu): bản vẽ chỉ còn chữ đó, vừa khung */
window.__edOpen = function(ch){ var n = U2N[(ch || '').codePointAt(0)]; if (!n) return false;
  finishPen(); BOARDS = [n]; BA = 0; sel = { kind: 'g', id: n, nodes: [], stroke: -1, comp: -1 }; getEd(sel); fitAll(); return true; };
function removeBoard(i){
  if (BOARDS.length < 2) return;
  BOARDS.splice(i, 1);
  if (i < BA || BA >= BOARDS.length) BA = Math.max(0, BA - 1);
  if (sel.kind === 'g') { finishPen(); sel = { kind: 'g', id: BOARDS[BA], nodes: [], stroke: -1, comp: -1 }; getEd(sel); fitAll(); } else render();
}
function goKey(k){   // hoàn tác / làm lại trên chữ khác → mở đúng chữ đó trước
  if (k === keyOf(sel)) return;
  var kind = k[0], id = k.slice(2);
  if (kind === 'g' && BOARDS.indexOf(id) >= 0) activate(BOARDS.indexOf(id)); else choose(kind, id);
}
function fitAll(){
  if (!multi()) return fit();
  var X = boardX(), x0 = -X[BA], x1 = X[X.length - 1] + boardW(BOARDS[BOARDS.length - 1]) - X[BA];
  var top = Math.max(FV.asc, FV.cap + 380) + 60, bot = Math.min(FV.desc, -220), h = top - bot, a = svgAspect(), ww = Math.max(x1 - x0 + 360, h * a);
  vb = { x: (x0 + x1) / 2 - ww / 2, w: ww, h: ww / a, y: 0 }; vb.y = -top - (vb.h - h) / 2; applyVB();
}
function drawBoards(u){
  var g = L.boards; clear(g); if (!multi()) return;
  var X = boardX(), y0 = Math.min(FV.desc, -220) + 40, y1 = Math.max(FV.asc, FV.cap + 300);
  BOARDS.forEach(function(id, i){
    var ox = X[i] - X[BA], w = boardW(id), on = i === BA;
    var t = el('text', { x: ox, y: -(y1 + 14 * u), class: 'ed-blab' + (on ? ' on' : ''), transform: 'scale(1,-1)', 'font-size': 12.5 * u });
    var lb = (i + 1) + ' · “' + chOf(id) + '” · ' + tr('boardWidth', { width: Math.round(w) }) + (on ? ' · ' + tr('editing') : '');
    if (lb.length * 7.6 > (w + BGAP * 0.8) / u) lb = (i + 1) + ' “' + chOf(id) + '”';   // khung hẹp (điện thoại) → nhãn ngắn
    t.textContent = lb; g.appendChild(t);
    if (on) { g.appendChild(el('rect', { x: 0, y: y0, width: w, height: y1 - y0, class: 'ed-bframe on', 'vector-effect': 'non-scaling-stroke' })); return; }
    var o = glyphOutline(id), gg = el('g', { transform: 'translate(' + ox + ' 0)', 'data-board': i });
    if (o) { gg.appendChild(el('path', { d: o.d, class: 'ed-bfill' })); o.s.forEach(function(st){ gg.appendChild(el('path', { d: 'M' + st.pts.map(function(p){ return r1(p[0]) + ' ' + r1(p[1]); }).join(' L'), class: 'ed-bbrush', 'stroke-width': st.w })); }); }
    if (OPT.axis) { var ya = FV.desc - 60, yb = FV.asc + 200; gg.appendChild(el('line', { x1: axisX(ya, w, id), y1: ya, x2: axisX(yb, w, id), y2: yb, class: 'ed-bax', 'vector-effect': 'non-scaling-stroke' })); }
    gg.appendChild(el('rect', { x: 0, y: y0, width: w, height: y1 - y0, class: 'ed-bframe', 'vector-effect': 'non-scaling-stroke' }));
    var tt = el('title', {}); tt.textContent = tr('editGlyph', { glyph: chOf(id) }); gg.appendChild(tt);
    g.appendChild(gg);
  });
}
/* thanh "Bản vẽ" trên khung: chữ đang có, nút thêm chữ, chép / dán dấu */
var strip = root.querySelector('.ed-boards');
if (!strip) { strip = document.createElement('div'); strip.className = 'ed-boards'; strip.setAttribute('role', 'group'); strip.setAttribute('aria-label', tr('boardAria')); var mn = root.querySelector('.ed-main'); mn.insertBefore(strip, mn.firstChild); }
strip.innerHTML = '<span class="ed-bl">' + tr('board') + '</span><span class="ed-bchips"></span>'
  + '<button type="button" class="ed-bbtn" data-b="add" aria-pressed="false" title="' + tr('addGlyphTitle') + '">' + tr('addChar') + '</button>'
  + '<span class="ed-bsep" aria-hidden="true"></span>'
  + '<button type="button" class="ed-bbtn" data-b="copy" title="' + tr('copyTitle') + '">' + tr('copy') + '</button>'
  + '<button type="button" class="ed-bbtn" data-b="paste" title="' + tr('pasteTitle') + '">' + tr('paste') + '</button>'
  + '<button type="button" class="ed-bbtn" data-b="swap" title="' + tr('replaceTitle') + '">' + tr('replace') + '</button>'
  + '<span class="ed-bmsg mini" aria-live="polite"></span>';
var bchips = strip.querySelector('.ed-bchips'), bmsg = strip.querySelector('.ed-bmsg');
function say2(t){ bmsg.textContent = t; }
function renderStrip(){
  var h = BOARDS.map(function(id, i){ var on = sel.kind === 'g' && i === BA;
    return '<span class="ed-bc' + (on ? ' on' : '') + '"><button type="button" class="bch" data-bi="' + i + '" aria-pressed="' + on + '" title="' + tr('editGlyph', { glyph: esc(chOf(id)) }) + '">' + esc(chOf(id)) + '</button>'
      + (BOARDS.length > 1 ? '<button type="button" class="bx" data-bx="' + i + '" aria-label="' + tr('removeGlyph', { glyph: esc(chOf(id)) }) + '" title="' + tr('removeGlyph', { glyph: esc(chOf(id)) }) + '">×</button>' : '') + '</span>'; }).join('');
  if (!h) h = '<span class="mini">' + tr('chooseGlyph') + '</span>';
  if (bchips.__h !== h) { var fa = document.activeElement, fk = fa && bchips.contains(fa) ? (fa.dataset.bi != null ? '[data-bi="' + fa.dataset.bi + '"]' : '.bch') : null;
    bchips.innerHTML = h; bchips.__h = h; if (fk) { var nf = bchips.querySelector(fk) || bchips.querySelector('.bch'); if (nf) nf.focus(); } }
  strip.querySelector('[data-b="add"]').setAttribute('aria-pressed', String(ADD));
  var hasSel = sel.nodes.length > 0 || (tool === 'comp' && sel.comp >= 0);
  strip.querySelector('[data-b="copy"]').disabled = !hasSel;
  strip.querySelector('[data-b="paste"]').disabled = !CLIP;
  strip.querySelector('[data-b="swap"]').disabled = !CLIP || !hasSel;
}
strip.addEventListener('click', function(ev){
  var b = ev.target.closest('button'); if (!b) return;
  if (b.dataset.bi != null) return activate(+b.dataset.bi);
  if (b.dataset.bx != null) return removeBoard(+b.dataset.bx);
  if (b.dataset.b === 'add') { ADD = !ADD; say2(ADD ? tr('addingGlyph') : ''); renderStrip(); }
  else if (b.dataset.b === 'copy') copySel();
  else if (b.dataset.b === 'paste') pasteClip('axis');
  else if (b.dataset.b === 'swap') pasteClip('swap');
});
/* chép / dán: lưu theo toạ độ thế giới của chữ đang sửa (đã áp layerT nếu đang sửa dấu) */
function curGid(){ return sel.kind === 'm' ? MK[sel.id][3] : sel.id; }
function curW(){ return sel.kind === 'm' ? (repRecipe() || {}).w || 600 : cur().w; }
function topOf(gid){ var c = chOf(gid); return c !== c.toLowerCase() ? FV.cap : FV.xh; }
function mapC(c, t){ return { closed: c.closed, nodes: c.nodes.map(function(n){ var o = { sm: n.sm }, q = ap(t, n.x, n.y); o.x = r1(q[0]); o.y = r1(q[1]);
  if (n.ix != null) { q = ap(t, n.ix, n.iy); o.ix = r1(q[0]); o.iy = r1(q[1]); } if (n.ox != null) { q = ap(t, n.ox, n.oy); o.ox = r1(q[0]); o.oy = r1(q[1]); } return o; }) }; }
function selContours(){
  var e = cur(), ids = [];
  if (tool === 'comp' && sel.comp >= 0) { var C = components(e.contours)[sel.comp]; if (C) ids = C.ci.slice(); }
  else sel.nodes.forEach(function(x){ if (ids.indexOf(x[0]) < 0) ids.push(x[0]); });
  return ids.sort(function(a, b){ return a - b; });
}
function bbOfCs(cs){ var P = []; cs.forEach(function(c){ P = P.concat(flatC(c)); }); return bboxOf(P); }
function copySel(){
  var ids = selContours(), e = cur(), T = layerT();
  if (!ids.length) { say2(tr('choosePart')); return; }
  var cs = ids.map(function(ci){ return mapC(e.contours[ci], T); }), bb = bbOfCs(cs), cy = (bb[1] + bb[3]) / 2, cx = (bb[0] + bb[2]) / 2, gid = curGid();
  CLIP = { cs: cs, bb: bb, cx: cx, cy: cy, dAx: cx - axisX(cy, curW()), top: topOf(gid), above: bb[1] > topOf(gid) * 0.85, from: chOf(gid) };
  say2(ids.length > 1 ? tr('copied', { count: ids.length, from: CLIP.from }) : tr('copiedOne', { from: CLIP.from })); renderStrip();
}
function pasteClip(mode){
  if (!CLIP) { say2(tr('nothingCopied')); return; }
  var e = cur(), T = layerT(), it = inv(T), dx = 0, dy = 0, gid = curGid(), old = mode === 'swap' ? selContours() : [];
  if (mode === 'swap' && !old.length) { say2(tr('chooseReplace')); return; }
  if (old.length) { var ob = bbOfCs(old.map(function(ci){ return mapC(e.contours[ci], T); })); dx = (ob[0] + ob[2]) / 2 - CLIP.cx; dy = ob[1] - CLIP.bb[1]; }   // vào đúng chỗ phần cũ: giữa theo x, đáy theo y
  else if (mode !== 'raw') { var ty = CLIP.cy + (CLIP.above ? topOf(gid) - CLIP.top : 0); dy = ty - CLIP.cy; dx = axisX(ty, curW()) + CLIP.dAx - CLIP.cx; }   // giữ lệch trục + khoảng cách tới đỉnh (thường ↔ hoa)
  push();
  old.slice().sort(function(a, b){ return b - a; }).forEach(function(ci){ e.contours.splice(ci, 1); });
  var n0 = e.contours.length;
  CLIP.cs.forEach(function(c){ e.contours.push(mapC(c, [it[0], it[1], it[2], it[3], it[0] * dx + it[2] * dy + it[4], it[1] * dx + it[3] * dy + it[5]])); });
  sel.nodes = []; for (var ci = n0; ci < e.contours.length; ci++) e.contours[ci].nodes.forEach(function(_, ni){ sel.nodes.push([ci, ni]); });
  sel.stroke = -1;
  if (tool === 'comp') { sel.comp = -1; components(e.contours).forEach(function(c, i){ if (c.ci.indexOf(n0) >= 0) sel.comp = i; }); }
  say2(old.length ? tr('replaced', { from: CLIP.from, to: chOf(gid) }) : tr('pasted', { from: CLIP.from, to: chOf(gid) }));
  commit();
}


/* ---------- live preview ---------- */
function glyphOutline(name){
  var ge = ED['g-' + name];
  if (ge && ge.touched) return { w: ge.w, d: opsToD(nodesToOps(ge.contours)), s: ge.strokes, T: null };
  var r = FV.recipes[name], H = window.__h11;
  // B → C: đã kéo thanh ở B (râu, vị trí dấu, cỡ dấu nặng) thì “Xem trong chữ” lấy nét từ B — trừ khi chữ / dấu của chữ đó đã vẽ tay ở C
  if (H && H.changed && H.changed() && !(r && r.m.some(function(mi){ var me = ED['m-' + mi.m]; return me && me.touched; }))) {
    var gi = r || FV.glyphs[name], ch = gi && String.fromCodePoint(gi.u);
    if (ch && H.has(ch)) { var bg = H.glyph(ch, true); if (bg && bg.svg) return { w: bg.w, raw: bg.svg, s: [] }; }
  }
  if (r) {
    var d = opsToD(r.s), strokes = [];
    r.m.forEach(function(mi){ d += opsToD(markOps(mi.m), mi.t); markStrokes(mi.m).forEach(function(st){ strokes.push({ w: st.w * Math.hypot(mi.t[0], mi.t[1]), pts: st.pts.map(function(p){ return ap(mi.t, p[0], p[1]); }) }); }); });
    return { w: r.w, d: d, s: strokes };
  }
  var g = FV.glyphs[name]; return g ? { w: g.w, d: opsToD(g.c), s: [] } : null;
}
/* cỡ xem trước: 0 = vừa khung, còn lại = px thật (như cỡ chữ trong app); kern tắt = giả lập Word / Excel */
var PV = { px: 0, kern: true }, PVS = [0, 10, 12, 16, 24, 36, 48, 72, 120, 200];
try { var _pv = JSON.parse(localStorage.getItem('fv-pv') || 'null'); if (_pv) { PV.px = +_pv.px || 0; PV.kern = _pv.kern !== false; } } catch (e) {}
(function(){
  var hd = root.querySelector('.ed-pvh'); if (!hd || hd.querySelector('.ed-zoom')) return;
  var z = document.createElement('div'); z.className = 'ed-zoom'; z.setAttribute('role', 'group'); z.setAttribute('aria-label', tr('previewSize'));
  z.innerHTML = '<button type="button" data-z="k" aria-pressed="true" hidden>kern</button>';   // bỏ nút kern (người dùng 27/10) — luôn xem có kern
  z.hidden = true; PV.kern = true;
  hd.appendChild(z);

  var sc = document.createElement('div'); sc.className = 'ed-pvsc'; pvSvg.parentNode.insertBefore(sc, pvSvg); sc.appendChild(pvSvg);
  function sync(){ z.querySelector('[data-z="k"]').setAttribute('aria-pressed', String(PV.kern)); try { localStorage.setItem('fv-pv', JSON.stringify(PV)); } catch (e) {} renderPreview(); }
  function zc(ev){ var b = ev.target.closest('button'); if (!b) return; var i = PVS.indexOf(PV.px);
    if (PV.px === 0 && b.dataset.z !== 'k') PV.px = b.dataset.z === '+' ? 48 : 16;   // đang “vừa khung”: + ra cỡ lớn, − ra cỡ nhỏ
    else if (b.dataset.z === '-') PV.px = PVS[Math.max(1, i - 1)]; else if (b.dataset.z === '+') PV.px = PVS[Math.min(PVS.length - 1, i + 1)]; else PV.kern = !PV.kern; sync(); }
  z.addEventListener('click', zc);
  /* phóng bằng chụm 2 ngón / lăn chuột (trang gọi qua window.__edPvZoom): px thật; đang “vừa khung” thì quy ra px đang hiện */
  window.__edPvZoom = { el: sc, get: function(){ if (PV.px) return PV.px; var vbw = (pvSvg.viewBox && pvSvg.viewBox.baseVal && pvSvg.viewBox.baseVal.width) || 1; return pvSvg.getBoundingClientRect().width / vbw * FV.upm; },
    set: function(px){ PV.px = Math.round(px); sync(); } };
  z.querySelector('[data-z="k"]').setAttribute('aria-pressed', String(PV.kern));
})();
function renderPreview(){
  var txt = pvIn.value || '', x = 0, lines = txt.split('\n'), h = '', y = 0, LH = FV.upm * 1.25, maxw = 0;
  var KN = PV.kern ? (FV.kern || {}) : {};
  lines.forEach(function(line){
    x = 0; var prev = null;
    Array.from(line).forEach(function(c){
      if (c === ' ') { x += (FV.glyphs[U2N[32]] || { w: 250 }).w; prev = null; return; }
      var n = U2N[c.codePointAt(0)], o = n && glyphOutline(n); if (!o) return;
      if (prev && KN[prev] && KN[prev][n]) x += KN[prev][n]; prev = n;
      h += '<g transform="translate(' + x + ' ' + (-y) + ')">' + (o.raw != null ? o.raw : '<path d="' + o.d + '"/>') + o.s.map(function(st){ return '<path class="pvb" stroke-width="' + st.w + '" d="M' + st.pts.map(function(p){ return r1(p[0]) + ' ' + r1(p[1]); }).join(' L') + '"/>'; }).join('') + '</g>';
      x += o.w;
    });
    maxw = Math.max(maxw, x); y += LH;
  });
  var top = FV.asc + 280, H = y - LH + top - FV.desc + 60;
  pvSvg.setAttribute('viewBox', '-40 ' + (-top) + ' ' + (maxw + 80) + ' ' + H);
  pvSvg.style.aspectRatio = (maxw + 80) + ' / ' + H;
  if (PV.px) { var k = PV.px / FV.upm; pvSvg.style.width = ((maxw + 80) * k) + 'px'; pvSvg.style.maxHeight = 'none'; pvSvg.style.height = (H * k) + 'px'; }
  else { pvSvg.style.width = ''; pvSvg.style.maxHeight = ''; pvSvg.style.height = ''; }
  pvSvg.innerHTML = '<g transform="scale(1,-1)">' + h + '</g>';
}
pvIn.addEventListener('input', renderPreview);
/* đổi VER ở A → bàn vẽ nạp nét của VER đó (dữ liệu từng VER = phần khác bản gốc); nét đã vẽ tay giữ nguyên */
(function(){ var VD = {}; try { VD = JSON.parse((document.getElementById('fv-verdata') || {}).textContent || '{}'); } catch (e) {}   // khối dữ liệu đứng trước script bàn vẽ
  var BASE = { glyphs: Object.assign({}, FV.glyphs), recipes: Object.assign({}, FV.recipes), marks: Object.assign({}, FV.marks) };
  function useVer(tag){ var d = VD[tag]; if (tag !== VD.__base && !d) return;
    ['glyphs', 'recipes', 'marks'].forEach(function(k){ FV[k] = Object.assign({}, BASE[k]); var o = d && d.ed && d.ed[k] || {}; Object.keys(o).forEach(function(n){ if (o[n] === null) delete FV[k][n]; else FV[k][n] = o[n]; }); });
    pristine = {}; Object.keys(ED).forEach(function(k){ if (!ED[k].touched && !(ED[k].note || '').trim()) delete ED[k]; });
    if (vb) render(); else renderPreview(); }
  window.addEventListener('fv-ver', function(e){ useVer(e.detail.tag); });
  if (window.__FV_VER) useVer(window.__FV_VER); })();
var _bT = null; window.addEventListener('fv-b-change', function(){ clearTimeout(_bT); _bT = setTimeout(renderPreview, 60); });   // B đổi → C vẽ lại xem trước

/* ---------- tools ---------- */
var bar = root.querySelector('.ed-bar');
/* nhóm bút vector kiểu Illustrator: 1 nút (icon = công cụ bút đang dùng, tam giác góc) → bấm mở danh sách: bút · + · − · đổi điểm góc */
var lastPen = 'pen';
var pgb = bar.querySelector('.ed-pgb'), pgf = bar.querySelector('.ed-pgf');
function penMenu(open){ if (!pgf) return; pgf.hidden = !open; pgb.setAttribute('aria-expanded', String(open)); if (open) { var on = pgf.querySelector('[aria-pressed="true"]') || pgf.querySelector('.ed-pgi'); if (on) on.focus(); } }
function setTool(t){ finishPen(); tool = t; if (t !== 'comp') sel.comp = -1; bar.querySelectorAll('[data-tool]').forEach(function(b){ b.setAttribute('aria-pressed', String(b.dataset.tool === t)); }); svg.dataset.tool = t; root.querySelector('.ed-brushrow').hidden = t !== 'brush';
  if (pgb) { var isPen = PENS.indexOf(t) >= 0; pgb.setAttribute('aria-pressed', String(isPen)); if (isPen) { lastPen = t; var it = pgf.querySelector('[data-tool="' + t + '"]'); pgb.querySelector('.ed-pgi-ic').innerHTML = it.querySelector('svg').outerHTML; pgb.title = tr('penGroupOpen', { tool: it.querySelector('span').textContent }); } }
  render(); }
document.addEventListener('pointerdown', function(ev){ if (pgf && !pgf.hidden && !ev.target.closest('.ed-pg')) penMenu(false); });
document.addEventListener('keydown', function(ev){ if (pgf && !pgf.hidden && ev.key === 'Escape') { penMenu(false); pgb.focus(); } });
bar.addEventListener('click', function(ev){
  var b = ev.target.closest('button'); if (!b) return;
  if (b === pgb) { if (PENS.indexOf(tool) < 0) setTool(lastPen); penMenu(pgf.hidden); return; }
  if (b.dataset.tool) { penMenu(false); return setTool(b.dataset.tool); }
  var a = b.dataset.ed;
  if (a === 'undo') undo(); else if (a === 'redo') redo();
  else if (a === 'smooth') toggleSmooth();
  else if (a === 'del') delSel();
  else if (a === 'zin') zoom(0.8); else if (a === 'zout') zoom(1.25); else if (a === 'fit') fitAll();
  else if (a === 'reset') { var c = root.querySelector('.ed-resetc'); c.querySelector('#ed-rcd').textContent = tr('resetGlyph', { glyph: label(sel) }); c.hidden = false; c.querySelector('[data-a="yes"]').focus(); }
});
root.querySelector('.ed-resetc').addEventListener('keydown', function(ev){ if (ev.key === 'Escape') { ev.stopPropagation(); this.hidden = true; } });
root.querySelector('.ed-resetc').addEventListener('pointerdown', function(ev){ ev.stopPropagation(); });   // popup giữa khung: không vẽ xuyên xuống canvas
root.querySelector('.ed-resetc').addEventListener('click', function(ev){
  if (ev.target === this) { this.hidden = true; return; }   // bấm ra ngoài hộp = Thôi
  var b = ev.target.closest('button'); if (!b) return; this.hidden = true;
  if (b.dataset.a === 'yes') { var e = cur(); push(); e.contours = opsToNodes(sel.kind === 'm' ? FV.marks[sel.id] : sourceOpsPristine()); e.strokes = []; sel.nodes = []; e.touched = false; e.reset = true; e.pendingSave = true; e.saveGen = (e.saveGen || 0) + 1; if (window.__FV_BRIDGE && window.__FV_BRIDGE.dirty) window.__FV_BRIDGE.dirty(keyOf(sel)); render(); schedSave(true); }
});
root.querySelectorAll('.ed-opts [data-opt]').forEach(function(b){
  b.setAttribute('aria-pressed', String(!!OPT[b.dataset.opt]));
  b.addEventListener('click', function(){
    OPT[b.dataset.opt] = !OPT[b.dataset.opt];
    b.setAttribute('aria-pressed', String(OPT[b.dataset.opt]));      // cùng handler ghi giá trị
    try { localStorage.setItem('fv-ed-opt', JSON.stringify(OPT)); } catch (er) {}
    stage.classList.toggle('no-rulers', !OPT.rulers);
    if (b.dataset.opt === 'rulers') { var a = svgAspect(); vb.h = vb.w / a; applyVB(); } else render();
  });
});
stage.classList.toggle('no-rulers', !OPT.rulers);
brushW.addEventListener('input', function(){ brushOut.textContent = brushW.value; });
noteEl.addEventListener('input', function(){ var e = cur(); e.note = noteEl.value; e.noteTouched = true; e.pendingSave = true; e.saveGen = (e.saveGen || 0) + 1; if (window.__FV_BRIDGE && window.__FV_BRIDGE.dirty) window.__FV_BRIDGE.dirty(keyOf(sel)); schedSave(); });
function zoom(f, cx, cy){ cx = cx == null ? vb.x + vb.w / 2 : cx; cy = cy == null ? vb.y + vb.h / 2 : cy; vb = { x: cx - (cx - vb.x) * f, y: cy - (cy - vb.y) * f, w: vb.w * f, h: vb.h * f }; applyVB(); }
svg.addEventListener('wheel', function(ev){ ev.preventDefault(); var w = toWorld(ev); zoom(ev.deltaY > 0 ? 1.12 : 0.89, w[0], -w[1]); }, { passive: false });

function hit(ev){ var t = document.elementFromPoint(ev.clientX, ev.clientY); return t && svg.contains(t) ? t : null; }
function toggleSmooth(){
  var e = cur(); if (!sel.nodes.length) return; push();
  sel.nodes.forEach(function(x){
    var c = e.contours[x[0]], n = c.nodes[x[1]], N = c.nodes.length;
    if (n.sm) { n.sm = false; return; }
    var p = c.nodes[(x[1] - 1 + N) % N], q = c.nodes[(x[1] + 1) % N];
    var dx = q.x - p.x, dy = q.y - p.y, L0 = Math.hypot(dx, dy) || 1; dx /= L0; dy /= L0;
    var li = n.ix != null ? Math.hypot(n.ix - n.x, n.iy - n.y) : Math.hypot(n.x - p.x, n.y - p.y) / 3;
    var lo = n.ox != null ? Math.hypot(n.ox - n.x, n.oy - n.y) : Math.hypot(q.x - n.x, q.y - n.y) / 3;
    n.ix = n.x - dx * li; n.iy = n.y - dy * li; n.ox = n.x + dx * lo; n.oy = n.y + dy * lo; n.sm = true;
  });
  commit();
}
function delSel(){
  var e = cur();
  if (sel.stroke >= 0) { push(); e.strokes.splice(sel.stroke, 1); sel.stroke = -1; commit(); return; }
  if (!sel.nodes.length) return; push();
  var by = {}; sel.nodes.forEach(function(x){ (by[x[0]] = by[x[0]] || []).push(x[1]); });
  Object.keys(by).sort(function(a, b){ return b - a; }).forEach(function(ci){
    var c = e.contours[ci]; by[ci].sort(function(a, b){ return b - a; }).forEach(function(ni){ c.nodes.splice(ni, 1); });
    if (c.nodes.length < 2) e.contours.splice(ci, 1);
  });
  sel.nodes = []; commit();
}
/* thêm / xoá điểm neo kiểu Illustrator: thêm = cắt đoạn cong tại t (de Casteljau), hình không đổi;
   xoá = bỏ điểm rồi khớp lại MỘT đoạn cong qua 2 điểm bên cạnh (giữ hướng tay nắm, bình phương tối thiểu — Schneider) */
function segPts(c, i){ var N = c.nodes, a = N[i], b = N[(i + 1) % N.length];
  return [[a.x, a.y], [a.ox != null ? a.ox : a.x, a.ox != null ? a.oy : a.y], [b.ix != null ? b.ix : b.x, b.ix != null ? b.iy : b.y], [b.x, b.y]]; }
function bzAt(P, t){ var u = 1 - t; return [u*u*u*P[0][0] + 3*u*u*t*P[1][0] + 3*u*t*t*P[2][0] + t*t*t*P[3][0], u*u*u*P[0][1] + 3*u*u*t*P[1][1] + 3*u*t*t*P[2][1] + t*t*t*P[3][1]]; }
function isLine(c, i){ var N = c.nodes, a = N[i], b = N[(i + 1) % N.length]; return a.ox == null && b.ix == null; }
function nearestSeg(e, p, tol){ var best = null;
  e.contours.forEach(function(c, ci){ var n = c.nodes.length, last = c.closed ? n : n - 1;
    for (var si = 0; si < last; si++){ var P = segPts(c, si);
      for (var k = 1; k < 64; k++){ var t = k / 64, q = bzAt(P, t), d = Math.hypot(q[0] - p[0], q[1] - p[1]);
        if (d < tol && (!best || d < best.d)) best = { ci: ci, si: si, t: t, d: d }; } } });
  if (best){ var P2 = segPts(e.contours[best.ci], best.si), lo = Math.max(0, best.t - 1 / 64), hi = Math.min(1, best.t + 1 / 64);   // tinh chỉnh t
    for (var it = 0; it < 20; it++){ var m1 = lo + (hi - lo) / 3, m2 = hi - (hi - lo) / 3, a1 = bzAt(P2, m1), a2 = bzAt(P2, m2);
      if (Math.hypot(a1[0] - p[0], a1[1] - p[1]) < Math.hypot(a2[0] - p[0], a2[1] - p[1])) hi = m2; else lo = m1; }
    best.t = (lo + hi) / 2; }
  return best; }
function addAnchor(e, hitSeg){ var c = e.contours[hitSeg.ci], si = hitSeg.si, N = c.nodes, a = N[si], b = N[(si + 1) % N.length], t = hitSeg.t;
  if (isLine(c, si)){ var nn = { x: r1(a.x + (b.x - a.x) * t), y: r1(a.y + (b.y - a.y) * t), sm: false }; N.splice(si + 1, 0, nn); return si + 1; }
  var P = segPts(c, si); function L(p, q){ return [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t]; }
  var p01 = L(P[0], P[1]), p12 = L(P[1], P[2]), p23 = L(P[2], P[3]), p012 = L(p01, p12), p123 = L(p12, p23), m = L(p012, p123);
  a.ox = r1(p01[0]); a.oy = r1(p01[1]); b.ix = r1(p23[0]); b.iy = r1(p23[1]);
  var n = { x: r1(m[0]), y: r1(m[1]), ix: r1(p012[0]), iy: r1(p012[1]), ox: r1(p123[0]), oy: r1(p123[1]), sm: true };
  N.splice(si + 1, 0, n); return si + 1; }
function delAnchor(e, ci, ni){ var c = e.contours[ci], N = c.nodes, n = N.length;
  if (n <= 2){ e.contours.splice(ci, 1); return; }
  var open = !c.closed && (ni === 0 || ni === n - 1);
  if (open){ N.splice(ni, 1); if (ni === 0) { N[0].ix = N[0].iy = null; } else { N[N.length - 1].ox = N[N.length - 1].oy = null; } return; }
  var ia = (ni - 1 + n) % n, ib = (ni + 1) % n, a = N[ia], b = N[ib], s1 = segPts(c, ia), s2 = segPts(c, ni);
  if (isLine(c, ia) && isLine(c, ni)){ N.splice(ni, 1); return; }
  var pts = [], k; for (k = 0; k <= 24; k++) pts.push(bzAt(s1, k / 24)); for (k = 1; k <= 24; k++) pts.push(bzAt(s2, k / 24));
  var u = [0]; for (k = 1; k < pts.length; k++) u.push(u[k - 1] + Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]));
  var tot = u[u.length - 1] || 1; u = u.map(function(v){ return v / tot; });
  function nrm(dx, dy){ var l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l]; }
  var t1 = a.ox != null ? nrm(a.ox - a.x, a.oy - a.y) : nrm(s1[2][0] - a.x, s1[2][1] - a.y), t2 = b.ix != null ? nrm(b.ix - b.x, b.iy - b.y) : nrm(s2[1][0] - b.x, s2[1][1] - b.y);
  var C00 = 0, C01 = 0, C11 = 0, X0 = 0, X1 = 0, P0 = [a.x, a.y], P3 = [b.x, b.y];
  pts.forEach(function(q, i){ var t = u[i], v = 1 - t, b0 = v*v*v, b1 = 3*v*v*t, b2 = 3*v*t*t, b3 = t*t*t, A1 = [t1[0] * b1, t1[1] * b1], A2 = [t2[0] * b2, t2[1] * b2];
    C00 += A1[0]*A1[0] + A1[1]*A1[1]; C01 += A1[0]*A2[0] + A1[1]*A2[1]; C11 += A2[0]*A2[0] + A2[1]*A2[1];
    var tx = q[0] - (P0[0] * (b0 + b1) + P3[0] * (b2 + b3)), ty = q[1] - (P0[1] * (b0 + b1) + P3[1] * (b2 + b3));
    X0 += A1[0]*tx + A1[1]*ty; X1 += A2[0]*tx + A2[1]*ty; });
  var det = C00 * C11 - C01 * C01, al, be, seg = Math.hypot(P3[0] - P0[0], P3[1] - P0[1]);
  if (Math.abs(det) > 1e-9){ al = (X0 * C11 - X1 * C01) / det; be = (C00 * X1 - C01 * X0) / det; }
  if (!(al > seg * 0.02) || !(be > seg * 0.02) || al > seg * 3 || be > seg * 3){ al = be = seg / 3; }
  a.ox = r1(a.x + t1[0] * al); a.oy = r1(a.y + t1[1] * al); b.ix = r1(b.x + t2[0] * be); b.iy = r1(b.y + t2[1] * be);
  a.sm = isSmooth(a) || a.sm; b.sm = isSmooth(b) || b.sm;
  N.splice(ni, 1); }
function anchorTol(){ return 9 * upp() / (Math.hypot(layerT()[0], layerT()[1]) || 1); }
function finishPen(){
  if (!pen) return; var e = cur(), c = e.contours[pen.c];
  if (c && c.nodes.length < 2) e.contours.splice(pen.c, 1);
  else if (c) c.closed = true;            // font outlines must be closed
  pen = null; render();
}

/* chụm 2 ngón trên bàn vẽ = phóng / kéo khung, KHÔNG phải thao tác vẽ (người dùng 27/10: chụm đang thành khung chọn).
   Ngón 1 chạm: chụp trạng thái; ngón 2 chạm: huỷ thao tác ngón 1 vừa bắt đầu (khung chọn, điểm bút, kéo điểm…), trả lại đúng như trước,
   rồi phóng quanh điểm giữa 2 ngón + kéo theo. Thả bớt ngón: ngón còn lại không vẽ tiếp cho tới khi nhấc hết. */
var TP = {}, TPn = 0, PZ = null, T0 = null, PZdone = false;
function vbPt(x, y){ var r = svg.getBoundingClientRect(); return [vb.x + (x - r.left) * vb.w / r.width, vb.y + (y - r.top) * vb.h / r.height]; }
function pzMid(){ var a = []; for (var k in TP) a.push(TP[k]); return { x: (a[0].x + a[1].x) / 2, y: (a[0].y + a[1].y) / 2, d: Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y) || 1 }; }
svg.addEventListener('pointerdown', function(ev){
  if (ev.pointerType !== 'touch') return;
  TP[ev.pointerId] = { x: ev.clientX, y: ev.clientY }; TPn++;
  if (TPn === 1) { PZdone = false; var e = cur(); T0 = { h: e.hist.length, s: snap(e), sel: JSON.stringify(sel), pen: pen ? JSON.parse(JSON.stringify(pen)) : null }; return; }
  ev.stopImmediatePropagation(); ev.preventDefault();
  if (TPn === 2 && !PZ) {
    if (T0) { var e2 = cur(); drag = null; GUIDES = null; while (e2.hist.length > T0.h) unpush(); var s0 = JSON.parse(T0.s); e2.contours = s0.c; e2.strokes = s0.s; Object.assign(sel, JSON.parse(T0.sel)); pen = T0.pen; }
    var m = pzMid(); PZ = { d0: m.d, vb0: Object.assign({}, vb), w0: vbPt(m.x, m.y) }; try { svg.setPointerCapture(ev.pointerId); } catch (_) {} render();
  }
}, true);
svg.addEventListener('pointermove', function(ev){
  if (ev.pointerType !== 'touch' || !TP[ev.pointerId]) return;
  TP[ev.pointerId] = { x: ev.clientX, y: ev.clientY };
  if (PZ && TPn >= 2) { ev.stopImmediatePropagation(); ev.preventDefault();
    var m = pzMid(), r = svg.getBoundingClientRect(), f = PZ.d0 / m.d, w = Math.min(Math.max(PZ.vb0.w * f, 20), 40000), h = w * PZ.vb0.h / PZ.vb0.w;
    vb = { x: PZ.w0[0] - (m.x - r.left) * w / r.width, y: PZ.w0[1] - (m.y - r.top) * h / r.height, w: w, h: h }; applyVB(); return; }
  if (PZdone) { ev.stopImmediatePropagation(); }
}, true);
function pzUp(ev){ if (ev.pointerType !== 'touch' || !TP[ev.pointerId]) return; delete TP[ev.pointerId]; TPn = Math.max(0, TPn - 1);
  if (PZ || PZdone) { ev.stopImmediatePropagation(); if (PZ) { PZ = null; PZdone = TPn > 0; } else if (!TPn) PZdone = false; }
  if (!TPn) { T0 = null; PZdone = false; } }
svg.addEventListener('pointerup', pzUp, true); svg.addEventListener('pointercancel', pzUp, true);
window.__edPinchState = function(){ return { n: TPn, pinch: !!PZ, vb: vb }; };
svg.addEventListener('pointerdown', function(ev){
  svg.focus({ preventScroll: true });
  if (ev.button === 1 || tool === 'hand' || ev.altKey && tool !== 'pen') { drag = { pan: true, sx: ev.clientX, sy: ev.clientY, vb: Object.assign({}, vb) }; svg.setPointerCapture(ev.pointerId); return; }
  var e = cur(), p = toLocal(ev), t = hit(ev);
  var bEl = t && t.closest && t.closest('[data-board]');
  if (bEl) { ev.preventDefault(); activate(+bEl.dataset.board); return; }   // bấm chữ khác trên bàn vẽ → sửa chữ đó
  ev.preventDefault(); svg.setPointerCapture(ev.pointerId);
  if (tool === 'brush') { drag = { brush: true, pts: [p] }; return; }
  var tl = ((ev.ctrlKey || ev.metaKey) && PENS.indexOf(tool) >= 0) ? 'select' : tool;   // Illustrator: giữ Ctrl / ⌘ khi cầm bút = chọn trực tiếp (kéo điểm neo)
  if (tl === 'convert') {   // Illustrator Anchor Point tool: bấm điểm mượt → góc; bấm kéo điểm góc → kéo tay nắm mượt; kéo tay nắm → bẻ góc
    if (t && t.dataset.h) { var hc = +t.dataset.c, hn = +t.dataset.n; push(); e.contours[hc].nodes[hn].sm = false; drag = { handle: { c: hc, n: hn, h: t.dataset.h }, moved: false, brk: true }; return; }
    if (t && t.classList && t.classList.contains('ed-n')) { var cc4 = +t.dataset.c, nn4 = +t.dataset.n, nd4 = e.contours[cc4].nodes[nn4]; push(); sel.nodes = [[cc4, nn4]];
      if (nd4.ix != null || nd4.ox != null) { nd4.ix = nd4.iy = nd4.ox = nd4.oy = null; nd4.sm = false; e.touched = true; commit(); return; }
      drag = { penHandle: nd4, start: [nd4.x, nd4.y] }; e.touched = true; render(); return; }
    return;
  }
  if (tl === 'addpt' || tl === 'delpt' || (tl === 'pen' && !pen)) {   // Illustrator: + / − điểm neo; bút khi chưa vẽ: bấm đường = thêm, bấm điểm = xoá
    var onNode = t && t.classList && t.classList.contains('ed-n');
    if (tl === 'pen' && onNode){ var cp = +t.dataset.c, np = +t.dataset.n; sel.nodes = [[cp, np]]; sel.stroke = -1; push(); var ndp = e.contours[cp].nodes[np];
      drag = { nodes: true, p0: p, last: p, orig: JSON.parse(JSON.stringify([ndp])), anchor: [ndp.x, ndp.y], moved: false, delOnClick: [cp, np] }; render(); return; }   // bút: kéo điểm neo = dời, bấm thả = xoá
    if (tl === 'delpt' && onNode){ push(); delAnchor(e, +t.dataset.c, +t.dataset.n); sel.nodes = []; e.touched = true; commit(); return; }
    if (tl === 'addpt' || tl === 'pen'){ var hs = nearestSeg(e, p, anchorTol());
      if (hs && !onNode){ push(); var nI = addAnchor(e, hs); sel.nodes = [[hs.ci, nI]]; e.touched = true; commit(); return; } }
    if (tl !== 'pen') return;
  }
  if (tl === 'pen') {
    if (pen && t && t.dataset.n === '0' && +t.dataset.c === pen.c && e.contours[pen.c].nodes.length > 2) { push(); e.contours[pen.c].closed = true; pen = null; commit(); return; }
    push();
    if (!pen) { e.contours.push({ closed: false, nodes: [] }); pen = { c: e.contours.length - 1 }; }
    if (OPT.snap && !ev.altKey) { var Tp = layerT(), sp = snapPt(ap(Tp, p[0], p[1]), upp()); p = ap(inv(Tp), sp.p[0], sp.p[1]); }
    var n = { x: r1(p[0]), y: r1(p[1]), sm: false }; e.contours[pen.c].nodes.push(n);
    sel.nodes = [[pen.c, e.contours[pen.c].nodes.length - 1]];
    drag = { penHandle: n, start: p }; e.touched = true; render(); return;
  }
  if (tool === 'comp') {
    var Cs = components(e.contours), pick = -1;
    Cs.forEach(function(c, i){ if (inPoly(c.outer, p[0], p[1]) && (pick < 0 || c.A < Cs[pick].A)) pick = i; });
    if (pick < 0) { var bd = 30 * upp() / (Math.hypot(layerT()[0], layerT()[1]) || 1); Cs.forEach(function(c, i){ var d = Math.hypot(c.cx - p[0], c.cy - p[1]); if (d < bd) { bd = d; pick = i; } }); }
    sel.comp = pick; sel.stroke = -1;
    if (pick < 0) { sel.nodes = []; render(); return; }
    var cc = Cs[pick]; sel.nodes = []; cc.ci.forEach(function(ci){ e.contours[ci].nodes.forEach(function(_, ni){ sel.nodes.push([ci, ni]); }); });
    push(); drag = { nodes: true, p0: p, last: p, orig: JSON.parse(JSON.stringify(sel.nodes.map(function(x){ return e.contours[x[0]].nodes[x[1]]; }))), anchor: [cc.cx, cc.cy], moved: false }; render(); return;
  }
  // select tool
  if (t && t.dataset.h) { var ci = +t.dataset.c, ni = +t.dataset.n; push(); drag = { handle: { c: ci, n: ni, h: t.dataset.h }, moved: false }; return; }
  if (t && t.classList && t.classList.contains('ed-n')) {
    var c2 = +t.dataset.c, n2 = +t.dataset.n, has = sel.nodes.some(function(x){ return x[0] === c2 && x[1] === n2; });
    if (ev.shiftKey) { sel.nodes = has ? sel.nodes.filter(function(x){ return !(x[0] === c2 && x[1] === n2); }) : sel.nodes.concat([[c2, n2]]); }
    else if (!has) sel.nodes = [[c2, n2]];
    sel.stroke = -1; push(); var nd0 = e.contours[c2].nodes[n2];
    drag = { nodes: true, p0: p, last: p, orig: JSON.parse(JSON.stringify(sel.nodes.map(function(x){ return e.contours[x[0]].nodes[x[1]]; }))), anchor: [nd0.x, nd0.y], moved: false }; render(); return;
  }
  if (t && t.dataset.s != null) { sel.stroke = +t.dataset.s; sel.nodes = []; push(); drag = { stroke: sel.stroke, last: p, moved: false }; render(); return; }
  if (t && t.dataset.c != null && t.classList.contains('ed-outline')) {
    var c3 = +t.dataset.c; sel.nodes = e.contours[c3].nodes.map(function(_, i){ return [c3, i]; }); sel.stroke = -1; push();
    var ac3 = polyAC(flatC(e.contours[c3]));
    drag = { nodes: true, p0: p, last: p, orig: JSON.parse(JSON.stringify(sel.nodes.map(function(x){ return e.contours[x[0]].nodes[x[1]]; }))), anchor: [ac3.x, ac3.y], moved: false }; render(); return;
  }
  sel.nodes = ev.shiftKey ? sel.nodes : []; sel.stroke = -1; drag = { marq: [p[0], p[1], p[0], p[1]] }; render();
});
svg.addEventListener('pointermove', function(ev){
  var e = cur();
  if (!drag) { if (tool === 'pen' && pen) { pen.hover = toLocal(ev); render(); } return; }
  if (drag.pan) { var r = svg.getBoundingClientRect(), k = vb.w / r.width; vb = { x: drag.vb.x - (ev.clientX - drag.sx) * k, y: drag.vb.y - (ev.clientY - drag.sy) * k, w: vb.w, h: vb.h }; applyVB(); return; }
  var p = toLocal(ev);
  if (drag.brush) { var l = drag.pts[drag.pts.length - 1]; if (Math.hypot(p[0] - l[0], p[1] - l[1]) > 2) drag.pts.push(p); render(); return; }
  if (drag.penHandle) { var n = drag.penHandle; if (Math.hypot(p[0] - n.x, p[1] - n.y) * 1 > 6 * upp()) { n.ox = r1(p[0]); n.oy = r1(p[1]); n.ix = r1(2 * n.x - p[0]); n.iy = r1(2 * n.y - p[1]); n.sm = true; } render(); return; }
  if (drag.handle) {
    var hh = drag.handle, nd = e.contours[hh.c].nodes[hh.n];
    if (hh.h === 'i') { nd.ix = r1(p[0]); nd.iy = r1(p[1]); } else { nd.ox = r1(p[0]); nd.oy = r1(p[1]); }
    if (nd.sm && !ev.altKey && !drag.brk) { var ox = hh.h === 'i' ? 'o' : 'i', vx = nd.x - (hh.h === 'i' ? nd.ix : nd.ox), vy = nd.y - (hh.h === 'i' ? nd.iy : nd.oy), lv = Math.hypot(vx, vy) || 1;
      var lo2 = nd[ox + 'x'] != null ? Math.hypot(nd[ox + 'x'] - nd.x, nd[ox + 'y'] - nd.y) : lv; nd[ox + 'x'] = r1(nd.x + vx / lv * lo2); nd[ox + 'y'] = r1(nd.y + vy / lv * lo2); }
    if (ev.altKey || drag.brk) nd.sm = false;
    drag.moved = true; render(); return;
  }
  if (drag.nodes) {
    var dx = p[0] - drag.p0[0], dy = p[1] - drag.p0[1];
    if (drag.delOnClick && !drag.moved && Math.hypot(dx, dy) < 4 * upp()) return;   // bút: rung tay nhẹ chưa tính là kéo if (ev.shiftKey) { if (Math.abs(dx) > Math.abs(dy)) dy = 0; else dx = 0; }
    GUIDES = null;
    if (OPT.snap && !ev.altKey && drag.anchor) {   // điểm neo (điểm được bấm, hoặc tâm thành phần) dính vào đường gần nhất
      var Tm = layerT(), it = inv(Tm), a0 = drag.anchor, aw = ap(Tm, a0[0] + dx, a0[1] + dy);
      var inSel = {}; sel.nodes.forEach(function(x){ inSel[x[0] + ':' + x[1]] = 1; });
      var sn = snapPt(aw, upp(), function(ci, ni){ return inSel[ci + ':' + ni]; });
      if (ev.shiftKey) { if (dy === 0) sn.gy = null, sn.p[1] = aw[1]; else sn.gx = null, sn.p[0] = aw[0]; }
      if (sn.gx || sn.gy) { var la = ap(it, sn.p[0], sn.p[1]); dx = la[0] - a0[0]; dy = la[1] - a0[1]; GUIDES = sn; }
    }
    sel.nodes.forEach(function(x, i){ var n0 = drag.orig[i], n = e.contours[x[0]].nodes[x[1]];
      n.x = r1(n0.x + dx); n.y = r1(n0.y + dy); if (n0.ix != null) { n.ix = r1(n0.ix + dx); n.iy = r1(n0.iy + dy); } if (n0.ox != null) { n.ox = r1(n0.ox + dx); n.oy = r1(n0.oy + dy); } });
    drag.moved = true; render(); return; }
  if (drag.stroke != null) { var dx2 = p[0] - drag.last[0], dy2 = p[1] - drag.last[1]; e.strokes[drag.stroke].pts.forEach(function(q){ q[0] += dx2; q[1] += dy2; }); drag.last = p; drag.moved = true; render(); return; }
  if (drag.marq) { drag.marq[2] = p[0]; drag.marq[3] = p[1]; render(); }
});
function endDrag(){
  if (!drag) return; var e = cur(), d = drag; drag = null; if (GUIDES) { GUIDES = null; }
  if (d.brush) { if (d.pts.length > 1) { push(); e.strokes.push({ w: +brushW.value, pts: rdp(d.pts, 2.5).map(function(q){ return [r1(q[0]), r1(q[1])]; }) }); commit(); } else render(); return; }
  if (d.penHandle) { commit(); return; }
  if (d.nodes && d.delOnClick && !d.moved) { delAnchor(e, d.delOnClick[0], d.delOnClick[1]); sel.nodes = []; e.touched = true; commit(); return; }   // bút: bấm thả không kéo = xoá điểm (đã push lúc bấm)
  if (d.handle || d.nodes || d.stroke != null) { if (d.moved) commit(); else { unpush(); render(); } return; }
  if (d.marq) {
    var a = d.marq, x0 = Math.min(a[0], a[2]), x1 = Math.max(a[0], a[2]), y0 = Math.min(a[1], a[3]), y1 = Math.max(a[1], a[3]);
    if (x1 - x0 > 2 || y1 - y0 > 2) e.contours.forEach(function(c, ci){ c.nodes.forEach(function(n, ni){ if (n.x >= x0 && n.x <= x1 && n.y >= y0 && n.y <= y1 && !sel.nodes.some(function(x){ return x[0] === ci && x[1] === ni; })) sel.nodes.push([ci, ni]); }); });
    render();
  }
}
svg.addEventListener('pointerup', endDrag); svg.addEventListener('pointercancel', endDrag);
svg.addEventListener('dblclick', function(ev){ var t = hit(ev); if (tool === 'select' && t && t.classList && t.classList.contains('ed-n')) { sel.nodes = [[+t.dataset.c, +t.dataset.n]]; toggleSmooth(); } });
if (window.__UB) __UB.reg('editor', undo, redo);
var edOn = false; document.addEventListener('pointerdown', function(ev){ edOn = root.contains(ev.target); }, true);   // phím tắt chỉ cho bàn vẽ khi vừa bấm vào nó
document.addEventListener('keydown', function(ev){
  if (!edOn && !root.matches(':hover') && !root.contains(document.activeElement)) return;
  var a = document.activeElement; if (a && (/TEXTAREA|INPUT/.test(a.tagName) || a.isContentEditable)) return;
  var k = ev.key.toLowerCase();
  if ((ev.ctrlKey || ev.metaKey) && k === 'z') { ev.preventDefault(); if (ev.shiftKey) redo(); else undo(); return; }
  if ((ev.ctrlKey || ev.metaKey) && k === 'c') { ev.preventDefault(); copySel(); return; }
  if ((ev.ctrlKey || ev.metaKey) && k === 'v') { ev.preventDefault(); pasteClip(ev.shiftKey ? 'raw' : 'axis'); return; }
  if ((ev.ctrlKey || ev.metaKey) && (k === '=' || k === '+' || k === '-')) { ev.preventDefault(); zoom(k === '-' ? 1.25 : 0.8); return; }   // phóng to / thu nhỏ: Ctrl + / − (như Illustrator)
  if (ev.ctrlKey || ev.metaKey) return;
  if (k === 'v') setTool('select'); else if (k === 'p') setTool('pen'); else if (k === 'b') setTool('brush'); else if (k === 'h') setTool('hand'); else if (k === 'c' && ev.shiftKey) setTool('convert'); else if (k === 'c') setTool('comp');
  else if (k === 's' && !ev.shiftKey) { var sb = root.querySelector('.ed-opts [data-opt="snap"]'); if (sb) sb.click(); }
  else if (k === 'enter' || k === 'escape') { if (pen) finishPen(); else { sel.nodes = []; sel.stroke = -1; render(); } }
  else if (k === 'delete' || k === 'backspace') { ev.preventDefault(); delSel(); }
  else if (/^arrow/.test(k) && sel.nodes.length) { ev.preventDefault(); var st = ev.shiftKey ? 10 : 1, dx = k === 'arrowleft' ? -st : k === 'arrowright' ? st : 0, dy = k === 'arrowup' ? st : k === 'arrowdown' ? -st : 0; var e = cur(); push(); sel.nodes.forEach(function(x){ moveNode(e.contours[x[0]].nodes[x[1]], dx, dy); }); commit(); }
  else if (k === 'f') fitAll(); else if (k === '+' || k === '=') setTool('addpt'); else if (k === '-' || k === '_') setTool('delpt');
});

/* ---------- save / load ---------- */
var db = null, timers = {}, stEl = root.querySelector('.ed-save');
function say(t){ stEl.innerHTML = t; }
function saveOne(k){
  var e = ED[k]; if (!e) return Promise.resolve();
  var s0 = { kind: k[0] === "m" ? "m" : "g", id: k.slice(2) };
  if (!db) return Promise.reject(new Error(tr('saveFailed')));
  var gen = e.saveGen || 0;
  var body = { key: k, kind: s0.kind === "m" ? "mark" : "glyph", id: s0.id, w: e.w,
    touched: !!e.touched, note: e.note || "", contours: e.touched ? nodesToOps(e.contours) : [],
    strokes: e.strokes, layer: s0.kind === "m" ? layerTFor(s0.id) : null, updatedAt: new Date().toISOString() };
  return db.doc(EDDOC + "/" + k).set(body).then(function(){
    if ((e.saveGen || 0) === gen) { e.reset = false; e.pendingSave = false; }
    say('');
    return body;
  });
}
function schedSave(now){
  var k = keyOf(sel), e = ED[k];
  if (window.__save) window.__save();
  if (!db) { say(tr('saveFailed')); return; }
  clearTimeout(timers[k]); say(tr('saving'));
  timers[k] = setTimeout(function(){
    saveOne(k).catch(function(er){ say(tr('saveErrorCode', { code: (er && er.code) || "?" })); });
  }, now ? 0 : 700);
}
window.__edFlush = function(){
  if (window.__save) window.__save();
  if (!db) return Promise.reject(new Error(tr('saveFailed')));
  function flushPending(){
    var keys = Object.keys(ED).filter(function(k){ return !!ED[k].pendingSave; });
    keys.forEach(function(k){ clearTimeout(timers[k]); });
    return Promise.all(keys.map(saveOne)).then(function(){
      return Object.keys(ED).some(function(k){ return !!ED[k].pendingSave; }) ? flushPending() : undefined;
    });
  }
  return flushPending();
};
function layerTFor(id){ var r = FV.recipes[MK[id][3]]; var mi = r && r.m.filter(function(x){ return x.m === id; })[0]; return mi ? mi.t : null; }
function label(s){ return s.kind === 'm' ? markLabel(s.id) : '“' + String.fromCodePoint((FV.recipes[s.id] || FV.glyphs[s.id]).u) + '”'; }
window.__edSummary = function(){
  var out = [];
  Object.keys(ED).forEach(function(k){ var e = ED[k]; if (!e.touched && !(e.note || '').trim()) return;
    var s = { kind: k[0], id: k.slice(2) };
    out.push(tr('summary', { glyph: label(s) }) + (e.touched ? ': ' + tr('summaryEdits', { paths: e.contours.length, strokes: e.strokes.length }) : '') + ((e.note || '').trim() ? ' — ' + e.note.trim() : ''));
  });
  return out.length ? out.join('\n') : '';
};
window.__edDb = function(d){
  db = d; if (!db) { say(tr('saveFailed')); return; }
  db.collection(EDDOC).get().then(function(qs){
    qs.docs.forEach(function(doc){ var v = doc.data() || {}; var s = { kind: v.kind === 'mark' ? 'm' : 'g', id: v.id }; if (s.kind === 'm' && !MK[s.id]) return; if (s.kind === 'g' && !FV.recipes[s.id] && !FV.glyphs[s.id]) return;
      var e = getEd(s); if (v.touched && v.contours) e.contours = opsToNodes(v.contours); e.strokes = v.strokes || []; e.touched = !!v.touched; e.note = v.note || ''; });
    say('');
    render(); if (window.__save) window.__save();
  }).catch(function(){ say(tr('readFailed')); });
};

/* boot */
setTool('select'); getEd(sel);
window.__edSetLocale = function(language){
  window.__FV_LOCALE = String(language || 'vi').toLowerCase().indexOf('en') === 0 ? 'en' : 'vi';
  render(); renderList(); renderStrip();
};
if (window.__FV_LOCALE) window.__edSetLocale(window.__FV_LOCALE);
function boot(){ fit(); }
if (document.fonts && document.fonts.ready) document.fonts.ready.then(boot); else boot();
window.addEventListener('resize', function(){ if (vb) { var a = svgAspect(); vb.h = vb.w / a; applyVB(); } });
})();
