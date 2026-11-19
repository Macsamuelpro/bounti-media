"""Per-project edit plans for UGC 1-13. Pieces are (clip, piece_index[, display_text]). Inserts trigger on caption text."""
SCREENS = {  # name: (file relative to scratchpad, scroll start frac, scroll end frac)
 "home": ("v7/web/home_full.png", 0.0, 0.10), "missions": ("ugc/screens/tall_Missions.png", 0.0, 0.55),
 "bwall": ("ugc/screens/tall_BWall.png", 0.0, 0.30), "house": ("ugc/screens/tall_House.png", 0.0, 0.40),
 "mine": ("ugc/screens/tall_Mine.png", 0.04, 0.45), "feed": ("ugc/screens/Feed.png", 0.0, 0.0),
 "detail": ("ugc/screens/tall_Affiliate.png", 0.0, 0.30), "trend": ("ugc/screens/tall_Trend.png", 0.0, 0.12),
 "status": ("ugc/screens/tall_Affiliate.png", 0.33, 0.33), "profile": ("ugc/screens/tall_Profile.png", 0.0, 0.25),
 "splash": ("ugc/screens/Bounti.png", 0.0, 0.0), "link": ("ugc/screens/LinkFlow.png", 0.0, 0.0),
 "signup": ("v7/web/app_top.png", 0.0, 0.0),
}
P = {}
P["UGC1"] = dict(title="You Don't Need Followers", style="rounded", anim="pop", music="lofi", lead0=0.0,
 pieces=[("c1", 1, "You don't need thousands of followers to earn money online."), ("c1", 2, "You just need to know where to look."),
         ("c2", 0, "There's actually a platform called Bounti,"), ("c2", 1, "where businesses and brands put up tasks"), ("c2", 2, "and people like you can complete them to earn rewards."),
         ("c3", 0, "So you can browse through different bounties,"), ("c3", 1, "find something you're interested in,"), ("c3", 2, "follow the instructions, complete the task, and get rewarded when it's approved."),
         ("c4", 0, "And the interesting part?"), ("c4", 1, "You don't have to build an audience or become an influencer to get started."),
         ("c5", 0, "Head over to earnbounti.com,"), ("c5", 1, "create your account"), ("c5", 2, "and find your next bounty.")],
 hook=dict(kind="text", text="NO\nFOLLOWERS?", t0=0.9, t1=2.6),
 inserts=[dict(kind="logo", at="There's actually"), dict(kind="screen", at="where businesses", until="So you can browse", screen="home", layout="cutout"),
          dict(kind="screen", at="So you can browse", until="follow the instructions", screen="missions", layout="cutout"),
          dict(kind="screen", at="follow the instructions", until="And the interesting", screen="detail", layout="cutout"),
          dict(kind="url", at="Head over")],
 sfx=[("There's actually", "pop-medium-in"), ("follow the instructions", "click-mouse-medium"), ("Head over", "notification-success-ding-ding")])
P["UGC2"] = dict(title="The Curiosity Gap", style="bar_pop", anim="pop", music="beat",
 pieces=[("c1", 0, "What if I told you there's a platform"), ("c1", 1, "where you can earn money"), ("c1", 2, "just by completing simple tasks for brands?"),
         ("c2", 0, "Yeah, it's called Bounti."), ("c2", 1, "It's basically a marketplace where businesses post bounties,"), ("c2", 2, "and people complete those tasks in exchange for rewards."),
         ("c3", 0, "So for example,"), ("c3", 1, "you could find a bounty that interests you,"), ("c3", 2, "check what the brand needs,"), ("c3", 3, "complete the required action"), ("c3", 4, "and submit it for approval."),
         ("c4", 0, "And there are different opportunities to discover,", (0.22, 2.05)), ("c4", 1, "depending on what businesses and brands are looking for."),
         ("c5", 0, "So instead of just scrolling past opportunities,"), ("c5", 1, "head over to earnbounti.com"), ("c5", 2, "and explore what's available.")],
 hook=dict(kind="screen_open", screen="feed", dur=1.0),
 inserts=[dict(kind="logo", at="Yeah, it's called"), dict(kind="screen", at="you could find a bounty", until="check what the brand", screen="missions", layout="cutout"),
          dict(kind="screen", at="check what the brand", until="complete the required", screen="detail", layout="cutout"),
          dict(kind="screen", at="complete the required", until="And there are", screen="trend", layout="cutout", tap=0.7),
          dict(kind="screen", at="And there are", until="depending on", screen="bwall", layout="cutout"), dict(kind="url", at="head over")],
 sfx=[("Yeah, it's called", "pop-medium-in"), ("and submit it", "click-mouse-medium"), ("head over", "notification-success-ding-ding")])
