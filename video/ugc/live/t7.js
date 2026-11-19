const { open, exposeApp } = require('./shell');
(async () => {
  const { b, p } = await open('Bounti Partners', { W: 472, H: 986, dsf: 1 });
  await exposeApp(p);
  let i = 0; const shot = async () => p.screenshot({ path: `ex_pw_${i++}.png` });
  const btns = () => p.evaluate(() => [...document.querySelectorAll('button,input,[contenteditable]')].filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.y > 0 && r.y < 986; }).map(b => { const r = b.getBoundingClientRect(); return `${Math.round(r.x + r.width / 2)},${Math.round(r.y + r.height / 2)} ${b.tagName[0]} ${(b.innerText || b.getAttribute('aria-label') || b.placeholder || '').replace(/\s+/g, ' ').slice(0, 24)}`; }).join(' | '));
  const tapT = async (t) => { const r = await p.evaluate((t) => { const e = [...document.querySelectorAll('button')].find(b => (b.innerText || '').trim().startsWith(t) && b.getBoundingClientRect().width > 0); if (!e) return null; e.scrollIntoView({ block: 'center' }); const q = e.getBoundingClientRect(); return [q.x + q.width / 2, q.y + q.height / 2]; }, t); if (!r) { console.log('MISS', t); return; } await p.mouse.click(r[0], r[1]); await p.waitForTimeout(1500); };
  await p.evaluate(() => __app.go('home')); await p.waitForTimeout(2000);
  await tapT('Create a campaign'); await shot(); console.log(1, await btns());
  await tapT('Engagement'); await shot(); console.log(2, await btns());
  await tapT('Continue'); await shot(); console.log(3, await btns());
  await b.close();
})();
