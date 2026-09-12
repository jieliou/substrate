# 008 verification #6 — the force-channel ear (pass 6).
# House bloodline: P20-P23 written in index.html header BEFORE this file ran.
#
# Pass 5 left the species question at the tail honestly UNMEASURED: the
# geometry ear (S v2) read 0.998 through the whole NOSOC act — the bond's
# arrangement outlives the bond. Pass 6 adds an ear in the FORCE channel
# (F = cross-correlation of the two tails' high-pass velocity residuals):
# geometry remembers, force forgets. If F hears E7 inside the act, the
# imprint becomes a differential reading (one node, two channels, two
# speeds of death) and the species question reopens with P23's thresholds.

import asyncio, json, pathlib, statistics, sys
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
RAMP = 10
N_EXPECTED = 1921
SEEDS = list(range(1, 13))
BASE_SEED = 7
EARS = ("I", "C", "J", "S", "F")

STEADY = {
    "FULL":  (20, 44),   "NN":  (65, 89),   "NS":  (110, 134),
    "NI":    (155, 179), "NOSOC": (200, 224),
    "FULL2": (245, 269), "NN2": (290, 314), "NS2": (335, 359),
    "NI2":   (380, 404), "NOSOC2": (425, 449),
}

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

def steady_medians(rep):
    samples = sorted(rep["samples"], key=lambda x: x["tau"])
    return samples, {k: {e: med(samples, lo, hi, e) for e in EARS}
                     for k, (lo, hi) in STEADY.items()}

def f_lags(samples, sm):
    """E7/E8 crossing lags on the F ear, both cycles."""
    out = {}
    for cyc in (0, 1):
        b = cyc * 225
        s = "" if cyc == 0 else "2"
        out[f"c{cyc+1}_E7_F"] = crossing_lag(
            samples, "F", b+180, sm["NI"+s]["F"], sm["NOSOC"+s]["F"])
        nxt = "FULL2" if cyc == 0 else "FULL"
        out[f"c{cyc+1}_E8_F"] = crossing_lag(
            samples, "F", b+225, sm["NOSOC"+s]["F"], sm[nxt]["F"])
    return out