P["UGC3"] = dict(title="Everyday Activities", style="underline", anim="fade", music="lofi", lead0=0.0,
 pieces=[("c1", 1, "Imagine getting rewarded for doing things that businesses and brands actually need people to do."),
         ("c2", 0, "That's actually the idea behind Bounti."), ("c2", 1, "It's a platform that connects businesses with people willing to complete specific tasks in exchange for rewards."),
         ("c3", 0, "And the process is pretty straightforward."), ("c3", 1, "You explore available bounties,"), ("c3", 2, "choose one,"), ("c3", 3, "check the requirements,"), ("c3", 4, "complete the task and submit it."),
         ("c4", 0, "So whether it's an online action,"), ("c4", 1, "a creative task"), ("c4", 2, "or another activity a brand needs done,"), ("c4", 3, "there's a whole world of opportunities to explore."),
         ("c5", 0, "Visit earnbounti.com and see what opportunities are available.")],
 hook=dict(kind="text", text="IMAGINE\nTHIS", t0=1.4, t1=2.9, punch=True),
 inserts=[dict(kind="logo", at="That's actually"), dict(kind="screen", at="You explore available", until="check the requirements", screen="missions", layout="cutout"),
          dict(kind="screen", at="check the requirements", until="So whether", screen="detail", layout="cutout", tap=0.8),
          dict(kind="screen", at="So whether", until="there's a whole", screen="bwall", layout="cutout"), dict(kind="url", at="Visit")],
 sfx=[("That's actually", "pop-medium-in"), ("choose one", "click-mouse-soft"), ("check the requirements", "click-mouse-soft"), ("complete the task", "click-mouse-soft"),
      ("there's a whole", "whoosh-medium-soft"), ("Visit", "notification-success-ding-ding")], whoosh0=True)
P["UGC4"] = dict(title="Let Me Show You", style="box_white", anim="slide_up", music="lofi", lead0=0.0,
 pieces=[("c1", 2, "I just found a platform where everyday people can earn rewards by completing tasks for businesses and brands. Let me show you."),
         ("c2", 0, "It's called Bounti,"), ("c2", 1, "and it's a marketplace that connects brands looking for specific actions"), ("c2", 2, "with people who are willing to complete them."),
         ("c3", 0, "Basically, you join as a hunter, explore the available bounties, pick one you like, follow the instructions and complete the task to receive its reward once approved."),
         ("c4", 0, "I like that you don't have to be an influencer or own a business to participate."), ("c4", 1, "You just need to find opportunities that work for you."),
         ("c5", 0, "So yeah, check out earnbounti.com."), ("c5", 1, "Create your account and see what's available.")],
 hook=dict(kind="text", text="I JUST\nFOUND THIS", t0=0.5, t1=2.2, punch=True),
 inserts=[dict(kind="logo", at="It's called Bounti"), dict(kind="screen", at="Basically, you join", until="I like that", screen="missions", layout="cutout", then=("detail", 0.55)),
          dict(kind="url", at="So yeah")],
 sfx=[("It's called Bounti", "pop-medium-in"), ("So yeah", "notification-success-ding-ding")])
