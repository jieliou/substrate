# 008 verification #9 — the die and the leash (pass 9).
# House bloodline: P29-P33 written in index.html header BEFORE this file ran.
#
# Pass 8's phantom control proved the post-cut F residue is a real in-world
# channel (phantom 0.0 vs real 0.1506). Two suspects were registered (cage
# geometry, shared RNG stream) and preparing this pass exposed a third that
# had been hiding in a comment since pass 4: EPS=0.02 means the NOSOC act
# never actually cuts the bond — K_O*EPS=3 of spring ties the two TAILS (the
# F ear's own nodes) through every "no social" window. Two probe doors:
#   ?rng=split  — worm B rolls its own die (door #4)
#   ?cut=1      — NOSOC truly cuts the bond, EPS -> 0 (door #5)
# Conditions: split / cut / splitcut x 12 worlds + default seed-7 no-touch.
# Baseline R_default = verify8 P26's offline real_c2_all (reused, no re-run).

import asyncio, json, pathlib, statistics
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
SEEDS = list(range(1, 13))
BASE_SEED = 7
N_EXPECTED = 1921
EARS = ("I", "C", "J", "S", "F")
DTS = 0.25
TAU_F = 2.0

STEADY = {
    "FULL":  (20, 44),   "NI":  (155, 179), "NOSOC": (200, 224),
    "FULL2": (245, 269), "NI2": (380, 404), "NOSOC2": (425, 449),
}

CONDITIONS = {          # name -> extra query
    "default":  "",
    "split":    "&rng=split",
    "cut":      "&cut=1",
    "splitcut": "&rng=split&cut=1",
}

def med(vals): return statistics.median(vals)

def steady_medians(rep):
    s = sorted(rep["samples"], key=lambda x: x["tau"])
    return {k: {e: med([r[e] for r in s if lo <= r["tau"] <= hi]) for e in EARS}
            for k, (lo, hi) in STEADY.items()}

def offline_F(rows_a, rows_b):
    alpha = DTS / TAU_F
    gXc, gPa, gPb = 0.0, 1e-6, 1e-6
    out = {}
    for ra, rb in zip(rows_a, rows_b):
        ax, ay = ra["va"]; bx, by = rb["vb"]
        gXc += (ax * bx + ay * by - gXc) * alpha
        gPa += (ax * ax + ay * ay - gPa) * alpha
        gPb += (bx * bx + by * by - gPb) * alpha
        f = gXc / (gPa * gPb + 1e-12) ** 0.5
        out[ra["tau"]] = max(0.0, min(1.0, f))
    return out

def window_median(fmap, lo, hi):
    return med([v for t, v in fmap.items() if lo <= t <= hi])

