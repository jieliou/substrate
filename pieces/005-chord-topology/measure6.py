#!/usr/bin/env python3
"""measure6 — the analytic twin: eikonal arrival-time fields on the carved bed.

Seventh pass. Sethian's Fast Marching (here: exact Dijkstra on the bed graph,
since the bed IS a graph) gives what the simulation can never state directly:
for each node, the OPTIMAL arrival time T_A(x), T_B(x) from each source, using
the same speed law the pulses obey (v = 2.6 * (0.25 + 1.5*min(D,1))).

The lag field phi(x) = T_A(x) - T_B(x) is a static property of the carved bed.
Every meeting the simulation produces must answer to it:

  - beat pair k co-arrives at x  iff  phi(x) ~ k * P_A * detune  (within FORM_W)
  - locked (d=0): ALL pairs demand phi ~ 0 — one static contour, forever.
  - slipping: pair k lives on contour phi = 0.24k (d=0.10) — an ORDERED family.

PREDICTIONS (written before first run — the charter's rule):

  P13 (band width follows terrain): the |phi| < FORM_W band is WIDE on mesh
      (gamma 0.60: many near-equal paths, flat phi) and NARROW on ridge
      (gamma 1.15: few fat channels, steep phi). Guess: mesh band >= 4x ridge
      band in node count.
  P14 (lock teleports because the contour is a SET, not a path): at gamma
      1.00, the phi~0 band is spatially spread (>= 3 units x-span) and/or
      splits into >1 connected component in the live subgraph — which is why
      measure4 saw the locked spring TELEPORT (litFrac 0.60, steps 2.9-5.0)
      with zero momentum: successive beats sample one static set in arbitrary
      order. Slip walks because its contour family is ordered by k.
  P15 (dwell where contours crowd): for d=0.10 the predicted spring dwells
      where successive contours (0.24s apart in phi) are spatially close
      (steep |grad phi|) and teleports where a contour's node set jumps
      components. Derived blind, THEN compared to organ positions of
      run3-g1.15-d0.10 (organs live where the spring dwells and re-feeds).
  P16 (irrationality is finite and terrain-sorted): actual organ sites sit
      within R_LOC (2.4) of a predicted contour on ridge; mesh runs deviate
      more (multi-path dispersion smears co-arrival off the optimal-time law).
"""
import json, heapq, math, sys
from collections import defaultdict

COLS, ROWS = 24, 17
JITTER = 0.36
I0 = 1.0
D_INIT, D_MIN = 0.35, 1e-4
PULSE_SPEED = 2.6
D_LIVE = 0.045
FORM_W = 0.30
PERIOD_A = 2.4
SEED = 20260727

M = 0xFFFFFFFF
def imul(a, b): return ((a & M) * (b & M)) & M

def make_rnd(seed):
    s = seed & M
    def rnd():
        nonlocal s
        s = (s + 0x6D2B79F5) & M
        t = imul(s ^ (s >> 15), (1 | s) & M)
        t = ((t + imul(t ^ (t >> 7), (61 | t) & M)) & M) ^ t
        return ((t ^ (t >> 14)) & M) / 4294967296
    return rnd

