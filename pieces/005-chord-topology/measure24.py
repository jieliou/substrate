# 005 measurement #24 — the hearth de-confound (twenty-fifth pass).
# Ephemeral verifier. The census (measure23) showed the founding has no
# dice under clean conditions: 8/8 landed 8.0570, and the 7.15/west
# basin appears only under machine load. But the piece's all-time depth
# record — min-x 1.1786, B's hearth, six hearth nodes — was set on that
# west founding (run22-B). One clean session-first run decides whether
# the hearth answers the law or the weather. Archive pre-read: run17
# (east) and run22-B (west) both read min-x 2.4922 at t=600 — the coup
# had erased the branch by six hundred seconds. Protocol identical to
# run22-B: founding g=1.15 d=-0.10 for 300 s, coup g=1.00 @300, held
# to 1800, uniform 30 s polling.
#
# PREDICTIONS (mirrored from index.html header, written before the run):
#   P81 founding no-dice — min-x@300 = 8.0570 exactly; count [47,63];
#       shareA [0.745,0.765]. Falsifier: 7.15 on session-first run.
#   P82 hearth answers the LAW — min-x 2.4922 @600, 1.1786 @900, six
#       hearth nodes by 1800. Falsifier A (weather): min-x >= 2.49 at
#       1800. Falsifier B (rungs yes, clock no): same rungs, different
#       times. Middle: past 2.49 onto rungs other than 1.1786.
#   P83 canon ignores founding — lit agreement vs run22-B@1800 >= 95%;
#       run17 lit relit >= 90%. Falsifier: <= 75%.
#   P84 instrument — re-mint 155 identical positions; zero JS errors;
#       fps >= 60.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
COUP_T, POLL, SECS = 300, 30, 1800
COUP_G = 1.00
OUT_FN, SHOT_FN = "run24-hearth.json", "score-hearth-clean.png"

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
    out = {"regime": "SESSION-FIRST clean: g=1.15 d=-0.10; coup g=%.2f @300, held to %d (hearth de-confound)" % (COUP_G, SECS),
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
        await page.screenshot(path=SHOT_FN)
        await browser.close()
    out["polls"] = polls
    out["final"] = final
    out["errors"] = errors
    with open(OUT_FN, "w") as f:
        json.dump(out, f, indent=1)
    for p in polls:
        if p["t"] % 300 == 0 or p["t"] in (60, 600, 900):
            print(p["t"], "g=%.3f" % p["gamma"], "meet", p["meetings"],
                  "played", p["playedNodes"], "W", p["playedNodesW"],
                  "litE", p["playedE"], "litW", p["playedW"],
                  "minx", (("%.4f" % p["minx"]) if p["minx"] is not None else "-"),
                  "shareA", "%.4f" % p["shareA"])
    sc = final["score"]
    lit = sc["playedE"] + sc["playedW"]
    tot = sc["fretE"] + sc["fretW"]
    print("frets", tot, "lit", lit, "(%.1f%%)" % (100.0 * lit / tot),
          "deepNodes", final["deepNodes"], "hearthNodes", final["hearthNodes"],
          "errors", len(errors), "fps", final["fps"])

asyncio.run(main())
