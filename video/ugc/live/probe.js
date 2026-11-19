const { chromium } = require('playwright');
const base = 'file:///home/user/Bounti/docs/design/export/';
(async () => {
  const b = await chromium.launch();
  for (const f of process.argv.slice(2)) {
    const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
    await ctx.route(/unpkg\.com/, r => r.continue({ url: r.request().url().replace('https://unpkg.com/', 'https://cdn.jsdelivr.net/npm/') }));
    const p = await ctx.newPage();
    await p.goto(base + encodeURIComponent(f + '.dc.html'), { waitUntil: 'networkidle', timeout: 30000 }); await p.waitForTimeout(1500);
    const info = await p.evaluate(() => {
      const out = [];
      document.querySelectorAll('*').forEach(e => {
        const cs = getComputedStyle(e);
        const clickable = e.tagName==='BUTTON' || e.tagName==='A' || cs.cursor==='pointer' || e.onclick;
        if (!clickable) return;
        const r = e.getBoundingClientRect(); if (r.width<4||r.height<4) return;
        const t = (e.innerText||e.getAttribute('aria-label')||'').replace(/\s+/g,' ').trim().slice(0,50);
        out.push(`${e.tagName} ${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)} "${t}"`);
      });
      return {h: document.documentElement.scrollHeight, title: document.title, out: out.slice(0,60)};
    });
    console.log('#####', f, info.title, 'h=', info.h); info.out.forEach(x=>console.log('  ',x));
    await p.screenshot({path:'probe_'+f+'.png'});
    await ctx.close();
  }
  await b.close();
})();
