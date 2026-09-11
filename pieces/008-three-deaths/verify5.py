# 008 verification #5 — tail-to-tail bond (pass 5).
# House bloodline: P17-P19 + verbatim P13/P14/P15a written in index.html
# header BEFORE this file ran.
#
# The injection-point law on trial: pass 4 failed P13/P14 three times with
# the bond at the heads (weak=decoration, strong=domination, middle=both
# taxed). Pass 5 moves the bond to the tails — farthest node from intent's
# injection. If the law is real, the force-budget conflict dissolves and
# the fourth cell finally passes. If I stays strangled, the law dies.

import asyncio, json, pathlib, statistics, sys
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
RAMP = 10
N_EXPECTED = 1921
SEEDS = list(range(1, 13))
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
    """P13 VERBATIM from verify4 (run-3 gates)."""
    fails = []
    for s in ("", "2"):
        F, NN, NS, NI, NO = (sm["FULL"+s], sm["NN"+s], sm["NS"+s],
                             sm["NI"+s], sm["NOSOC"+s])
        if not (F["I"] >= 0.35 and F["C"] >= 0.80 and F["J"] >= 0.10):
            fails.append("FULL"+s)
        if not (NN["I"] >= 0.45 and NN["C"] >= 0.80 and NN["J"] <= 0.5*F["J"]):
            fails.append("NN"+s)
        if not (NS["I"] >= 0.20 and NS["C"] <= 0.60 and NS["J"] >= 0.10):
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
    """P14 VERBATIM from verify4 (run-2 gates)."""
    fails = []
    for s in ("", "2"):
        if not (sm["NI"+s]["S"] >= sm["FULL"+s]["S"] + 0.10
                and sm["NI"+s]["S"] >= 0.8):
            fails.append("NI"+s)
    return fails

def sd(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.stdev(xs), 3) if len(xs) > 1 else None

async def main():
    async with async_playwright() as pw:
        seed_runs = {}
        for s in SEEDS:
            seed_runs[s] = await probe(pw, s, 0)
            print(f"world {s}: n={seed_runs[s]['n']} hash={seed_runs[s]['hash']}", flush=True)
        rep7b = await probe(pw, BASE_SEED, 0)

    seed_lags, seed_sm = {}, {}
    for s in SEEDS:
        seed_lags[s], seed_sm[s] = lags_for(seed_runs[s])

    verdicts = {}

    # P13 — fourth cell + regression, verbatim
    cell_fails = {s: cells_ok(seed_sm[s]) for s in SEEDS}
    p13 = all(not f for f in cell_fails.values())
    verdicts["P13_fourth_cell_and_regression"] = {
        "fails": {s: f for s, f in cell_fails.items() if f}, "pass": p13 }

    # P14 — kill intent, the bond gets louder, verbatim
    p14_fails = {s: p14_ok(seed_sm[s]) for s in SEEDS}
    p14 = all(not f for f in p14_fails.values())
    verdicts["P14_social_loudens_when_intent_dies"] = {
        "fails": {s: f for s, f in p14_fails.items() if f},
        "S_FULL_med": round(statistics.median(seed_sm[s]["FULL"]["S"] for s in SEEDS), 3),
        "S_NI_med":   round(statistics.median(seed_sm[s]["NI"]["S"] for s in SEEDS), 3),
        "pass": p14 }

    # P15a — species regression, seed axis only (phase axis stands on pass 4)
    e7c1 = [seed_lags[s]["c1_E7_social_death"] for s in SEEDS]
    e7c2 = [seed_lags[s]["c2_E7_social_death"] for s in SEEDS]
    sd_c1, sd_c2 = sd(e7c1), sd(e7c2)
    p15a = (all(v is not None for v in e7c1+e7c2)
            and sd_c1 is not None and sd_c1 <= 1.0
            and sd_c2 is not None and sd_c2 <= 1.0)
    verdicts["P15a_timetable_seed_axis"] = {
        "E7_c1": e7c1, "E7_c2": e7c2, "sd_c1": sd_c1, "sd_c2": sd_c2,
        "pass": p15a }

    # P17 — the injection-point law (headline)
    full_I = [seed_sm[s]["FULL"]["I"] for s in SEEDS]
    med_full_I = round(statistics.median(full_I), 3)
    p17 = p13 and med_full_I >= 0.5
    verdicts["P17_injection_point_law"] = {
        "median_FULL_I": med_full_I, "run3_was": 0.21,
        "per_world_FULL_I": [round(v,3) for v in full_I],
        "pass": p17 }

    # P18 — the chain tax (sign test) + J-deafness (frequency separation)
    tax_signs_c1 = [seed_sm[s]["NOSOC"]["C"] > seed_sm[s]["FULL"]["C"] for s in SEEDS]
    tax_signs_c2 = [seed_sm[s]["NOSOC2"]["C"] > seed_sm[s]["FULL2"]["C"] for s in SEEDS]
    tax_mag = [round(seed_sm[s]["NOSOC"]["C"] - seed_sm[s]["FULL"]["C"], 4) for s in SEEDS]
    p18a = sum(tax_signs_c1) >= 9
    jdiff = [abs(seed_sm[s]["FULL"]["J"] - seed_sm[s]["NOSOC"]["J"]) for s in SEEDS]
    med_jdiff = round(statistics.median(jdiff), 4)
    p18b = med_jdiff <= 0.03
    verdicts["P18_chain_tax_and_J_deafness"] = {
        "tax_sign_c1": sum(tax_signs_c1), "tax_sign_c2_heldout": sum(tax_signs_c2),
        "tax_magnitude_c1": tax_mag, "median_J_diff": med_jdiff,
        "pass_a_sign": p18a, "pass_b_deaf": p18b, "pass": p18a and p18b }

    # P19 — instrument
    seed_hashes = [seed_runs[s]["hash"] for s in SEEDS]
    all_runs = list(seed_runs.values()) + [rep7b]
    p19 = (rep7b["hash"] == seed_runs[BASE_SEED]["hash"]
           and len(set(seed_hashes)) == len(seed_hashes)
           and all(r["n"] == N_EXPECTED for r in all_runs)
           and all(r["errors"] == 0 and not r["pageerrors"] for r in all_runs))
    verdicts["P19_instrument"] = {
        "repeat_hash_match": rep7b["hash"] == seed_runs[BASE_SEED]["hash"],
        "distinct_seed_hashes": len(set(seed_hashes)),
        "pass": p19 }

    out = HERE / "verify5-verdicts.json"
    out.write_text(json.dumps({
        "verdicts": verdicts,
        "seed_lags": seed_lags,
        "steady_seed7": {k: {e: round(v,4) for e,v in d.items()} for k,d in seed_sm[BASE_SEED].items()},
    }, indent=2))
    ok = all(v["pass"] for v in verdicts.values())
    for k, v in verdicts.items():
        slim = {kk: vv for kk, vv in v.items() if kk not in ("per_world_FULL_I","tax_magnitude_c1","E7_c1","E7_c2")}
        print(k, "→", json.dumps(slim))
    print("ALL PASS" if ok else "SOMETHING DIED (read the body)")
    sys.exit(0 if ok else 1)

asyncio.run(main())
