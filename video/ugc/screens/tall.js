const { chromium } = require('playwright');
const base = 'file:///home/user/Bounti/docs/design/export/';
(async () => {
  const b = await chromium.launch();
  for (const [f, H] of [['Missions', 2600], ['BWall', 2000], ['House', 2400], ['Mine', 2900], ['Affiliate', 1500], ['Trend', 1300], ['Profile', 1800], ['Feed', 844], ['Bounti', 844], ['LinkFlow', 844]]) {
    const ctx = await b.newContext({ viewport: { width: 390, height: H }, deviceScaleFactor: 3 });
    await ctx.route(/unpkg\.com/, r => r.continue({ url: r.request().url().replace('https://unpkg.com/', 'https://cdn.jsdelivr.net/npm/') }));
    const p = await ctx.newPage();
    await p.goto(base + encodeURIComponent(f + '.dc.html'), { waitUntil: 'networkidle', timeout: 30000 }); await p.waitForTimeout(1800);
    await p.screenshot({ path: 'tall_' + f + '.png' }); console.log(f, H); await ctx.close();
  }
  await b.close();
})();
