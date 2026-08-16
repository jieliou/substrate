# 005 measurement #12 — the ember test (餘燼會不會冷). Ephemeral verifier.
#
# measure11 ended law v3: flesh memory = a time constant PLUS a residual
# bias, and the bias is the biography (final east occupancy 0.074/0.244/
# 0.314 for fwd 60/180/540, strictly monotone, replicating while death
# times swing). But the 450 s window only proved the bias OUTLIVES the
# window. This run asks the permanence question: is the afterglow a
# second, slower time constant (an ember that cools), or a structural
# rewrite (the biography carved something the hold cannot erase)?
#
# Protocol: single condition, the strongest biography.
#   warm 60s @ g=1.00 -> fwd @ g=1.15 for 540s -> hold g=1.00 for 1800s.
#   Sample every 5s: east occupancy share, east organ mean-x (WHERE do
#   the embers sit — hugging the cut at x~14, or deep in the east?),
#   resurrection count (death signature = share<0.15 x4 consecutive;
#   resurrection = subsequent recovery >= 0.20).
#
# PREDICTIONS (written before first run):
#   P32 permanence — committing to STRUCTURAL: east share at t+1800 >=
#       0.5 x its t+450 value (i.e. the afterglow loses less than half
#       over a window 4x longer than the one that already failed to
#       kill it). Basis: measure11's 540s ghost was declared dead at
#       t+320 and RESURRECTED — re-nucleation implies an anchor that
#       does not deplete (cut geometry / carved groove), not a burning
#       stock. Falsifier: share decays below the 0.15 death line by
#       t+1800 and stays there 60s+ => the bias is an ember after all;
#       fit its tau and law v4 becomes a two-time-constant cascade.
#   P33 anchor location — committing to CUT-HUGGING: mean-x of east
#       organs over the final 600s sits in [14, 18] (near the border),
#       not deep east (>20). Basis: journal 08-16 "border organs keep
#       re-nucleating near the cut". Falsifier: mean-x > 20 => the
#       groove itself (deep territory) is the anchor, and the cut is
#       incidental.
#   P34 same physics — zero JS errors across the 40 min run.
#   CAVEAT (pre-registered): single realization. measure11 showed death
#       TIMES swing wildly across realizations but occupancy REPLICATES;
#       P32/P33 read occupancy and location, the replicating layer, so
#       one run is evidential (not just exploratory) — but a clean
#       refutation still deserves a second realization before law v4.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
QS = "?g=1.00&d=0.10"
WARM_S = 60
FWD_S = 540
HOLD_S = 1800
SAMPLE_S = 5
G_HIGH = 1.15
G_LOW = 1.00

SAMPLE_JS = """() => {
  let wOld = 0, wNew = 0, count = 0, eastX = 0, eastW = 0;
  for (const o of ORGANS) {
    count++;
    let mx = 0;
    for (const m of o.members) mx += G.nodes[m].x;
    mx /= o.members.length;
    if (mx < 14) { wOld += o.w; }
    else { wNew += o.w; eastX += mx * o.w; eastW += o.w; }
  }
  return {
    organs: count, wOld: wOld, wNew: wNew,
    eastMeanX: eastW > 0 ? eastX / eastW : null,
    meetings: STATS.meetings, kicks: STATS.kicks, hats: STATS.hats
  };
}"""

def share_east(s):
    tot = s["wOld"] + s["wNew"]
    return s["wNew"] / tot if tot > 0 else 0.0

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(BASE + QS)
        samples = []
        t = 0
        total = WARM_S + FWD_S + HOLD_S
        pushed_high = pushed_low = False
        while t < total:
            await page.wait_for_timeout(SAMPLE_S * 1000)
            t += SAMPLE_S
            if t >= WARM_S and not pushed_high:
                await page.evaluate(f"setGamma({G_HIGH})")
                pushed_high = True
            if t >= WARM_S + FWD_S and not pushed_low:
                await page.evaluate(f"setGamma({G_LOW})")
                pushed_low = True
            s = await page.evaluate(SAMPLE_JS)
            s["t"] = t
            s["phase"] = "warm" if t <= WARM_S else ("fwd" if t <= WARM_S + FWD_S else "hold")
            samples.append(s)
            if t % 300 == 0:
                print(f"t={t} phase={s['phase']} share={share_east(s):.3f} "
                      f"eastX={s['eastMeanX'] and round(s['eastMeanX'],1)}", flush=True)
        await browser.close()

    hold0 = WARM_S + FWD_S
    hold = [s for s in samples if s["phase"] == "hold"]

    def share_at(rel_t):
        best = min(hold, key=lambda s: abs((s["t"] - hold0) - rel_t))
        return round(share_east(best), 3)

    marks = {rt: share_at(rt) for rt in (450, 900, 1350, 1800)}

    # resurrection ledger
    deaths, resurrections = 0, 0
    run, dead = 0, False
    for s in hold:
        sh = share_east(s)
        if not dead:
            run = run + 1 if sh < 0.15 else 0
            if run == 4:
                deaths += 1; dead = True; run = 0
        else:
            if sh >= 0.20:
                resurrections += 1; dead = False
    final_dead = dead

    # anchor location: mean of eastMeanX over final 600s (weight-bearing samples only)
    tail = [s for s in hold if (s["t"] - hold0) > HOLD_S - 600 and s["eastMeanX"] is not None]
    anchor_x = round(sum(s["eastMeanX"] for s in tail) / len(tail), 2) if tail else None

    verdict = {
        "share_marks": marks,
        "retention_1800_vs_450": round(marks[1800] / marks[450], 3) if marks[450] else None,
        "deaths": deaths, "resurrections": resurrections, "final_dead": final_dead,
        "anchor_mean_x_final600": anchor_x,
        "errors": len(errors),
    }
    with open("run12-ember.json", "w") as f:
        json.dump({"qs": QS, "warm_s": WARM_S, "fwd_s": FWD_S, "hold_s": HOLD_S,
                   "samples": samples, "verdict": verdict}, f, indent=1)

    print("---- verdicts ----", flush=True)
    print(f"share marks (t+450/900/1350/1800): {marks}", flush=True)
    r = verdict["retention_1800_vs_450"]
    print(f"P32 retention: {r} -> {'STRUCTURAL (>=0.5)' if r is not None and r >= 0.5 else 'EMBER-DECAY or dead'}", flush=True)
    print(f"P33 anchor x (final 600s): {anchor_x} -> "
          f"{'CUT-HUGGING' if anchor_x is not None and 14 <= anchor_x <= 18 else ('DEEP-EAST' if anchor_x and anchor_x > 20 else 'ambiguous/none')}", flush=True)
    print(f"ledger: deaths={deaths} resurrections={resurrections} final_dead={final_dead}", flush=True)
    print(f"P34 errors: {len(errors)}", flush=True)

asyncio.run(main())
