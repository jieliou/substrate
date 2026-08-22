# 005 measurement #19 — the tortoise question (twentieth pass).
# Ephemeral verifier. measure18 held to 1800 s — the longest window
# in this piece's history. Founding g=1.15 d=-0.10 for 300 s, coup
# setGamma(0.80) at t=300, then 1500 s of commons. Uniform 30 s
# polling. Question: pass nineteen ended with min x still creeping
# at t=600 (8.06 -> 7.15 -> 6.53 -> 6.07). Ballistic depth is bought
# in thirty seconds and frozen; is diffusive depth bought forever and
# never frozen? sqrt-t projection: 4.95 crossing near t ~ 900-1200,
# final min x ~ 3.3.
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P59 cadence control — founding floor in the N=4 band: played
#       54-55, west 8, minx 8.06 at t=300.
#   P60 tortoise core — min x passes 4.95 before t=1200; final in
#       [2.5, 4.0]; tortoise does NOT beat the hare (final > 2.17).
#       Falsifiers: asymptote >= 5.5 (wall east of the deep band) or
#       final < 2.17 (tortoise wins; v8's breadth-not-depth dies).
#   P61 score fills but never finishes — lit fraction >= 80% by 1800
#       but < 100%; playedW/fretW >= 0.5. Falsifier: drip dries
#       (< 5 new in last 600 s) with lit fraction < 70%.
#   P62 instrument — zero JS errors, fps >= 60 after 30 min, biomass
#       finite, gamma pinned 0.80.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
SECS, POLL = 1800, 30
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
    out = {"regime": "g=1.15 d=-0.10; coup g=0.80 @300, held to 1800 (tortoise window)",
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
        await page.screenshot(path="score-tortoise.png")
        await browser.close()
    out["polls"] = polls
    out["final"] = final
    out["errors"] = errors
    with open("run19-tortoise.json", "w") as f:
        json.dump(out, f, indent=1)
    for p in polls:
        print(p["t"], "g=%.3f" % p["gamma"], "meet", p["meetings"],
              "played", p["playedNodes"], "W", p["playedNodesW"],
              "minx", (("%.2f" % p["minx"]) if p["minx"] is not None else "-"),
              "shareA", "%.3f" % p["shareA"])
    print("deepNodes", final["deepNodes"], "hearthNodes", final["hearthNodes"],
          "errors", len(errors))

asyncio.run(main())
