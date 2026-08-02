# 005 measurement #3 — ridge fine-scan. Ephemeral verifier.
# Question: measure2 found the cathedral on a knife edge (γ=1.15: 2 organs,
# meanW≈7.4, 58 conducts/60s — organ-as-music) between mesh-commons (γ=0.6)
# and tree-estrangement (γ≥1.30). But the scan was coarse (0.6 / 1.15 / 1.30 /
# 1.60) and the 1.15 run's JSON wasn't kept. How WIDE is the ridge band, what
# do its two edges look like, and does slip (Δ) move it?
#
# PREDICTIONS (written before running — 2026-08-03 01:3x):
#   P8 band width ≲0.10: define "cathedral state" = alive ≤3 AND meanW ≥3.0
#      AND conducts ≥40/60s. Predict it holds at γ=1.15 (replication) and at
#      most ONE neighbor (1.10 or 1.20). At 1.05 the mesh side has already
#      diluted it (alive ≥5, meanW <2); at 1.25 the tree side has starved it
#      (meetings ≤10, alive ≤1). The cathedral is a band, not a plateau.
#   P9 slip kills the music but not the church: at γ=1.15, Δ=0.10 —
#      re-alignment makes coincidence pulsed instead of continuous. Predict
#      conducts collapse below 25/60s (organ stops being continuous music),
#      but the organs SURVIVE (alive ≤3, biomass ≥5): the few channels mean
#      re-alignment keeps hitting the same loci, so feeding stays targeted.
#      The ridge position itself does not move (terrain is bed-carving,
#      independent of timing).
#   P10 two edges, two shapes: mesh→ridge is GRADUAL (alive declines
#      monotonically 1.05→1.15; contact surface shrinks continuously) but
#      ridge→tree is a CLIFF (somewhere in (1.20, 1.30] organs hit 0 while
#      meetings stay >0 — the contact-without-constitution state; a
#      percolation-style connectivity collapse, not a fade). Corollary:
#      slip does NOT rescue γ=1.30 (terrain binds, timing doesn't):
#      (1.30, 0.10) still forms 0 organs.
import asyncio, json, statistics
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
GRID = [  # (gamma, detune, seconds)
    (1.05, 0.00, 60),
    (1.10, 0.00, 60),
    (1.15, 0.00, 60),  # replication of measure2 ridge point
    (1.20, 0.00, 60),
    (1.25, 0.00, 60),
    (1.05, 0.10, 60),
    (1.10, 0.10, 60),
    (1.15, 0.10, 60),  # P9
    (1.20, 0.10, 60),
    (1.25, 0.10, 60),
    (1.30, 0.10, 60),  # P10 corollary — slip cannot rescue the tree
]

async def run_one(pw, g, det, secs):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(f"{BASE}?g={g:.2f}")
    await page.wait_for_function("window.STATS !== undefined")
    await page.evaluate(f"window.setDet({det})")
    await page.wait_for_timeout(2000)
    await page.evaluate("window.STATS.reset()")
    await page.wait_for_timeout(secs * 1000)
    out = await page.evaluate("""() => {
      const S = window.STATS, st = window.state();
      return { meetings: S.meetings, formed: S.organsFormed, died: S.organsDied,
               reinforced: S.reinforced, conducts: S.conducts,
               deadLog: S.deadLog.slice(), organs: st.organs,
               biomass: st.biomass, sinkX: st.sinkX, gamma: st.gamma };
    }""")
    fps = await page.evaluate("parseFloat(document.getElementById('fps').textContent) || -1")
    await browser.close()
    out["errors"] = errors; out["fps"] = fps
    return out

def career_stats(r):
    dead = r["deadLog"]; alive = r["organs"]
    all_c = [d["conducts"] for d in dead] + [o["c"] for o in alive]
    tot = sum(all_c)
    med_dead = statistics.median([d["conducts"] for d in dead]) if dead else float("nan")
    unperf = sum(1 for c in all_c if c == 0)
    top = max(all_c) if all_c else 0
    top_share = top / tot if tot else float("nan")
    mean_life = statistics.mean([d["life"] for d in dead]) if dead else float("nan")
    return med_dead, unperf, len(all_c), top_share, mean_life

async def main():
    async with async_playwright() as pw:
        print(f"{'γ':>5} {'Δ':>5} {'meet':>5} {'form':>5} {'reinf':>6} {'cond':>5} {'died':>5} "
              f"{'alive':>6} {'Σw':>7} {'meanW':>6} {'locus':>22} "
              f"{'medD':>5} {'unperf':>7} {'topShr':>7} {'life':>6}")
        for g, det, secs in GRID:
            r = await run_one(pw, g, det, secs)
            organs = r["organs"]; alive = len(organs)
            meanw = statistics.mean(o["w"] for o in organs) if organs else 0.0
            xs = [o["meanX"] for o in organs]
            if xs:
                mx = statistics.mean(xs)
                sx = statistics.stdev(xs) if len(xs) > 1 else 0.0
                locus = f"meanX {mx:5.1f} sd {sx:4.1f} (sink {r['sinkX']:.1f})"
            else:
                locus = "—"
            md, unperf, n_all, tshr, mlife = career_stats(r)
            print(f"{g:5.2f} {det:5.2f} {r['meetings']:5d} {r['formed']:5d} {r['reinforced']:6d} "
                  f"{r['conducts']:5d} {r['died']:5d} {alive:6d} {r['biomass']:7.2f} "
                  f"{meanw:6.2f} {locus:>22} {md:5} {unperf:4d}/{n_all:<2d} {tshr:7.2f} {mlife:6.1f}")
            if r["errors"]:
                print("  JS ERRORS:", r["errors"])
            if r["fps"] > 0 and r["fps"] < 55:
                print(f"  LOW FPS: {r['fps']}")
            with open(__file__.replace("measure3.py", f"run3-g{g:.2f}-d{det:.2f}.json"), "w") as f:
                json.dump({"gamma": g, "det": det, **{k: r[k] for k in
                          ("meetings","formed","reinforced","conducts","died",
                           "biomass","organs","deadLog","fps")}}, f, indent=1)

asyncio.run(main())
