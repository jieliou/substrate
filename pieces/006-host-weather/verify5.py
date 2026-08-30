#!/usr/bin/env python3
"""006 pass 5 — the memory strip (developing L3's door).

L3's death (run 3): the ear recorded 561 strong marks and the strata built
every bead — but VIEW is 72 epochs (~3.6 min) while CAP holds ~2 h, and the
22:21 verdict frame sat 20 minutes after the last pulse: everything heard,
nothing visible. The ear heard; the eye cannot see history.

The strip: a footer band across the full canvas. x = epoch index on a fixed
day-long score (DAY_EPOCHS = 28800 = 24 h of listening; score time is epochs
HEARD, not wall time — the strip pauses when the ear closes, same no-wall-clock
law as the pulse organ). Each committed epoch writes one vertical tick into
its slot: height and colour from (regime, pulse), ember pulses taller and
warmer, strong pulses (>=0.5) deposit a bead above the tick. The band fills
left to right like a seismograph drum; after a full day the drum wraps.
Detail decays (strata forget past CAP); summary persists (the strip holds the
whole life). One glance holds the day. This is also the score the future
sound pass will read.

PREDICTIONS — written 2026-08-31 00:4x, BEFORE implementing/running
(charter discipline, craft rule 8):

S1 (nothing the ear heard is lost): replaying the full run-3 day
   (23,751 epochs) through the piece's own replayStrip path yields exactly
   561 beads — the count the ear recorded. Falsifier: any bead dropped
   (buffer overflow, wrap bug) or duplicated.

S2 (one glance holds the day): grouping run-3 strong marks into clusters
   (gap > 120 epochs), the strip must resolve them — >= 15 clusters, and
   every pair of consecutive cluster centres >= 10 px apart at a 1280 px
   canvas. (Hourly grid predicts ~52 px.) Falsifier: compression merges
   the day into an unreadable blob.

S3 (duration survives compression — the run-3 new sense): the Sunday
   weekly-recycle cluster (the 659 s breath near 05:00) spans >= 5x the
   median cluster's epoch extent on the strip. Duration-as-timbre must
   remain legible at day scale. Falsifier: at strip resolution all events
   flatten to indistinguishable single ticks.

S4 (JS-python organ equivalence, pass-3 convention): the tick buffer the
   page builds (Float32Array, f32 quantised) FNV-hashes identical to an
   independent python mirror of stripTick across all 23,751 epochs, and
   bead slot lists match exactly. Falsifier: the renderer and the mirror
   disagree anywhere.

S5 (instrument): live smoke — strip renders and fills from the left edge
   with slate founding ticks; zero JS errors; fps >= 50 (swiftshader
   baseline 96); stripCheck ok (last tick rebuilt from stored inputs is
   float-identical); rebuildCheck still ok (strata untouched).
"""
import asyncio, json, struct, time
from playwright.async_api import async_playwright

DIR = "/Users/jie/Dev/substrate/pieces/006-host-weather"
BASE = f"file://{DIR}/index.html"

# --- constants mirrored from index.html (must match exactly) ---
DAY_EPOCHS = 28800
STRIP_Y0 = -0.90
AMPS = [0.010, 0.016, 0.030, 0.046, 0.060]   # slate..straining (regime+1)
PULSE_AMP = 0.055
EMBER = [0.92, 0.52, 0.20]
REGCOL = [
    [0.42, 0.45, 0.48],
    [0.36, 0.53, 0.72],
    [0.32, 0.72, 0.80],
    [0.85, 0.60, 0.25],
    [0.88, 0.34, 0.18],
]

def f32(x):
    return struct.unpack('<f', struct.pack('<f', x))[0]

def strip_tick(i, regime, pulse):
    """Python mirror of stripTick — returns the 12 floats of one tick."""
    slot = i % DAY_EPOCHS
    x = -0.97 + 1.94 * (slot + 0.5) / DAY_EPOCHS
    p = pulse or 0
    base = REGCOL[regime + 1]
    if p > 0:
        col = [base[k] + (EMBER[k] - base[k]) * (0.25 + 0.75 * p) for k in range(3)]
    else:
        col = base
    amp = AMPS[regime + 1] + PULSE_AMP * p
    a = 0.10 + 0.55 * p
    return [x, STRIP_Y0, col[0], col[1], col[2], a,
            x, STRIP_Y0 + amp, col[0], col[1], col[2], a]

def fnv_f32(vals):
    h = 0x811c9dc5
    for v in vals:
        for b in struct.pack('<f', v):
            h ^= b
            h = (h * 0x01000193) & 0xFFFFFFFF
    return h

