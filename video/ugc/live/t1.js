const { open, exposeApp } = require('./shell');
(async () => {
  const { b, p } = await open('Bounti');
  console.log(await exposeApp(p));
  await p.evaluate(() => { __app.skipSplash(); __app.go('feed'); }); await p.waitForTimeout(2500);
  await p.screenshot({ path: 'ex_feed_0.png' });
  const r = await p.evaluate(() => { const f = __app.frameRef.current; const r = f.getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; });
  console.log('frame', r);
  const cl = await p.evaluate(() => { const o = []; document.querySelectorAll('*').forEach(e => { const cs = getComputedStyle(e); if (!(e.tagName === 'BUTTON' || cs.cursor === 'pointer')) return; const r = e.getBoundingClientRect(); if (r.width < 8 || r.y > 990 || r.y < 0) return; o.push(`${e.tagName} ${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)} "${(e.innerText || e.getAttribute('aria-label') || '').replace(/\s+/g, ' ').slice(0, 40)}"`); }); return o; });
  cl.slice(0, 50).forEach(x => console.log(' ', x));
  await b.close();
})();
