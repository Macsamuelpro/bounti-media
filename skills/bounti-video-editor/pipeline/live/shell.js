// shared helpers for driving the Bounti prototype shell
const { chromium } = require('playwright');
const BASE = 'http://127.0.0.1:8765/';
async function open(file, opts = {}) {
  const b = await chromium.launch();
  const W = opts.W || 472, H = opts.H || 986;
  const ctx = await b.newContext({ viewport: { width: W, height: H }, deviceScaleFactor: opts.dsf || 2 });
  await ctx.route(/unpkg\.com/, r => r.continue({ url: r.request().url().replace('https://unpkg.com/', 'https://cdn.jsdelivr.net/npm/') }));
  const p = await ctx.newPage();
  await p.goto(BASE + encodeURIComponent(file + '.dc.html'), { waitUntil: 'networkidle', timeout: 45000 });
  await p.waitForTimeout(1200);
  return { b, ctx, p };
}
// find the DCLogic component that owns go()
async function exposeApp(p, fn = 'go') {
  return p.evaluate((fn) => {
    const seen = new Set();
    for (const el of document.querySelectorAll('*')) {
      const k = Object.keys(el).find(k => k.startsWith('__reactFiber'));
      if (!k) continue;
      let f = el[k];
      while (f) { const s = f.stateNode && f.stateNode.logic; if (s && typeof s[fn] === "function") { window.__app = s; return Object.keys(s.state); } f = f.return; }
    }
    return null;
  }, fn);
}
module.exports = { open, exposeApp };
