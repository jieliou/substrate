# 005 measurement #18 — the amplitude law (nineteenth pass).
# Ephemeral verifier. measure17 with ONE variable changed: the coup
# strikes gamma 0.80 instead of 1.00. One 600 s run — founding
# g=1.15 d=-0.10 for 300 s, coup setGamma(0.80) at t=300, held to
# 600 with no restoration. Uniform 30 s polling (measure15/17 cadence).
# Question: law v8 says depth = the migration's amplitude. All three
# prior coups struck gamma 1.00; does a harsher law dose a bigger
# amplitude (min shareA < 0.406) and a deeper lease (min x < 2.17)?
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P55 cadence control — founding returns the 30 s floor exactly
#       (played 54, west 8, minx 8.06 at t=300); fourth exact return.
#   P56 harsher law, bigger migration (core) — min shareA < 0.406
#       (band guess 0.28-0.40); coup minute >= 30 new played nodes;
#       drip 420-600 >= 7. Falsifier: min shareA 0.43-0.52 (overshoot
#       saturates at gamma <= 1.0; amplitude is flesh-intrinsic).
#   P57 depth follows amplitude — min x < 2.17, set in the first coup
#       minute; linear guess: shareA ~0.35 buys min x ~1.5 (hearth
#       band). Falsifier: min x 2.3-2.6 (depth saturated; the knob is
#       not the law's value).
#   P58 instrument — zero JS errors, fps >= 60, biomass finite, gamma
#       pinned 0.80 through the second half.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
SECS, POLL = 600, 30
COUP_T = 300
COUP_G = 0.80

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

async def main():
    out = {"regime": "g=1.15 d=-0.10; coup g=0.80 @300, held to 600 (no restoration)",
           "secs": SECS}
    polls, errors = [], []
    async with async_playwright() as pw:
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
                await page.evaluate("() => window.setGamma(%.2f)" % COUP_G)
        final = await page.evaluate("""() => ({
            meetX: STATS.meetX, meetT: STATS.meetT, kicks: STATS.kicks,
            score: window.score(),
            deepNodes: G.nodes.filter(n => n.played && n.x >= 4.0 && n.x <= 5.25).length,
            hearthNodes: G.nodes.filter(n => n.played && n.x < 1.5).length,
            fps: (document.getElementById('fps') || {}).textContent || null })""")
        await page.screenshot(path="score-amplitude.png")
        await browser.close()
    out["polls"] = polls
    out["final"] = final
    out["errors"] = errors
    with open("run18-amplitude.json", "w") as f:
        json.dump(out, f, indent=1)
    for p in polls:
        print(p["t"], "g=%.3f" % p["gamma"], "meet", p["meetings"],
              "played", p["playedNodes"], "W", p["playedNodesW"],
              "minx", (("%.2f" % p["minx"]) if p["minx"] is not None else "-"),
              "shareA", "%.3f" % p["shareA"])
    print("deepNodes", final["deepNodes"], "hearthNodes", final["hearthNodes"],
          "errors", len(errors))

asyncio.run(main())
