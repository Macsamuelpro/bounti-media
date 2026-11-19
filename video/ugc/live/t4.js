const { open, exposeApp } = require('./shell');
(async () => {
  const { b, p } = await open('Bounti', { W: 472, H: 986, dsf: 1 });
  await exposeApp(p);
  await p.evaluate(() => { __app.skipSplash(); __app.setState({ connected: { tiktok: true, instagram: true, youtube: true, snapchat: true } }); __app.go('feed'); }); await p.waitForTimeout(5000);
  const shot = async (n) => { await p.screenshot({ path: `ex_scr_${n}.png` }); };
  let i = 0;
  // My Hunts
  const clickTxt = async (t) => { const r = await p.evaluate((t) => { const e = [...document.querySelectorAll('button')].find(b => (b.innerText || b.getAttribute('aria-label') || '').trim().startsWith(t) && b.getBoundingClientRect().width > 0); if (!e) return null; const q = e.getBoundingClientRect(); return [q.x + q.width / 2, q.y + q.height / 2]; }, t); if (r) await p.mouse.click(r[0], r[1]); else console.log('miss', t); await p.waitForTimeout(1800); };
  await clickTxt('My Hunts'); await shot(i++); await p.mouse.move(236,500); await p.mouse.wheel(0,600); await p.waitForTimeout(800); await shot(i++);
  for (const s of ['house', 'profile', 'missions', 'crew']) { await p.evaluate((s) => __app.go(s), s); await p.waitForTimeout(2200); await shot(i++); }
  await p.evaluate(() => __app.go('landing')); await p.waitForTimeout(1500); await shot(i++);
  await clickTxt('Start Earning'); await shot(i++);
  console.log(await p.evaluate(() => [...document.querySelectorAll('button')].filter(b => b.getBoundingClientRect().width > 0).map(b => (b.innerText||'').replace(/\s+/g,' ').slice(0,30)).join(' | ')));
  await b.close();
})();
