// node proof.js FONT_A [FONT_B|-] OUT.png grid|text   (env VNSET, FS, MW, GUIDES=1 vẽ line biên)
const { chromium } = require('playwright'); const fs = require('fs');
const [A, B, OUT, MODE] = process.argv.slice(2);
const VN = process.env.VNSET || 'aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệiìíỉĩịoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữựyỳýỷỹỵđ';
const FS = +(process.env.FS || 84), MW = +(process.env.MW || 70);
const hasB = B && B !== '-';
const ff = (n, p) => `@font-face{font-family:${n};src:url(data:font/otf;base64,${fs.readFileSync(p).toString('base64')})}`;
let body;
if (MODE === 'grid') {
  const row = s => [...s].map(c => `<span>${c}</span>`).join('');
  const up = process.env.NOUP ? '' : VN.toUpperCase();
  body = `<div class="g fa">${row(VN)}</div>` + (up ? `<div class="g fa">${row(up)}</div>` : '') + (hasB ? `<div class="g fb">${row(VN)}</div>` + (up ? `<div class="g fb">${row(up)}</div>` : '') : '');
} else {
  const T = process.env.TEXT || `người ươn ưa, cửa, TƯƠNG LAI<br>thưởng thức, mười, ưu tú, ƯỚC MƠ<br>phố cổ, ấm áp, ồn ào · ẨM THỰC<br>ịạẹọụỵ ợự · mì, mị. ủy ban, ơn · đã ĐƯỢC<br>ố ấ ồ Ố Ấ · ẩ ể ổ Ẩ · ở ử “cổ,” Người ƯT · ỸỶỲÝ ỹỷỳý`;
  body = `<div class="t fa">${T}</div>` + (hasB ? `<div class="t fb">${T}</div>` : '');
}
const guides = process.env.GUIDES ? '.g span{box-shadow:inset 1px 0 #e33,inset -1px 0 #e33}' : '';
const html = `<html><head><meta charset="utf-8"><style>${ff('FA', A)}${hasB ? ff('FB', B) : ''}
body{margin:20px;background:#fff;color:#111}.fa{font-family:FA}.fb{font-family:FB}
.g{font-size:${FS}px;line-height:1.5;display:flex;flex-wrap:wrap;width:2400px;gap:0 ${process.env.GUIDES ? 30 : 0}px}.g span{display:inline-block;min-width:${MW}px;text-align:center}${guides}
.t{font-size:${FS}px;line-height:1.35;margin-bottom:30px;width:2400px}</style></head><body>${body}</body></html>`;
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 2440, height: 400 } });
  await p.setContent(html); await p.evaluate(() => document.fonts.ready);
  console.log((await p.evaluate(() => [...document.fonts].map(f => f.family + ':' + f.status))).join(' '));
  await p.screenshot({ path: OUT, fullPage: true }); await b.close(); })();
