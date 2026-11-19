"""Shot lists for the six launch films. Shots start at (line index, seconds into that line), snapped to the music beat.
Poses: x, y as frame fractions, s scale, yaw/pitch/roll degrees, z depth px. Each layout has an H (16:9) and V (9:16) version."""
def K(*pairs): return list(pairs)
def hero(rec, head, move="right", spd=1.0, explode=None, bg="paper", sfx=()):
    yaw0 = {"right": -34, "left": 34, "orbit": 38, "rise": -18, "flat": -10}[move]
    H = dict(rec=rec, spd=spd, keys=K((0, dict(x=1.15 if move == "right" else (-0.15 if move == "left" else 0.66), y=0.52 if move != "rise" else 1.25, s=0.86, yaw=yaw0, pitch=8 if move != "flat" else 52, roll=-4)),
                                      (0.35 if move != "orbit" else 0.0, dict(x=0.66, y=0.52, s=0.88, yaw=-16, pitch=4, roll=-2)),
                                      (1, dict(x=0.65, y=0.51, s=0.93, yaw=-8 if move != "orbit" else -30, pitch=2, roll=0))))
    V = dict(rec=rec, spd=spd, keys=K((0, dict(x=1.4 if move == "right" else (-0.4 if move == "left" else 0.5), y=0.60 if move != "rise" else 1.3, s=0.98, yaw=yaw0, pitch=8 if move != "flat" else 52, roll=-4)),
                                      (0.35 if move != "orbit" else 0.0, dict(x=0.5, y=0.60, s=1.0, yaw=-14, pitch=4, roll=-2)),
                                      (1, dict(x=0.5, y=0.59, s=1.06, yaw=-6 if move != "orbit" else -28, pitch=2, roll=0))))
    if explode: H["explode"] = explode; V["explode"] = explode
    return dict(kind="phones", bg=bg, phones=[H], phones_v=[V], head=dict(lines=head, x=0.27, y=0.5), head_v=dict(lines=head, y=0.15), sfx=list(sfx))
def trio(recs, head, bg="paper"):
    a, b, c = recs
    H = [dict(rec=a, keys=K((0, dict(x=0.5, y=0.54, s=0.70, yaw=0, z=300)), (0.4, dict(x=0.28, y=0.53, s=0.72, yaw=26, z=220)), (1, dict(x=0.27, y=0.53, s=0.74, yaw=22, z=200))), z=200),
         dict(rec=c, keys=K((0, dict(x=0.5, y=0.54, s=0.70, yaw=0, z=300)), (0.4, dict(x=0.72, y=0.53, s=0.72, yaw=-26, z=220)), (1, dict(x=0.73, y=0.53, s=0.74, yaw=-22, z=200))), z=200),
         dict(rec=b, keys=K((0, dict(x=0.5, y=0.62, s=0.76, yaw=0, pitch=14, z=0)), (0.4, dict(x=0.5, y=0.55, s=0.80, yaw=0, pitch=4)), (1, dict(x=0.5, y=0.54, s=0.84, yaw=0, pitch=2))), z=0)]
    V = [dict(rec=a, keys=K((0, dict(x=0.5, y=0.62, s=0.8, z=300)), (0.4, dict(x=0.17, y=0.6, s=0.82, yaw=30, z=320)), (1, dict(x=0.16, y=0.6, s=0.84, yaw=26, z=300))), z=300),
         dict(rec=c, keys=K((0, dict(x=0.5, y=0.62, s=0.8, z=300)), (0.4, dict(x=0.83, y=0.6, s=0.82, yaw=-30, z=320)), (1, dict(x=0.84, y=0.6, s=0.84, yaw=-26, z=300))), z=300),
         dict(rec=b, keys=K((0, dict(x=0.5, y=0.68, s=0.86, pitch=14)), (0.4, dict(x=0.5, y=0.61, s=0.92, pitch=4)), (1, dict(x=0.5, y=0.6, s=0.96, pitch=2))), z=0)]
    return dict(kind="phones", bg=bg, phones=H, phones_v=V, head=dict(lines=head, x=0.5, y=0.1), head_v=dict(lines=head, y=0.12))