P["UGC5"] = dict(title="How It Works (Tutorial)", style="box_black", anim="fade", music="lofi",
 pieces=[("c1", 0, "Let me show you how to find and complete a bounty on Bounti."), ("c1", 1, "First, you head over to Bounti and explore the available opportunities."),
         ("c2", 1, "When you find a bounty you're interested in,"), ("c2", 2, "open it"), ("c2", 3, "and take a look at the details."),
         ("c3", 0, "You'll see what the brand wants, the instructions you need to follow"), ("c3", 1, "and the reward attached to that particular task."), ("c3", 2, "If everything looks good, you can proceed to participate."),
         ("c4", 0, "Once you've completed the required action,"), ("c4", 1, "follow the submission process"), ("c4", 2, "and send it for verification."), ("c4", 3, "When your submission is approved, the reward follows."),
         ("c5", 0, "And that's basically how bounty hunting works on Bounti."), ("c5", 1, "Pretty straightforward, right?"), ("c5", 2, "Visit earnbounti.com to get started.")],
 hook=dict(kind="cutout_pop"),
 inserts=[dict(kind="screen", at="Let me show you", until="When you find", screen="missions", layout="cutout"),
          dict(kind="screen", at="When you find", until="If everything", screen="detail", layout="cutout", tap=0.3),
          dict(kind="screen", at="If everything", until="And that's basically", screen="trend", layout="cutout", tap=0.15, then=("status", 0.7)),
          dict(kind="url", at="Visit")],
 sfx=[("open it", "click-mouse-medium"), ("follow the submission", "click-mouse-medium"), ("and send it", "whoosh-medium-soft"), ("When your submission", "notification-success-ding-ding"), ("Visit", "tone-ding-mid")])
P["UGC6"] = dict(title="Storytime", style="highlighter", anim="word_by_word", music="lofi",
 pieces=[("c1", 0, "So I was scrolling through the internet one day"), ("c1", 1, "and I came across something I honestly found pretty interesting."), ("c1", 2, "It was this platform called..."), ("c1", 3, "Bounti."),
         ("c2", 0, "At first,"), ("c2", 1, "I wanted to understand what it was actually about."),
         ("c3", 0, "Turns out it's a platform where businesses and brands post different tasks"), ("c3", 1, "and people can participate in those tasks"), ("c3", 2, "in exchange for rewards."),
         ("c4", 0, "And I thought about it."), ("c4", 1, "There are so many businesses looking for people to engage with their products, content and services."),
         ("c5", 0, "Bounti basically creates a place where those opportunities can be discovered"), ("c5", 1, "by people willing to complete them."),
         ("c6", 0, "You can join as a hunter,"), ("c6", 1, "explore the available bounties"), ("c6", 2, "and find something that works for you."),
         ("c7", 0, "Anyway, that's how I discovered Bounti."), ("c7", 1, "I thought it was worth sharing."), ("c7", 2, "You can check it out at earnbounti.com.")],
 hook=dict(kind="text", text="STORYTIME", t0=0.15, t1=1.6, wobble=True),
 inserts=[dict(kind="logo", at="Bounti."), dict(kind="screen", at="Turns out", until="And I thought", screen="missions", layout="cutout"),
          dict(kind="screen", at="explore the available", until="Anyway", screen="bwall", layout="cutout"), dict(kind="url", at="You can check")],
 sfx=[("Bounti.", "pop-medium-in"), ("There are so many", "riser-1s-soft"), ("You can check", "notification-success-ding-ding")], whoosh0=True)
P["UGC7"] = dict(title="Problem / Solution", style="hormozi", anim="pop", music="beat",
 pieces=[("c1", 0, "Think about how much time you spend on social media every single day."), ("c1", 1, "Now think about what you actually get back from all that time."),
         ("c2", 0, "We scroll through posts,"), ("c2", 1, "watch videos,"), ("c2", 2, "engage with content"), ("c2", 3, "and interact with different brands every day."),
         ("c3", 0, "But what if there was a way to participate in activities that businesses actually need people to do"), ("c3", 1, "and get rewarded for completing them?"),
         ("c4", 0, "That's where Bounti comes in."), ("c4", 1, "It's a platform where businesses post bounties"), ("c4", 2, "and people can complete tasks for rewards."),
         ("c5", 0, "Instead of just being online,"), ("c5", 1, "you can explore opportunities to actually participate."), ("c5", 2, "Maybe it's time to make your time online a little more interesting."), ("c5", 3, "Check out earnbounti.com.")],
 hook=dict(kind="punch", t0=0.0),
 icons=[("We scroll", "smartphone"), ("watch videos", "play"), ("engage with", "heart"), ("and interact", "store")],
 inserts=[dict(kind="screen", at="That's where", until="Instead of just", screen="feed", layout="cutout", then=("missions", 0.35)), dict(kind="url", at="Check out")],
 sfx=[("That's where", "pop-medium-in"), ("Check out", "notification-success-ding-ding")])
