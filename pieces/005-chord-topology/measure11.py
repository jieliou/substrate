# 005 measurement #11 — the biography sweep (鬼城壽命 vs 東都年資). Ephemeral verifier.
#
# measure10 measured ONE ghost's lifetime: built east for 180s, then held
# g=1.00 and watched it die at t+180-210. That number — ~200s — is either
# a MATERIAL CONSTANT of the bed (a starvation clock that ticks the same
# for every ghost) or a FUNCTION OF HISTORY (a capital held longer digs a
# deeper groove: more organ mass, more mature mutual feeding, slower death).
# The two-layer law says the flesh forgets in ~200s; this run asks whether
# "200s" is a property of flesh, or of THIS flesh's particular biography.
#
# Protocol: three exposures, same loop otherwise.
#   warm 60s @ g=1.00 -> fwd @ g=1.15 for FWD in {60, 180, 540} -> rev
#   hold g=1.00 for 450s. Measure per condition:
#     - t_death: first rev-relative t where east organ share < 0.15 for
#       4 consecutive samples (20s), matching run10's death signature
#     - birth size: east share + wNew at end of fwd (ghost mass at birth)
#
# PREDICTIONS (written before first run):
#   P30 biography — committing to HISTORY-DEPENDENT: t_death is monotone
#       increasing across 60 -> 180 -> 540, and t_death(540) >= 1.5x
#       t_death(60). Basis: the ghost's temporary survival runs on the
#       slip circuit re-feeding the east (measure8); a longer-held east
#       has strictly more organ mass to burn and more mature feeding
#       loops, so starvation should take longer. Falsifier: all three
#       lifetimes within +-30s of each other => the starvation clock is
#       a material constant; history sets the ghost's SIZE, not its SPAN.
#   P31 same physics — zero JS errors across all three runs (~39 min).
#   CAVEAT logged before running: run9 vs run10 diverged hugely within
#       180s of same-protocol rev (0.68 vs 0.16 at t+180) — single
#       realization per condition makes this an EXPLORATORY sweep; the
#       minimum bar for P30 is strict monotone ordering of all three
#       (random chance 1/6), not any single lifetime value.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
QS = "?g=1.00&d=0.10"
WARM_S = 60
REV_S = 450
SAMPLE_S = 5
G_HIGH = 1.15
G_LOW = 1.00
EXPOSURES = [60, 180, 540]

SAMPLE_JS = """() => {
  const conf = [], cont = [];
  for (const n of G.nodes) {
    const t = n.terr;
    if (Math.abs(t) > 0.15) conf.push([n.x, t < 0 ? 'A' : 'B']);
    else cont.push(n.x);
  }
  let wOld = 0, wNew = 0, count = 0;
  for (const o of ORGANS) {
    count++;
    let mx = 0;
    for (const m of o.members) mx += G.nodes[m].x;
    mx /= o.members.length;
    if (mx < 14) wOld += o.w; else wNew += o.w;
  }
  return {
    censusA: conf.filter(c => c[1] === 'A').length,
    censusB: conf.filter(c => c[1] === 'B').length,
    contested: cont.length,
    organs: count, wOld: wOld, wNew: wNew,
    meetings: STATS.meetings, kicks: STATS.kicks, hats: STATS.hats
  };
}"""

def share_east(s):
    tot = s["wOld"] + s["wNew"]
    return s["wNew"] / tot if tot > 0 else 0.0

async def run_condition(pw, fwd_s):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(BASE + QS)
    samples = []
    t = 0
    total = WARM_S + fwd_s + REV_S
    pushed_high = pushed_low = False
    while t < total:
        await page.wait_for_timeout(SAMPLE_S * 1000)
        t += SAMPLE_S
        if t >= WARM_S and not pushed_high:
            await page.evaluate(f"setGamma({G_HIGH})")
            pushed_high = True
        if t >= WARM_S + fwd_s and not pushed_low:
            await page.evaluate(f"setGamma({G_LOW})")
            pushed_low = True
        s = await page.evaluate(SAMPLE_JS)
        s["t"] = t
        s["phase"] = "warm" if t <= WARM_S else ("fwd" if t <= WARM_S + fwd_s else "rev")
        samples.append(s)
    await browser.close()
    return {"fwd_s": fwd_s, "errors": errors, "samples": samples}

def analyze(cond):
    fwd_s = cond["fwd_s"]
    rev0 = WARM_S + fwd_s
    fwd = [s for s in cond["samples"] if s["phase"] == "fwd"]
    rev = [s for s in cond["samples"] if s["phase"] == "rev"]
    birth_share = share_east(fwd[-1]) if fwd else None
    birth_w = fwd[-1]["wNew"] if fwd else None
    # death: first rev t where share < 0.15 for 4 consecutive samples
    t_death = None
    run = 0
    for s in rev:
        if share_east(s) < 0.15:
            run += 1
            if run == 4:
                t_death = s["t"] - rev0 - 3 * SAMPLE_S
                break
        else:
            run = 0
    return {"fwd_s": fwd_s, "birth_share": round(birth_share, 3),
            "birth_wNew": round(birth_w, 2), "t_death": t_death,
            "final_share": round(share_east(rev[-1]), 3) if rev else None,
            "errors": len(cond["errors"])}

async def main():
    results = []
    async with async_playwright() as pw:
        for fwd_s in EXPOSURES:
            cond = await run_condition(pw, fwd_s)
            cond["verdict"] = analyze(cond)
            results.append(cond)
            print(f"fwd={fwd_s}: {cond['verdict']}", flush=True)

    with open("run11-biography.json", "w") as f:
        json.dump({"qs": QS, "warm_s": WARM_S, "rev_s": REV_S,
                   "exposures": EXPOSURES,
                   "conditions": results}, f, indent=1)

    v = [c["verdict"] for c in results]
    deaths = [x["t_death"] for x in v]
    print("---- P30 ----", flush=True)
    print(f"deaths (60/180/540): {deaths}", flush=True)
    if all(d is not None for d in deaths):
        monotone = deaths[0] < deaths[1] < deaths[2]
        ratio = deaths[2] / deaths[0] if deaths[0] else None
        print(f"monotone: {monotone}, ratio540/60: {ratio}", flush=True)
        print(f"P30 {'CONFIRMED' if monotone and ratio and ratio >= 1.5 else 'REFUTED-or-PARTIAL'}", flush=True)
    else:
        survivors = [EXPOSURES[i] for i, d in enumerate(deaths) if d is None]
        print(f"no-death-within-450s for exposures: {survivors} — ghost outlived window", flush=True)
    print(f"P31 errors: {[x['errors'] for x in v]}", flush=True)

asyncio.run(main())
