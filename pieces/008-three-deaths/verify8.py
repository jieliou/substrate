# 008 verification #8 — the phantom pair (pass 8).
# House bloodline: P25-P28 written in index.html header BEFORE this file ran.
#
# Pass 7 proved the post-cut F residue is head-independent ("the room, not
# the relationship") but could not separate a PHYSICAL room (shared
# containment geometry) from NO room at all (two identical bodies breathing
# in the same slow band; the clamped finite-window correlation rectifies
# same-band noise into a positive floor). The control that decides: pair
# worm A's tail from world k with worm B's tail from world j != k — same
# make, same schedule, zero shared anything. If the phantom pair correlates
# like the real pair, the room was never there.
#
# WORLD CHANGES: NONE. Probe export only (va/vb smoothed tail velocities);
# hash string unchanged — pass-7 physics must reproduce to the digit (P28).

import asyncio, json, pathlib, statistics
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
SEEDS = list(range(1, 13))
BASE_SEED = 7
N_EXPECTED = 1921
EARS = ("I", "C", "J", "S", "F")
DTS = 0.25          # sample spacing (s)
TAU_F = 2.0         # F-ear EMA time constant (s) — mirrors index.html

STEADY = {
    "FULL":  (20, 44),   "NI":  (155, 179), "NOSOC": (200, 224),
    "FULL2": (245, 269), "NI2": (380, 404), "NOSOC2": (425, 449),
}

def med(vals):
    return statistics.median(vals)

def steady_medians(rep):
    s = sorted(rep["samples"], key=lambda x: x["tau"])
    return {k: {e: med([r[e] for r in s if lo <= r["tau"] <= hi]) for e in EARS}
            for k, (lo, hi) in STEADY.items()}

def offline_F(rows_a, rows_b):
    """Recompute the F ear offline from exported smoothed tail velocities.
    rows_a supplies worm A's tail (va), rows_b supplies worm B's tail (vb).
    Same clamped-EMA recursion as index.html, at the 0.25s sample grid.
    Returns {tau: F} for every sample instant."""
    alpha = DTS / TAU_F
    gXc, gPa, gPb = 0.0, 1e-6, 1e-6
    out = {}
    for ra, rb in zip(rows_a, rows_b):
        ax, ay = ra["va"]
        bx, by = rb["vb"]
        gXc += (ax * bx + ay * by - gXc) * alpha
        gPa += (ax * ax + ay * ay - gPa) * alpha
        gPb += (bx * bx + by * by - gPb) * alpha
        f = gXc / (gPa * gPb + 1e-12) ** 0.5
        out[ra["tau"]] = max(0.0, min(1.0, f))
    return out

def window_median(fmap, lo, hi):
    return med([v for t, v in fmap.items() if lo <= t <= hi])

async def probe(pw, seed):
    url = (HERE / "index.html").as_uri() + f"?probe=1&seed={seed}"
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 720})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(url)
    await page.wait_for_function("window.__done === true", timeout=300000)
    rep = await page.evaluate("window.__report()")
    await browser.close()
    rep["pageerrors"] = errors
    return rep

