# 008 verification #4 — the fourth death (pass 4).
# House bloodline: P13-P16 written in index.html header BEFORE this file.
#
# Two worms, one bond. The social layer lives in neither body. The species
# question: pass 3 sorted deaths into statistical (narrow gallery, mean
# resists the clock) and circumstantial (wide gallery, mean obeys it).
# The bond's death should be a THIRD species — death by timetable: after
# the cut, separation is driven by the deterministic target dance, shared
# by every world, sensitive to WHEN the executioner strikes.
# Two axes disentangle the three: across SEEDS E7 should collapse to a
# point (unlike E5); across TPHASE it should scatter (unlike E3).

import asyncio, json, pathlib, statistics, sys
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
RAMP = 10
N_EXPECTED = 1921
SEEDS = list(range(1, 13))
PHASES = list(range(0, 12))     # tphase seconds; phase 0 == seed-7 run
BASE_SEED = 7

STEADY = {
    "FULL":  (20, 44),   "NN":  (65, 89),   "NS":  (110, 134),
    "NI":    (155, 179), "NOSOC": (200, 224),
    "FULL2": (245, 269), "NN2": (290, 314), "NS2": (335, 359),
    "NI2":   (380, 404), "NOSOC2": (425, 449),
}

def events(cycle):
    b = cycle * 225
    s = "" if cycle == 0 else "2"
    return [
        ("E1_noise_death",       "J", b+45,  "FULL"+s,  "NN"+s),
        ("E2_noise_rebirth",     "J", b+90,  "NN"+s,    "NS"+s),
        ("E3_structure_death",   "C", b+90,  "NN"+s,    "NS"+s),
        ("E4_structure_rebirth", "C", b+135, "NS"+s,    "NI"+s),
        ("E5_intent_death",      "I", b+135, "NS"+s,    "NI"+s),
        ("E6_intent_rebirth",    "I", b+180, "NI"+s,    "NOSOC"+s),
        ("E7_social_death",      "S", b+180, "NI"+s,    "NOSOC"+s),
        ("E8_social_rebirth",    "S", b+225, "NOSOC"+s, "FULL2" if cycle==0 else "FULL"),
    ]

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

async def probe(pw, seed, tphase):
    url = (HERE / "index.html").as_uri() + f"?probe=1&seed={seed}&tphase={tphase}"
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
    sm = {k: {e: med(samples, lo, hi, e) for e in ("I","C","J","S")}
          for k, (lo, hi) in STEADY.items()}
    out = {}
    for cyc in (0, 1):
        for name, ear, T, oa, na in events(cyc):
            if ear == "I":  # pass-2 instrument repair: dead anchor = design 0
                live = sm[oa][ear] if "death" in name else sm[na][ear]
                m_old = live if "death" in name else 0.0
                m_new = 0.0 if "death" in name else live
            else:
                m_old, m_new = sm[oa][ear], sm[na][ear]
            out[f"c{cyc+1}_{name}"] = crossing_lag(samples, ear, T, m_old, m_new)
    return out, sm

def cells_ok(sm):
    """P13: body ears keep the four cells under the coupled physics,
    plus the fourth cell (NOSOC = full-alive bodies, silent bond)."""
    fails = []
    for s in ("", "2"):
        F, NN, NS, NI, NO = (sm["FULL"+s], sm["NN"+s], sm["NS"+s],
                             sm["NI"+s], sm["NOSOC"+s])
        if not (F["I"] >= 0.35 and F["C"] >= 0.80 and F["J"] >= 0.10):
            fails.append("FULL"+s)
        if not (NN["I"] >= 0.45 and NN["C"] >= 0.80 and NN["J"] <= 0.5*F["J"]):
            fails.append("NN"+s)
        if not (NS["I"] >= 0.20 and NS["C"] <= 0.60 and NS["J"] >= 0.10):  # P13' run-2 gate
            fails.append("NS"+s)
        if not (abs(NI["I"]) <= 0.25 and NI["C"] >= 0.80 and NI["J"] >= 0.10):
            fails.append("NI"+s)
        if not (NO["I"] >= 0.35 and NO["C"] >= 0.80 and NO["J"] >= 0.10
                and NO["S"] <= 0.5*F["S"]):
            fails.append("NOSOC"+s)
        if not (F["S"] >= 0.25):
            fails.append("S_FULL"+s)
    return fails

def p14_ok(sm):
    fails = []
    for s in ("", "2"):
        if not (sm["NI"+s]["S"] >= sm["FULL"+s]["S"] + 0.10
                and sm["NI"+s]["S"] >= 0.8):  # P14' run-2 gate
            fails.append("NI"+s)
    return fails

def sd(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.stdev(xs), 3) if len(xs) > 1 else None

