# 005 measurement #22 — the absolute-canon question (twenty-third pass).
# Ephemeral verifier. Law v12 says the constitution legislates tempo and
# binding, not territory. Its strongest form: the reachable set in
# ABSOLUTE bars is a lattice constant. Standing absolute counts:
# 0.80 died at 154, 0.90 passed 146 creeping, 0.95 paused at 111,
# 1.00 stood at 99 at only 600 s. Two sequential runs, same founding
# protocol as measure17-21 (g=1.15 d=-0.10 for 300 s, coup at t=300,
# uniform 30 s polling):
#   run A: coup g=0.80, held to 3600 (re-test of run19's adjournment —
#          real death near the canon, or drought?)
#   run B: coup g=1.00, held to 1800 (the divergence point — its book
#          is ~the candidate canon; must it read nine-tenths of it?)
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P72 real death — 0.80@3600 lit in [150,168] with trailing-600
#       drip <= 3. Falsifier: lit >= 175 or drip >= 8 still flowing.
#   P73 catch-up — 1.00@1800 lit >= 125 (81% of book). Falsifier:
#       <= 110 with dead drip. Middle 111-124 / still climbing =
#       verdict deferred (gate too slow for the window).
#   P74 one book positionally — cross-law lit/dark agreement >= 90%
#       (0.80@3600 vs run21 0.90@3600); >= 90% of run19's lit set lit
#       again here. Falsifier: <= 75% (convergence of size, not canon).
#   P75 instrument — re-mint 248 / 155 at identical positions; founding
#       count in N=8 band (54-58); founding min x 8.0570; zero JS
#       errors; fps >= 60 through both runs.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
COUP_T, POLL = 300, 30
RUNS = [
    ("g0.80x3600", 0.80, 3600, "run22-canon-g0.80.json", "score-canon-g080.png"),
    ("g1.00x1800", 1.00, 1800, "run22-canon-g1.00.json", "score-canon-g100.png"),
]

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

async def one_run(pw, tag, coup_g, secs, out_fn, shot_fn):
    out = {"regime": "g=1.15 d=-0.10; coup g=%.2f @300, held to %d (absolute-canon)" % (coup_g, secs),
           "secs": secs}
    polls, errors = [], []
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(BASE + "?g=1.15&d=-0.10")
    for t in range(POLL, secs + 1, POLL):
        await page.wait_for_timeout(POLL * 1000)
        snap = await page.evaluate(SNAP_JS)
        snap["t"] = t
        polls.append(snap)
        if t == COUP_T:
            await page.evaluate("() => window.setGamma(%.2f)" % coup_g)
    final = await page.evaluate("""() => ({
        meetX: STATS.meetX, meetT: STATS.meetT, kicks: STATS.kicks,
        score: window.score(),
        deepNodes: G.nodes.filter(n => n.played && n.x >= 4.0 && n.x <= 5.25).length,
        hearthNodes: G.nodes.filter(n => n.played && n.x < 1.5).length,
        fps: (document.getElementById('fps') || {}).textContent || null })""")
    await page.screenshot(path=shot_fn)
    await browser.close()
    out["polls"] = polls
    out["final"] = final
    out["errors"] = errors
    with open(out_fn, "w") as f:
        json.dump(out, f, indent=1)
    print("=== %s ===" % tag)
    for p in polls:
        if p["t"] % 300 == 0:
            print(p["t"], "g=%.3f" % p["gamma"], "meet", p["meetings"],
                  "played", p["playedNodes"], "W", p["playedNodesW"],
                  "litE", p["playedE"], "litW", p["playedW"],
                  "minx", (("%.2f" % p["minx"]) if p["minx"] is not None else "-"),
                  "shareA", "%.3f" % p["shareA"])
    sc = final["score"]
    lit = sc["playedE"] + sc["playedW"]
    tot = sc["fretE"] + sc["fretW"]
    print("frets", tot, "lit", lit, "(%.1f%%)" % (100.0 * lit / tot),
          "deepNodes", final["deepNodes"], "hearthNodes", final["hearthNodes"],
          "errors", len(errors), "fps", final["fps"])

async def main():
    async with async_playwright() as pw:
        for tag, g, secs, fn, shot in RUNS:
            await one_run(pw, tag, g, secs, fn, shot)

asyncio.run(main())
