# 004 fourth pass — perceptibility smoke: do the reveals actually reveal?
# This pass is DISPLAY work, so the verifier verifies display: state
# assertions plus screenshots read by eye afterwards.
#
# REVISED after first run (2026-07-30 00:5x): the original PV2 asserted
# "lock = psi spread < 0.15" — flat-line intuition from CONTINUOUS
# coupling, and the screenshot refuted it: pulse-coupled lock is a
# sawtooth that stands in place (kicks cancel the walk, teeth remain).
# Lock criterion is therefore the pass-3 instrument: unwrapped-psi drift
# rate ~ 0, i.e. the WALK stalls — not the teeth vanishing. Also added:
# in-page readPixels, because the deaf screenshot came back white while
# the sim demonstrably ran (120 fps HUD) — adjudicates piece-bug vs
# swiftshader capture flake.
#
# PREDICTIONS (PV2/PV4 rewritten before second run):
#   PV1  Deaf (K=0): tremors stay exactly 0 (hear() gates them), the psi
#        trace lives, wrapped-psi sweeps its range (spread > 0.6).
#   PV2  Lock regime (gamma=1.6, K=6, sign=-1, 30 s): hears flow,
#        tremors observed alive in at least one poll, and |drift rate|
#        of unwrapped psi over the last half < 0.010 cyc/s (walk stalled;
#        deaf rate is -0.0379).
#   PV3  Zero JS errors in both runs; psi sampling ~4/s.
#   PV4  In-page readback: canvas center patch has nonzero pixels in
#        BOTH runs (the piece always draws; a white Playwright shot with
#        nonzero readback = capture flake, documented not fixed).
import asyncio, json
from playwright.async_api import async_playwright

URL = "file:///Users/jie/Dev/substrate/pieces/004-coupled-metronomes/index.html"

async def run_one(pw, name, gam, det, k, sign, secs, shot):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    await page.wait_for_function("window.STATS !== undefined")
    await page.evaluate(f"window.setGamma({gam}); window.setDet({det}); window.setK({k}); window.setSign({sign});")
    await page.wait_for_timeout(6000)
    await page.evaluate("window.STATS.reset()")
    trem_seen = 0
    for _ in range(secs * 2):                      # poll tremors at 2 Hz
        await page.wait_for_timeout(500)
        alive = await page.evaluate("window.tremors.length")
        trem_seen = max(trem_seen, alive)
    out = await page.evaluate("""() => {
      const S = window.STATS, n = S.psi.length;
      let mn = 1e9, mx = -1e9;
      for (const v of S.psi) { if (v < mn) mn = v; if (v > mx) mx = v; }
      const u = S.psiU, t = S.psiT, h = n >> 1;
      const rate2 = h > 2 ? (u[n-1] - u[h]) / (t[n-1] - t[h]) : null;
      /* in-page readback: 100x100 center patch, count lit pixels */
      const cv = document.getElementById("c");
      const g = cv.getContext("webgl2");
      const px = new Uint8Array(100 * 100 * 4);
      g.readPixels(cv.width/2 - 50, cv.height/2 - 50, 100, 100, g.RGBA, g.UNSIGNED_BYTE, px);
      let lit = 0;
      for (let i = 0; i < px.length; i += 4) if (px[i] + px[i+1] + px[i+2] > 12) lit++;
      return { psiN: n, spread: +(mx - mn).toFixed(3),
               rate2: rate2 === null ? null : +rate2.toFixed(4),
               hears: S.hearA + S.hearB, meetings: S.meetings,
               litFrac: +(lit / 10000).toFixed(3),
               label: document.getElementById("regime").textContent };
    }""")
    await page.screenshot(path=shot)
    await browser.close()
    out.update({ "run": name, "tremMax": trem_seen, "jsErrors": errors,
                 "psiRate": round(out["psiN"] / secs, 2) })
    return out

async def main():
    async with async_playwright() as pw:
        deaf = await run_one(pw, "deaf",  1.0, 0.10, 0.0, -1, 20, "shot-deaf.png")
        lock = await run_one(pw, "lock",  1.6, 0.10, 6.0, -1, 30, "shot-lock.png")
    print(json.dumps(deaf, indent=1))
    print(json.dumps(lock, indent=1))
    v1 = deaf["tremMax"] == 0 and deaf["spread"] > 0.6
    v2 = lock["hears"] > 10 and lock["tremMax"] > 0 and lock["rate2"] is not None and abs(lock["rate2"]) < 0.010
    v3 = not deaf["jsErrors"] and not lock["jsErrors"] and deaf["psiRate"] > 3.0 and lock["psiRate"] > 3.0
    v4 = deaf["litFrac"] > 0.005 and lock["litFrac"] > 0.005
    v5 = "deaf" in deaf["label"] and ("locked" in lock["label"] or "negotiating" in lock["label"])
    print("PV1 deaf-clean   :", "PASS" if v1 else "FAIL")
    print("PV2 walk-stalls  :", "PASS" if v2 else "FAIL")
    print("PV3 no-errors    :", "PASS" if v3 else "FAIL")
    print("PV4 canvas-drawn :", "PASS" if v4 else "FAIL")
    print("PV5 label-honest :", "PASS" if v5 else "FAIL")

asyncio.run(main())