async def main():
    async with async_playwright() as pw:
        seed_runs, phase_runs = {}, {}
        for s in SEEDS:
            seed_runs[s] = await probe(pw, s, 0)
            print(f"world {s}: n={seed_runs[s]['n']} hash={seed_runs[s]['hash']}", flush=True)
        phase_runs[0] = seed_runs[BASE_SEED]
        for k in PHASES[1:]:
            phase_runs[k] = await probe(pw, BASE_SEED, k)
            print(f"tphase {k}: n={phase_runs[k]['n']} hash={phase_runs[k]['hash']}", flush=True)
        rep7b = await probe(pw, BASE_SEED, 0)

    seed_lags, seed_sm = {}, {}
    for s in SEEDS:
        seed_lags[s], seed_sm[s] = lags_for(seed_runs[s])
    phase_lags = {}
    for k in PHASES:
        phase_lags[k], _ = lags_for(phase_runs[k])

    verdicts = {}

    # P13 — fourth cell + regression of the original four, all 12 worlds x 2 cycles
    cell_fails = {s: cells_ok(seed_sm[s]) for s in SEEDS}
    p13 = all(not f for f in cell_fails.values())
    verdicts["P13_fourth_cell_and_regression"] = {
        "fails": {s: f for s, f in cell_fails.items() if f}, "pass": p13 }

    # P14 — kill intent, the bond gets LOUDER (two masters on one head)
    p14_fails = {s: p14_ok(seed_sm[s]) for s in SEEDS}
    p14 = all(not f for f in p14_fails.values())
    verdicts["P14_social_loudens_when_intent_dies"] = {
        "fails": {s: f for s, f in p14_fails.items() if f},
        "S_FULL_med": round(statistics.median(seed_sm[s]["FULL"]["S"] for s in SEEDS), 3),
        "S_NI_med":   round(statistics.median(seed_sm[s]["NI"]["S"] for s in SEEDS), 3),
        "pass": p14 }

    # P15 — species verdict: death by timetable (two axes)
    e7c1 = [seed_lags[s]["c1_E7_social_death"] for s in SEEDS]
    e7c2 = [seed_lags[s]["c2_E7_social_death"] for s in SEEDS]
    sd_c1, sd_c2 = sd(e7c1), sd(e7c2)
    p15a = (all(v is not None for v in e7c1+e7c2)
            and sd_c1 is not None and sd_c1 <= 1.0   # P15' run-2 gate
            and sd_c2 is not None and sd_c2 <= 1.0)
    e7ph = [phase_lags[k]["c1_E7_social_death"] for k in PHASES]
    e3ph = [phase_lags[k]["c1_E3_structure_death"] for k in PHASES]
    sd_ph_e7, sd_ph_e3 = sd(e7ph), sd(e3ph)
    p15b = (all(v is not None for v in e7ph+e3ph)
            and sd_ph_e7 is not None and sd_ph_e3 is not None
            and sd_ph_e7 >= 2.5 * max(sd_ph_e3, 0.25))
    verdicts["P15_death_by_timetable"] = {
        "seed_axis": {"E7_c1": e7c1, "E7_c2": e7c2, "sd_c1": sd_c1, "sd_c2": sd_c2,
                      "pass": p15a},
        "phase_axis": {"E7": e7ph, "E3": e3ph, "sd_E7": sd_ph_e7, "sd_E3": sd_ph_e3,
                       "pass": p15b},
        "pass": p15a and p15b }

    # P16 — instrument: two doors, both real; deterministic narratives
    seed_hashes = [seed_runs[s]["hash"] for s in SEEDS]
    phase_hashes = [phase_runs[k]["hash"] for k in PHASES]
    all_runs = list(seed_runs.values()) + [phase_runs[k] for k in PHASES[1:]] + [rep7b]
    p16 = (rep7b["hash"] == seed_runs[BASE_SEED]["hash"]
           and len(set(seed_hashes)) == len(seed_hashes)
           and len(set(phase_hashes)) == len(phase_hashes)
           and all(r["n"] == N_EXPECTED for r in all_runs)
           and all(r["errors"] == 0 and not r["pageerrors"] for r in all_runs))
    verdicts["P16_instrument"] = {
        "repeat_hash_match": rep7b["hash"] == seed_runs[BASE_SEED]["hash"],
        "distinct_seed_hashes": len(set(seed_hashes)),
        "distinct_phase_hashes": len(set(phase_hashes)),
        "pass": p16 }

    gallery = {}
    for s in SEEDS:
        for k, v in seed_lags[s].items():
            gallery.setdefault(k.split("_",1)[1] + "_" + k.split("_",1)[0], None)
    # full lag tables reported as data
    out = HERE / "verify4-verdicts.json"
    out.write_text(json.dumps({
        "verdicts": verdicts,
        "seed_lags": seed_lags,
        "phase_lags": phase_lags,
        "steady_seed7": {k: {e: round(v,4) for e,v in d.items()} for k,d in seed_sm[BASE_SEED].items()},
    }, indent=2))
    ok = all(v["pass"] for v in verdicts.values())
    for k, v in verdicts.items():
        slim = {kk: vv for kk, vv in v.items()
                if kk not in ("seed_axis","phase_axis")} if k=="P15_death_by_timetable" else v
        if k == "P15_death_by_timetable":
            slim["sd_seed_c1"] = v["seed_axis"]["sd_c1"]; slim["sd_seed_c2"] = v["seed_axis"]["sd_c2"]
            slim["sd_phase_E7"] = v["phase_axis"]["sd_E7"]; slim["sd_phase_E3"] = v["phase_axis"]["sd_E3"]
        print(k, "→", json.dumps(slim))
    print("ALL PASS" if ok else "SOMETHING DIED (read the body)")
    sys.exit(0 if ok else 1)

asyncio.run(main())
