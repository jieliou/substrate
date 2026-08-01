# 005 measurement #2 — terrain axis + organ careers. Ephemeral verifier.
# Question: first light killed the cathedral on the DETUNE axis (Δ=0 grew the
# most/thinnest/most-scattered organs — ubiquity dilutes memory). But Δ=0's
# dilution was SPATIAL: coincidence everywhere on the mesh (locus sd 3.3).
# The terrain knob γ controls exactly that — tree carving (γ high) forces
# meetings through few channels. So: is the law about TEMPORAL ubiquity of
# coincidence, or SPATIAL ubiquity of its loci?
#
# PREDICTIONS (written before running — 2026-08-02 02:3x):
#   P5 cathedral-by-terrain: γ=1.60, Δ=0 — tree collapses coincidence loci
#      to few channels → FEWER organs than γ=1.00 Δ=0 (8 → ≤4), FATTER
#      (meanW 0.82 → >1.3), TIGHTER (locus sd 3.3 → <1.5). If it holds, the
#      law refines: SPATIAL scarcity of coincidence concentrates memory —
#      the lock was never the problem, the mesh's everywhere-ness was.
#   P6 symmetric dilution: γ=0.60, Δ=0.10 — meshier bed multiplies paths,
#      re-alignment loci spread → MORE organs than γ=1.00 Δ=0.10 (5 → >5),
#      thinner (meanW 1.39 → lower), looser (sd 0.9 → higher). Dilution is
#      terrain-controlled in BOTH directions.
#   P7 career concentration: everywhere, most chapels die unperformed
#      (median dead-organ conducts = 0) and the top living organ takes ≥50%
#      of all conducts — feeding extends life extends chances (rich-get-
#      richer), so re-performance should be far more unequal than formation.
import asyncio, json, statistics
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
GRID = [  # (gamma, detune, seconds)
    (1.60, 0.00, 60),  # P5 — tree + lock
    (1.60, 0.10, 60),  # P5 control — tree + slip
    (0.60, 0.00, 60),  # P6 control — mesh + lock
    (0.60, 0.10, 60),  # P6 — mesh + slip
]
BASELINE = {  # γ=1.00 from first light (run-d*.json), for the table only
    (1.00, 0.00): dict(alive=8, meanW=0.82, sd=3.3),
    (1.00, 0.10): dict(alive=5, meanW=1.39, sd=0.9),
}

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
            with open(__file__.replace("measure2.py", f"run2-g{g:.2f}-d{det:.2f}.json"), "w") as f:
                json.dump({"gamma": g, "det": det, **{k: r[k] for k in
                          ("meetings","formed","reinforced","conducts","died",
                           "biomass","organs","deadLog","fps")}}, f, indent=1)
        print("\nbaseline γ=1.00 (first light):", BASELINE)

asyncio.run(main())
