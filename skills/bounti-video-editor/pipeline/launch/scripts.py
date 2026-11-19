"""Bounti launch videos: six scripts (2 hunter, 2 partner, 2 publisher). Copy comes from the design export
(docs/design/export) wherever possible. No prices, margins or partner costs are shown or said.
Scene kinds: words (kinetic type, *word* = gold highlight), icons, phone (live prototype recording), logo (end card).
Recording specs are (recording, from_s, to_s) from scratchpad/ugc/live."""
HUNTER_URL = "earnbounti.com"; PARTNER_URL = "partners.earnbounti.com"
V = {}
V["H1-Simple-Tasks"] = dict(voice="af_heart", music="City Sunshine", beats=[
 dict(vo="Meet Bounti.", scene=dict(kind="logo", sub="")),
 dict(vo="Simple tasks. Real rewards.", scene=dict(kind="words", text="Simple tasks.\n*Real* rewards.", bg="paper")),
 dict(vo="Like, follow, comment, share and more.", scene=dict(kind="icons", items=[("heart", "Like"), ("user-plus", "Follow"), ("message-circle", "Comment"), ("share-2", "Share")], bg="ink")),
 dict(vo="Swipe through bounties made for you.", scene=dict(kind="phone", rec=[("browse_feed", 0.8, 7.2)], text="Swipe through\n*bounties*.")),
 dict(vo="Pick one, follow the steps, and we check it for you.", scene=dict(kind="phone", rec=[("find_claim", 4.6, 9.4)], text="Follow the\n*steps*.")),
 dict(vo="Your reward lands after the last checks.", scene=dict(kind="phone", rec=[("find_claim", 12.9, 15.8)], text="Reward\n*lands*.", zoom=(0.86, 1.35))),
 dict(vo="Do the things you already do, and get paid for it.", scene=dict(kind="words", text="Do what you\nalready do.\nGet *paid*.", bg="paper")),
 dict(vo="Bounti. Start earning at earnbounti dot com.", scene=dict(kind="logo", sub="Simple tasks. Real rewards.", url=HUNTER_URL)),
])
V["H2-Bigger-Bounties"] = dict(voice="am_fenrir", music="Beat One", beats=[
 dict(vo="Bounti is here.", scene=dict(kind="logo", sub="")),
 dict(vo="Want bigger bounties?", scene=dict(kind="words", text="Want *bigger*\nbounties?", bg="ink")),
 dict(vo="Missions. Install, sign up, level up, then get paid.", scene=dict(kind="phone", rec=[("missions_detail", 0.4, 6.5)], text="*Missions*.")),
 dict(vo="Every mission shows you how it works, step by step.", scene=dict(kind="phone", rec=[("missions_detail", 10.4, 16.0)], text="Step by\n*step*.")),
 dict(vo="Then track every hunt, from act now to being checked.", scene=dict(kind="phone", rec=[("my_hunts", 0.6, 9.0)], text="Track every\n*hunt*.")),
 dict(vo="Your phone. Real money.", scene=dict(kind="words", text="Your phone.\n*Real* money.", bg="paper")),
 dict(vo="Bounti. Get it at earnbounti dot com.", scene=dict(kind="logo", sub="Bigger bounties.", url=HUNTER_URL)),
])
V["P1-Real-People"] = dict(voice="am_michael", music="Advertime", beats=[
 dict(vo="Your brand needs real people.", scene=dict(kind="words", text="Your brand needs\n*real* people.", bg="paper")),
 dict(vo="Not just impressions.", scene=dict(kind="words", text="Not just\nimpressions.", bg="ink", strike=True)),
 dict(vo="With Bounti Partners, you choose the result you want.", scene=dict(kind="icons", items=[("heart", "Engagement"), ("users", "Community"), ("mouse-pointer-click", "Traffic"), ("clipboard-list", "Leads"), ("smartphone", "App growth"), ("badge-check", "Conversions")], bg="paper")),
 dict(vo="Pick a goal, add your link, and choose who takes part.", scene=dict(kind="phone", rec=[("partner_create", 0.6, 13.4)], text="Set it up\nin *steps*.")),
 dict(vo="Then real people take action.", scene=dict(kind="phone", rec=[("browse_feed", 0.8, 6.0)], text="*Real* people.\nReal actions.")),
 dict(vo="Real people. Real actions. Real growth.", scene=dict(kind="words", text="Real people.\nReal actions.\nReal *growth*.", bg="ink")),
 dict(vo="Bounti Partners. Start at partners dot earnbounti dot com.", scene=dict(kind="logo", sub="Bounti Partners", url=PARTNER_URL)),
])
V["P2-Business-Growth"] = dict(voice="bm_george", music="Beat One", beats=[
 dict(vo="Engagement. Community. Traffic.", scene=dict(kind="icons", items=[("heart", "Engagement"), ("users", "Community"), ("mouse-pointer-click", "Traffic")], bg="paper")),
 dict(vo="Leads. App growth. Conversions.", scene=dict(kind="icons", items=[("clipboard-list", "Leads"), ("smartphone", "App growth"), ("badge-check", "Conversions")], bg="ink")),
 dict(vo="Run high-performing campaigns with Bounti.", scene=dict(kind="phone", rec=[("partner_create", 0.4, 6.4)], text="Run your\n*campaigns*.")),
 dict(vo="Get real people to take action.", scene=dict(kind="phone", rec=[("find_claim", 4.6, 9.2)], text="*Real* people\ntake action.")),
 dict(vo="And turn engagement into measurable results.", scene=dict(kind="words", text="Engagement into\n*measurable* results.", bg="paper")),
 dict(vo="Get real business growth with Bounti. Partners dot earnbounti dot com.", scene=dict(kind="logo", sub="Get real business growth.", url=PARTNER_URL)),
])
V["U1-Add-The-Wall"] = dict(voice="af_heart", music="Advertime", beats=[
 dict(vo="Got an app, a site or a game?", scene=dict(kind="icons", items=[("smartphone", "App"), ("globe", "Site"), ("gamepad-2", "Game")], bg="paper")),
 dict(vo="Add the Bounti wall.", scene=dict(kind="words", text="Add the\n*Bounti* wall.", bg="ink")),
 dict(vo="Your users open it right inside your app.", scene=dict(kind="phone", rec=[("pub_wall", 0.6, 4.2)], text="Inside *your*\napp.")),
 dict(vo="They complete real bounties and earn your own reward. Coins, gems, points, whatever you call it.", scene=dict(kind="phone", rec=[("pub_wall", 4.0, 8.6)], text="They earn\n*your* reward.")),
 dict(vo="And you earn every time a bounty is counted.", scene=dict(kind="words", text="You earn\nevery *time*.", bg="paper")),
 dict(vo="Bounti for publishers. Partners dot earnbounti dot com.", scene=dict(kind="logo", sub="Bounti for publishers", url=PARTNER_URL)),
])
V["U2-Set-Up"] = dict(voice="am_michael", music="City Sunshine", beats=[
 dict(vo="Turn your app into a place to earn.", scene=dict(kind="words", text="Turn your app\ninto a place\nto *earn*.", bg="paper")),
 dict(vo="Name your app.", scene=dict(kind="phone", rec=[("pub_setup", 0.6, 4.4)], text="Name your\n*app*.", zoom=(0.0, 1.16, 0.35, "static"))),
 dict(vo="Add your link.", scene=dict(kind="phone", rec=[("pub_setup", 4.4, 6.6)], text="Add your\n*link*.", zoom=(0.0, 1.16, 0.35, "static"))),
 dict(vo="Pick how bounties show, and open one link inside your app.", scene=dict(kind="phone", rec=[("pub_setup", 7.7, 11.5)], text="One *link*.")),
 dict(vo="Your users earn. You earn.", scene=dict(kind="phone", rec=[("pub_wall", 3.6, 8.6)], text="They earn.\nYou *earn*.")),
 dict(vo="Bounti for publishers. Partners dot earnbounti dot com.", scene=dict(kind="logo", sub="Bounti for publishers", url=PARTNER_URL)),
])