P["UGC10"] = dict(title="First Impression", style="rounded", anim="pop", music="lofi",
 pieces=[("c1", 0, "Okay, so I've just discovered this platform called Bounti and I want to see what it's all about."),
         ("c2", 0, "Apparently, it's a platform where businesses post different tasks"), ("c2", 1, "and people can complete them to earn rewards."), ("c2", 2, "So let's have a look."),
         ("c3", 0, "Okay, this is the hunter dashboard."), ("c3", 1, "And here we have the available bounties."), ("c3", 2, "Let's open one."),
         ("c4", 0, "Oh, interesting. So you can actually see what the task requires, the instructions and the reward before participating."),
         ("c5", 0, "I like that you can browse through different opportunities and decide which ones make sense for you."),
         ("c6", 0, "Well, that's my first look at Bounti. I'm definitely interested in exploring more."), ("c6", 1, "You can check it out at earnbounti.com.")],
 hook=dict(kind="screen_open", screen="splash", dur=1.0),
 inserts=[dict(kind="screen", at="Okay, this is", until="And here we have", screen="profile", layout="cutout"),
          dict(kind="screen", at="And here we have", until="Oh, interesting", screen="missions", layout="cutout"),
          dict(kind="screen", at="Oh, interesting", until="I like that", screen="detail", layout="cutout"),
          dict(kind="screen", at="I like that", until="Well, that's", screen="bwall", layout="cutout"), dict(kind="url", at="You can check")],
 sfx=[("Okay, so I've", "whoosh-fast-medium"), ("Let's open one", "click-mouse-medium"), ("Oh, interesting", "pop-medium-in"), ("You can check", "notification-success-ding-ding")])
P["UGC11"] = dict(title="One-Day Challenge", style="bar_pop", anim="pop", music="beat", timer=True,
 pieces=[("c1", 0, "I'm giving myself one day to see how many bounties I can actually complete on Bounti."), ("c1", 1, "So here's the plan."),
         ("c2", 0, "I'm going to explore the available bounties,"), ("c2", 1, "find the ones I can realistically complete"), ("c2", 2, "and see how far I can get."), ("c2", 3, "First, I'm checking out what's available."),
         ("c3", 0, "Okay, I found a few interesting ones."), ("c3", 1, "Now I'm going through the requirements because I don't want to participate in something I can't properly complete."),
         ("c4", 0, "Let's get started."), ("c4", 1, "After completing the required tasks,"), ("c4", 2, "I'll submit my entries"), ("c4", 3, "and see which ones get approved."),
         ("c5", 0, "Well,"), ("c5", 1, "that's my little bounty challenge. I'll let you know how it goes."), ("c5", 2, "You can try exploring your own opportunities at earnbounti.com.")],
 hook=dict(kind="text", text="ONE DAY.\nHOW MANY\nBOUNTIES?", t0=0.0, t1=2.0),
 inserts=[dict(kind="screen", at="First, I'm checking", until="Now I'm going", screen="missions", layout="cutout"),
          dict(kind="screen", at="Now I'm going", until="Let's get started", screen="detail", layout="cutout"),
          dict(kind="screen", at="Let's get started", until="and see which", screen="trend", layout="cutout", tap=0.4),
          dict(kind="screen", at="and see which", until="Well,", screen="mine", layout="cutout"), dict(kind="url", at="You can try")],
 sfx=[("I'm giving", "whoosh-fast-hard"), ("Let's get started", "click-clap-firm"), ("You can try", "notification-success-ding-ding")])
P["UGC12"] = dict(title="Green-Screen Commentary", style="hormozi", anim="pop", music="beat", greenscreen="home",
 pieces=[("c1", 0, "Wait."), ("c1", 1, "Why are more people not talking about platforms that connect ordinary people with brands looking for help?"), ("c1", 2, "Look at this."),
         ("c2", 0, "This is Bounti."), ("c2", 1, "And the idea is actually quite interesting. Businesses and brands can create bounties for specific activities they need people to complete."),
         ("c3", 0, "Then people can join as hunters,"), ("c3", 1, "browse the opportunities"), ("c3", 2, "and participate in the ones they're interested in."),
         ("c4", 0, "So instead of businesses having to find every individual person themselves,"), ("c4", 1, "they have a platform where they can make these opportunities available."),
         ("c5", 0, "And for hunters,"), ("c5", 1, "it's a place to discover tasks and earn rewards for completing them."),
         ("c6", 0, "Honestly,"), ("c6", 1, "I think more people should know about this."), ("c6", 2, "Go to earnbounti.com and check it out.")],
 hook=dict(kind="none"), bg_switch=[("Then people can join", "missions"), ("And for hunters", "bwall")],
 inserts=[dict(kind="screen", at="they have a platform", until="And for hunters", screen="house", layout="full"), dict(kind="url", at="Go to")],
 sfx=[("Wait.", "whoosh-fast-medium"), ("Look at this", "pop-medium-in"), ("This is Bounti", "tone-ding-mid"), ("Go to", "notification-success-ding-ding")])
