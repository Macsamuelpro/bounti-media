const { chromium } = require('playwright');
const base = 'http://127.0.0.1:8765/';
const [f, ...clicks] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  await ctx.route(/unpkg\.com/, r => r.continue({ url: r.request().url().replace('https://unpkg.com/', 'https://cdn.jsdelivr.net/npm/') }));
  const p = await ctx.newPage();
  await p.goto(base + encodeURIComponent(f + '.dc.html'), { waitUntil: 'networkidle', timeout: 30000 }); await p.waitForTimeout(2500);
  let i = 0; await p.screenshot({ path: `ex_${f}_${i++}.png` });
  for (const c of clicks) {
    if (c.startsWith('wait:')) { await p.waitForTimeout(+c.slice(5)); }
    else if (c.startsWith('scroll:')) { await p.mouse.move(195, 500); await p.mouse.wheel(0, +c.slice(7)); await p.waitForTimeout(700); }
    else if (c.startsWith("xy:")) { const [x,y]=c.slice(3).split(",").map(Number); await p.mouse.click(x,y); await p.waitForTimeout(1200);} else { const loc = p.getByText(c, { exact: false }).first(); try { await loc.click({ timeout: 4000, force: true }); } catch (e) { console.log('fail', c, e.message.split('\n')[0]); } await p.waitForTimeout(1200); }
    await p.screenshot({ path: `ex_${f}_${i++}.png` });
    const txt = await p.evaluate(() => document.body.innerText.replace(/\s+/g, ' ').slice(0, 400)); console.log(i - 1, c, '::', txt);
  }
  await b.close();
})();
