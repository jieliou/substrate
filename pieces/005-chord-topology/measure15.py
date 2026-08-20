# 005 measurement #15 — the constitutional moment (sixteenth pass).
# Ephemeral verifier. One 600 s run, three eras: founding+adjournment
# (g=1.15 d=-0.10, 0-300), coup/interregnum (setGamma(1.00), 300-360),
# restoration (setGamma(1.15), 360-600). Question: can the adjourned
# legislature be reconvened — does the frontier reopen?
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P42 baseline replicates — <= 2 new played nodes t=90..300; phase-I west
#       excursions (x < 9.5) <= 3, all inside the first minute.
#   P43 interregnum carves — fretE or fretW shifts >= 10% (t=300 vs 360);
#       meetings continue during the coup.
#   P44 frontier reopens — >= 6 new played nodes in 360-600; sub: growth
#       concentrates in the first ~90 s post-restoration, then decays.
#   P45 deep west still dark — zero played nodes in x 4.0-5.25;
#       min meet x >= 5.5.
#   P46 instrument — zero JS errors, fps >= 60, biomass finite every poll.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
SECS, POLL = 600, 30
COUP_T, RESTORE_T = 300, 360
MOAT_X = 9.5
DEEP_LO, DEEP_HI = 4.0, 5.25

SNAP_JS = """() => {
    const s = window.score(), st = window.state();
    let pt = 0, pw = 0, mn = null;
    for (const n of G.nodes) if (n.played) { pt++; if (n.x < 9.5) pw++; }
    for (const x of STATS.meetX) if (mn === null || x < mn) mn = x;
    return { pageT: +st.t.toFixed(1), meetings: STATS.meetings,
             playedNodes: pt, playedNodesW: pw, minx: mn,
             fretE: s.fretE, fretW: s.fretW,
             playedE: s.playedE, playedW: s.playedW,
             biomass: st.biomass, shareA: st.terr.shareA, gamma: st.gamma };
}"""

async def main():
    out = {"regime": "g=1.15 d=-0.10, coup g=1.00 @300-360", "secs": SECS}
    polls, errors = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(BASE + "?g=1.15&d=-0.10")
        for t in range(POLL, SECS + 1, POLL):
            await page.wait_for_timeout(POLL * 1000)
            snap = await page.evaluate(SNAP_JS)
            snap["t"] = t
            polls.append(snap)
            if t == COUP_T:
                await page.evaluate("() => window.setGamma(1.00)")
            elif t == RESTORE_T:
                await page.evaluate("() => window.setGamma(1.15)")
        final = await page.evaluate("""() => ({
            meetX: STATS.meetX, meetT: STATS.meetT, kicks: STATS.kicks,
            score: window.score(),
            deepNodes: G.nodes.filter(n => n.played && n.x >= 4.0 && n.x <= 5.25).length,
            fps: (document.getElementById('fps') || {}).textContent || null })""")
        await page.screenshot(path="score-coup.png")
        await browser.close()

    by_t = {p["t"]: p for p in polls}
    pageT = lambda t: by_t[t]["pageT"]
    # phase-I excursions (meetT vs page clock)
    exc1 = [(t, x) for x, t in zip(final["meetX"], final["meetT"])
            if x < MOAT_X and t <= pageT(COUP_T)]
    exc3 = [(t, x) for x, t in zip(final["meetX"], final["meetT"])
            if x < MOAT_X and t > pageT(RESTORE_T)]
    minx = min(final["meetX"]) if final["meetX"] else None
    growth_frozen = by_t[300]["playedNodes"] - by_t[90]["playedNodes"]
    growth_post = by_t[600]["playedNodes"] - by_t[360]["playedNodes"]
    buckets = {f"{t-60}-{t}": by_t[t]["playedNodes"] - by_t[t-60]["playedNodes"]
               for t in range(120, 601, 60)}
    fe0, fe1 = by_t[300]["fretE"], by_t[360]["fretE"]
    fw0, fw1 = by_t[300]["fretW"], by_t[360]["fretW"]
    fret_shift = max(abs(fe1 - fe0) / max(fe0, 1), abs(fw1 - fw0) / max(fw0, 1))
    coup_meets = by_t[360]["meetings"] - by_t[300]["meetings"]
    first_min_ok = all(t - final["meetT"][0] < 60 for t, x in exc1) if exc1 else True
    fps_digits = "".join(c for c in (final["fps"] or "") if c.isdigit())
    fps = int(fps_digits) if fps_digits else None
    bio_ok = all(isinstance(p["biomass"], (int, float)) and p["biomass"] == p["biomass"]
                 for p in polls)

    out["polls"] = polls
    out["phase1"] = {"excursions": len(exc1), "all_first_minute": first_min_ok,
                     "growth_90_300": growth_frozen}
    out["coup"] = {"fret_shift": round(fret_shift, 3), "meetings": coup_meets,
                   "shareA_300": by_t[300]["shareA"], "shareA_360": by_t[360]["shareA"]}
    out["post"] = {"growth_360_600": growth_post, "excursions": len(exc3),
                   "buckets": buckets}
    out["deep"] = {"deepNodes": final["deepNodes"], "minx": round(minx, 2) if minx else None}
    out["totals"] = {"meetings": polls[-1]["meetings"], "kicks": final["kicks"],
                     "fps": fps, "playedNodes_final": by_t[600]["playedNodes"]}
    out["errors"] = errors

    out["P42"] = "PASS" if (growth_frozen <= 2 and len(exc1) <= 3 and first_min_ok) else "FAIL"
    out["P43"] = "PASS" if (fret_shift >= 0.10 and coup_meets > 0) else "FAIL"
    out["P44"] = "PASS" if growth_post >= 6 else "FAIL"
    out["P45"] = "PASS" if (final["deepNodes"] == 0 and (minx is None or minx >= 5.5)) else "FAIL"
    out["P46"] = "PASS" if (not errors and fps and fps >= 60 and bio_ok) else "FAIL"

    with open("run15-coup.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in
                      ["phase1", "coup", "post", "deep", "totals",
                       "P42", "P43", "P44", "P45", "P46"]}, indent=1))

asyncio.run(main())
