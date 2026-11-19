const { open, exposeApp } = require('./shell');
(async () => {
  const { b, p } = await open('Bounti');
  await exposeApp(p);
  await p.evaluate(() => { __app.skipSplash(); __app.go('feed'); }); await p.waitForTimeout(6000);
  for (let i = 0; i < 4; i++) {
    await p.mouse.move(236, 600); await p.mouse.wheel(0, 900); await p.waitForTimeout(1500);
    await p.screenshot({ path: `ex_feed_${i + 1}.png`, scale: 'css' });
    const cl = await p.evaluate(() => { const o = []; document.querySelectorAll('button').forEach(e => { const r = e.getBoundingClientRect(); if (r.width < 8 || r.y > 990 || r.y < 0 || r.y > 860) return; o.push(`${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)} "${(e.innerText || e.getAttribute('aria-label') || '').replace(/\s+/g, ' ').slice(0, 40)}"`); }); return o; });
    console.log(i + 1, cl.join(' | '));
  }
  await b.close();
})();
