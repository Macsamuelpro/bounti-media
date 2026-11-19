# Live prototype recordings for UGC inserts

The phone screens in the UGC edits are real interactions with the Bounti design prototype
(`Bounti/docs/design/export`), not screenshots.

1. Serve the export: `cd Bounti/docs/design/export && python3 -m http.server 8765 --bind 127.0.0.1`
2. Record: `node rec.js <name>` for each name in `recs.js` (Playwright, CDP screencast at real time, taps logged).
   The shell is drawn at scale 2 in a 944x1972 viewport. Linked accounts are set through the app's own `connected` state.
3. Convert: `python3 live.py <name>` gives `rec/<name>.mp4` (24 fps, screen crop, touch rings at taps, yuv420p).
4. Copy `rec/<name>.mp4` and the `<name>.json` (end, events, crop) into `scratchpad/ugc/live/`.

Recordings: browse_feed, find_claim (steps sheet, check, +25 pending), missions_detail, trend_rules,
my_hunts, dashboard, house, signup, partner_create (stops before any pricing screen: partner prices never shown).
