# 005 measurement #20 — the dose question (twenty-first pass).
# Ephemeral verifier. Law v9 closed with a sentence that is secretly
# a prediction: "gamma 1.00 was never a lenient law — it is the most
# lenient law that can still march." Passes 19-20 measured only the
# ENDPOINTS of the dose axis (1.00 army / 0.80 settlers). measure20 =
# the measure19 protocol at two intermediate doses: founding g=1.15
# d=-0.10 for 300 s, coup setGamma(G) at t=300, held to 1800 s,
# uniform 30 s polling, run twice: G = 0.90 and G = 0.95.
# Question: where does the army dissolve into settlers, and how does
# the book thicken as the law loosens?
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P63 cadence control — founding floor in the N=5 band: played
#       54-55, west 8, minx 8.06 at t=300, BOTH runs.
#   P64 dissolution point (core — v9's closing line on trial) — v9
#       read literally says marching fails below 1.00: both doses
#       show the settler signature (no pendulum overshoot: shareA
#       glides to parity and wanders, no dip-and-recover; depth
#       record NOT set-and-frozen in the coup minute; coup-minute
#       meetings not W-dominant). Falsifier: gamma 0.95 marches
#       (dip-and-recover, record set by t=360 then frozen >= 600 s,
#       W-heavy coup minute) — boundary moves inside (0.95, 1.00).
#   P65 the book thickens monotonically — total minted frets ordered
#       155 (1.00) < g0.95 < g0.90 < 248 (0.80); bands: 0.95 in
#       [160, 205], 0.90 in [195, 240]. Falsifier: ordering breaks.
#   P66 adjournment is NOT monotone in the dose — adjournment time =
#       book size / reading rate, factors pull opposite ways. 0.90
#       adjourns inside the window (trailing-600 s drip < 5 somewhere
#       in [900, 1800]); 0.95 does NOT adjourn by 1800. Falsifier:
#       0.95 adjourns before 0.90.
#   P67 instrument — zero JS errors, fps >= 60 after each 30-minute
#       run, biomass finite, gamma pinned at the coup value.
#       Variance discipline (run18-vs-run19): diffusive-regime min x
#       is leap-dominated — verdict rides on SHAPE (overshoot /
#       freeze / direction), not the depth digit.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
SECS, POLL = 1800, 30
COUP_T = 300
DOSES = [0.90, 0.95]

SNAP_JS = """() => {
    const s = window.score(), st = window.state();
    let pt = 0, pw = 0, mn = null;
    for (const n of G.nodes) if (n.played) { pt++; if (n.x < 9.5) pw++; }
    for (const x of STATS.meetX) if (mn === null || x < mn) mn = x;
    return { pageT: +st.t.toFixed(1), meetings: STATS.meetings,
             playedNodes: pt, playedNodesW: pw, minx: mn,
             fretE: s.fretE, fretW: s.fretW,
             playedE: s.playedE, playedW: s.playedW,
             biomass: st.biomass, shareA: st.terr.shareA, gamma: st.gamma };
}"""

async def run_dose(pw, g):
    tag = "g%.2f" % g
    out = {"regime": "g=1.15 d=-0.10; coup g=%.2f @300, held to 1800 (dose curve)" % g,
           "secs": SECS}
    polls, errors = [], []
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(BASE + "?g=1.15&d=-0.10")
    for t in range(POLL, SECS + 1, POLL):
        await page.wait_for_timeout(POLL * 1000)
        snap = await page.evaluate(SNAP_JS)
        snap["t"] = t
        polls.append(snap)
        if t == COUP_T:
            await page.evaluate("() => window.setGamma(%.2f)" % g)
    final = await page.evaluate("""() => ({
        meetX: STATS.meetX, meetT: STATS.meetT, kicks: STATS.kicks,
        score: window.score(),
        deepNodes: G.nodes.filter(n => n.played && n.x >= 4.0 && n.x <= 5.25).length,
        hearthNodes: G.nodes.filter(n => n.played && n.x < 1.5).length,
        fps: (document.getElementById('fps') || {}).textContent || null })""")
    await page.screenshot(path="score-dose-%s.png" % tag)
    await browser.close()
    out["polls"] = polls
    out["final"] = final
    out["errors"] = errors
    with open("run20-dose-%s.json" % tag, "w") as f:
        json.dump(out, f, indent=1)
    print("=== dose", tag, "===")
    for p in polls:
        print(p["t"], "g=%.3f" % p["gamma"], "meet", p["meetings"],
              "played", p["playedNodes"], "W", p["playedNodesW"],
              "minx", (("%.2f" % p["minx"]) if p["minx"] is not None else "-"),
              "shareA", "%.3f" % p["shareA"])
    # trailing-600s drip per poll from t=900 on (adjournment detector)
    by_t = {p["t"]: p["playedNodes"] for p in polls}
    for t in range(900, SECS + 1, 300):
        drip = by_t[t] - by_t[t - 600]
        print("drip trailing-600 @", t, "=", drip)
    # coup-minute meeting direction (from meetT/meetX)
    wm = sum(1 for mt, mx in zip(final["meetT"], final["meetX"])
             if COUP_T <= mt <= COUP_T + 60 and mx < 9.5)
    em = sum(1 for mt, mx in zip(final["meetT"], final["meetX"])
             if COUP_T <= mt <= COUP_T + 60 and mx >= 9.5)
    print("coup-minute meetings W", wm, "E", em)
    print("deepNodes", final["deepNodes"], "hearthNodes", final["hearthNodes"],
          "errors", len(errors))

async def main():
    async with async_playwright() as pw:
        for g in DOSES:
            await run_dose(pw, g)

asyncio.run(main())
