# 008 verification #3 — the gallery of deaths (pass 3).
# House bloodline: P9-P12 written in index.html header BEFORE this file.
#
# Pass 2 verdict: intent's death is circumstantial — a narrative, not a
# statistic. This pass builds the ensemble the single worm doesn't have:
# 12 worlds (seed 1..12) x 2 cycles = 24 independent deaths per event.
# The DISTRIBUTION is the instrument reading. Self-averaging layers
# (C: 24 springs, J: 25 nodes) should be narrow peaks in the gallery;
# the single-DOF intent layer should be a scatter that SPANS ZERO.
#
# P12 doubles as the philosophical gate: same seed -> same hash. The
# variance lives BETWEEN worlds, never inside one. Circumstance != chance.

import asyncio, json, pathlib, statistics, sys
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
RAMP = 10
N_EXPECTED = 1621
SEEDS = list(range(1, 13))
REPEAT_SEED = 7

STEADY = {
    "FULL":  (20, 44),   "NN":  (65, 89),   "NS":  (110, 134), "NI":  (155, 179),
    "FULL2": (200, 224), "NN2": (245, 269), "NS2": (290, 314), "NI2": (335, 359),
}

def events(cycle):
    b = cycle * 180
    sfx = "" if cycle == 0 else "2"
    return [
        ("E1_noise_death",       "J", b+45,  "FULL"+sfx, "NN"+sfx),
        ("E2_noise_rebirth",     "J", b+90,  "NN"+sfx,   "NS"+sfx),
        ("E3_structure_death",   "C", b+90,  "NN"+sfx,   "NS"+sfx),
        ("E4_structure_rebirth", "C", b+135, "NS"+sfx,   "NI"+sfx),
        ("E5_intent_death",      "I", b+135, "NS"+sfx,   "NI"+sfx),
        ("E6_intent_rebirth",    "I", b+180, "NI"+sfx,   "FULL2" if cycle==0 else "FULL"),
    ]
    # (E6 cycle2 new-state window is past horizon; live anchor uses old FULL — see lag())

def med(samples, lo, hi, key):
    return statistics.median(s[key] for s in samples if lo <= s["tau"] <= hi)

def crossing_lag(samples, ear, T, m_old, m_new):
    mid = (m_old + m_new) / 2
    rising = m_new > m_old
    win = [s for s in samples if T <= s["tau"] <= T + 30]
    for i in range(len(win) - 2):
        trio = win[i:i+3]
        if all((s[ear] > mid) == rising for s in trio):
            return round(trio[0]["tau"] - (T + RAMP/2), 2)
    return None

async def probe(pw, seed):
    url = (HERE / "index.html").as_uri() + f"?probe=1&seed={seed}"
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width":1280,"height":720})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(url)
    await page.wait_for_function("window.__done === true", timeout=300000)
    rep = await page.evaluate("window.__report()")
    await browser.close()
    rep["pageerrors"] = errors
    return rep

def lags_for(rep):
    samples = sorted(rep["samples"], key=lambda x: x["tau"])
    sm = {k: {e: med(samples, lo, hi, e) for e in ("I","C","J")}
          for k, (lo, hi) in STEADY.items()}
    out = {}
    for cyc in (0, 1):
        for name, ear, T, oa, na in events(cyc):
            if ear == "I":  # pass-2 instrument repair: dead anchor = design 0
                live = sm[oa][ear] if "death" in name else sm["FULL" if na not in sm else na][ear]
                dead = 0.0
                m_old = live if "death" in name else dead
                m_new = dead if "death" in name else live
            else:
                m_old, m_new = sm[oa][ear], sm[na][ear]
            out[f"c{cyc+1}_{name}"] = crossing_lag(samples, ear, T, m_old, m_new)
    return out, sm

