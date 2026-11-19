const { open, exposeApp } = require('./shell');
(async () => {
  const { b, p } = await open('Bounti Partners', { W: 472, H: 986, dsf: 1 });
  await exposeApp(p);
  let i = 0; const shot = async () => p.screenshot({ path: `ex_pp_${i++}.png` });
  const btns = () => p.evaluate(() => [...document.querySelectorAll('button,input')].filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.y > 0 && r.y < 986; }).map(b => `${b.tagName[0]} ${(b.innerText || b.getAttribute('aria-label') || b.placeholder || b.value || '').replace(/\s+/g, ' ').slice(0, 26)}`).join(' | '));
  const tapT = async (t) => { const r = await p.evaluate((t) => { const e = [...document.querySelectorAll('button')].find(b => (b.innerText || '').trim().startsWith(t) && b.getBoundingClientRect().width > 0); if (!e) return null; e.scrollIntoView({ block: 'center' }); const q = e.getBoundingClientRect(); return [q.x + q.width / 2, q.y + q.height / 2]; }, t); if (!r) { console.log('MISS', t); return; } await p.mouse.click(r[0], r[1]); await p.waitForTimeout(1500); };
  await p.evaluate(() => __app.go('pubsetup')); await p.waitForTimeout(2500); await shot(); console.log(0, await btns());
  for (const t of (process.argv[2] || '').split('|').filter(Boolean)) { if (t.startsWith('type')) { const [k, v] = [+t[4], t.slice(6)]; await p.locator('input').nth(k).fill(v); await p.waitForTimeout(600); } else if (t.startsWith('js:')) { await p.evaluate((t) => [...document.querySelectorAll('button')].find(b => (b.innerText || '').includes(t)).click(), t.slice(3)); await p.waitForTimeout(1500); } else if (t.startsWith('scroll')) { await p.mouse.move(236, 500); await p.mouse.wheel(0, 500); await p.waitForTimeout(900);} else await tapT(t); await shot(); console.log(i - 1, t, '::', await btns()); }
  await b.close();
})();
