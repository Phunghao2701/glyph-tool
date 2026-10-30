// Sinh vk_own.css: chép mọi luật CSS cũ (layer vk-legacy) đang chạm thành phần Việt Font Kit (.vk …) thành luật riêng :where(.vk) …
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const out = new Map(); const base = new Map();
  for (const theme of ['light', 'dark']) for (const w of [1280, 390]) {
    const p = await b.newPage({ viewport: { width: w, height: 900 }, colorScheme: theme });
    await p.goto('file://' + process.argv[2]); await p.waitForTimeout(900);
    const r = await p.evaluate(() => {
      const res = [];
      const strip = s => s.replace(/::?(before|after|placeholder|-webkit-[\w-]+|-moz-[\w-]+|marker|selection|hover|focus-visible|focus-within|focus|active|disabled|empty|checked|first-child|last-child|nth-child\([^)]*\)|not\([^)]*\))/g, '');
      const visit = (rules, ctx, inLegacy) => { for (const ru of rules) {
        if (ru instanceof CSSLayerBlockRule) { visit(ru.cssRules, ctx, ru.name === 'vk-legacy'); continue; }
        if (ru instanceof CSSMediaRule) { visit(ru.cssRules, ctx.concat('@media ' + ru.conditionText), inLegacy); continue; }
        if (ru instanceof CSSSupportsRule) { visit(ru.cssRules, ctx.concat('@supports ' + ru.conditionText), inLegacy); continue; }
        if (!inLegacy || !ru.selectorText) continue;
        const pg = ru.selectorText.split(/,(?![^(]*\))/).map(s => s.trim()).filter(s => /^(:root|html|body)(?![\w-])/.test(s) && !/\s/.test(s.replace(/\([^)]*\)/g, '')));
        if (pg.length) res.push(['BASE', ctx.join('|'), pg.join(','), ru.style.cssText, ru.cssText]);
        const parts = ru.selectorText.split(/,(?![^(]*\))/).map(s => s.trim()).filter(s => {
          if (/^(\*|html|body|:root)\b/.test(s) || /:root/.test(s)) return false;
          let els; try { els = document.querySelectorAll(strip(s) || '*'); } catch (e) { return false; }
          for (const e of els) if (e.closest('.vk')) return true; return false;
        });
        if (parts.length) res.push([ctx.join('|'), parts.map(s => ':where(.vk) ' + s).join(','), ru.style.cssText, ru.cssText]);
      } };
      for (const st of document.styleSheets) { try { visit(st.cssRules, [], false); } catch (e) {} }
      return res;
    });
    for (const x of r) { if (x[0] === 'BASE') base.set(x[4], x.slice(1, 4)); else out.set(x[3], x.slice(0, 3)); }
    await p.close();
  }
  // giữ thứ tự gốc: Map giữ thứ tự chèn của lần đầu
  let css = '/* vk_own.css — CSS RIÊNG của thành phần Việt Font Kit, chép từ tpl/styles.css (lớp cũ) lúc tách CSS 27/10.\n   Nằm trong @layer vk-own (trên vk-legacy): sửa giao diện thành phần thì sửa ở đây / vfk_ui.py, không sửa styles.css.\n   Sinh bằng gen_own.js; đã kiểm bằng ảnh chụp computed style (t_snap.js) — trước / sau giống hệt. */\n';
  for (const [ctx, sel, body] of out.values()) {
    let r = sel + '{' + body + '}';
    for (const c of ctx ? ctx.split('|').reverse() : []) r = c + '{' + r + '}';
    css += r + '\n';
  }
  fs.writeFileSync(process.argv[3], css);
  // vk_base.css: luật cấp trang (:root / html / body) của lớp cũ — KHÔNG layer, vì khung artifact (claude.ai) tự chèn
  // body{background:#fff;color:#000} không layer, sẽ thắng mọi luật trong @layer → trang tối thành nền trắng (lỗi 27/10).
  let bc = '/* vk_base.css — luật cấp trang (:root / html / body) chép từ tpl/styles.css, KHÔNG layer (thắng body{background:#fff} khung artifact chèn). Sinh bằng gen_own.js. */\n';
  for (const [ctx, sel, body] of base.values()) { let r = sel + '{' + body + '}'; for (const c of ctx ? ctx.split('|').reverse() : []) r = c + '{' + r + '}'; bc += r + '\n'; }
  if (process.argv[4]) fs.writeFileSync(process.argv[4], bc);
  console.log('base', base.size, 'luật'); console.log(out.size, 'luật', css.length, 'B'); await b.close();
})();
