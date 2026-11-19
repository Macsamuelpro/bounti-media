const { open, exposeApp } = require('./shell'); const R = require('./recs');
(async () => { const { b, p } = await open('Bounti', R.V); await exposeApp(p); await R.boot(p, 'feed'); console.log(await R.frameRect(p));
 await p.screenshot({ path: 'ex_s2_0.png' }); await R.swipeTo(p, 1); await p.screenshot({ path: 'ex_s2_1.png' }); await b.close(); })();
