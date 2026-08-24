# 005 measurement #23 — the founding census (twenty-fourth pass).
# Ephemeral verifier. Pass 23 found the founding bimodal under an
# identical harness: run A landed the 8.0570 attractor (count 60,
# W 8), run B back-to-back landed 7.15 (count 65, W 15) — a value
# previously seen only under a 5 s harness tick (measure16). Eight
# consecutive foundings, 300 s each, fresh browser per run, no coup.
# Splits load-keyed vs jitter-stochastic; maps basin frequencies.
#
# PREDICTIONS (mirrored from index.html header, written before census):
#   P76 branch commits in first minute — minx(60) == minx(300) in
#       >= 7/8 runs. Falsifier: deepening > 0.5 after t=60 in >= 2.
#   P77 both basins real — 8.0570 majority (>= 5/8) AND 7.15 appears
#       >= 1. Falsifier A: 8/8 identical (load-keyed). Falsifier B:
#       a third minx value (rung ladder inside the founding).
#   P78 count rides the branch — every 7.15 run's count > every
#       8.0570 run's count. Falsifier: overlap.
#   P79 share rides nothing — all shareA in [0.748, 0.760].
#   P80 instrument — 8/8 complete, zero JS errors.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
N_RUNS, SECS, POLL = 8, 300, 30

SNAP_JS = """() => {
    const s = window.score(), st = window.state();
    let pt = 0, pw = 0, mn = null;
    for (const n of G.nodes) if (n.played) { pt++; if (n.x < 9.5) pw++; }
    for (const x of STATS.meetX) if (mn === null || x < mn) mn = x;
    return { meetings: STATS.meetings, playedNodes: pt, playedNodesW: pw,
             minx: mn, playedE: s.playedE, playedW: s.playedW,
             shareA: st.terr.shareA, gamma: st.gamma };
}"""

async def one_founding(pw, idx):
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
    await browser.close()
    return {"run": idx, "polls": polls, "errors": errors}

async def main():
    runs = []
    async with async_playwright() as pw:
        for i in range(N_RUNS):
            r = await one_founding(pw, i)
            runs.append(r)
            f = r["polls"][-1]
            m60 = next(p for p in r["polls"] if p["t"] == 60)
            print("run", i, "count", f["playedNodes"], "W", f["playedNodesW"],
                  "minx", "%.4f" % f["minx"], "minx@60", "%.4f" % m60["minx"],
                  "shareA", "%.4f" % f["shareA"],
                  "litW", f["playedW"], "err", len(r["errors"]))
    with open("run23-census.json", "w") as fh:
        json.dump({"n": N_RUNS, "secs": SECS, "runs": runs}, fh, indent=1)
    minxs = sorted(set(round(r["polls"][-1]["minx"], 2) for r in runs))
    print("distinct minx values:", minxs)

asyncio.run(main())
