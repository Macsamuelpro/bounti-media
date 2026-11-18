const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3 })).newPage();
  await p.goto('https://earnbounti.com/', { waitUntil: 'networkidle' });
  const info = await p.evaluate(() => {
    const pick = sel => {
      const e = document.querySelector(sel); if (!e) return null; const s = getComputedStyle(e);
      return { text: e.innerText.slice(0, 40), font: s.fontFamily, weight: s.fontWeight, size: s.fontSize, ls: s.letterSpacing, color: s.color, bg: s.backgroundColor };
    };
    const fonts = Array.from(document.fonts).map(f => f.family + ' ' + f.weight + ' ' + f.style + ' ' + f.status);
    return { body: getComputedStyle(document.body).backgroundColor, h1: pick('h1'), h2: pick('h2'), p: pick('p'), btn: pick('a,button'),
             fonts: Array.from(new Set(fonts)).slice(0, 20) };
  });
  console.log(JSON.stringify(info, null, 1));
  const secs = await p.$$('section'); let i = 0;
  for (const s of secs) { try { await s.screenshot({ path: 'sec_' + String(i).padStart(2, '0') + '.png' }); } catch (e) {} i++; }
  console.log('sections', secs.length);
  await b.close();
})();
