# 005 measurement #21 — the three-fifths question (twenty-second pass).
# Ephemeral verifier. Law v11 says the law's value legislates the book's
# thickness, not its readable share — every parliament stalls near the
# same ~60%. Its weakest point is gamma 0.90: at 1800 s it sat at 57%
# and was still reading (drip600 = 13). measure21 = the longest window
# in the piece's history: founding g=1.15 d=-0.10 for 300 s, coup
# setGamma(0.90) at t=300, held to 3600 s. Uniform 30 s polling.
# Companion instrument (same pass): archival dark-fret maps from the
# five existing run files — see analyze21.py.
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P68 (archival) the shadow is structure, not dice — dark frets sit
#       west of lit (mean x), at higher |phi|; cross-dose (0.90 vs
#       0.95) dark/lit agreement >= 75% on spatially shared frets;
#       same-law control (run18 vs run19) higher. Falsifier: uniform
#       stats or chance-level agreement.
#   P69 the stall — lit fraction <= 68% at 3600 with trailing-600
#       drip < 5 established by t <= 3000 (bursty resurgences allowed;
#       the CEILING is the claim). Falsifier: lit >= 72% with drip
#       still >= 8 at 3600 — v11's readable-share clause dies.
#   P70 the shadow predicts the stall — >= 70% of this run's dark set
#       at 3600 is also dark in run20-dose-g0.90 at 1800 (fresh dice,
#       doubled window, same shadow). Falsifier: < 50% (darkness
#       churns; the stall is rate, not territory).
#   P71 instrument — lattice re-mints exactly 200 frets at the same
#       positions; zero JS errors; fps >= 60 after 60 min; biomass
#       finite; gamma pinned 0.90.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
SECS, POLL = 3600, 30
COUP_T = 300
COUP_G = 0.90

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
    out = {"regime": "g=1.15 d=-0.10; coup g=0.90 @300, held to 3600 (three-fifths window)",
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
        await page.screenshot(path="score-threefifths.png")
        await browser.close()
    out["polls"] = polls
    out["final"] = final
    out["errors"] = errors
    with open("run21-threefifths.json", "w") as f:
        json.dump(out, f, indent=1)
    for p in polls:
        print(p["t"], "g=%.3f" % p["gamma"], "meet", p["meetings"],
              "played", p["playedNodes"], "W", p["playedNodesW"],
              "minx", (("%.2f" % p["minx"]) if p["minx"] is not None else "-"),
              "shareA", "%.3f" % p["shareA"])
    print("deepNodes", final["deepNodes"], "hearthNodes", final["hearthNodes"],
          "errors", len(errors))

asyncio.run(main())
