"""UGC v2 (Mac 2026-11-19): every video its own editing style, music, hook and caption look. Text never over faces.
Only UGC5 and UGC12 are green screen (two different formats, torso only). UGC2 uses Mac's L8 podcast-card style.
App moments reuse the live prototype inserts from ugc_projects (matched to the lines)."""
ST = {
 "UGC1": dict(style="punch", cap=("hormozi", "pop"), hook=["NO FOLLOWERS", "NEEDED."], hook_t=(0.15, 2.4)),
 "UGC2": dict(style="cards", cap=("minimal_caps", "rise_per_word"), hook=["What if?"], hook_t=(0.0, 1.9),
              cards=[("Yeah, it's called", "logo"), ("And there are different", "word:Endless")]),
 "UGC3": dict(style="split", cap=("minimal", "fade"), hook=["brands need people.", "you're people."], hook_t=(0.2, 3.0), ay=0.42),
 "UGC4": dict(style="loom", cap=("box_white", "slide_up"), hook=["found this today"], hook_t=(0.1, 2.6)),
 "UGC5": dict(style="gs_side", cap=("bar_pop", "pop"), hook=["How it works,", "in 3 steps."], hook_t=(0.0, 2.6),
              steps=[("First, you head", "1", "Explore"), ("When you find", "2", "Open and read"), ("If everything", "3", "Do it and submit")],
              backdrop=[(None, [("browse_feed", 0.5, 1.0)])]),
 "UGC6": dict(style="cinema", cap=("elegant_serif", "fade"), hook=["So I found this..."], hook_t=(0.0, 3.2)),
 "UGC7": dict(style="contrast", cap=("impact_clean", "stamp"), hook=["How many hours", "did you scroll today?"], hook_t=(0.0, 2.3),
              words=[("We scroll", "Scroll."), ("watch videos", "Watch."), ("engage with", "Engage."), ("and interact", "Interact.")], turn="That's where"),
 "UGC10": dict(style="duet", cap=("rounded", "pop"), hook=["First look:", "Bounti"], hook_t=(0.1, 2.6)),
 "UGC11": dict(style="vlog", cap=("comic", "bounce"), hook=["DAY 1"], hook_t=(0.0, 2.0),
               checklist=[("First, I'm checking", "Explore bounties"), ("Now I'm going", "Check requirements"), ("I'll submit", "Submit entries")]),
 "UGC12": dict(style="gs_float", cap=("hormozi", "pop"), hook=["Why is nobody", "talking about this?"], hook_t=(0.0, 3.0)),
 "UGC13": dict(style="chat", cap=("box_black", "pop"), hook=["you need to see this"], hook_t=(0.3, 3.0), bubbles=[("It's called Bounti", "link")]),
}
