# 005 measurement #13 — the score pass (fourteenth). Ephemeral verifier.
# The analytic twin moves into the page: phi = T_A - T_B on the LIVE bed,
# frets = live edges where the fields oppose hard (dense co-arrival
# isolines), biography lights the played bars. This run checks the map
# against measure6's geography and renders measure7's refusal.
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P34 twin comes home — lock bed (g=1.15 d=0): frets in BOTH halves;
#       west frets recover >= 2 of the three ghost dwells x ~ 5.0/6.4/7.9
#       (within 1.0, phi < 0).
#   P35 biography lights the east — g=1.15 d=+0.10, 60 s: playedE >= 4,
#       playedW == 0.
#   P36 confiscation rendered — g=1.15 d=-0.10, 60 s: playedW <= 1
#       despite >= 15 meetings (the clock cannot buy the west).
#   P37 display-only — zero JS errors; meetings/kicks in regime ranges.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
GHOST_X = [5.0, 6.4, 7.9]

async def run_regime(browser, qs, secs, shot=None):
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(BASE + qs)
    await page.wait_for_timeout(secs * 1000)
    data = await page.evaluate("""() => ({
        score: window.score(), meetings: STATS.meetings, kicks: STATS.kicks,
        organs: ORGANS.length, sinkX: G.nodes[G.sink].x,
        detune: detune, gamma: gamma })""")
    if shot:
        await page.screenshot(path=shot)
    await page.close()
    data["errors"] = errors
    return data

async def main():
    out = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])

        # --- P34: lock bed, map only (12 s: one refresh + settle) ---
        lock = await run_regime(browser, "?g=1.15&d=0", 12, shot="score-lock.png")
        s = lock["score"]
        west = [f for f in s["frets"] if f["phi"] < 0]
        hits = []
        for gx in GHOST_X:
            near = [f for f in west if abs(f["x"] - gx) <= 1.0]
            if near: hits.append({"ghost_x": gx, "n": len(near),
                                  "xs": sorted(round(f["x"], 1) for f in near)[:6]})
        p34 = s["fretE"] > 0 and s["fretW"] > 0 and len(hits) >= 2
        out["lock"] = {"fretE": s["fretE"], "fretW": s["fretW"],
                       "ghost_dwell_hits": hits, "errors": lock["errors"],
                       "P34": "PASS" if p34 else "FAIL"}

        # --- P35: east slip, biography lights east only ---
        east = await run_regime(browser, "?g=1.15&d=0.10", 60, shot="score-east.png")
        s = east["score"]
        p35 = s["playedE"] >= 4 and s["playedW"] == 0
        out["east"] = {"fretE": s["fretE"], "fretW": s["fretW"],
                       "playedE": s["playedE"], "playedW": s["playedW"],
                       "meetings": east["meetings"], "kicks": east["kicks"],
                       "organs": east["organs"], "errors": east["errors"],
                       "P35": "PASS" if p35 else "FAIL"}

        # --- P36: ghost run, west must stay dark ---
        ghost = await run_regime(browser, "?g=1.15&d=-0.10", 60, shot="score-ghost.png")
        s = ghost["score"]
        p36 = s["playedW"] <= 1 and ghost["meetings"] >= 15
        out["ghost"] = {"fretE": s["fretE"], "fretW": s["fretW"],
                        "playedE": s["playedE"], "playedW": s["playedW"],
                        "meetings": ghost["meetings"], "kicks": ghost["kicks"],
                        "organs": ghost["organs"], "errors": ghost["errors"],
                        "P36": "PASS" if p36 else "FAIL"}

        await browser.close()

    all_err = out["lock"]["errors"] + out["east"]["errors"] + out["ghost"]["errors"]
    out["P37"] = "PASS" if not all_err else "FAIL"
    with open("run13-score.json", "w") as f:
        json.dump(out, f, indent=1)
    for k in ("lock", "east", "ghost"):
        r = out[k]
        print(k, {kk: vv for kk, vv in r.items() if kk not in ("errors", "ghost_dwell_hits")})
    print("ghost_dwell_hits:", out["lock"]["ghost_dwell_hits"])
    print("P37:", out["P37"], "errors:", all_err[:3])

asyncio.run(main())
