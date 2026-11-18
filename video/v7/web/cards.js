const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 4 })).newPage();
  await p.goto('https://earnbounti.com/', { waitUntil: 'networkidle' });
  await p.addStyleTag({ content: 'header, nav, [class*=sticky], [class*=Sticky] { position: static !important; } ' });
  await p.evaluate(() => { document.querySelectorAll('*').forEach(e => { const s = getComputedStyle(e); if (s.position === 'fixed' || s.position === 'sticky') e.style.position = 'static'; }); });
  const wanted = ['Link your accounts', 'Follow counted', 'Cash out to', 'People you brought', 'Your wallet', 'Like a video', 'Follow Bounty', 'every tap counts', 'go get it', 'Lagos Nights'];
  for (const w of wanted) {
    const h = await p.evaluateHandle((txt) => {
      const all = Array.from(document.querySelectorAll('body *')).filter(e => e.childElementCount === 0 && e.textContent.trim().startsWith(txt));
      if (!all.length) return null;
      let e = all[0];
      for (let i = 0; i < 8 && e.parentElement; i++) {
        const s = getComputedStyle(e); const r = e.getBoundingClientRect();
        if ((s.borderRadius !== '0px' && (s.backgroundColor !== 'rgba(0, 0, 0, 0)' || s.boxShadow !== 'none')) && r.width > 180) return e;
        e = e.parentElement;
      }
      return e;
    }, w);
    const el = h.asElement();
    if (!el) { console.log('missing', w); continue; }
    await el.scrollIntoViewIfNeeded(); await p.waitForTimeout(400);
    const box = await el.boundingBox();
    await el.screenshot({ path: 'card_' + w.replace(/\W+/g, '_') + '.png', omitBackground: true });
    console.log('ok', w, Math.round(box.width), Math.round(box.height));
  }
  await b.close();
})();