P["UGC13"] = dict(title="Friend-to-Friend", style="minimal", anim="fade", music="lofi", lead0=0.0,
 pieces=[("c1", 0, "If you're someone who spends a lot of time on your phone,"), ("c1", 1, "let me introduce you to something."), ("c1", 2, "It's called Bounti."),
         ("c2", 0, "Basically,"), ("c2", 1, "it's a platform where brands and businesses post tasks"), ("c2", 2, "that people can complete in exchange for rewards."),
         ("c3", 0, "You can join as a hunter,"), ("c3", 1, "browse through the available bounties"), ("c3", 2, "and choose the ones that interest you."),
         ("c4", 0, "And the cool thing is that you can actually see what each task requires"), ("c4", 1, "before you decide to participate."),
         ("c5", 0, "So you're not just randomly doing things, you're choosing specific opportunities."), ("c5", 1, "Anyway, I thought I'd share this with you. Check out earnbounti.com and see what's available.")],
 hook=dict(kind="text_small", text="LET ME PUT YOU ON.", t0=0.0, t1=1.8),
 inserts=[dict(kind="screen", at="It's called Bounti", until="Basically", screen="feed", layout="cutout"),
          dict(kind="screen", at="And the cool thing", until="So you're not", screen="detail", layout="cutout"), dict(kind="url", at="Anyway")],
 sfx=[("If you're someone", "swish-soft"), ("It's called Bounti", "pop-medium-in"), ("And the cool thing", "tone-ding-mid"), ("Anyway", "notification-success-ding-ding")])

# ---------------------------------------------------------------------------------------------
# Live inserts (Mac, 2026-11-19): fewer inserts, only where a line describes something on screen,
# and every phone shows the working Bounti prototype (docs/design/export) driven by real taps,
# recorded by live/rec.js. Specs are (recording, from_s, to_s) played back to back.
FIND_CLAIM = [("find_claim", 0.9, 6.9), ("find_claim", 7.4, 9.0), ("find_claim", 12.9, 15.4)]   # browse, open a like bounty, steps, check, reward pending
CLAIM_ONLY = [("find_claim", 4.6, 9.0), ("find_claim", 12.9, 15.6)]
BROWSE = [("browse_feed", 0.5, 8.7)]
REQS = [("trend_rules", 0.8, 13.4)]
def L(at, until, spec, coin=None, **k): return dict(kind="screen", at=at, until=until, live=spec, layout="cutout", coin=coin, **k)
P["UGC1"]["inserts"] = [dict(kind="logo", at="There's actually"), L("So you can browse", "And the interesting", FIND_CLAIM, 8.7), dict(kind="url", at="Head over")]
P["UGC1"]["sfx"] = [("There's actually", "pop-medium-in"), ("Head over", "notification-success-ding-ding")]
P["UGC2"]["hook"] = dict(kind="text", text="WHAT IF?", t0=0.2, t1=1.7, punch=True)
P["UGC2"]["inserts"] = [dict(kind="logo", at="Yeah, it's called"), L("you could find a bounty", "And there are", FIND_CLAIM, 8.7), dict(kind="url", at="head over")]
P["UGC2"]["sfx"] = [("Yeah, it's called", "pop-medium-in"), ("head over", "notification-success-ding-ding")]
P["UGC3"]["inserts"] = [dict(kind="logo", at="That's actually"), L("You explore available", "So whether", REQS), dict(kind="url", at="Visit")]
P["UGC3"]["sfx"] = [("That's actually", "pop-medium-in"), ("Visit", "notification-success-ding-ding")]
P["UGC4"]["inserts"] = [dict(kind="logo", at="It's called Bounti"), L("Basically, you join", "I like that", FIND_CLAIM, 8.7), dict(kind="url", at="So yeah")]
P["UGC4"]["sfx"] = [("It's called Bounti", "pop-medium-in"), ("So yeah", "notification-success-ding-ding")]
P["UGC5"]["inserts"] = [L("Let me show you", "When you find", BROWSE),
                        L("When you find", "If everything", [("missions_detail", 1.0, 4.0), ("missions_detail", 10.4, 16.0)]),
                        L("If everything", "And that's basically", CLAIM_ONLY, 5.5), dict(kind="url", at="Visit")]