def duo(lap, ph, head, bg="paper"):
    return dict(kind="duo", bg=bg,
        laptop=dict(rec=lap, keys=K((0, dict(x=0.30, y=0.60, s=0.92, yaw=30, pitch=-16, z=200)), (0.45, dict(x=0.40, y=0.56, s=1.0, yaw=16, pitch=-14)), (1, dict(x=0.41, y=0.55, s=1.05, yaw=10, pitch=-12)))),
        phone=dict(rec=ph, keys=K((0, dict(x=1.1, y=0.66, s=0.64, yaw=-30, roll=-6)), (0.4, dict(x=0.79, y=0.62, s=0.66, yaw=-16, roll=-2, z=-80)), (1, dict(x=0.78, y=0.61, s=0.68, yaw=-10, z=-100)))),
        laptop_v=dict(rec=lap, keys=K((0, dict(x=0.5, y=0.44, s=0.82, yaw=26, pitch=-16, z=200)), (0.45, dict(x=0.45, y=0.41, s=0.88, yaw=14, pitch=-14)), (1, dict(x=0.44, y=0.40, s=0.92, yaw=8, pitch=-12)))),
        phone_v=dict(rec=ph, keys=K((0, dict(x=1.3, y=0.70, s=0.70, yaw=-30, roll=-6)), (0.4, dict(x=0.73, y=0.68, s=0.72, yaw=-16, z=-80)), (1, dict(x=0.72, y=0.67, s=0.74, yaw=-10, z=-100)))),
        head=dict(lines=head, x=0.5, y=0.1), head_v=dict(lines=head, y=0.13))
