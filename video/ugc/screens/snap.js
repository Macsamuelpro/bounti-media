const { chromium } = require('playwright');
const base = 'file:///home/user/Bounti/docs/design/export/';
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3 });
  await ctx.route(/unpkg\.com/, r => r.continue({ url: r.request().url().replace('https://unpkg.com/', 'https://cdn.jsdelivr.net/npm/') }));
  for (const f of ['Bounti', 'Feed', 'Missions', 'Mine', 'House', 'Profile', 'BWall', 'LinkFlow', 'Trend', 'Affiliate']) {
    const p = await ctx.newPage(); const errs = [];
    p.on('pageerror', e => errs.push(e.message.slice(0, 80)));
    try { await p.goto(base + encodeURIComponent(f + '.dc.html'), { waitUntil: 'networkidle', timeout: 30000 }); await p.waitForTimeout(1500);
      const h = await p.evaluate(() => document.documentElement.scrollHeight);
      await p.screenshot({ path: f + '.png' }); console.log(f, 'h', h, (await p.evaluate(() => document.body.innerText)).slice(0, 120).replace(/\n+/g, ' | '), errs.join(';'));
    } catch (e) { console.log(f, 'ERR', e.message.slice(0, 100)); }
    await p.close();
  }
  await b.close();
})();
