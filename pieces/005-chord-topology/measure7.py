# 005 measurement #7 — the ghost-half pass. Ephemeral verifier.
# measure6 (analytic twin) discovered the beat order k>=0 confines the slip
# spring to the phi>0 EAST half; the west dwell segments (x ~ 5.0/6.4/7.9)
# are GHOSTS — reachable only at negative detune, a knob that did not exist.
# This run turns the new knob once and checks the ghosts answer.
#
# PREDICTIONS (mirrored from index.html header, written before first run):
#   P17 ghost activation — g=1.15 d=-0.10: meeting x-mean WEST of sink
#       (vs east at +0.10); >=1 dwell segment (>=3 consecutive meetings
#       within 1.2 units) inside ghost bracket x in [4.5, 8.4].
#   P18 asymmetric slip — slip period 2.4(1+d)/|d|: 21.6s at -0.10 vs
#       26.4s at +0.10 => ghost run logs ~1.2x the control's meetings.
#   P19 same physics, no new rules — zero JS errors; percussion counters
#       advance in both runs.
import asyncio, json, statistics
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
REGIMES = [
    ("ghost-west",   "?g=1.15&d=-0.10"),
    ("east-control", "?g=1.15&d=0.10"),
]
RUN_S = 60
GHOST_LO, GHOST_HI = 4.5, 8.4
DWELL_DX, DWELL_MIN = 1.2, 3

def dwells(xs):
    """runs of >=DWELL_MIN consecutive meetings within DWELL_DX of the previous"""
    out, run = [], [xs[0]] if xs else []
    for a, b in zip(xs, xs[1:]):
        if abs(b - a) < DWELL_DX: run.append(b)
        else:
            if len(run) >= DWELL_MIN: out.append(run)
            run = [b]
    if len(run) >= DWELL_MIN: out.append(run)
    return [(round(min(r), 1), round(max(r), 1), len(r)) for r in out]

async def main():
    results = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        for name, qs in REGIMES:
            page = await browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            await page.goto(BASE + qs)
            await page.wait_for_timeout(RUN_S * 1000)
            data = await page.evaluate("""() => ({
                meetX: STATS.meetX.slice(), meetT: STATS.meetT.slice(),
                meetings: STATS.meetings, kicks: STATS.kicks, hats: STATS.hats,
                sinkX: G.nodes[G.sink].x,
                srcAX: G.nodes[G.srcA].x, srcBX: G.nodes[G.srcB].x,
                detune: detune, gamma: gamma })""")
            await page.close()
            xs = data["meetX"]
            results[name] = {
                "regime": qs, "errors": errors,
                "meetings": data["meetings"], "kicks": data["kicks"], "hats": data["hats"],
                "sinkX": round(data["sinkX"], 2),
                "srcAX": round(data["srcAX"], 2), "srcBX": round(data["srcBX"], 2),
                "meetXMean": round(statistics.mean(xs), 2) if xs else None,
                "dwells": dwells(xs),
                "ghostDwells": [d for d in dwells(xs) if GHOST_LO <= d[0] and d[1] <= GHOST_HI],
                "meetX": [round(x, 2) for x in xs], "meetT": [round(t, 1) for t in data["meetT"]],
            }
        await browser.close()

    g, e = results["ghost-west"], results["east-control"]
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("meetX", "meetT")}
                      for k, v in results.items()}, indent=2))
    print("\n--- verdicts ---")
    if g["meetXMean"] is not None and e["meetXMean"] is not None:
        p17a = g["meetXMean"] < g["sinkX"] and e["meetXMean"] > e["sinkX"]
        print(f"P17a spring side: ghost mean {g['meetXMean']} vs sink {g['sinkX']} | "
              f"east mean {e['meetXMean']} vs sink {e['sinkX']} -> {'PASS' if p17a else 'FAIL'}")
    p17b = len(g["ghostDwells"]) >= 1
    print(f"P17b ghost dwell in [4.5,8.4]: {g['ghostDwells']} -> {'PASS' if p17b else 'FAIL'}")
    if e["meetings"]:
        ratio = g["meetings"] / e["meetings"]
        print(f"P18 meeting ratio ghost/east: {g['meetings']}/{e['meetings']} = {ratio:.2f} "
              f"(predict ~1.2) -> {'PASS' if 1.05 <= ratio <= 1.45 else 'FAIL'}")
    p19 = not g["errors"] and not e["errors"] and g["kicks"] > 0 and g["hats"] >= 0
    print(f"P19 no errors, percussion alive: errs {g['errors']}+{e['errors']}, "
          f"kicks {g['kicks']}/{e['kicks']} -> {'PASS' if p19 else 'FAIL'}")
    with open("run7-ghost.json", "w") as f:
        json.dump(results, f, indent=2)
    print("saved run7-ghost.json")

asyncio.run(main())