def build_graph(seed):
    rnd = make_rnd(seed)
    nodes, index = [], []
    for r in range(ROWS):
        index.append([])
        for c in range(COLS):
            x = c + (0.5 if r % 2 else 0) + (rnd() - 0.5) * JITTER
            y = r * 0.866 + (rnd() - 0.5) * JITTER
            index[r].append(len(nodes))
            nodes.append({"x": x, "y": y, "p": 0.0, "inj": 0.0})
    edges = []
    def add_edge(a, b):
        dx = nodes[a]["x"] - nodes[b]["x"]; dy = nodes[a]["y"] - nodes[b]["y"]
        edges.append({"a": a, "b": b, "L": math.hypot(dx, dy),
                      "D": D_INIT * (0.7 + 0.6 * rnd())})
    for r in range(ROWS):
        for c in range(COLS):
            i = index[r][c]
            if c + 1 < COLS: add_edge(i, index[r][c + 1])
            if r + 1 < ROWS:
                add_edge(i, index[r + 1][c])
                d = c + 1 if r % 2 else c - 1
                if 0 <= d < COLS: add_edge(i, index[r + 1][d])
    adj = [[] for _ in nodes]
    for k, e in enumerate(edges):
        adj[e["a"]].append(k); adj[e["b"]].append(k)
    mid = ROWS // 2
    srcA, srcB, sink = index[mid][0], index[mid][COLS - 1], index[mid][COLS // 2]
    nodes[srcA]["inj"] = I0; nodes[srcB]["inj"] = I0; nodes[sink]["inj"] = -2 * I0
    return nodes, edges, adj, srcA, srcB, sink

def carve(nodes, edges, adj, sink, gamma, iters=400, sweeps=6, dt=0.55):
    for _ in range(iters):
        for _s in range(sweeps):
            for i, n in enumerate(nodes):
                if i == sink: n["p"] = 0.0; continue
                wsum, acc = 0.0, n["inj"]
                for k in adj[i]:
                    e = edges[k]
                    j = e["b"] if e["a"] == i else e["a"]
                    w = e["D"] / e["L"]
                    wsum += w; acc += w * nodes[j]["p"]
                if wsum > 0: n["p"] = acc / wsum
        for e in edges:
            q = abs((e["D"] / e["L"]) * (nodes[e["a"]]["p"] - nodes[e["b"]]["p"])) * 2.2
            fq = q ** gamma
            e["D"] += dt * (fq / (1 + fq) - e["D"])
            if e["D"] < D_MIN: e["D"] = D_MIN

def travel(e):  # same speed law as stepPulses
    return e["L"] / (PULSE_SPEED * (0.25 + 1.5 * min(e["D"], 1.0)))

def dijkstra(nodes, edges, adj, src, live):
    T = [math.inf] * len(nodes); T[src] = 0.0
    pq = [(0.0, src)]
    while pq:
        t, i = heapq.heappop(pq)
        if t > T[i]: continue
        for k in adj[i]:
            if not live[k]: continue
            e = edges[k]
            j = e["b"] if e["a"] == i else e["a"]
            nt = t + travel(e)
            if nt < T[j] - 1e-12: T[j] = nt; heapq.heappush(pq, (nt, j))
    return T

def components(node_set, nodes, edges, adj, live):
    seen, comps = set(), []
    for start in node_set:
        if start in seen: continue
        comp, stack = [], [start]; seen.add(start)
        while stack:
            i = stack.pop(); comp.append(i)
            for k in adj[i]:
                if not live[k]: continue
                e = edges[k]
                j = e["b"] if e["a"] == i else e["a"]
                if j in node_set and j not in seen:
                    seen.add(j); stack.append(j)
        comps.append(comp)
    return comps

def analyze(gamma, det=0.10):
    nodes, edges, adj, srcA, srcB, sink = build_graph(SEED)
    carve(nodes, edges, adj, sink, gamma)
    live = [e["D"] >= D_LIVE * 0.6 for e in edges]
    TA = dijkstra(nodes, edges, adj, srcA, live)
    TB = dijkstra(nodes, edges, adj, srcB, live)
    reach = [i for i in range(len(nodes))
             if math.isfinite(TA[i]) and math.isfinite(TB[i])]
    phi = {i: TA[i] - TB[i] for i in reach}
    out = {"gamma": gamma, "liveEdges": sum(live), "reach": len(reach),
           "phiMin": min(phi.values()), "phiMax": max(phi.values())}
    # locked band: |phi| < FORM_W
    band = {i for i in reach if abs(phi[i]) < FORM_W}
    xs = sorted(nodes[i]["x"] for i in band)
    comps = components(band, nodes, edges, adj, live)
    out["band"] = {"n": len(band),
                   "xSpan": (round(xs[0], 2), round(xs[-1], 2)) if xs else None,
                   "meanX": round(sum(xs) / len(xs), 2) if xs else None,
                   "components": len(comps),
                   "compSizes": sorted((len(c) for c in comps), reverse=True)}
    # contour family for slip: phi = k * P_A * det
    step = PERIOD_A * det
    walk, kmin = [], math.ceil(out["phiMin"] / step)
    kmax = math.floor(out["phiMax"] / step)
    for k in range(kmin, kmax + 1):
        target = k * step
        cn = [i for i in reach if abs(phi[i] - target) < FORM_W / 2]
        if not cn: walk.append(None); continue
        cx = sum(nodes[i]["x"] for i in cn) / len(cn)
        cy = sum(nodes[i]["y"] for i in cn) / len(cn)
        walk.append({"k": k, "n": len(cn), "x": round(cx, 2), "y": round(cy, 2)})
    steps = []
    prev = None
    for w in walk:
        if w is None: prev = None; continue
        if prev is not None:
            steps.append(round(math.hypot(w["x"] - prev["x"], w["y"] - prev["y"]), 2))
        prev = w
    out["contours"] = {"k": (kmin, kmax), "step_s": round(step, 3),
                       "walk": [w for w in walk if w], "stepDists": steps}
    if steps:
        dw = sum(1 for s in steps if s < 1.0); tp = sum(1 for s in steps if s > 2.0)
        out["contours"]["dwellFrac"] = round(dw / len(steps), 2)
        out["contours"]["teleportFrac"] = round(tp / len(steps), 2)
    return out, nodes, phi, reach

if __name__ == "__main__":
    gammas = [float(g) for g in sys.argv[1:]] or [0.60, 1.00, 1.15]
    results = []
    for g in gammas:
        r, nodes, phi, reach = analyze(g)
        results.append(r)
        print(json.dumps(r, indent=1))
    with open("run6-eikonal.json", "w") as f:
        json.dump(results, f, indent=1)
    print("saved run6-eikonal.json")