async def main():
    async with async_playwright() as pw:
        seed_runs = {}
        for s in SEEDS:
            seed_runs[s] = await probe(pw, s, 0)
            print(f"world {s}: n={seed_runs[s]['n']} hash={seed_runs[s]['hash']}", flush=True)
        rep7b = await probe(pw, BASE_SEED, 0)

    world = {}
    for s in SEEDS:
        samples, sm = steady_medians(seed_runs[s])
        world[s] = {"samples": samples, "sm": sm, "flags": f_lags(samples, sm)}

    def med_over_worlds(act, ear):
        return round(statistics.median(world[s]["sm"][act][ear] for s in SEEDS), 4)

    verdicts = {}

    # P20 — the forgetting channel
    ni_f  = [(med_over_worlds("NI","F"), med_over_worlds("NI2","F"))]
    p20a = med_over_worlds("NI","F") >= 0.35 and med_over_worlds("NI2","F") >= 0.35
    p20b = med_over_worlds("NOSOC","F") <= 0.15 and med_over_worlds("NOSOC2","F") <= 0.15
    e7c1 = [world[s]["flags"]["c1_E7_F"] for s in SEEDS]
    e7c2 = [world[s]["flags"]["c2_E7_F"] for s in SEEDS]
    # separation guard (run-1 lesson): a crossing may only count when the
    # two anchors are actually apart — flat-signal crossings are noise
    # (pass 5 P15a's trap, reproduced by run 1's degenerate m_old=m_new=0).
    def sep_ok(s_, cyc):
        a = "" if cyc == 0 else "2"
        return abs(world[s_]["sm"]["NI"+a]["F"] - world[s_]["sm"]["NOSOC"+a]["F"]) >= 0.1
    good_c1 = sum(1 for s_, v in zip(SEEDS, e7c1) if v is not None and v <= 20 and sep_ok(s_, 0))
    good_c2 = sum(1 for s_, v in zip(SEEDS, e7c2) if v is not None and v <= 20 and sep_ok(s_, 1))
    p20c = good_c1 >= 10 and good_c2 >= 10
    verdicts["P20_forgetting_channel"] = {
        "NI_F_med": (med_over_worlds("NI","F"), med_over_worlds("NI2","F")),
        "NOSOC_F_med": (med_over_worlds("NOSOC","F"), med_over_worlds("NOSOC2","F")),
        "E7_F_c1": e7c1, "E7_F_c2": e7c2,
        "heard_within_20s": (good_c1, good_c2),
        "pass_a_carrier": p20a, "pass_b_forgets": p20b, "pass_c_heard": p20c,
        "pass": p20a and p20b and p20c }

    # P21 — two clocks at one address (the imprint as differential reading)
    p21 = (med_over_worlds("NOSOC","S") >= 0.9 and med_over_worlds("NOSOC2","S") >= 0.9
           and med_over_worlds("NOSOC","F") <= 0.15 and med_over_worlds("NOSOC2","F") <= 0.15)
    verdicts["P21_two_clocks_one_address"] = {
        "NOSOC_S_geo_med": (med_over_worlds("NOSOC","S"), med_over_worlds("NOSOC2","S")),
        "NOSOC_F_force_med": (med_over_worlds("NOSOC","F"), med_over_worlds("NOSOC2","F")),
        "pass": p21 }

    # P22 — regressions + instrument
    full_I = [world[s]["sm"]["FULL"]["I"] for s in SEEDS]
    med_full_I = round(statistics.median(full_I), 3)
    jdiff = [abs(world[s]["sm"]["FULL"]["J"] - world[s]["sm"]["NOSOC"]["J"]) for s in SEEDS]
    med_jdiff = round(statistics.median(jdiff), 4)
    seed_hashes = [seed_runs[s]["hash"] for s in SEEDS]
    all_runs = list(seed_runs.values()) + [rep7b]
    instrument = (rep7b["hash"] == seed_runs[BASE_SEED]["hash"]
                  and len(set(seed_hashes)) == len(seed_hashes)
                  and all(r["n"] == N_EXPECTED for r in all_runs)
                  and all(r["errors"] == 0 and not r["pageerrors"] for r in all_runs))
    p22 = med_full_I >= 0.5 and med_jdiff <= 0.03 and instrument
    verdicts["P22_regressions_instrument"] = {
        "median_FULL_I": med_full_I, "median_J_diff": med_jdiff,
        "repeat_hash_match": rep7b["hash"] == seed_runs[BASE_SEED]["hash"],
        "distinct_seed_hashes": len(set(seed_hashes)),
        "pass": p22 }

    # P23 — species at the tail, reopened as a QUESTION (never gated)
    def sd(xs):
        xs = [x for x in xs if x is not None]
        return round(statistics.stdev(xs), 3) if len(xs) > 1 else None
    sd_c1, sd_c2 = sd(e7c1), sd(e7c2)
    def classify(v):
        if v is None: return "unmeasured"
        if v <= 1.0: return "timetable"
        if v >= 3.0: return "circumstantial"
        return "gray"
    verdicts["P23_species_question"] = {
        "applicable": verdicts["P20_forgetting_channel"]["pass"],
        "sd_c1": sd_c1, "sd_c2": sd_c2,
        "verdict_c1": classify(sd_c1), "verdict_c2": classify(sd_c2),
        "pass": True }  # registered as a question — reported, not gated

    # NN cells — pre-registered caveat data (carrier off), reported unforced
    nn_report = {
        "NN_F_med": (med_over_worlds("NN","F"), med_over_worlds("NN2","F")),
        "note": "carrier (noise) off — F expected low regardless of bond; data, not gate"}

    out = HERE / "verify6-verdicts.json"  # run 2 overwrites run 1 (repair recorded in index.html header)
    out.write_text(json.dumps({
        "verdicts": verdicts,
        "NN_caveat": nn_report,
        "steady_seed7": {k: {e: round(v,4) for e,v in world[BASE_SEED]["sm"][k].items()}
                         for k in STEADY},
        "E8_F_lags": {f"c{c+1}": [world[s]["flags"][f"c{c+1}_E8_F"] for s in SEEDS] for c in (0,1)},
    }, indent=2))
    ok = all(v["pass"] for v in verdicts.values())
    for k, v in verdicts.items():
        slim = {kk: vv for kk, vv in v.items() if kk not in ("E7_F_c1","E7_F_c2")}
        print(k, "→", json.dumps(slim))
    print("NN caveat →", json.dumps(nn_report))
    print("ALL PASS" if ok else "SOME FAIL", "— verdicts in", out.name)

asyncio.run(main())
