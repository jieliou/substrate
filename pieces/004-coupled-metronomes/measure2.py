# 004 second pass — adjudicate jitter-vs-repulsion with the unwrapped-psi
# drift instrument. PREDICTIONS (written before running):
#   PA  K=0 drift rate = -Delta/(T(1+Delta)) = -0.0379 cyc/s at Delta=0.10.
#   PB  If hypothesis (a) [slip-counter jitter]: rate ~flat vs K (coupling
#       too weak / kicks cancel), previous "2 slips" were boundary noise.
#   PC  If hypothesis (b) [genuine repulsion]: |rate| grows with K at
#       sign=-1, and FALLS (or locks) at sign=+1 — the delayed-coupling
#       sign story confirmed either way it points.
import asyncio, json
from playwright.async_api import async_playwright

URL = "file:///Users/jie/Dev/substrate/pieces/004-coupled-metronomes/index.html"
RUNS = [  # (detune, K, sign, seconds)
    (0.10, 0.0, -1, 30),
    (0.10, 1.0, -1, 30),
    (0.10, 2.0, -1, 30),
    (0.10, 1.0, +1, 30),
    (0.10, 2.0, +1, 30),
]

async def run_one(pw, det, k, sign, secs):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    await page.wait_for_function("window.STATS !== undefined")
    await page.evaluate(f"window.setDet({det}); window.setK({k}); window.setSign({sign});")
    await page.wait_for_timeout(2000)
    await page.evaluate("window.STATS.reset()")
    await page.wait_for_timeout(secs * 1000)
    out = await page.evaluate("""() => {
      const S = window.STATS;
      const u = S.psiU, n = u.length;
      const t = S.psiT;
      const rate = n > 4 ? (u[n-1] - u[0]) / (t[n-1] - t[0]) : null;
      // piecewise: first vs second half rate (locks show as rate2 -> 0)
      const h = n >> 1;
      const rate1 = h > 2 ? (u[h] - u[0]) / (t[h] - t[0]) : null;
      const rate2 = h > 2 ? (u[n-1] - u[h]) / (t[n-1] - t[h]) : null;
      return { hearA: S.hearA, hearB: S.hearB, meetings: S.meetings,
               rate: rate && +rate.toFixed(4), rate1: rate1 && +rate1.toFixed(4),
               rate2: rate2 && +rate2.toFixed(4),
               uFirst: +u[0].toFixed(3), uLast: +u[n-1].toFixed(3) };
    }""")
    await browser.close()
    out.update({"det": det, "K": k, "sign": sign, "jsErrors": errors})
    return out

async def main():
    async with async_playwright() as pw:
        for det, k, sign, secs in RUNS:
            print(json.dumps(await run_one(pw, det, k, sign, secs)))

if __name__ == "__main__":
    asyncio.run(main())
