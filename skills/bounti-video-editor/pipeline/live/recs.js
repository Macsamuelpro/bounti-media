// Live recordings of the Bounti design prototype (docs/design/export), one per narration beat.
// Shells render at scale 2 inside a 944x1972 viewport so frames are sharp. All actions are real clicks/scrolls.
const V = { W: 944, H: 1972, dsf: 1 };
const LINKED = { tiktok: true, instagram: true, youtube: true, snapchat: true };
const boot = async (p, screen, wait = 5500) => {
  await p.evaluate(([sc, L]) => { __app.fit = () => __app.setState({ scale: 2 }); __app.fit(); if (__app.skipSplash) { __app.skipSplash(); __app.setState({ connected: L }); } __app.go(sc); }, [screen, LINKED]);
  await p.waitForTimeout(wait);
};
const frameRect = (p) => p.evaluate(() => { const r = __app.frameRef.current.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); });
const visBtn = (p, t) => p.evaluate((t) => [...document.querySelectorAll('button')].some(b => { const q = b.getBoundingClientRect(); return (b.innerText || '').includes(t) && q.width > 0 && q.y > 0 && q.y < innerHeight; }), t);
const swipeTo = async (p, txt, max = 12) => { for (let i = 0; i < max; i++) { if (await visBtn(p, txt)) return i; await p.mouse.move(472, 1100); await p.mouse.wheel(0, 700); await p.waitForTimeout(1300); } throw new Error('card not found ' + txt); };
// visible swipes to a feed card, then claim it through the instructions sheet, live verification and reward
const findClaim = async (a, swipes = 3) => {
  for (let i = 0; i < swipes; i++) { await a.wait(i ? 1500 : 900); await a.flick(); }
  if (!(await visBtn(a.p, '+25'))) await swipeTo(a.p, '+25');
  await a.wait(900); await a.tapEl('+25'); await a.wait(2300); await a.tapEl("I've done it"); await a.wait(10000);
};
module.exports = {
  V, boot, frameRect, swipeTo,
  // swipe through the hunter feed: affiliate, watch, like, trend push
  browse_feed: { view: V, prep: (p) => boot(p, 'feed'), run: async (a) => { for (let i = 0; i < 4; i++) { await a.wait(i ? 1700 : 900); await a.flick(); } await a.wait(1800); } },
  // like bounty only (starts on the card)
  claim_like: { view: V, prep: async (p) => { await boot(p, 'feed'); await swipeTo(p, '+25'); }, run: async (a) => { await a.wait(900); await a.tapEl('+25'); await a.wait(2300); await a.tapEl("I've done it"); await a.wait(10000); } },
  // browse a few cards, pick the like bounty, follow the steps, verification, reward lands as pending
  find_claim: { view: V, prep: (p) => boot(p, 'feed'), run: (a) => findClaim(a, 2) },
  // missions list, then open the featured mission: how it works, reward, pending then withdrawable
  missions_detail: { view: V, prep: (p) => boot(p, 'missions'), run: async (a) => { await a.wait(900); await a.scroll(900, 1100, 472, 1300); await a.wait(700); await a.scroll(-900, 900, 472, 1300); await a.wait(600); await a.tapEl('Featured mission'); await a.wait(4500); } },
  // a trend push mission: the brief, the timer, the post ready to send, and what doesn't count
  trend_rules: { view: V, prep: (p) => boot(p, 'missions'), run: async (a) => { await a.wait(700); await a.scroll(520, 800, 472, 1300); await a.wait(500); await a.tapEl('Quote the Harmattan drop'); await a.wait(2600); await a.scroll(600, 1200, 472, 1500); await a.wait(3000); } },
  // My Hunts: act now, being checked, building up
  my_hunts: { view: V, prep: (p) => boot(p, 'feed'), run: async (a) => { await a.wait(700); await a.tapEl('My Hunts'); await a.wait(2200); await a.scroll(700, 1300, 472, 1200); await a.wait(1500); await a.scroll(700, 1300, 472, 1200); await a.wait(2000); } },
  // hunter dashboard (profile): balances, checking / confirmed / available
  dashboard: { view: V, prep: (p) => boot(p, 'feed'), run: async (a) => { await a.wait(600); await a.tapEl('Profile'); await a.wait(3000); await a.scroll(420, 1200, 472, 1200); await a.wait(2200); } },
  // the bounty house: drops, announcements, latest bounties
  house: { view: V, prep: (p) => boot(p, 'feed'), run: async (a) => { await a.wait(600); await a.tapEl('The Bounty House'); await a.wait(2400); await a.scroll(800, 1600, 472, 1200); await a.wait(1200); await a.scroll(800, 1600, 472, 1200); await a.wait(1800); } },
  // landing then sign up
  signup: { view: V, prep: (p) => boot(p, 'landing', 2500), run: async (a) => { await a.wait(1600); await a.tapEl('Start Earning'); await a.wait(3200); } },
  // partner creates a bounty: type, action, link, who takes part (stops before any pricing screen)
  partner_create: { file: 'Bounti Partners', view: V, prep: (p) => boot(p, 'home', 3000), run: async (a) => {
    await a.wait(900); await a.tapEl('Create a campaign'); await a.wait(1500); await a.tapEl('Engagement'); await a.wait(1400);
    await a.tapEl('Follow / Subscribe'); await a.wait(900);
    const inp = a.p.locator('input').first(); await inp.scrollIntoViewIfNeeded(); await a.wait(700);
    const bb = await inp.boundingBox(); await a.tap(bb.x + bb.width / 2, bb.y + bb.height / 2); await a.p.keyboard.type('instagram.com/zurifashion', { delay: 55 }); await a.wait(1800);
    await a.tapEl('Continue'); await a.wait(3000); } },
  // publisher: name the app, pick Game, add it, then choose how bounties show (scrolls past the reward amounts quickly)
  pub_setup: { file: 'Bounti Partners', view: V, prep: (p) => boot(p, 'pubsetup', 3000), run: async (a) => {
    await a.wait(800); const inp = a.p.locator('input').first(); const bb = await inp.boundingBox(); await a.tap(bb.x + bb.width / 2, bb.y + bb.height / 2);
    await a.p.keyboard.type('Kopa Quest', { delay: 70 }); await a.wait(500); await a.tapEl('Game'); await a.wait(500);
    const l = a.p.locator('input').nth(1); const lb = await l.boundingBox(); await a.tap(lb.x + lb.width / 2, lb.y + lb.height / 2); await a.p.keyboard.type('https://play.google.com/store/apps/kopaquest', { delay: 22 }); await a.wait(400);
    await a.tapEl('Add it'); await a.wait(1600); await a.reveal('Preview the wall', 1300); await a.wait(400); await a.tapEl('bounty wall'); await a.wait(2400); } },
  // publisher preview: the game, then the Bounti wall inside it
  pub_wall: { file: 'Bounti Partners', view: V, prep: async (p) => { await boot(p, 'pubsetup', 3000); await p.evaluate(() => [...document.querySelectorAll('button')].find(b => (b.innerText || '').includes('Preview the wall')).click()); await p.waitForTimeout(1500); },
    run: async (a) => { await a.wait(1200); await a.tapJs('Free'); await a.wait(2600); await a.scroll(300, 900, 472, 1300); await a.wait(2000); } },
};
