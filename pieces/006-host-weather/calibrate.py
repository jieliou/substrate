# 006 sensor calibration — ephemeral, pre-band-tuning instrument probe.
# Question: how long must the fixed task be before host contention is
# legible through macOS QoS protection? Runs the bench at three M sizes,
# quiet vs saturated (cpu_count+2 busy procs), same browser context.
# Bands get set from THIS table, not from guesses (run-2 lesson).
import asyncio, os, subprocess, sys
from playwright.async_api import async_playwright

BENCH = """(M) => {
  const rep = () => {
    const t0 = performance.now();
    let x = 0x9e3779b9 >>> 0;
    for (let i = 0; i < M; i++) {
      x ^= x << 13; x >>>= 0; x ^= x >>> 17; x ^= x << 5; x >>>= 0;
    }
    window.__sink = x;
    return performance.now() - t0;
  };
  const t = [];
  for (let k = 0; k < 24; k++) t.push(rep());
  t.sort((a, b) => a - b);
  return { med: t[12], p90: t[Math.floor(24 * 0.9)] };
}"""

def busy(n, secs):
    code = f"import time\nt=time.time()+{secs}\nwhile time.time()<t: pass\n"
    return [subprocess.Popen([sys.executable, "-c", code]) for _ in range(n)]

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page()
        await page.goto("about:blank")
        for shift in (19, 21, 23):
            M = 1 << shift
            await page.evaluate(BENCH, M)          # warm
            quiet = await page.evaluate(BENCH, M)
            procs = busy((os.cpu_count() or 8) + 2, 14)
            await page.wait_for_timeout(2000)      # let load settle
            loaded = await page.evaluate(BENCH, M)
            for p in procs: p.kill()
            r = loaded["med"] / quiet["med"] if quiet["med"] else float("nan")
            print(f"M=1<<{shift}  quiet {quiet['med']:.3f}ms (p90 {quiet['p90']:.3f})"
                  f"  loaded {loaded['med']:.3f}ms (p90 {loaded['p90']:.3f})"
                  f"  ratio {r:.3f}")
        await browser.close()

asyncio.run(main())