async def main():
    async with async_playwright() as pw:
        runs = {}
        for s in SEEDS:
            runs[s] = await probe(pw, s)
            print(f"world {s}: n={runs[s]['n']} hash={runs[s]['hash']}", flush=True)
        rep7b = await probe(pw, REPEAT_SEED)

    gallery = {}   # event -> list of 24 lags
    per_world = {}
    for s in SEEDS:
        lg, _ = lags_for(runs[s])
        per_world[s] = lg
        for k, v in lg.items():
            ev = k.split("_", 1)[1]
            gallery.setdefault(ev, []).append(v)

    verdicts = {}
    def sd(xs):
        xs = [x for x in xs if x is not None]
        return round(statistics.stdev(xs), 3) if len(xs) > 1 else None

    # P9 — gallery signature: scatter itself stratifies by layer
    sds = {ev: sd(v) for ev, v in gallery.items()}
    self_avg = ["E1_noise_death","E2_noise_rebirth","E3_structure_death","E4_structure_rebirth"]
    none_missing = all(v is not None for ev in gallery for v in gallery[ev])
    p9 = (none_missing and sds["E5_intent_death"] is not None and sds["E3_structure_death"] is not None
          and sds["E5_intent_death"] >= 2.5 * max(sds["E3_structure_death"], 1e-9)
          and all(sds[e] is not None and sds[e] <= 1.5 for e in self_avg))
    verdicts["P9_gallery_signature"] = {"sd": sds, "none_missing": none_missing, "pass": p9}

    # P10 — the ensemble of narratives self-averages (split-half on worlds)
    e5 = gallery["E5_intent_death"]
    even = [v for i, s in enumerate(SEEDS) for v in
            (per_world[s]["c1_E5_intent_death"], per_world[s]["c2_E5_intent_death"]) if s % 2 == 0]
    odd  = [v for i, s in enumerate(SEEDS) for v in
            (per_world[s]["c1_E5_intent_death"], per_world[s]["c2_E5_intent_death"]) if s % 2 == 1]
    dmean = (None if (None in even or None in odd) else
             round(abs(statistics.mean(even) - statistics.mean(odd)), 3))
    verdicts["P10_narrative_ensemble_selfavg"] = {
        "mean_even": None if None in even else round(statistics.mean(even), 3),
        "mean_odd":  None if None in odd  else round(statistics.mean(odd), 3),
        "delta": dmean, "mean_all": round(statistics.mean([v for v in e5 if v is not None]), 3),
        "pass": dmean is not None and dmean <= 1.5 }

    # P11 — circumstance spans zero; statistics does not
    e3 = gallery["E3_structure_death"]
    p11 = (all(v is not None for v in e5) and all(v is not None for v in e3)
           and min(e5) < 0 < max(e5) and min(e3) > 0)
    verdicts["P11_span_zero"] = {
        "E5_min": min(e5), "E5_max": max(e5), "E3_min": min(e3), "E3_max": max(e3),
        "E5_all": e5, "pass": p11 }

    # P12 — instrument: deterministic narratives, distinct worlds
    hashes = [runs[s]["hash"] for s in SEEDS]
    p12 = (runs[REPEAT_SEED]["hash"] == rep7b["hash"]
           and len(set(hashes)) == len(hashes)
           and all(runs[s]["n"] == N_EXPECTED for s in SEEDS) and rep7b["n"] == N_EXPECTED
           and all(runs[s]["errors"] == 0 and not runs[s]["pageerrors"] for s in SEEDS))
    verdicts["P12_instrument"] = {
        "repeat_seed": REPEAT_SEED, "repeat_hash_match": runs[REPEAT_SEED]["hash"] == rep7b["hash"],
        "distinct_hashes": len(set(hashes)), "n_worlds": len(SEEDS),
        "pass": p12 }

    # E6 + full gallery reported as data
    out = HERE / "verify3-verdicts.json"
    out.write_text(json.dumps({"verdicts": verdicts, "gallery": gallery,
                               "per_world": per_world}, indent=2))
    ok = all(v["pass"] for v in verdicts.values())
    for k, v in verdicts.items():
        print(k, "→", json.dumps({kk: vv for kk, vv in v.items() if kk not in ("E5_all",)}))
    print("ALL PASS" if ok else "SOMETHING DIED (read the body)")
    sys.exit(0 if ok else 1)

asyncio.run(main())
