const { chromium } = require('playwright');
(async () => { const b = await chromium.launch();
 for (const f of ['Bounti Desktop', 'Landing Desktop', 'DeskFeed', 'DeskMissions', 'PHome', 'PCampaign', 'PAffResults', 'PLift']) {
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.route(/unpkg\.com/, r => r.continue({ url: r.request().url().replace('https://unpkg.com/', 'https://cdn.jsdelivr.net/npm/') }));
  const p = await ctx.newPage(); await p.goto('http://127.0.0.1:8765/' + encodeURIComponent(f + '.dc.html'), { waitUntil: 'networkidle' }); await p.waitForTimeout(4500);
  await p.screenshot({ path: `ex_d_${f.replace(' ', '')}.png` }); console.log(f, (await p.evaluate(() => document.body.innerText.replace(/\s+/g, ' ').slice(0, 120))));
  await ctx.close(); }
 await b.close(); })();
