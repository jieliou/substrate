# 004 fifth pass — smoke test for the realised-beat readout.
# Checks: (a) the HUD beat figure tracks the measured common period,
# (b) the "faster than both" verdict appears exactly in the condition
# measure5 found it (K=4, D=0.10 at gamma=1.6) and not in the deaf run,
# (c) no JS errors, fps healthy.
import asyncio, json
from playwright.async_api import async_playwright

URL = "file:///Users/jie/Dev/substrate/pieces/004-coupled-metronomes/index.html"
RUNS = [(1.6, 0.10, 0.0, -1, 24), (1.6, 0.10, 4.0, -1, 30), (1.6, 0.10, 6.0, -1, 30)]

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
      const per = (n, t0, t1) => (n > 2 && t1 > t0) ? (t1 - t0) / (n - 1) : null;
      // tail-8 mean rebuilt from fire timestamps — the SAME window the HUD uses
      const tail = ts => { if (ts.length < 4) return null;
        const k = Math.min(8, ts.length - 1), a = ts[ts.length - 1 - k], b = ts[ts.length - 1];
        return (b - a) / k; };
      return { label: document.getElementById('regime').textContent,
               fps: document.getElementById('fps').textContent,
               perA: per(S.fireA, S.tA0, S.tA1), perB: per(S.fireB, S.tB0, S.tB1),
               tailA: tail(S.fireTA), tailB: tail(S.fireTB) };
    }""")
    await browser.close()
    out.update({"K": k, "det": det, "jsErrors": errors})
    return out

async def main():
    async with async_playwright() as pw:
        for gam, det, k, sign, secs in RUNS:
            r = await run_one(pw, gam, det, k, sign, secs)
            meas = tail = None
            if r["perA"] and r["perB"]:
                meas = round(0.5 * (r["perA"] + r["perB"]), 3)
            if r["tailA"] and r["tailB"]:
                tail = round(0.5 * (r["tailA"] + r["tailB"]), 3)
            print(json.dumps({**r, "runMeanBeat": meas, "tailBeat": tail}), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
