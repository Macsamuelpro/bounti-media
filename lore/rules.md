# How the Most Wanted series runs

Read `canon.md` and `state.json` before doing anything. Channel: @earnbounti on X through Buffer (organization 69a8f39ac9f20bfac0447f37, channel 6ae27a622f1f5ed648047f89).

## 1. Each daily run

1. Pull this repo (`git pull`).
2. **Verdicts first.** For every drop in `state.json` with `verdict: null` that went out more than 48 hours ago, read its Buffer post with `includeMetrics: true` (metrics refresh daily and can lag up to 24 hours). If the BOUNTY REQUIRED target is met, the villain is CAPTURED. If it is not met and the drop is more than 72 hours old, the villain ESCAPED. Otherwise wait for a later run. Exception: the Counterfeit King always escapes.
3. **Decide whether today is a drop day** (section 2). If not, save `state.json` with `last_run` and stop.
4. **Plan the drop** (sections 3 and 4), write the thread (section 5), render the poster (section 6), commit and push, then schedule it in Buffer and record it in `state.json`.

## 2. Rhythm: it should feel alive, not mechanical

- On average one drop every 3 days, but vary the gap between 2 and 4 days.
- About one drop in five is a **double**: two villains on the same day in two different windows (for example a returning villain in the morning and a new one in the afternoon).
- Now and then (no more than once every 5 drops) a **cameo**: a villain from a higher tier is glimpsed briefly (a short rumour thread with their poster and a big bounty), then disappears again for several drops. This is how the bigger story is teased, like One Piece showing the Emperors early.
- Avoid Saturdays (the weakest day on X). Prefer Tuesday to Thursday for the biggest moments.
- **Time windows (Africa/Lagos):** 09:30 to 11:30, or 14:00 to 17:00 (this also catches US mornings). Pick a random minute; never exactly on :00 or :30. Schedule at least 20 minutes ahead of the run.

## 3. Who appears

- The story opens tier by tier. Tier 1 villains are introduced first, one at a time. Tier 2 opens only once at least three Tier 1 villains have had a verdict. Tier 3 opens once most of Tier 2 has, and so on. The Counterfeit King appears only as a cameo or rumour until Tier 4 is open.
- First four in order: Barnaby Vane, Silas Kroft, Morwenna Salt, Roderick Krieger. After that, choose the order that makes the best story.
- A villain who ESCAPED returns 2 to 4 drops later, angrier, with a new chapter. **Each return raises the bounty by 1.5 to 2 times**, within the tier's range in `canon.md` (an Emperor's and the King's can climb without limit).
- A CAPTURED villain does not get a new poster, but can be mentioned in other villains' stories (a captured villain can even break out much later, once, as a big moment).
- Several villains are on the run at once. Mix them: new faces, returning escapees, the occasional cameo.

## 4. BOUNTY REQUIRED

- Exactly one task per drop, on a metric Buffer reports for the post: likes (reactions), replies (comments), or reposts if Buffer reports them. Check what `includeMetrics` returns before choosing.
- Base it on real results. Take the median of that metric over the last 10 drops in `state.json` (first drops, with no history: 50 likes for Tier 1). Multiply by the tier: Tier 1 x0.8 to 1.2, Tier 2 x1.2 to 1.6, Tier 3 x1.6 to 2.2, Tier 4 x2.2 to 3, the King x3 to 4. Round to a tidy number (40, 75, 150, 1,000).
- A returning escapee gets a harder task than last time (about x1.3), sometimes on a different metric.
- Targets should be reachable with a push. If the last 5 drops all escaped, ease off; if the last 5 were all captured, push harder.

## 5. The thread

- **Tweet 1** (with the poster image), first line in capitals:
  `BOUNTY REQUIRED: <number> <LIKES|REPLIES|REPOSTS>`
  then a blank line, then 1 to 3 short lines: who, the bounty in AURA, the hook. A verdict or return says so here.
- **Tweets 2 to 4:** the story beat (section "How every arc is written" in `canon.md`). Short, vivid, one beat per tweet. Each tweet at most 270 characters.
- **Last tweet** ends with a nudge: report sightings in the replies, or what happens if the target is missed.
- **Voice:** Bounti's X voice: young, playful, global, confident. At most one emoji per tweet. No links. No hashtags. Never mention Bounti's internals, money amounts (only AURA), partners, or any real person, brand, platform or country. Never use em dashes.
- **Continuity:** every thread continues from that villain's `lore_so_far` and must not contradict `canon.md`. Before a villain's first arc and before each new beat, search the web for their One Piece parallel's story to understand it, then write our own version. Never copy One Piece names, places, lines or events.
- After posting, add any new facts to that villain's `lore_so_far` in `state.json`.

## 6. The poster

- Render: `python3 poster/render.py <villain-id> <bounty> <wanted|captured|escaped> posters/<YYYY-MM-DD>-<villain-id>-<n>.jpg` from the repo root (needs Pillow).
- Commit and push the poster before scheduling. The image URL is `https://raw.githubusercontent.com/Macsamuelpro/bounti-media/main/posters/<file>`.
- A verdict drop uses the CAPTURED or ESCAPED stamp on the villain's last bounty. A return drop uses `wanted` with the new bounty.

## 7. Scheduling in Buffer

`create_post` with `channelId` above, `schedulingType: automatic`, `mode: customScheduled`, `dueAt` in +01:00, `text` equal to tweet 1, and `metadata.twitter.thread` holding every tweet in order (tweet 1 with the poster in `assets`: `{ "image": { "url": "<raw url>", "metadata": { "altText": "Bounti wanted poster: <name>, <bounty> AURA" } } }`). Record the returned post ID in `state.json`.

If anything fails (render, push, Buffer), do not post half a drop: write the plan into `state.json` under `pending` with the error, and try again on the next run.
