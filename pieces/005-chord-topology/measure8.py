# 005 measurement #8 — the relocation pass (遷都直播). Ephemeral verifier.
# measure4 found regime change = relocation of the capital (mesh capital at the
# sink delta, ridge capital deep in B's homeland; gamma=1.10 a literal
# interregnum). The homeland pass gave the renderer a slow ledger (terr EMA,
# ~10 strikes to convert, tau=90s relaxation). All verdicts so far are STEADY
# STATES — this run performs the transition LIVE: push gamma 1.00 -> 1.15
# mid-run and watch the old capital wither, the new one flood, the frontier
# walk east. The eighth pass taught that occupation has inertia ("the analytic
# twin knows distances, not territory") — this run measures that inertia's
# time constant directly.
#
# PREDICTIONS (written before first run):
#   P20 frontier walk — after the switch the A:B frontier (x where confident-
#       node A-share crosses 0.5) moves from ~11.5 toward >=16, monotonically
#       (allowing +-1 jitter), NOT instantaneously: half-distance (~x 14)
#       reached no earlier than +30s and no later than +150s post-switch.
#       (<20s would falsify EMA-paced relocation; never reaching 15 by +180s
#       would falsify that runtime carving can complete the regime change.)
#   P21 capital crossover — organ biomass east of x=14 (new capital) exceeds
#       biomass west of x=14 (old delta) somewhere in (+30s, +120s]; by +90s
#       the old-delta biomass falls below 30% of its pre-switch value
#       (organ tau=25s starvation while the spring waters the east).
#   P22 interregnum crossed in TIME — meetings/15s dips by >=40% (vs the
#       pre-switch mean) during the first 60s post-switch, then recovers:
#       the gamma=1.10 valley is a bed property, and the carve passes through
#       it dynamically. Counter-hypothesis (occupation-inertia bridge): the
#       terr ledger keeps old meeting sites alive and the dip stays <25%.
#       Committing to the valley (>=40%); a bridge verdict would be the
#       ninth-pass discovery, not a failure of the instrument.
#   P23 same physics — zero JS errors; kicks/hats keep advancing; fps sane.
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
QS = "?g=1.00&d=0.10"          # baseline slip — capital at the sink delta
WARM_S = 60                     # steady state before the push
POST_S = 180                    # relocation window (terr tau=90s -> ~2 tau)
SAMPLE_S = 5
SWITCH_G = 1.15

SAMPLE_JS = """() => {
  const conf = [], cont = [];
  for (const n of G.nodes) {
    const t = n.terr;
    if (Math.abs(t) > 0.15) conf.push([n.x, t < 0 ? 'A' : 'B']);
    else cont.push(n.x);
  }
  // frontier: x where per-bin A-share crosses 0.5 (bins of 2 units)
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
        total = WARM_S + POST_S
        switched = False
        while t < total:
            await page.wait_for_timeout(SAMPLE_S * 1000)
            t += SAMPLE_S
            if t >= WARM_S and not switched:
                await page.evaluate(f"setGamma({SWITCH_G})")
                switched = True
            s = await page.evaluate(SAMPLE_JS)
            s["t"] = t
            s["phase"] = "warm" if t <= WARM_S else "post"
            samples.append(s)
        sink = await page.evaluate("G.nodes[G.sink].x")
        await browser.close()

    out = {"qs": QS, "switch_g": SWITCH_G, "warm_s": WARM_S, "post_s": POST_S,
           "sinkX": round(sink, 2), "errors": errors, "samples": samples}
    with open("run8-relocation.json", "w") as f:
        json.dump(out, f, indent=1)

    # ---- verdicts ----
    warm = [s for s in samples if s["phase"] == "warm"]
    post = [s for s in samples if s["phase"] == "post"]
    def rate(ss):  # meetings per 15s from cumulative counter
        if len(ss) < 2: return []
        out = []
        for a, b in zip(ss, ss[1:]):
            out.append((b["meetings"] - a["meetings"]) * 15 / SAMPLE_S)
        return out
    pre_rate = rate(warm[3:])  # skip startup
    post_rate = rate(post)
    fr = [(s["t"] - WARM_S, s["frontier"]) for s in post if s["frontier"]]
    print("errors:", errors)
    print("pre-switch meet/15s:", [round(r,1) for r in pre_rate])
    print("post-switch meet/15s:", [round(r,1) for r in post_rate])
    print("frontier walk (t_post, x):", [(t, round(x,1)) for t, x in fr])
    print("wOld/wNew trajectory:")
    for s in samples:
        print(f"  t={s['t']:3d} {s['phase']:4s} g={s['gamma']:.2f} organs={s['organs']:2d} "
              f"wOld={s['wOld']:6.2f} wNew={s['wNew']:6.2f} "
              f"census A:B:c = {s['censusA']}:{s['censusB']}:{s['contested']} "
              f"frontier={round(s['frontier'],1) if s['frontier'] else '—'}")

asyncio.run(main())
