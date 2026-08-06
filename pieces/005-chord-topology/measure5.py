# 005 measurement #5 — the percussion pass. Ephemeral verifier.
# Prompted by Jie's studio visit (2026-08-06): "rhythmic drums would make it
# more watchable." Design answer: no sequencer — the event stream IS the
# drummer (sink arrival = kick, shadow death = hat tick, meeting = accent).
# The interesting claim is that REGIME becomes GROOVE for free.
#
# Verification is event-level (STATS counters at the event sites), so it is
# independent of AudioContext state — headless needs no user gesture. What a
# human must still judge: mix balance, kick weight, hat annoyance (listed in
# handoff as the live-ears item).
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   PD1 groove from regime — ridge-locked (g=1.15 d=0): kick inter-onset
#       CV < 0.35 (near-isochronous pulse). Slip (g=1.0 d=0.10): CV > 0.6
#       (broken beat, kicks cluster with meeting phrases).
#   PD2 hat density tracks border contact — hats/min: mesh (g=0.6 d=0.10)
#       highest, ridge lowest, slip between.
#   PD3 zero JS errors; percussion caps separate (no melodic starvation —
#       structural: PERC_CAP is its own counter; asserted by code review,
#       runtime check here = no errors + counters advance).
import asyncio, statistics
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
REGIMES = [
    ("ridge-locked", "?g=1.15&d=0"),
    ("slip-baseline", "?g=1.0&d=0.1"),
    ("mesh-slip", "?g=0.6&d=0.1"),
]
RUN_S = 50

def cv(times):
    if len(times) < 3: return None
    gaps = [b - a for a, b in zip(times, times[1:])]
    m = statistics.mean(gaps)
    return statistics.pstdev(gaps) / m if m > 0 else None

async def run():
    results = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        for name, qs in REGIMES:
            page = await browser.new_page(viewport={"width": 1280, "height": 800})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            await page.goto(BASE + qs)
            await page.wait_for_timeout(3000)          # bed carve + settle
            await page.evaluate("STATS.reset()")
            await page.wait_for_timeout(RUN_S * 1000)
            s = await page.evaluate(
                "({kicks: STATS.kicks, hats: STATS.hats, kickT: STATS.kickT.slice(),"
                "  meetings: STATS.meetings, shadows: STATS.shadows})")
            results[name] = {**s, "errors": errors}
            await page.close()
        await browser.close()

    print(f"{'regime':<14}{'kicks':>6}{'hats':>6}{'meet':>6}{'shad':>6}{'kickCV':>8}{'hats/min':>9}{'err':>5}")
    for name, r in results.items():
        c = cv(r["kickT"])
        hpm = r["hats"] / (RUN_S / 60)
        r["cv"], r["hpm"] = c, hpm
        print(f"{name:<14}{r['kicks']:>6}{r['hats']:>6}{r['meetings']:>6}{r['shadows']:>6}"
              f"{(f'{c:.3f}' if c is not None else '  n/a'):>8}{hpm:>9.1f}{len(r['errors']):>5}")

    ridge, slip, mesh = results["ridge-locked"], results["slip-baseline"], results["mesh-slip"]
    print("\nVERDICTS:")
    if ridge["cv"] is not None and slip["cv"] is not None:
        print(f"  PD1 ridge CV<0.35: {'PASS' if ridge['cv'] < 0.35 else 'FAIL'} ({ridge['cv']:.3f});"
              f" slip CV>0.6: {'PASS' if slip['cv'] > 0.6 else 'FAIL'} ({slip['cv']:.3f})")
    else:
        print("  PD1 UNDECIDABLE — too few kicks; that itself is a finding (report counts)")
    order = mesh["hpm"] > slip["hpm"] > ridge["hpm"]
    print(f"  PD2 hats/min mesh>slip>ridge: {'PASS' if order else 'FAIL'}"
          f" ({mesh['hpm']:.1f} / {slip['hpm']:.1f} / {ridge['hpm']:.1f})")
    errs = sum(len(r["errors"]) for r in results.values())
    print(f"  PD3 zero JS errors: {'PASS' if errs == 0 else 'FAIL'} ({errs})")
    for name, r in results.items():
        for e in r["errors"][:3]: print(f"    [{name}] {e}")

asyncio.run(run())
