# 005 measurement #9 — the return pass (反向遷都 / hysteresis loop). Ephemeral verifier.
# measure8 performed the relocation LIVE (1.00 -> 1.15): frontier walked a
# staircase, the old capital starved then REVIVED as a waypoint, and the
# meeting rate never dipped — the interregnum exists on the map, not on any
# journey. Verdict: the bed has hysteresis — state depends on path.
# This run CLOSES THE LOOP: warm at 1.00, push to 1.15 (replicating #8),
# then push BACK to 1.00 and watch the return. Hysteresis is a loop with
# area: if the bed truly remembers, the round trip must NOT restore the
# starting state — the eastern ex-capital should persist as residue, and
# the return trip should ride roads the forward trip built.
#
# PREDICTIONS (written before first run):
#   P24 return completes — after the reverse switch the frontier walks back
#       west and reaches x <= 13 by +180s. (Failure mode worth naming: the
#       east HOLDS — occupation inertia strong enough to block reverse
#       relocation entirely. That would be a discovery, not an instrument
#       failure, but committing to completion: the slip spring still favors
#       the sink delta at gamma=1.00, and terr tau=90s allows ~2tau decay.)
#   P25 residue (THE hysteresis signature) — the loop does not close: over
#       the final 15s, eastern organ biomass share wNew/(wOld+wNew) stays
#       > 0.10, strictly above the warm-phase maximum share. The east was
#       essentially empty before the excursion; if it returns to empty the
#       loop has no area and "bed hysteresis" was an overclaim (P22's
#       seamless crossing would need a different explanation).
#   P26 tempo asymmetry — the return is FASTER than the outbound trip:
#       t_half(rev) < t_half(fwd), where t_half = time from switch until the
#       frontier crosses the midpoint between its at-switch position and the
#       other regime's settled frontier. Reason: the outbound trip had to
#       carve the eastern capital from nothing; the return re-enters western
#       structure that measure8 showed SURVIVES (the old capital revived to
#       12.9 — the roads never closed).
#   P27 same physics — zero JS errors; kicks/hats keep advancing.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
QS = "?g=1.00&d=0.10"
WARM_S = 60
FWD_S = 180
REV_S = 180
SAMPLE_S = 5
G_HIGH = 1.15
G_LOW = 1.00

