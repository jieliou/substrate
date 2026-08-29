# 006 measurement #2 — the first workday (long ambient run).
# Detached day-long listener: opens the piece once, polls a TINY snapshot
# every 5 min (the run-1 autopsy showed the harness's own evaluate is
# weather — polls stay small and sparse, and every poll is timestamped so
# it can be identified in the strata it may itself cause). Terminates at a
# fixed deadline, dumps the full epoch record + a preserved-buffer frame.
#
# QUESTION (written before the run): can the piece see my workday?
# The host's KNOWN schedule today (Asia/Taipei):
#   ~06:30 morning ritual (bot session, file writes)
#   ~08:00 / 14:00 / 20:00 crawl batches (scrapling + camoufox browsers)
#   hourly heartbeats (bot session tool calls)
#   ~22:00 evening automation (fresh headless claude session + git)
# PREDICTIONS:
#   D1 the crawl batches are the loudest regular weather — camoufox is a
#      whole extra browser; each batch window shows a sustained regime
#      lift (>= 3 consecutive epochs above still) within +-20 min of
#      08:00 / 14:00 / 20:00.
#   D2 heartbeat beats are visible but small — brief breathing flickers
#      near hour marks, not sustained lifts.
#   D3 the quietest hours are 03:00-06:00 (no schedule, no Jie).
#   D4 GC heartbeat persists all day at roughly page-age-regular
#      intervals, and stays distinguishable from host weather because its
#      frame-sd co-bursts (the body signs its own spikes).
import asyncio, json, time, base64
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/006-host-weather/index.html"
DEADLINE = time.time() + 71500        # ~22:30 Taipei tonight
POLL_S = 300

TINY = """() => {
  const e = STATS.epochs[STATS.epochs.length - 1] || null;
  return { n: STATS.epochs.length, founding: STATS.founding,
           errs: STATS.errors.length, fps: STATS.fps,
           last: e && { i: e.i, ratio: e.ratio, regime: e.regime, sd: e.sd } };
}"""

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(BASE)
        with open("day-ambient.jsonl", "a") as log:
            log.write(json.dumps({"t": time.time(), "event": "start"}) + "\n")
            log.flush()
            while time.time() < DEADLINE:
                await page.wait_for_timeout(POLL_S * 1000)
                snap = await page.evaluate(TINY)
                snap["t"] = time.time()
                log.write(json.dumps(snap) + "\n")
                log.flush()
        full = await page.evaluate("() => STATS.epochs")
        with open("run2-workday.json", "w") as f:
            json.dump({"t_end": time.time(), "harness_errors": errors,
                       "epochs": full}, f)
        d = await page.evaluate(
            "() => document.getElementById('c').toDataURL('image/png')")
        with open("workday.png", "wb") as f:
            f.write(base64.b64decode(d.split(",", 1)[1]))
        await browser.close()

asyncio.run(main())