async def probe(pw, seed, extra):
    url = (HERE / "index.html").as_uri() + f"?probe=1&seed={seed}{extra}"
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
        runs = {}          # (cond, seed) -> rep
        for cond in ("split", "cut", "splitcut"):
            for s in SEEDS:
                runs[(cond, s)] = await probe(pw, s, CONDITIONS[cond])
                print(f"{cond} world {s}: hash={runs[(cond,s)]['hash']} "
                      f"n={runs[(cond,s)]['n']}", flush=True)
        runs[("default", BASE_SEED)] = await probe(pw, BASE_SEED, "")
        print(f"default world 7: hash={runs[('default',BASE_SEED)]['hash']}", flush=True)
        rep_split_b = await probe(pw, BASE_SEED, CONDITIONS["split"])
        rep_cut_b   = await probe(pw, BASE_SEED, CONDITIONS["cut"])

    rows = {k: sorted(r["samples"], key=lambda x: x["tau"]) for k, r in runs.items()}
    verdicts = {}

    # ---- baselines from pass 8 (offline estimator, same worlds) ----
    v8 = json.loads((HERE / "verify8-verdicts.json").read_text())
    base_c2_all = v8["verdicts"]["P26_phantom_pair"]["real_c2_all"]
    R_default = med(base_c2_all)                      # 0.1506
    R_default_c1 = v8["verdicts"]["P26_phantom_pair"]["R_real_c1"]

    # ---- per-condition offline residues ----
    cond_stats = {}
    for cond in ("split", "cut", "splitcut"):
        c2, c1 = [], []
        for s in SEEDS:
            fmap = offline_F(rows[(cond, s)], rows[(cond, s)])
            c2.append(round(window_median(fmap, *STEADY["NOSOC2"]), 4))
            c1.append(round(window_median(fmap, *STEADY["NOSOC"]), 4))
        cond_stats[cond] = {"c2_all": c2, "c1_all": c1,
                            "R_c2": round(med(c2), 4), "R_c1": round(med(c1), 4)}

    def ratio_and_verdict(R_cond):
        if R_default <= 1e-6: return None, "undefined"
        r = round(R_cond / R_default, 3)
        if r <= 0.2: return r, "collapsed"
        if r >= 0.5: return r, "exonerated"
        return r, "partial"

    # ---- P30: the leash (cut alone) ----
    r30, v30 = ratio_and_verdict(cond_stats["cut"]["R_c2"])
    verdicts["P30_the_leash"] = {
        "R_default_c2": round(R_default, 4), "R_cut_c2": cond_stats["cut"]["R_c2"],
        "ratio": r30, "verdict": ("LEASH" if v30 == "collapsed" else v30),
        "R_cut_c1": cond_stats["cut"]["R_c1"], "R_default_c1": R_default_c1,
        "cut_c2_all": cond_stats["cut"]["c2_all"],
        "pass": v30 in ("collapsed", "exonerated") }

    # ---- P31: the die (split alone) ----
    r31, v31 = ratio_and_verdict(cond_stats["split"]["R_c2"])
    verdicts["P31_the_die"] = {
        "R_split_c2": cond_stats["split"]["R_c2"], "ratio": r31,
        "verdict": ("DICE" if v31 == "collapsed" else v31),
        "R_split_c1": cond_stats["split"]["R_c1"],
        "split_c2_all": cond_stats["split"]["c2_all"],
        "pass": v31 in ("collapsed", "exonerated") }

    # ---- P32: closure (both doors) ----
    r32, v32 = ratio_and_verdict(cond_stats["splitcut"]["R_c2"])
    if v30 == "collapsed" or v31 == "collapsed":
        closure = "consistent" if v32 == "collapsed" else "INCONSISTENT"
    elif v32 == "collapsed":
        closure = "stacked-channels"
    else:
        closure = "suspects-exhausted-reopen-phantom-read"
    verdicts["P32_closure"] = {
        "R_splitcut_c2": cond_stats["splitcut"]["R_c2"], "ratio": r32,
        "closure": closure,
        "splitcut_c2_all": cond_stats["splitcut"]["c2_all"],
        "pass": closure in ("consistent", "stacked-channels") }

    # ---- P33: seed-7 under each door ----
    s7 = {}
    for cond in ("split", "cut", "splitcut"):
        sm7 = steady_medians(runs[(cond, BASE_SEED)])
        fmap = offline_F(rows[(cond, BASE_SEED)], rows[(cond, BASE_SEED)])
        s7[cond] = {"insim_NOSOC": round(sm7["NOSOC"]["F"], 4),
                    "insim_NOSOC2": round(sm7["NOSOC2"]["F"], 4),
                    "offline_NOSOC2": round(window_median(fmap, *STEADY["NOSOC2"]), 4)}
    verdicts["P33_seed7"] = {**s7, "pass": True}   # reported either way

    # ---- P29: instrument + no-touch ----
    v7 = json.loads((HERE / "verify7-verdicts.json").read_text())
    stored = v7["steady_seed7_free0"]
    sm_def = steady_medians(runs[("default", BASE_SEED)])
    no_touch = all(round(sm_def[k][e], 4) == stored[k][e] for k in STEADY for e in EARS)
    def_hash = runs[("default", BASE_SEED)]["hash"]
    cond_hashes = {c: [runs[(c, s)]["hash"] for s in SEEDS]
                   for c in ("split", "cut", "splitcut")}
    all_runs = list(runs.values()) + [rep_split_b, rep_cut_b]
    verdicts["P29_instrument"] = {
        "no_touch_vs_pass7": no_touch,
        "split_repeat_match": rep_split_b["hash"] == runs[("split", BASE_SEED)]["hash"],
        "cut_repeat_match": rep_cut_b["hash"] == runs[("cut", BASE_SEED)]["hash"],
        "doors_reach_physics": all(
            cond_hashes[c][BASE_SEED-1] != def_hash for c in cond_hashes),
        "distinct_within_condition": all(
            len(set(h)) == len(h) for h in cond_hashes.values()),
        "n_ok": all(r["n"] == N_EXPECTED for r in all_runs),
        "zero_errors": all(r["errors"] == 0 and not r["pageerrors"] for r in all_runs),
    }
    verdicts["P29_instrument"]["pass"] = all(
        v for k, v in verdicts["P29_instrument"].items() if k != "pass")

    out = {"verdicts": verdicts,
           "steady_seed7_default": {k: {e: round(sm_def[k][e], 4) for e in EARS}
                                     for k in STEADY}}
    (HERE / "verify9-verdicts.json").write_text(json.dumps(out, indent=1))
    for k, v in verdicts.items():
        line = {kk: vv for kk, vv in v.items()
                if not kk.endswith("_all") and kk != "pass"}
        print(f"{k}: {'PASS' if v['pass'] else 'FAIL'} {line}", flush=True)

asyncio.run(main())
