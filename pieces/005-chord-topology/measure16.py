# 005 measurement #16 — the slow restoration (seventeenth pass).
# Ephemeral verifier. One 600 s run, four eras: founding+adjournment
# (g=1.15 d=-0.10, 0-300), coup/interregnum (setGamma(1.00), 300-360,
# identical to pass sixteen — internal control), SLOW restoration
# (gamma ramped linearly 1.00 -> 1.15 over 120 s, one step per 5 s,
# 360-480), settled ridge (480-600). Question: is the silent return
# the ridge law's doing or the return direction's? Pass sixteen could
# not tell — law and direction changed together. Here the return
# marches home under the mesh's own constitution first.
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P47 three-peat determinism — founding replicates (played ~54, west ~8,
#       minx ~8.06 at t=300); coup minute sings again (>= 20 new played
#       nodes 300-360, minx <= 6.0, shareA -> ~0.50).
#   P48 the separation — LAW wins: early ramp (360-420, g < ~1.07) adds
#       >= 6 played nodes, >= 1 west of x 9.5; late ramp + settle
#       (420-600) adds <= 2. Direction wins if all of 360-600 adds <= 2.
#   P49 flesh clock is law-gated — shareA <= 0.60 until g crosses ~1.10
#       (t ~ 440), crosses 0.70 only after t ~ 500, finishes 0.70-0.76.
#       Falsifier: >= 0.65 before t=440.
#   P50 instrument — zero JS errors, fps >= 60, biomass finite every
#       poll, sampled gamma walks the ramp (>= 3 distinct mid values).
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
SECS, TICK = 600, 5
COUP_T, RAMP_T0, RAMP_T1 = 300, 360, 480
G_LO, G_HI = 1.00, 1.15

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
    out = {"regime": "g=1.15 d=-0.10; coup g=1.00 @300; ramp 1.00->1.15 @360-480; settle @480-600",
           "secs": SECS}
    polls, errors = [], []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page(viewport={"width": 1280, "height": 800})
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(BASE + "?g=1.15&d=-0.10")
        for t in range(TICK, SECS + 1, TICK):
            await page.wait_for_timeout(TICK * 1000)
            if t == COUP_T:
                await page.evaluate("() => window.setGamma(1.00)")
            elif RAMP_T0 < t <= RAMP_T1:
                g = G_LO + (G_HI - G_LO) * (t - RAMP_T0) / (RAMP_T1 - RAMP_T0)
                await page.evaluate(f"() => window.setGamma({g:.4f})")
            # poll: 30 s cadence through the founding, 15 s from the coup on
            if (t <= COUP_T and t % 30 == 0) or (t > COUP_T and t % 15 == 0):
                snap = await page.evaluate(SNAP_JS)
                snap["t"] = t
                polls.append(snap)
        final = await page.evaluate("""() => ({
            meetX: STATS.meetX, meetT: STATS.meetT, kicks: STATS.kicks,
            score: window.score(),
            deepNodes: G.nodes.filter(n => n.played && n.x >= 4.0 && n.x <= 5.25).length,
            fps: (document.getElementById('fps') || {}).textContent || null })""")
        await page.screenshot(path="score-slowramp.png")
        await browser.close()
    out["polls"] = polls
    out["final"] = final
    out["errors"] = errors
    with open("run16-slowramp.json", "w") as f:
        json.dump(out, f, indent=1)
    # quick console digest
    for p in polls:
        print(p["t"], "g=%.3f" % p["gamma"], "meet", p["meetings"],
              "played", p["playedNodes"], "W", p["playedNodesW"],
              "minx", p["minx"], "shareA", "%.3f" % p["shareA"])
    print("deepNodes", final["deepNodes"], "errors", len(errors))

asyncio.run(main())
