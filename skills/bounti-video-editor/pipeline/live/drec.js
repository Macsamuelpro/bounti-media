// Desktop live recordings (1440x900 design canvas). usage: node drec.js <name>
const fs = require('fs'); const { chromium } = require('playwright');
const R = {
  d_landing: { file: 'Landing Desktop', run: async (a) => { await a.wait(1800); await a.scroll(700, 2600); await a.wait(900); await a.scroll(-700, 1800); await a.wait(600); } },
  d_feed: { file: 'DeskFeed', run: async (a) => { await a.wait(1200); await a.hover(1215, 300); await a.wait(700); await a.flick(800, 620, 520); await a.wait(1500); await a.flick(800, 620, 520); await a.wait(1500); await a.hover(1370, 330); await a.wait(1500); } },
  d_missions: { file: 'DeskMissions', run: async (a) => { await a.wait(1200); await a.hover(1650, 205); await a.wait(800); await a.scroll(500, 1800, 900, 600); await a.wait(800); await a.hover(1050, 470); await a.wait(1200); await a.scroll(-500, 1500, 900, 600); await a.wait(800); } },
  d_signup: { file: 'Bounti Desktop', run: async (a) => { await a.wait(1000); await a.click(690, 240); await a.p.keyboard.type('amaka.hunts', { delay: 70 }); await a.click(690, 300); await a.p.keyboard.type('amaka@mail.com', { delay: 45 }); await a.wait(900); } },
};
const name = process.argv[2]; const D = R[name];
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1440, height: 900 } });
  await ctx.route(/unpkg\.com/, r => r.continue({ url: r.request().url().replace('https://unpkg.com/', 'https://cdn.jsdelivr.net/npm/') }));
  const p = await ctx.newPage(); await p.goto('http://127.0.0.1:8765/' + encodeURIComponent(D.file + '.dc.html'), { waitUntil: 'networkidle' }); await p.waitForTimeout(3500);
  const dir = 'rec/' + name; fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  const cdp = await ctx.newCDPSession(p); const frames = []; let n = 0, t0 = null;
  cdp.on('Page.screencastFrame', async (f) => { const ts = f.metadata.timestamp; if (t0 === null) t0 = ts; const fn = `${dir}/f${String(n++).padStart(5, '0')}.jpg`; fs.writeFileSync(fn, Buffer.from(f.data, 'base64')); frames.push([+(ts - t0).toFixed(4), fn]); try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch (e) {} });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 93, maxWidth: 1440, maxHeight: 900 });
  const tS = Date.now(), ev = [], now = () => (Date.now() - tS) / 1000;
  const a = { p, wait: (ms) => p.waitForTimeout(ms),
    hover: async (x, y) => { const s = 18; const from = await p.evaluate(() => [innerWidth / 2, innerHeight / 2]); for (let i = 1; i <= s; i++) { await p.mouse.move(from[0] + (x - from[0]) * i / s, from[1] + (y - from[1]) * i / s); await p.waitForTimeout(16); } ev.push({ t: now(), x, y, kind: 'hover' }); },
    click: async (x, y) => { await p.mouse.move(x, y); ev.push({ t: now(), x, y, kind: 'tap' }); await p.mouse.down(); await p.waitForTimeout(90); await p.mouse.up(); await p.waitForTimeout(300); },
    scroll: async (dy, ms = 1500, x = 720, y = 450) => { await p.mouse.move(x, y); const st = Math.max(8, Math.round(ms / 25)); let done = 0; for (let i = 1; i <= st; i++) { const e = 1 - Math.pow(1 - i / st, 3); const tg = Math.round(dy * e); await p.mouse.wheel(0, tg - done); done = tg; await p.waitForTimeout(ms / st); } },
    flick: async (dy, x, y) => { await p.mouse.move(x, y); ev.push({ t: now(), x, y, kind: 'swipe' }); await p.mouse.wheel(0, dy); } };
  await D.run(a); await p.waitForTimeout(300); await cdp.send('Page.stopScreencast');
  fs.writeFileSync(`${dir}/meta.json`, JSON.stringify({ frames, end: now(), events: ev, crop: [0, 0, 1440, 900] }));
  console.log(name, frames.length, 'frames', now().toFixed(1), 's'); await b.close();
})();
