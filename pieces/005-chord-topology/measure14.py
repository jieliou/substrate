# 005 measurement #14 — the deep lease (fifteenth pass). Ephemeral verifier.
# One 600 s ghost window (g=1.15 d=-0.10). The biography layer — which never
# forgets a meeting — arbitrates the deepest dwell's "never" between three
# shapes: WALL (kinematic bound, more time buys nothing), RARITY (stationary
# extreme-value tail), LEGISLATION (the bed itself is carved west; records
# land late instead of early-dense).
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P38 rent recurs at scale — west excursions (meet x < 9.5, moat not line)
#       >= 20; west played frets >= 24.
#   P39 deepest dwell stays dark — zero played frets in x 4.0-5.25 (phi<0);
#       min meeting x >= 5.5.
#   P40 wall is stationary — depth(300)/depth(600) >= 0.8 (baseline x0=10.6)
#       AND depth-record count among excursions <= ln(n)+2.
#   P41 instrument — zero JS errors, fps >= 60 at end, meetings 250-450.
import asyncio, json, math
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
SECS, POLL = 600, 30
SEAM_X0 = 10.6          # east-run seam baseline (run13 min meet x)
MOAT_X = 9.5            # west excursion = meeting x < MOAT_X (P35 lesson)
DEEP_LO, DEEP_HI = 4.0, 5.25

async def main():
    out = {"regime": "g=1.15 d=-0.10", "secs": SECS}
    polls, errors = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(BASE + "?g=1.15&d=-0.10")
        for t in range(POLL, SECS + 1, POLL):
            await page.wait_for_timeout(POLL * 1000)
            snap = await page.evaluate("""() => {
                const s = window.score();
                let mn = null;
                for (const x of STATS.meetX) if (mn === null || x < mn) mn = x;
                return { meetings: STATS.meetings, playedW: s.playedW,
                         playedE: s.playedE, minx: mn };
            }""")
            snap["t"] = t
            polls.append(snap)
        final = await page.evaluate("""() => ({
            meetX: STATS.meetX, meetT: STATS.meetT,
            meetings: STATS.meetings, kicks: STATS.kicks,
            organs: ORGANS.length, score: window.score(),
            fps: (document.getElementById('fps') || {}).textContent || null })""")
        await page.screenshot(path="score-deep.png")
        await browser.close()

    # --- analysis ---
    t0 = final["meetT"][0] if final["meetT"] else 0.0
    ev = sorted(
        (t - t0, x) for x, t in zip(final["meetX"], final["meetT"]) if x < MOAT_X)
    n = len(ev)
    records, cur = [], None
    for t, x in ev:
        if cur is None or x < cur:
            cur = x
            records.append({"t": round(t, 1), "x": round(x, 2)})
    minx = cur
    s = final["score"]
    deep_played = [f for f in s["frets"]
                   if DEEP_LO <= f["x"] <= DEEP_HI and f["phi"] < 0 and f["played"]]
    depth = {p["t"]: (SEAM_X0 - p["minx"]) if p["minx"] is not None else 0.0
             for p in polls}
    d300, d600 = depth.get(300, 0.0), depth.get(600, 0.0)
    ratio = (d300 / d600) if d600 > 0 else None
    rec_limit = (math.log(n) + 2) if n > 0 else None
    fps_digits = "".join(c for c in (final["fps"] or "") if c.isdigit())
    fps = int(fps_digits) if fps_digits else None

    out["polls"] = polls
    out["excursions"] = {"n": n, "minx": minx,
                         "records": records, "rec_limit": rec_limit,
                         "first_third_records": sum(1 for r in records
                                                    if ev and r["t"] <= ev[-1][0] / 3)}
    out["deep_band"] = {"played": len(deep_played),
                        "frets": [{"x": f["x"], "phi": f["phi"]} for f in deep_played]}
    out["depth"] = {"d300": round(d300, 2), "d600": round(d600, 2),
                    "ratio": round(ratio, 3) if ratio is not None else None}
    out["totals"] = {"meetings": final["meetings"], "kicks": final["kicks"],
                     "organs": final["organs"], "playedW": s["playedW"],
                     "playedE": s["playedE"], "fretW": s["fretW"],
                     "fretE": s["fretE"], "fps": fps}
    out["errors"] = errors

    out["P38"] = "PASS" if (n >= 20 and s["playedW"] >= 24) else "FAIL"
    out["P39"] = "PASS" if (not deep_played and (minx is None or minx >= 5.5)) else "FAIL"
    out["P40"] = ("PASS" if (ratio is not None and ratio >= 0.8
                             and rec_limit is not None
                             and len(records) <= rec_limit) else "FAIL")
    out["P41"] = ("PASS" if (not errors and fps and fps >= 60
                             and 250 <= final["meetings"] <= 450) else "FAIL")

    with open("run14-deeplease.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in
                      ["excursions", "deep_band", "depth", "totals",
                       "P38", "P39", "P40", "P41"]}, indent=1))

asyncio.run(main())
