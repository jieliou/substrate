# 005 measurement #4 — the valley autopsy. Ephemeral verifier.
# Question: measure3 found γ=1.10 is a VALLEY (12 meet / meanW 1.94 / 35 cond,
# thinner than both 1.05 mesh-commons and 1.15 ridge-cathedral) and guessed
# "mesh→ridge is not continuous shrinkage but discrete junction pruning —
# 1.10 happens to break at a big junction". That guess was inferred from
# meeting COUNTS. Nobody had looked at the collision topology itself.
#
# INSTRUMENT HISTORY (kept honestly — the instrument taught the physics):
#   v1: Dijkstra equal-time front over all live edges, constant speed.
#       Returned the SAME 2-node front at every γ — contradicting the known
#       meeting collapse (37/12/13/4 per 60s). Self-refuted: fronts do not
#       walk all live edges at one speed. They branch top-3 BY D, share
#       energy as (D/Dmax)^0.6, travel at v=2.6·(0.25+1.5·min(D,1)) (a fat
#       channel is ~5× faster than a live-threshold one), and collisions
#       kill pulses — the interface is a creature of channel HIERARCHY.
#   v2: exact single-beat event-driven replica. Validation anchor ×25 beats
#       gave 25/25/50/25 vs measured 37/12/13/4 — not even multiples of 25:
#       beats are NOT independent. Slow channels carry pulses for 10-30s
#       (23 hops × up to 1.3s/hop), so the locked state is a STANDING
#       INTERFERENCE of ~10 overlapping wave generations, not a repeating
#       clean beat. (This is itself a finding: 004's reverb chamber lives
#       inside every locked beat of 005.)
#   v3 (this file): multi-beat 60s event-driven sim + REAL 60s STATS run on
#       the same bed. Validation: sim landed 34/17/2 vs real 37/12/4 at
#       γ=1.05/1.10/1.20 — but over-counted the ridge 4× (66 vs 13-17).
#       Bed drift was ruled out by direct test (108 live edges at t9 and
#       t71, zero died/born, D stable to 4 decimals). Diagnosis: the sim's
#       determinism holds borderline coincidence windows permanently open;
#       the real system's frame jitter makes knife-edge sites probabilistic.
#       The sim gets the SITES right (its ridge meetX superset contains the
#       real run's dominant {15.5, 18.2}); rates at the ridge are its known
#       blind spot. Verdicts below therefore rest on REAL meetX/shadowX
#       distributions; the sim supplies territory + reach structure only.
#
# PREDICTIONS (written before running — 2026-08-05 01:4x, restated on the
# collision interface after v1's self-refutation, mechanism unchanged):
#   P11 structure-specific loss, not uniform thinning:
#       1.05→1.10 live capacity drops <25%, but the collision interface
#       (real meetings+shadows per 60s) drops >=50%. A connectivity event.
#   P12 non-monotonic junction capacity: the strongest meeting-site's local
#       capacity (Σ live D within R_LOC of the site) DIPS at 1.10 — lower
#       than at 1.05 and lower than at 1.15.
#   P13 two different junctions (riskiest): the dominant meeting site at
#       1.15 sits near the spring-pass well (within R_LOC=2.4 of
#       (18.2, 7.1)); the strongest site at 1.05 sits somewhere ELSE
#       (> 2.4 away from the 1.15 site). 1.10 = the interregnum: the mesh
#       capital already dead, the ridge capital not yet dominant.
import asyncio, heapq, json
from collections import Counter
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
GAMMAS = [1.05, 1.10, 1.15, 1.20]
D_LIVE, E_DECAY, E_CUTOFF = 0.045, 0.88, 0.05
BRANCH_MAX, REFRACTORY, COINCIDE, PERIOD = 3, 0.90, 0.15, 2.4
WELL, R_LOC = (18.2, 7.1), 2.4

def vel(D): return 2.6 * (0.25 + 1.5 * min(D, 1.0))

