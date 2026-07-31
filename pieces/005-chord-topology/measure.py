# 005 measurement — first light. Ephemeral verifier (craft rule 7: 驗證裝置化).
# Probes the predictions written in index.html BEFORE this ran:
#   P1: Δ=0.10 few organs, all near the mouth
#   P2: Δ=0 one cathedral; Δ=0.35 many weak scattered chapels
#   P3: starvation inversion — survival peaks at MID Δ, not tight rhythm
#   P4: conducts/meetings < 0.5 (hyperedge stricter than pairwise)
import asyncio, json, statistics
from playwright.async_api import async_playwright

URL = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
RUNS = [  # (detune, seconds)
    (0.00, 60),   # P2 cathedral
    (0.05, 60),   # P3 starvation side (slip ~50s)
    (0.10, 60),   # P1 locus (slip ~26s)
    (0.35, 60),   # P2/P3 scatter side (slip ~9.3s)
]

async def run_one(pw, det, secs):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    await page.wait_for_function("window.STATS !== undefined")
    await page.evaluate(f"window.setDet({det})")
    await page.wait_for_timeout(2000)
    await page.evaluate("window.STATS.reset()")
    t0 = await page.evaluate("window.state().t")
    await page.wait_for_timeout(secs * 1000)
    out = await page.evaluate("""() => {
      const S = window.STATS, st = window.state();
      return { meetings: S.meetings, shadows: S.shadows,
               formed: S.organsFormed, died: S.organsDied,
               reinforced: S.reinforced, conducts: S.conducts,
               conductT: S.conductT.slice(),
               organs: st.organs, biomass: st.biomass, sinkX: st.sinkX, t: st.t };
    }""")
    fps = await page.evaluate("parseFloat(document.getElementById('fps').textContent) || -1")
    await browser.close()
    out["dt_wall"] = out["t"] - t0
    out["errors"] = errors
    out["fps"] = fps
    return out

async def main():
    async with async_playwright() as pw:
        print(f"{'Δ':>5} {'meet':>5} {'form':>5} {'reinf':>6} {'cond':>5} {'died':>5} "
              f"{'alive':>6} {'Σw':>7} {'meanW':>6} {'locus':>22} {'c/m':>5}")
        for det, secs in RUNS:
            r = await run_one(pw, det, secs)
            organs = r["organs"]
            alive = len(organs)
            meanw = statistics.mean(o["w"] for o in organs) if organs else 0.0
            xs = [o["meanX"] for o in organs]
            if xs:
                mx = statistics.mean(xs)
                sx = statistics.stdev(xs) if len(xs) > 1 else 0.0
                locus = f"meanX {mx:5.1f} sd {sx:4.1f} (sink {r['sinkX']:.1f})"
            else:
                locus = "—"
            cm = r["conducts"] / r["meetings"] if r["meetings"] else float("nan")
            # survivors that re-performed: conducted at least twice is not directly
            # per-organ tracked in first light; proxy = conducts vs alive
            print(f"{det:5.2f} {r['meetings']:5d} {r['formed']:5d} {r['reinforced']:6d} "
                  f"{r['conducts']:5d} {r['died']:5d} {alive:6d} {r['biomass']:7.2f} "
                  f"{meanw:6.2f} {locus:>22} {cm:5.2f}")
            if r["errors"]:
                print("  JS ERRORS:", r["errors"])
            if r["fps"] > 0 and r["fps"] < 55:
                print(f"  LOW FPS: {r['fps']}")
            detail = {"det": det, **{k: r[k] for k in
                      ("meetings","formed","reinforced","conducts","died","biomass","organs","fps")}}
            with open(__file__.replace("measure.py", f"run-d{det:.2f}.json"), "w") as f:
                json.dump(detail, f, indent=1)

asyncio.run(main())
