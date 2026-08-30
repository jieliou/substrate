# 006 measurement #4 — the third workday (live memory strip).
# Same detached-listener protocol as day-ambient2.py, but the piece now
# carries the pass-5 memory strip. Runs 2-3 proved the ear (replay) and
# the organ (live); pass 5 was verified by REPLAY of run 3. This run asks
# whether the strip earns its keep LIVE: a whole workday growing on the
# footer band as it happens, so the final frame — unlike run 3's 22:21
# geometry-blind frame — holds the entire day at a glance. Launched
# 2026-08-31 02:3x, a MONDAY: crawl batches 08/14/20 + hourly crawlScan +
# 22:00 nightly automation; NO Sunday organs (weekly recycle 05:00,
# auto-prune 03:00 were Sunday-only).
#
# PREDICTIONS (written before launch, charter discipline):
#   M1 (the score fills): the strip's filled extent tracks epochs/28800
#      continuously — headless page never hides, so zero gaps; final
#      stripWritten == committed epochs count.
#   M2 (the strip answers L3 live): the FINAL frame carries >= 90% of
#      steady-state top-of-hour strong beads — nothing scrolls off,
#      because the strip does not scroll. (Run 3's verdict frame held
#      ~3.6 min; this one must hold ~20 h.)
#   M3 (Monday physiology): zero duration-bars > 5 min on the strip —
#      the 659 s recycle breath was a Sunday organ. Every strong event
#      today should be a ~1-2 min bead (crawlScan class). Falsifier: a
#      long bar appears = an unscheduled long-running organ (a finding).
#   M4 (instrument): zero JS errors across ~20 h; stripCheck ok at
#      close; rebuildCheck ok; fps at machine cadence throughout.
import asyncio, json, time
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/006-host-weather/index.html"
DEADLINE = time.time() + 71400        # ~22:30 Taipei tonight
POLL_S = 300

TINY = """() => {
  const e = STATS.epochs[STATS.epochs.length - 1] || null;
  return { n: STATS.epochs.length, founding: STATS.founding,
           errs: STATS.errors.length, fps: STATS.fps,
           stripWritten: STATS.stripWritten,
           last: e && { i: e.i, ratio: e.ratio, regime: e.regime,
                        sd: e.sd, pulse: e.pulse } };
}"""

FINAL = """() => ({
  t_end: Date.now() / 1000,
  harness_errors: STATS.errors,
  stripWritten: STATS.stripWritten,
  stripCheck: STATS.stripCheck(),
  rebuildCheck: STATS.rebuildCheck(),
  epochs: STATS.epochs,
})"""

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(BASE)
        with open("day-ambient3.jsonl", "a") as log:
            log.write(json.dumps({"t": time.time(), "event": "start"}) + "\n")
            log.flush()
            while time.time() < DEADLINE:
                await asyncio.sleep(POLL_S)
                try:
                    tiny = await page.evaluate(TINY)
                    tiny["t"] = time.time()
                    tiny["pageerrors"] = len(errors)
                    log.write(json.dumps(tiny) + "\n")
                    log.flush()
                except Exception as ex:
                    log.write(json.dumps({"t": time.time(), "event": "poll-error",
                                          "err": str(ex)}) + "\n")
                    log.flush()
            final = await page.evaluate(FINAL)
            final["pageerrors"] = errors
            with open("run4-workday-strip.json", "w") as f:
                json.dump(final, f)
            await page.screenshot(path="workday4-live-strip.png")
            log.write(json.dumps({"t": time.time(), "event": "end",
                                  "epochs": final["stripWritten"]}) + "\n")
            log.flush()
        await browser.close()

asyncio.run(main())