def simulate(bed, T=64.4):
    """multi-beat event-driven replica of the pulse physics on a frozen bed"""
    nodes, edges = bed["nodes"], bed["edges"]
    adj = [[] for _ in nodes]
    for k, e in enumerate(edges):
        adj[e["a"]].append(k); adj[e["b"]].append(k)
    fired = [-1e9] * len(nodes); owner = [None] * len(nodes)
    meets, shads = [], []
    seq = 0; pq = []
    t = PERIOD
    while t <= T:  # locked: both sources fire together, first beat at 2.4
        for (s, v) in ((bed["srcA"], 0), (bed["srcB"], 1)):
            heapq.heappush(pq, (t, seq, s, 1.0, -1, v, True)); seq += 1
        t += PERIOD
    while pq:
        t, _, i, en, fe, src, launch = heapq.heappop(pq)
        if launch: fired[i] = -1e9          # piece force-clears source ref
        if t < fired[i] + REFRACTORY:
            if owner[i] is not None and owner[i] != src:
                rec = {"t": round(t, 2), "x": nodes[i]["x"], "y": nodes[i]["y"]}
                (meets if t - fired[i] < COINCIDE else shads).append(rec)
            continue
        fired[i] = t; owner[i] = src
        cand = [k for k in adj[i] if k != fe and edges[k]["D"] > D_LIVE]
        if not cand: continue
        cand.sort(key=lambda k: -edges[k]["D"])
        take = cand[:BRANCH_MAX]; Dmax = edges[take[0]]["D"]
        for k in take:
            e = edges[k]
            child = en * E_DECAY * (e["D"] / Dmax) ** 0.6
            if child < E_CUTOFF: continue
            j = e["b"] if e["a"] == i else e["a"]
            heapq.heappush(pq, (t + e["L"] / vel(e["D"]), seq, j, child, k, src, False))
            seq += 1
    W = lambda rs: [r for r in rs if 4.4 <= r["t"] <= 64.4]
    return W(meets), W(shads), owner

def local_cap(bed, x, y):
    """Σ live D within R_LOC of (x,y) — junction capacity"""
    nodes = bed["nodes"]
    return round(sum(e["D"] for e in bed["edges"] if e["D"] >= D_LIVE and
        min((nodes[e["a"]]["x"]-x)**2 + (nodes[e["a"]]["y"]-y)**2,
            (nodes[e["b"]]["x"]-x)**2 + (nodes[e["b"]]["y"]-y)**2) <= R_LOC**2), 3)

async def run_one(pw, g):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(f"{BASE}?g={g:.2f}")
    await page.wait_for_function("window.STATS !== undefined")
    await page.wait_for_timeout(9000)
    bed = await page.evaluate("""() => ({
      nodes: G.nodes.map(n => ({x: +n.x.toFixed(3), y: +n.y.toFixed(3)})),
      edges: G.edges.map(e => ({a: e.a, b: e.b, L: +e.L.toFixed(3), D: +e.D.toFixed(4)})),
      srcA: G.srcA, srcB: G.srcB, sink: G.sink })""")
    await page.screenshot(path=f"/Users/jie/Dev/substrate/pieces/005-chord-topology/topo-g{g:.2f}.png")
    await page.evaluate("STATS.reset()")
    await page.wait_for_timeout(62000)   # real 60s+ observation on the SAME bed
    real = await page.evaluate("""() => ({
      meetings: STATS.meetings, shadows: STATS.shadows,
      meetX: STATS.meetX.map(x => +x.toFixed(1)),
      meetT: STATS.meetT.map(t => +t.toFixed(1)),
      shadowX: STATS.shadowX.map(x => +x.toFixed(1)) })""")
    await browser.close()

    meets, shads, owner = simulate(bed)
    live = [e for e in bed["edges"] if e["D"] >= D_LIVE]
    mx = Counter(real["meetX"]).most_common(5)
    # dominant real site: most frequent meetX, with mean y of sim meets near it
    sites = []
    for x, n in mx:
        ys = [r["y"] for r in meets + shads if abs(r["x"] - x) < 1.0]
        y = sum(ys) / len(ys) if ys else 7.0
        sites.append({"x": x, "y": round(y, 1), "hits": n, "cap": local_cap(bed, x, y)})
    return {"gamma": g, "jsErrors": errors,
            "liveEdges": len(live), "liveCap": round(sum(e["D"] for e in live), 2),
            "territorySim": [sum(1 for o in owner if o == 0), sum(1 for o in owner if o == 1)],
            "real": {"meetings": real["meetings"], "shadows": real["shadows"],
                     "interface": real["meetings"] + real["shadows"],
                     "meetT": real["meetT"]},
            "sim": {"meets": len(meets), "shadows": len(shads),
                    "meetXs": sorted(set(round(r["x"], 1) for r in meets))},
            "realSites": sites}

async def main():
    async with async_playwright() as pw:
        out = []
        for g in GAMMAS:
            r = await run_one(pw, g)
            out.append(r)
            print(json.dumps(r, ensure_ascii=False))
        with open("/Users/jie/Dev/substrate/pieces/005-chord-topology/run4-topology.json", "w") as f:
            json.dump(out, f, indent=1)

asyncio.run(main())
