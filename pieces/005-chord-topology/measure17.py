# 005 measurement #17 — the long interregnum (eighteenth pass).
# Ephemeral verifier. One 600 s run, two eras: founding+adjournment
# (g=1.15 d=-0.10, 0-300), then coup setGamma(1.00) at t=300 and
# NOTHING else — the mesh law holds for 300 s with no restoration.
# Question: law v7's second clause — does the singing survive flesh
# equilibrium, or does the ratchet need BOTH a permissive law and a
# migrating frontier? Uniform 30 s polling = measure15 cadence, so
# the founding doubles as the (g2) cadence-observer control.
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P51 cadence control — founding returns the 30s-cadence floor exactly
#       (played 54, west 8, minx 8.06 at t=300); coup minute sings
#       (>= 15 new played nodes 300-360).
#   P52 flesh clause is real (core) — shareA settles 0.48-0.55 by t~390
#       and stays; new played nodes 420-600 <= 4. Falsifier: >= 15 new
#       in 420-600 (pure value-gating — mesh alone leases forever).
#   P53 depth is migration-bounded — final minx in [2.0, 4.0], reached
#       before t~420. Falsifiers: minx < 1.5 (hearth; unbounded) or
#       stuck ~4.9 (60 s was already full depth).
#   P54 instrument — zero JS errors, fps >= 60, biomass finite, gamma
#       pinned 1.00 through the second half.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
SECS, POLL = 600, 30
COUP_T = 300

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
    out = {"regime": "g=1.15 d=-0.10; coup g=1.00 @300, held to 600 (no restoration)",
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
                await page.evaluate("() => window.setGamma(1.00)")
        final = await page.evaluate("""() => ({
            meetX: STATS.meetX, meetT: STATS.meetT, kicks: STATS.kicks,
            score: window.score(),
            deepNodes: G.nodes.filter(n => n.played && n.x >= 4.0 && n.x <= 5.25).length,
            fps: (document.getElementById('fps') || {}).textContent || null })""")
        await page.screenshot(path="score-interregnum.png")
        await browser.close()
    out["polls"] = polls
    out["final"] = final
    out["errors"] = errors
    with open("run17-interregnum.json", "w") as f:
        json.dump(out, f, indent=1)
    for p in polls:
        print(p["t"], "g=%.3f" % p["gamma"], "meet", p["meetings"],
              "played", p["playedNodes"], "W", p["playedNodesW"],
              "minx", (("%.2f" % p["minx"]) if p["minx"] is not None else "-"),
              "shareA", "%.3f" % p["shareA"])
    print("deepNodes", final["deepNodes"], "errors", len(errors))

asyncio.run(main())
