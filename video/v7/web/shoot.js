const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  for (const [name, url] of [["home","https://earnbounti.com/"],["partners","https://partners.earnbounti.com/"],["app","https://app.earnbounti.com/"]]) {
    try {
      const r = await p.goto(url, { waitUntil: 'networkidle', timeout: 45000 });
      await p.waitForTimeout(1500);
      console.log(name, r && r.status(), await p.title(), (await p.evaluate(() => document.body.innerText)).slice(0, 300).replace(/\n+/g, ' | '));
      await p.screenshot({ path: `${name}_top.png` });
      await p.screenshot({ path: `${name}_full.png`, fullPage: true });
    } catch (e) { console.log(name, 'ERR', e.message.slice(0, 120)); }
  }
  await b.close();
})();
