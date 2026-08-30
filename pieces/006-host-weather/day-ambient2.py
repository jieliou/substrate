# 006 measurement #3 — the second workday (live organ).
# Same detached-listener protocol as day-ambient.py (run 2), but the piece
# now carries the pass-3 persistence ear. Run 2 proved the organ on REPLAY
# (19/19 hourly pulses, zero off-hour strong marks); this run asks whether
# it fires LIVE, in the strata, as the day happens. Launched 2026-08-30
# 02:3x — a Sunday: the host's schedule differs from run 2's Saturday
# (auto-prune 03:00, weekly recycle 05:00, finance scan 09:00 — all
# top-of-hour, so they COINCIDE with the crawlScan pulse grid and cannot
# be separated by timing alone; only amplitude/duration could tell them
# apart, and the wall may flatten that distinction).
#
# PREDICTIONS (written before launch, charter discipline):
#   L1 (organ fires live): >= 90% of steady-state top-of-hours (birth and
#      fill era excluded) carry a strong pulse (pulse >= 0.5) in epochs
#      landing 0-3 min after the hour. Replay said 19/19; live gets a 90%
#      bar because live founding/fill conditions vary.
#   L2 (no unscheduled fire): zero strong pulses landing entirely outside
#      top-of-hour +-5 min windows. Falsifier: unscheduled saturation
#      exists (Spotlight, backupd, ...) — which would itself be a finding.
#   L3 (beads in the strata): the final preserved frame (last ~2 h of
#      retained epochs, CAP 2400) shows >= 2 visible ember beads.
#   L4 (organ is founding-independent): the launcher-storm founding does
#      NOT distort the organ — pulses fire correctly because the rolling
#      median self-baselines. (The identity/legibility split, verified.)
import asyncio, json, time, base64
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/006-host-weather/index.html"
DEADLINE = time.time() + 71400        # ~22:30 Taipei tonight
POLL_S = 300

TINY = """() => {
  const e = STATS.epochs[STATS.epochs.length - 1] || null;
  return { n: STATS.epochs.length, founding: STATS.founding,
           errs: STATS.errors.length, fps: STATS.fps,
           last: e && { i: e.i, ratio: e.ratio, regime: e.regime,
                        sd: e.sd, pulse: e.pulse } };
}"""

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(BASE)
        with open("day-ambient2.jsonl", "a") as log:
            log.write(json.dumps({"t": time.time(), "event": "start"}) + "\n")
            log.flush()
            while time.time() < DEADLINE:
                await page.wait_for_timeout(POLL_S * 1000)
                snap = await page.evaluate(TINY)
                snap["t"] = time.time()
                log.write(json.dumps(snap) + "\n")
                log.flush()
        full = await page.evaluate("() => STATS.epochs")
        with open("run3-workday-live.json", "w") as f:
            json.dump({"t_end": time.time(), "harness_errors": errors,
                       "epochs": full}, f)
        d = await page.evaluate(
            "() => document.getElementById('c').toDataURL('image/png')")
        with open("workday2.png", "wb") as f:
            f.write(base64.b64decode(d.split(",", 1)[1]))
        await browser.close()

asyncio.run(main())

# ============================================================
# RESULTS (2026-08-30 22:4x — verdicts on L1-L4, analysis inline in session):
#   L1 PASS 18/20 (exactly at the 90% bar). The two misses (03:00 deaf,
#      04:00 faint 0.33) are the ORGAN'S OWN YOUTH: the rolling median was
#      still contaminated by birth-era elevated benches — the ear needs
#      ~2 hours to forget its own birth before it can hear the world.
#      The two-layer split (founding=identity / slow median=ruler) has its
#      own smaller birth-certificate problem, now quantified.
#   L2 letter-DIE, spirit-PASS. 173 "off-window" strong marks — ALL inside
#      the 05:00 event, which ran 659s (11 min): Sunday weekly recycle
#      (cron 0 5 * * 0), ten times longer than the hourly scan. Zero
#      unscheduled events all day. The prediction's ±3min window was
#      ignorance about job durations, not an organ fault. NEW SENSE
#      DISCOVERED: the strata can now tell the host's organs apart by
#      DURATION — recycle = 11-min ember bar, scan = 1-min bead.
#   L3 DIE — instrument-geometry ignorance: VIEW=72 epochs (~3.6 min) is
#      the visible window, not CAP (~2 h). The beads were recorded (561
#      strong epochs, ember geometry built) but scrolled off before the
#      22:21 frame. The eye cannot see what the ear heard. Opens the next
#      door: a memory-strip 顯影 (retained epochs compressed into a
#      footer band) so one glance holds the day.
#   L4 PASS — founding was storm-inflated (early ratios ~0.94), the organ
#      self-baselined and fired correctly: identity/legibility split
#      verified LIVE.
#   Instrument: 23,751 epochs, zero JS errors, zero harness errors.
# ============================================================