SAMPLE_JS = """() => {
  const conf = [], cont = [];
  for (const n of G.nodes) {
    const t = n.terr;
    if (Math.abs(t) > 0.15) conf.push([n.x, t < 0 ? 'A' : 'B']);
    else cont.push(n.x);
  }
  const bins = {};
  for (const [x, s] of conf) {
    const b = Math.floor(x / 2) * 2;
    (bins[b] = bins[b] || { a: 0, n: 0 }).n++;
    if (s === 'A') bins[b].a++;
  }
  const keys = Object.keys(bins).map(Number).sort((p, q) => p - q);
  let frontier = null, prev = null;
  for (const k of keys) {
    const share = bins[k].a / bins[k].n;
    if (prev && prev.share >= 0.5 && share < 0.5) {
      const f = (0.5 - share) / (prev.share - share);
      frontier = k + 1 - 2 * f; break;
    }
    prev = { k, share };
  }
  let wOld = 0, wNew = 0, count = 0;
  const xs = [];
  for (const o of ORGANS) {
    count++;
    let mx = 0;
    for (const m of o.members) mx += G.nodes[m].x;
    mx /= o.members.length;
    xs.push(mx);
    if (mx < 14) wOld += o.w; else wNew += o.w;
  }
  return {
    censusA: conf.filter(c => c[1] === 'A').length,
    censusB: conf.filter(c => c[1] === 'B').length,
    contested: cont.length,
    frontier: frontier,
    organs: count, wOld: wOld, wNew: wNew,
    organX: xs,
    meetings: STATS.meetings, kicks: STATS.kicks, hats: STATS.hats,
    gamma: gamma
  };
}"""

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
        page = await browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.goto(BASE + QS)
        samples = []
        t = 0
        total = WARM_S + FWD_S + REV_S
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
            s["phase"] = "warm" if t <= WARM_S else ("fwd" if t <= WARM_S + FWD_S else "rev")
            samples.append(s)
        sink = await page.evaluate("G.nodes[G.sink].x")
        await browser.close()

    out = {"qs": QS, "loop": [G_LOW, G_HIGH, G_LOW],
           "warm_s": WARM_S, "fwd_s": FWD_S, "rev_s": REV_S,
           "sinkX": round(sink, 2), "errors": errors, "samples": samples}
    with open("run9-return.json", "w") as f:
        json.dump(out, f, indent=1)

    # ---- verdicts ----
    warm = [s for s in samples if s["phase"] == "warm"]
    fwd = [s for s in samples if s["phase"] == "fwd"]
    rev = [s for s in samples if s["phase"] == "rev"]

    def share_east(s):
        tot = s["wOld"] + s["wNew"]
        return s["wNew"] / tot if tot > 0 else 0.0

    # P24 — return completes
    rev_fr = [(s["t"] - WARM_S - FWD_S, s["frontier"]) for s in rev if s["frontier"]]
    final_fr = rev_fr[-1][1] if rev_fr else None
    p24 = final_fr is not None and final_fr <= 13.0

    # P25 — residue: final 15s east share > 0.10 and > warm max
    warm_max_share = max((share_east(s) for s in warm), default=0.0)
    tail = rev[-3:]
    tail_share = sum(share_east(s) for s in tail) / max(len(tail), 1)
    p25 = tail_share > 0.10 and tail_share > warm_max_share

    # P26 — tempo asymmetry via symmetric half-crossing metric
    def t_half(phase_samples, t0_offset, start_fr, target_fr):
        if start_fr is None or target_fr is None: return None
        mid = (start_fr + target_fr) / 2
        rising = target_fr > start_fr
        for s in phase_samples:
            if s["frontier"] is None: continue
            if (rising and s["frontier"] >= mid) or (not rising and s["frontier"] <= mid):
                return s["t"] - t0_offset
        return None
    warm_fr_settled = next((s["frontier"] for s in reversed(warm) if s["frontier"]), None)
    fwd_fr_settled = next((s["frontier"] for s in reversed(fwd) if s["frontier"]), None)
    fwd_start = next((s["frontier"] for s in fwd if s["frontier"]), None)
    rev_start = next((s["frontier"] for s in rev if s["frontier"]), None)
    th_fwd = t_half(fwd, WARM_S, fwd_start, fwd_fr_settled)
    th_rev = t_half(rev, WARM_S + FWD_S, rev_start, warm_fr_settled)
    p26 = th_fwd is not None and th_rev is not None and th_rev < th_fwd

    # P27 — same physics
    p27 = not errors and samples[-1]["kicks"] > samples[0]["kicks"]

    print("errors:", errors)
    print(f"P24 return completes (final frontier {final_fr}): {'PASS' if p24 else 'FAIL'}")
    print(f"P25 residue (tail east share {tail_share:.3f} vs warm max {warm_max_share:.3f}): "
          f"{'PASS' if p25 else 'FAIL'}")
    print(f"P26 tempo asymmetry (t_half fwd {th_fwd}s vs rev {th_rev}s): "
          f"{'PASS' if p26 else 'FAIL'}")
    print(f"P27 same physics: {'PASS' if p27 else 'FAIL'}")
    print("trajectory:")
    for s in samples:
        print(f"  t={s['t']:3d} {s['phase']:4s} g={s['gamma']:.2f} organs={s['organs']:2d} "
              f"wOld={s['wOld']:6.2f} wNew={s['wNew']:6.2f} eastShare={share_east(s):.2f} "
              f"census A:B:c = {s['censusA']}:{s['censusB']}:{s['contested']} "
              f"frontier={round(s['frontier'],1) if s['frontier'] else '—'}")

asyncio.run(main())
