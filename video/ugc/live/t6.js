const { open, exposeApp } = require('./shell');
(async () => {
  const { b, p } = await open('Bounti Partners', { W: 472, H: 986, dsf: 1 });
  console.log(await exposeApp(p));
  let i = 0; const shot = async () => p.screenshot({ path: `ex_pw_${i++}.png` });
  const btns = () => p.evaluate(() => [...document.querySelectorAll('button')].filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.y > 0 && r.y < 986; }).map(b => { const r = b.getBoundingClientRect(); return `${Math.round(r.x + r.width / 2)},${Math.round(r.y + r.height / 2)} ${(b.innerText || b.getAttribute('aria-label') || '').replace(/\s+/g, ' ').slice(0, 26)}`; }).join(' | '));
  await p.evaluate(() => __app.go('home')); await p.waitForTimeout(2500); await shot(); console.log('HOME', await btns());
  await p.evaluate(() => __app.go('wizard')); await p.waitForTimeout(2500); await shot(); console.log('WIZ', await btns());
  await b.close();
})();