P["UGC5"]["sfx"] = [("Visit", "notification-success-ding-ding")]
P["UGC6"]["inserts"] = [dict(kind="logo", at="Bounti."), L("You can join as a hunter", "Anyway", BROWSE), dict(kind="url", at="You can check")]
P["UGC6"]["sfx"] = [("Bounti.", "pop-medium-in"), ("You can check", "notification-success-ding-ding")]
P["UGC7"]["inserts"] = [L("That's where", "Instead of just", [("find_claim", 3.6, 9.0), ("find_claim", 12.9, 15.4)], 6.5), dict(kind="url", at="Check out")]
P["UGC10"]["hook"] = dict(kind="none")
P["UGC10"]["inserts"] = [dict(kind="logo", at="Okay, so I've"), L("Okay, this is", "And here we have", [("dashboard", 0.7, 6.0)]),
                         L("And here we have", "Let's open one", [("missions_detail", 0.8, 5.5)]),
                         L("Let's open one", "I like that", [("missions_detail", 10.4, 16.0)]),
                         L("I like that", "Well, that's", [("house", 0.6, 9.0)]), dict(kind="url", at="You can check")]
P["UGC10"]["sfx"] = [("Okay, so I've", "pop-medium-in"), ("You can check", "notification-success-ding-ding")]
P["UGC11"]["inserts"] = [L("First, I'm checking", "Now I'm going", BROWSE), L("Now I'm going", "Let's get started", REQS),
                         L("After completing", "Well,", [("my_hunts", 0.6, 10.0)]), dict(kind="url", at="You can try")]
P["UGC12"]["greenscreen"] = [("signup", 0.0, 1.6)]
P["UGC12"]["bg_switch"] = [("And the idea", [("partner_create", 0.5, 13.5)]), ("Then people can join", BROWSE), ("And for hunters", CLAIM_ONLY)]
P["UGC12"]["inserts"] = [dict(kind="url", at="Go to")]
P["UGC13"]["inserts"] = [dict(kind="logo", at="It's called Bounti"), L("You can join as a hunter", "And the cool thing", BROWSE),
                         L("And the cool thing", "So you're not", [("trend_rules", 3.9, 13.4)]), dict(kind="url", at="Anyway")]
P["UGC10"]["sfx"] = [("Okay, so I've", "pop-medium-in"), ("You can check", "notification-success-ding-ding")]
P["UGC13"]["sfx"] = [("It's called Bounti", "pop-medium-in"), ("Anyway", "notification-success-ding-ding")]
# fit fixes: every played segment ends inside its line window (no reward or rule cut off)
REQS_SHORT = [("trend_rules", 3.8, 11.4)]
P["UGC2"]["inserts"][1] = L("you could find a bounty", "So instead", FIND_CLAIM, 8.7)
P["UGC3"]["inserts"][1] = L("You explore available", "So whether", [("trend_rules", 3.6, 11.5)])
P["UGC6"]["inserts"][1] = L("You can join as a hunter", "Anyway", [("browse_feed", 0.5, 8.6)])
P["UGC10"]["inserts"][1] = L("Okay, this is", "And here we have", [("dashboard", 0.7, 4.0)])
P["UGC10"]["inserts"][4] = L("I like that", "Well, that's", [("house", 0.6, 8.9)])
P["UGC11"]["inserts"][1] = L("Now I'm going", "Let's get started", REQS_SHORT)
P["UGC11"]["inserts"][2] = L("After completing", "Well,", [("my_hunts", 0.6, 8.5)])
P["UGC13"]["inserts"][2] = L("And the cool thing", "So you're not", [("trend_rules", 3.9, 13.2)])