def T(lines, bg="ink", **k): return dict(kind="type", lines=lines, bg=bg, **k)
def LOGO(sub, url, bg="paper"): return dict(kind="logo", sub=sub, url=url, bg=bg, sfx=[(0.05, "sting-minimal-short", -8)])
def at(li, off, shot, tr="whip", **k): d = dict(shot); d.update(at=(li, off), tr=tr, **k); return d
FILMS = {}
# ---------------- HUNTERS ----------------
FILMS["H1-No-Catch"] = dict(music="hunter", reveal_line=2, lead=0.35, gaps={1: 0.45, 2: 0.5}, shots=[
 at(0, 0.0, T(["Another app that", "pays you to *tap*?"], "paper"), "cut"),
 at(0, 2.9, T(["*Sure.*"], "ink", size=260), "cut"),
 at(1, 0.0, T(["Except this one", "*checks* the work."], "ink"), "cut"),
 at(1, 2.9, T(["And actually", "*pays*."], "ink", size=200), "cut"),
 at(2, 0.0, LOGO("", ""), "zoom"),
 at(3, 0.0, duo("d_feed", ("browse_feed", 0.8, 7.0), ["Follow. Watch. *Join.*"])),
 at(3, 3.2, trio([("browse_feed", 2.8, 3.6), ("browse_feed", 4.4, 5.6), ("browse_feed", 6.2, 7.4)], ["The small things", "you *already* do."])),
 at(3, 6.0, hero(("find_claim", 12.6, 15.6), ["A reward on", "*every* one."], "orbit")),
 at(4, 0.0, hero(("find_claim", 4.4, 7.6), ["Every bounty says", "*exactly* what to do."], "right", explode=(1.0, 0.8))),
 at(4, 3.4, hero(("find_claim", 7.4, 12.8), ["You do it.", "We *check* it."], "left", spd=1.3)),
 at(4, 5.6, hero(("find_claim", 12.9, 15.8), ["Your reward", "*lands*."], "rise"), sfx=[(0.9, "money-coin-drop", -12)]),
 at(5, 0.0, T(["No deposits.", "No bets.", "Nothing to buy."], "ink", stagger=0.85, size=150), "cut"),
 at(5, 2.85, T(["*Ever.*"], "paper", size=260), "cut"),
 at(6, 0.0, duo("d_landing", ("dashboard", 0.8, 8.0), ["Cash out when", "*you're* ready."])),
 at(7, 0.0, LOGO("Simple tasks. Real rewards.", "earnbounti.com"), "zoom"),
])
FILMS["H2-Your-Phone"] = dict(music="hunter", reveal_line=3, lead=0.5, gaps={0: 0.35, 2: 0.55}, shots=[
 at(0, 0.0, T(["Quick question."], "paper", size=170), "cut"),
 at(1, 0.0, T(["What did your phone", "pay you last *month*?"], "ink"), "cut"),
 at(2, 0.0, T(["*Exactly.*"], "paper", size=240), "cut"),
 at(3, 0.0, LOGO("", ""), "zoom"),
 at(3, 1.0, hero(("browse_feed", 0.6, 8.6), ["Your scroll,", "now *rewarded*."], "right", spd=1.2)),
 at(3, 4.2, hero(("find_claim", 4.6, 15.6), ["Claim in", "*seconds*."], "orbit", spd=2.2), sfx=[(3.4, "money-coin-drop", -12)]),
 at(4, 0.0, duo("d_missions", ("missions_detail", 0.4, 6.4), ["Want *bigger*", "bounties?"])),
 at(4, 2.6, hero(("missions_detail", 10.4, 16.0), ["Install. Sign up.", "Level up. *Get paid.*"], "left")),
 at(5, 0.0, trio([("house", 1.2, 4.0), ("my_hunts", 1.2, 6.0), ("dashboard", 1.0, 4.0)], ["Bring your *crew*."])),
 at(5, 3.0, hero(("my_hunts", 1.0, 9.0), ["Keep the", "*streak* alive."], "rise")),
 at(6, 0.0, T(["Your phone.", "*Real* money."], "ink", size=190), "cut"),
 at(7, 0.0, LOGO("Start today.", "earnbounti.com"), "zoom"),
])
# ---------------- PARTNERS ----------------
FILMS["P1-Real-People"] = dict(music="partner", reveal_line=2, lead=0.4, gaps={0: 0.3, 1: 0.55}, shots=[
 at(0, 0.0, T(["*50,000* people", "saw your ad."], "paper"), "cut"),
 at(0, 2.0, T(["Lovely."], "ink", size=220), "cut"),
 at(1, 0.0, T(["How many", "*did* anything?"], "paper"), "cut"),
 at(2, 0.0, LOGO("Bounti Partners", ""), "zoom"),
 at(2, 1.8, duo("d_feed", ("browse_feed", 0.8, 7.5), ["*Real* people", "behind your brand."])),
 at(2, 5.0, hero(("partner_create", 3.05, 7.4), ["You choose", "the *action*."], "right")),
 at(3, 0.0, hero(("partner_create", 6.0, 13.4), ["Add your link.", "Go *live*."], "left", spd=1.6)),
 at(4, 0.0, hero(("find_claim", 7.4, 12.8), ["Every action", "is *checked*."], "orbit", spd=1.3)),
 at(4, 2.2, T(["Doesn't pass?", "You're *not charged*."], "ink", size=140), "cut"),
 at(5, 0.0, T(["Follows drop off?", "*Replaced free*", "for 30 days."], "paper", size=140, stagger=0.45), "cut"),
 at(6, 0.0, T(["Real people.", "Real actions.", "Real *growth*."], "ink", stagger=0.85, size=160), "cut"),
 at(7, 0.0, LOGO("Bounti Partners", "partners.earnbounti.com"), "zoom"),
])
FILMS["P2-Pay-For-Results"] = dict(music="partner", reveal_line=1, lead=0.4, gaps={0: 0.4, 1: 0.45}, shots=[
 at(0, 0.0, T(["What if you only paid", "for what *happened*?"], "paper"), "cut"),
 at(1, 0.0, T(["Not impressions.", "Not reach.", "*Actions.*"], "ink", stagger=0.95, size=170), "cut"),
 at(2, 0.0, trio([("partner_create", 3.05, 4.8), ("partner_create", 4.4, 7.4), ("browse_feed", 2.6, 6.6)], ["Every *goal*,", "one place."])),
 at(2, 4.2, duo("d_missions", ("partner_create", 4.0, 13.4), ["Leads. Installs.", "*Conversions.*"])),
 at(3, 0.0, hero(("browse_feed", 0.6, 8.6), ["In front of", "*real* people."], "right", spd=1.3)),
 at(3, 2.8, hero(("find_claim", 7.4, 15.4), ["Every action", "*checked*."], "left", spd=1.6), sfx=[(4.0, "money-coin-drop", -13)]),
 at(4, 0.0, T(["One clear price", "per action.", "*Nothing hidden.*"], "ink", stagger=0.6, size=150), "cut"),
 at(5, 0.0, T(["Real business", "*growth*."], "paper", size=200), "cut"),
 at(6, 0.0, LOGO("Bounti Partners", "partners.earnbounti.com"), "zoom"),
])
# ---------------- PUBLISHERS ----------------
FILMS["U1-The-Wall"] = dict(music="publisher", reveal_line=2, lead=0.4, gaps={0: 0.3, 1: 0.55}, shots=[
 at(0, 0.0, T(["Coins. Gems.", "*Points.*"], "paper", size=190), "cut"),
 at(1, 0.0, T(["What if every reward", "*earned you* money?"], "ink"), "cut"),
 at(2, 0.0, LOGO("The Bounti wall", ""), "zoom"),
 at(2, 1.9, hero(("pub_wall", 0.6, 4.4), ["Right inside", "*your* app."], "rise")),
 at(3, 0.0, hero(("pub_wall", 3.6, 8.6), ["Real bounties.", "*Your* reward."], "orbit")),
 at(3, 3.6, trio([("pub_wall", 4.0, 6.0), ("pub_wall", 4.6, 8.6), ("pub_wall", 5.2, 8.6)], ["They never", "*leave* your app."])),
 at(4, 0.0, T(["Bounti pays you", "for *every* bounty", "they complete."], "ink", stagger=0.5, size=140), "cut"),
 at(5, 0.0, T(["Your users stay.", "*You earn.*"], "paper", stagger=0.8, size=180), "cut"),
 at(6, 0.0, LOGO("Bounti for publishers", "partners.earnbounti.com"), "zoom"),
])
FILMS["U2-Easy-Setup"] = dict(music="publisher", reveal_line=1, lead=0.4, gaps={0: 0.5, 1: 0.45}, shots=[
 at(0, 0.0, T(["Quick and painless", "integrations."], "paper"), "cut"),
 at(0, 2.7, T(["Said *nobody*.", "Ever."], "ink", stagger=0.6, size=190), "cut"),
 at(1, 0.0, T(["This one", "*actually* is."], "paper", size=190), "cut"),
 at(2, 0.0, dict(hero(("pub_setup", 0.6, 4.4), ["Name your *app*."], "right"), crop_top=True)),
 at(2, 3.0, T(["Coins. Gems. Points.", "*Your call.*"], "paper", stagger=0.5, size=150), "cut"),
 at(3, 0.0, hero(("pub_setup", 7.7, 11.5), ["Ready-made wall,", "or your *own* screens."], "left")),
 at(4, 0.0, hero(("pub_wall", 0.6, 4.6), ["One link.", "*You're set.*"], "orbit")),
 at(5, 0.0, T(["Your users earn.", "You earn.", "*Every time.*"], "ink", stagger=0.75, size=160), "cut"),
 at(6, 0.0, LOGO("Bounti for publishers", "partners.earnbounti.com"), "zoom"),
])