async def main():
    async with async_playwright() as pw:
        reps = {}
        for s in SEEDS:
            reps[s] = await probe(pw, s)
            print(f"world {s}: hash={reps[s]['hash']} n={reps[s]['n']}", flush=True)
        repb = await probe(pw, BASE_SEED)   # determinism repeat

    rows = {s: sorted(reps[s]["samples"], key=lambda x: x["tau"]) for s in SEEDS}
    sm = {s: steady_medians(reps[s]) for s in SEEDS}
    verdicts = {}

    # ---- P25: offline ear validation (same-world reconstruction vs in-sim) ----
    nosoc_windows = [("NOSOC", *STEADY["NOSOC"]), ("NOSOC2", *STEADY["NOSOC2"])]
    diffs = []
    per_world_offline = {}
    for s in SEEDS:
        fmap = offline_F(rows[s], rows[s])
        per_world_offline[s] = fmap
        for name, lo, hi in nosoc_windows:
            d = abs(window_median(fmap, lo, hi) - sm[s][name]["F"])
            diffs.append(round(d, 4))
    p25 = med(diffs) <= 0.05 and max(diffs) <= 0.15
    verdicts["P25_offline_ear_validation"] = {
        "median_abs_diff": round(med(diffs), 4), "max_abs_diff": round(max(diffs), 4),
        "gate": "median<=0.05 and max<=0.15", "pass": p25 }

    # ---- P26: the phantom pair (primary cycle = NOSOC2, the higher-residue one) ----
    # Real pairs measured with the SAME offline estimator for symmetry.
    real_c2 = [window_median(per_world_offline[s], *STEADY["NOSOC2"]) for s in SEEDS]
    real_c1 = [window_median(per_world_offline[s], *STEADY["NOSOC"]) for s in SEEDS]
    phantom_pairs = [(k, (k % 12) + 1) for k in SEEDS]
    ph_c2, ph_c1, ph_full = [], [], []
    for a, b in phantom_pairs:
        fmap = offline_F(rows[a], rows[b])
        ph_c2.append(window_median(fmap, *STEADY["NOSOC2"]))
        ph_c1.append(window_median(fmap, *STEADY["NOSOC"]))
        ph_full.append(window_median(fmap, *STEADY["FULL"]))
    R_real, R_ph = med(real_c2), med(ph_c2)
    ratio = round(R_ph / R_real, 3) if R_real > 1e-6 else None
    if ratio is None:
        verdict = "undefined"
    elif ratio >= 0.5:
        verdict = "spectrum"      # the room is the make of the bodies
    elif ratio <= 0.2:
        verdict = "room"          # a physical in-world channel survives the control
    else:
        verdict = "gray"
    verdicts["P26_phantom_pair"] = {
        "R_real_c2": round(R_real, 4), "R_phantom_c2": round(R_ph, 4),
        "ratio": ratio, "verdict": verdict,
        "R_real_c1": round(med(real_c1), 4), "R_phantom_c1": round(med(ph_c1), 4),
        "phantom_FULL_median": round(med(ph_full), 4),
        "real_c2_all": [round(v, 4) for v in real_c2],
        "phantom_c2_all": [round(v, 4) for v in ph_c2],
        "pass": verdict in ("spectrum", "room") }   # gray = not resolved

    # ---- P27: the seed-7 anomaly — does it need both halves of world 7? ----
    a7 = [window_median(offline_F(rows[7], rows[j]), *STEADY["NOSOC2"])
          for j in SEEDS if j != 7]
    b7 = [window_median(offline_F(rows[j], rows[7]), *STEADY["NOSOC2"])
          for j in SEEDS if j != 7]
    pop = med(ph_c2)
    a7m, b7m = med(a7), med(b7)
    joint = a7m <= 1.5 * pop and b7m <= 1.5 * pop
    verdicts["P27_seed7_anomaly"] = {
        "seed7_real_NOSOC2_F_insim": round(sm[7]["NOSOC2"]["F"], 4),
        "A7_with_strangers_median": round(a7m, 4),
        "B7_with_strangers_median": round(b7m, 4),
        "population_phantom_median": round(pop, 4),
        "verdict": "joint-realization" if joint else "loud-body",
        "pass": True }   # two-outcome discriminator, reported either way

    # ---- P28: instrument + no-touch proof against pass 7 stored medians ----
    hashes = [reps[s]["hash"] for s in SEEDS]
    all_runs = list(reps.values()) + [repb]
    v7 = json.loads((HERE / "verify7-verdicts.json").read_text())
    stored = v7["steady_seed7_free0"]
    no_touch = all(
        round(sm[BASE_SEED][k][e], 4) == stored[k][e]
        for k in STEADY for e in EARS)
    instrument = (
        repb["hash"] == reps[BASE_SEED]["hash"]
        and len(set(hashes)) == len(hashes)
        and all(r["n"] == N_EXPECTED for r in all_runs)
        and all(r["errors"] == 0 and not r["pageerrors"] for r in all_runs)
        and no_touch)
    verdicts["P28_instrument_no_touch"] = {
        "repeat_match": repb["hash"] == reps[BASE_SEED]["hash"],
        "distinct_hashes": len(set(hashes)),
        "n_ok": all(r["n"] == N_EXPECTED for r in all_runs),
        "zero_errors": all(r["errors"] == 0 and not r["pageerrors"] for r in all_runs),
        "pass7_steady_medians_reproduced": no_touch,
        "pass": instrument }

    gated = ("P25_offline_ear_validation", "P26_phantom_pair", "P28_instrument_no_touch")
    ok = all(verdicts[k]["pass"] for k in gated)

    out = HERE / "verify8-verdicts.json"
    out.write_text(json.dumps({"verdicts": verdicts}, indent=2))
    for k, v in verdicts.items():
        print(k, "→", json.dumps(v))
    print("ALL PASS" if ok else "SOME FAIL", "— verdicts in", out.name)

asyncio.run(main())
