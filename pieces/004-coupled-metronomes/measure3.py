# 004 third pass — P5: does terrain coherence rescue the beat?
# PREDICTIONS (written before running):
#   PD  K=0 drift is gamma-independent: -0.0379 cyc/s at Delta=0.10
#       (clock physics doesn't touch the bed).
#   PE  At gamma=1.6 (tree = single dominant channel = coherent delay
#       line) coupling strength rises well beyond mesh's +-7% drift
#       modulation; lock (rate2 -> ~0) plausible at K=2 for one sign.
#   PF  Sign asymmetry is the coherence SIGNATURE: mesh gave near-
#       symmetric +-7%; if transit is now single-path, one sign should
#       clearly beat the other (which one depends on tau* mod T — no
#       prior commitment, honest uncertainty).
# Settle time raised to 6s: the bed must re-carve toward the new gamma
# before stats start (DT_CARVE converges in a few seconds at 120 fps).
import asyncio, json
from playwright.async_api import async_playwright

URL = "file:///Users/jie/Dev/substrate/pieces/004-coupled-metronomes/index.html"
RUNS = [  # (gamma, detune, K, sign, seconds)
    (1.6, 0.10, 0.0, -1, 30),
    (1.6, 0.10, 2.0, -1, 30),
    (1.6, 0.10, 2.0, +1, 30),
    (1.6, 0.10, 1.0, -1, 30),
    (1.6, 0.10, 1.0, +1, 30),
]

async def run_one(pw, gam, det, k, sign, secs):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    await page.wait_for_function("window.STATS !== undefined")
    await page.evaluate(f"window.setGamma({gam}); window.setDet({det}); window.setK({k}); window.setSign({sign});")
    await page.wait_for_timeout(6000)
    await page.evaluate("window.STATS.reset()")
    await page.wait_for_timeout(secs * 1000)
    out = await page.evaluate("""() => {
      const S = window.STATS;
      const u = S.psiU, t = S.psiT, n = u.length;
      const rate = n > 4 ? (u[n-1] - u[0]) / (t[n-1] - t[0]) : null;
      const h = n >> 1;
      const rate1 = h > 2 ? (u[h] - u[0]) / (t[h] - t[0]) : null;
      const rate2 = h > 2 ? (u[n-1] - u[h]) / (t[n-1] - t[h]) : null;
      return { hearA: S.hearA, hearB: S.hearB, meetings: S.meetings, shadows: S.shadows,
               rate: rate && +rate.toFixed(4), rate1: rate1 && +rate1.toFixed(4),
               rate2: rate2 && +rate2.toFixed(4) };
    }""")
    await browser.close()
    out.update({"gamma": gam, "det": det, "K": k, "sign": sign, "jsErrors": errors})
    return out

async def main():
    async with async_playwright() as pw:
        for gam, det, k, sign, secs in RUNS:
            print(json.dumps(await run_one(pw, gam, det, k, sign, secs)))

if __name__ == "__main__":
    asyncio.run(main())
