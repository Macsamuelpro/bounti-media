const { chromium } = require('playwright');
(async () => { const b = await chromium.launch();
 for (const [f, W, H] of [['Bounti Partners', 1440, 900], ['PWizard', 1440, 900], ['PHome', 1440, 900], ['Bounti Partners', 390, 844]]) {
  const ctx = await b.newContext({ viewport: { width: W, height: H } });
  await ctx.route(/unpkg\.com/, r => r.continue({ url: r.request().url().replace('https://unpkg.com/', 'https://cdn.jsdelivr.net/npm/') }));
  const p = await ctx.newPage(); await p.goto('http://127.0.0.1:8765/' + encodeURIComponent(f + '.dc.html'), { waitUntil: 'networkidle' }); await p.waitForTimeout(3000);
  await p.screenshot({ path: `ex_p_${f.replace(' ', '')}_${W}.png` });
  console.log(f, W, (await p.evaluate(() => [...document.querySelectorAll('button')].filter(b => b.getBoundingClientRect().width > 0).map(b => (b.innerText || b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').slice(0, 28)).join(' | '))).slice(0, 700));
  await ctx.close(); }
 await b.close(); })();
