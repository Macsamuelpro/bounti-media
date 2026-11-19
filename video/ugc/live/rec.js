// Record a live interaction with the Bounti design prototype as a real-time frame sequence.
// usage: node rec.js <name>   (steps come from recs.js)
const fs = require('fs');
const { open, exposeApp } = require('./shell');
const RECS = require('./recs');
const name = process.argv[2]; const R = RECS[name]; if (!R) throw new Error('no rec ' + name);
(async () => {
  const { b, ctx, p } = await open(R.file || 'Bounti', R.view || {});
  await exposeApp(p);
  if (R.prep) await R.prep(p);
  const dir = 'rec/' + name; fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  const cdp = await ctx.newCDPSession(p);
  const frames = []; let n = 0; let t0 = null;
  cdp.on('Page.screencastFrame', async (f) => {
    const ts = f.metadata.timestamp; if (t0 === null) t0 = ts;
    const fn = `${dir}/f${String(n++).padStart(5, '0')}.jpg`;
    fs.writeFileSync(fn, Buffer.from(f.data, 'base64')); frames.push([+(ts - t0).toFixed(4), fn]);
    try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch (e) {}
  });
  const W = (R.view && R.view.W) || 472, H = (R.view && R.view.H) || 986, dsf = (R.view && R.view.dsf) || 2;
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 93, maxWidth: W * dsf, maxHeight: H * dsf, everyNthFrame: 1 });
  const tStart = Date.now(); const ev = [];
  const now = () => (Date.now() - tStart) / 1000;
  const api = {
    p, wait: (ms) => p.waitForTimeout(ms),
    tap: async (x, y, hold = 110) => { await p.mouse.move(x, y); ev.push({ t: now(), x, y, kind: 'tap' }); await p.mouse.down(); await p.waitForTimeout(hold); await p.mouse.up(); },
    // smooth finger-like scroll: eased wheel steps
    scroll: async (dy, ms = 700, x = 236, y = 560) => { await p.mouse.move(x, y); ev.push({ t: now(), x, y, kind: 'swipe', dy, ms }); const steps = Math.max(6, Math.round(ms / 16)); let done = 0; for (let i = 1; i <= steps; i++) { const e = 1 - Math.pow(1 - i / steps, 3); const tgt = Math.round(dy * e); await p.mouse.wheel(0, tgt - done); done = tgt; await p.waitForTimeout(ms / steps); } },
    flick: async (dy = 700, x = 472, y = 1300) => { await p.mouse.move(x, y); ev.push({ t: now(), x, y, kind: 'swipe', dy }); await p.mouse.wheel(0, dy); },
    js: (f, a) => p.evaluate(f, a),
    tapEl: async (txt, hold = 110) => { const r = await p.evaluate((t) => { const e = [...document.querySelectorAll('button')].find(b => { const q = b.getBoundingClientRect(); return ((b.innerText || '') + ' ' + (b.getAttribute('aria-label') || '')).includes(t) && q.width > 0 && q.y > 0 && q.y < innerHeight; }); if (!e) return null; const q = e.getBoundingClientRect(); return [q.x + q.width / 2, q.y + q.height / 2]; }, txt); if (!r) throw new Error('no button ' + txt); await api.tap(r[0], r[1], hold); }, mark: (label) => ev.push({ t: now(), kind: 'mark', label }),
  };
  try { p.__frame = await RECS.frameRect(p); } catch (e) {}
  await p.waitForTimeout(300);
  await R.run(api);
  await p.waitForTimeout(400);
  await cdp.send('Page.stopScreencast');
  // wall-clock offset between screencast timestamps and our event clock: first frame ~ tStart
  fs.writeFileSync(`${dir}/meta.json`, JSON.stringify({ frames, end: now(), events: ev, crop: R.crop || (p.__frame || null), dsf, W, H }, null, 0));
  console.log(name, 'frames', frames.length, 'dur', frames.length ? frames[frames.length - 1][0] : 0, 'events', ev.length);
  await b.close();
})();
