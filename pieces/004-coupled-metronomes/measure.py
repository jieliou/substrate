# 004 measurement — first light. Ephemeral verifier (craft rule 7: 驗證裝置化).
# Conditions probe the predictions written in index.html BEFORE this ran:
#   P1: K=0 reproduces 003     P2: sparse hears, narrow tongue
#   P3: lock at nonzero lag    P4: near-threshold intermittency
import asyncio, json, statistics
from playwright.async_api import async_playwright

URL = "file:///Users/jie/Dev/substrate/pieces/004-coupled-metronomes/index.html"
RUNS = [  # (detune, K, seconds)
    (0.10, 0.0, 20),   # P1 baseline — compare 003 row Δ=0.10
    (0.10, 0.6, 20),   # threshold guess
    (0.10, 1.5, 20),   # strong coupling — lock?
    (0.30, 1.5, 20),   # high detune — P2 says no lock
]

async def run_one(pw, det, k, secs):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    await page.wait_for_function("window.STATS !== undefined")
    await page.evaluate(f"window.setDet({det}); window.setK({k});")
    await page.wait_for_timeout(2000)              # settle initial claims
    await page.evaluate("window.STATS.reset()")
    await page.wait_for_timeout(secs * 1000)
    out = await page.evaluate("""() => {
      const S = window.STATS, st = window.state();
      const psi = S.psi, n = psi.length;
      const w = Math.min(n, 32);
      let mn = 1e9, mx = -1e9;
      for (let i = n - w; i < n; i++) { if (psi[i] < mn) mn = psi[i]; if (psi[i] > mx) mx = psi[i]; }
      const gaps = [];
      for (let i = 1; i < S.meetT.length; i++) gaps.push(S.meetT[i] - S.meetT[i-1]);
      return {
        meetings: S.meetings, shadows: S.shadows, slips: S.slips,
        hearA: S.hearA, hearB: S.hearB,
        psiFirst: n ? +psi[0].toFixed(3) : null,
        psiLast: n ? +psi[n-1].toFixed(3) : null,
        tailSpread: n ? +(mx - mn).toFixed(3) : null,
        maxMeetGap: gaps.length ? +Math.max(...gaps).toFixed(2) : null,
        pulses: window.pulses.length, t: +st.t.toFixed(1)
      };
    }""")
    fps = await page.evaluate("document.getElementById('fps').textContent")
    regime = await page.evaluate("document.getElementById('regime').textContent")
    await browser.close()
    out.update({"det": det, "K": k, "fps": fps, "regime": regime, "jsErrors": errors})
    return out

async def main():
    async with async_playwright() as pw:
        for det, k, secs in RUNS:
            r = await run_one(pw, det, k, secs)
            print(json.dumps(r))

if __name__ == "__main__":
    asyncio.run(main())