async def main():
    d = json.load(open(f"{DIR}/run3-workday-live.json"))
    eps = d['epochs']
    print(f"run 3: {len(eps)} epochs")

    # ---------- python-side S1/S2/S3 (properties of the data + mapping) ----------
    strong = [e for e in eps if (e.get('pulse') or 0) >= 0.5]
    print(f"S1 python: strong marks = {len(strong)} (expect 561)")

    clusters = []
    for e in strong:
        if clusters and e['i'] - clusters[-1][-1]['i'] <= 120:
            clusters[-1].append(e)
        else:
            clusters.append([e])
    centers = [(c[0]['i'] + c[-1]['i']) / 2 for c in clusters]
    extents = [max(1, c[-1]['i'] - c[0]['i']) for c in clusters]
    seps_px = [(centers[k+1] - centers[k]) / DAY_EPOCHS * 1.94 / 2 * 1280
               for k in range(len(centers) - 1)]
    min_sep = min(seps_px) if seps_px else 0
    s2 = len(clusters) >= 15 and min_sep >= 10
    print(f"S2: clusters={len(clusters)}, min consecutive sep={min_sep:.1f}px "
          f"-> {'PASS' if s2 else 'DIE'}")

    ext_sorted = sorted(extents)
    med_ext = ext_sorted[len(ext_sorted) // 2]
    max_ext = max(extents)
    k_max = extents.index(max_ext)
    s3 = max_ext >= 5 * med_ext
    print(f"S3: max cluster extent={max_ext} epochs (cluster {k_max}, "
          f"start i={clusters[k_max][0]['i']}), median={med_ext} "
          f"-> ratio {max_ext/med_ext:.1f}x -> {'PASS' if s3 else 'DIE'}")

    # python mirror hash over all ticks (last-write-wins per slot, in order)
    tick_floats = []
    bead_slots_py = []
    for e in eps:
        tick_floats.extend(strip_tick(e['i'], e['regime'], e.get('pulse') or 0))
        if (e.get('pulse') or 0) >= 0.5:
            bead_slots_py.append(e['i'] % DAY_EPOCHS)
    py_hash = fnv_f32(tick_floats)
    print(f"S4 python: tick stream hash={py_hash}, beads={len(bead_slots_py)}")

    # ---------- browser: real code path ----------
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(BASE)

        # live smoke first: let founding land + a few judged epochs
        await page.wait_for_timeout(45000)
        smoke = await page.evaluate("""() => ({
            n: STATS.epochs.length, founding: STATS.founding,
            errs: STATS.errors, fps: STATS.fps,
            stripCheck: STATS.stripCheck(),
            rebuildCheck: STATS.rebuildCheck(),
            stripWritten: STATS.stripWritten })""")
        print(f"S5 smoke: epochs={smoke['n']} founding={smoke['founding']} "
              f"fps={smoke['fps']:.0f} errs={smoke['errs']} "
              f"stripCheck={smoke['stripCheck']} rebuild ok={smoke['rebuildCheck']['ok']} "
              f"written={smoke['stripWritten']}")
        s5 = (not smoke['errs'] and not errors and smoke['fps'] >= 50
              and smoke['stripCheck']['ok'] and smoke['rebuildCheck']['ok'])
        await page.screenshot(path=f"{DIR}/pass5-smoke.png")

        # replay the full run-3 day through the piece's own strip path
        payload = [{"regime": e['regime'], "pulse": e.get('pulse') or 0}
                   for e in eps]
        rep = await page.evaluate("arr => STATS.replayStrip(arr)", payload)
        print(f"S1 js: beads={rep['beads']} ticks={rep['ticks']}")
        s1 = rep['beads'] == 561 == len(bead_slots_py)
        s4 = (rep['hash'] == py_hash and rep['beadSlots'] == bead_slots_py)
        print(f"S1 -> {'PASS' if s1 else 'DIE'}")
        print(f"S4: js hash={rep['hash']} vs py {py_hash}; "
              f"bead slots match={rep['beadSlots'] == bead_slots_py} "
              f"-> {'PASS' if s4 else 'DIE'}")

        # verdict frame: the whole second workday in one band
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{DIR}/workday3-strip.png")
        print(f"S5 -> {'PASS' if s5 else 'DIE'}")
        await browser.close()

    print("\nverdict:", "ALL PASS" if all([s1, s2, s3, s4, s5]) else "DEATHS ABOVE")

asyncio.run(main())
