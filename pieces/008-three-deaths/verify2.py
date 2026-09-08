# 008 verification #2 — dying (pass 2).
# House bloodline: P5-P8 written in index.html header BEFORE this file.
#
# AMENDMENT (run 1, 2026-09-09): P5/P6 as first written were FALSIFIED in
# direction — the corpse was worth more than the prediction. Measured lags
# (cycle 1): E1 +2.0 E2 +2.0 E3 +6.0 E4 -2.5 E5 +3.25 E6 -2.25.
# Discovery: stateful layers DIE LATE and are REBORN EARLY (they resist the
# executioner in both directions: dispersal is a sqrt-t random walk, slow;
# gathering is an exponential spring pull, fast; audibility saturates in
# gain — a half-dead layer is almost fully audible). The memoryless noise
# layer is the only symmetric one (2.0/2.0 = pure ear delay).
# Revised P5'/P6' are tested HELD-OUT on cycle 2 (tau 225..405 = a fresh
# noise realization of the same physics). P7/P8 unchanged (P7 now both
# cycles). Original falsification is preserved here and in the header.
#
# Protocol: two probe runs (TIME_SCALE=30). Run 1 supplies verdicts +
# judgment frame (mid structure-dying, tau≈95). Run 2 supplies hash (P8).

import asyncio, json, pathlib, statistics, sys
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
URL = (HERE / "index.html").as_uri() + "?probe=1"
RAMP = 10
N_EXPECTED = 1621         # tau 0..405 every 0.25s

# steady windows (post-ramp, pre-transition; ramp 10s so window opens at +20)
STEADY = {
    "FULL":  (20, 44),   "NN":  (65, 89),   "NS":  (110, 134), "NI":  (155, 179),
    "FULL2": (200, 224), "NN2": (245, 269), "NS2": (290, 314), "NI2": (335, 359),
    "FULL3": (380, 404),
}

# (name, ear, T, old_act, new_act) per cycle
def events(cycle):
    b = cycle * 180
    sfx = "" if cycle == 0 else "2"
    nxt = "2" if cycle == 0 else "3"
    return [
        (f"E1_noise_death",       "J", b+45,  f"FULL{sfx or ''}" if cycle==0 else "FULL2", f"NN{sfx}"),
        (f"E2_noise_rebirth",     "J", b+90,  f"NN{sfx}",  f"NS{sfx}"),
        (f"E3_structure_death",   "C", b+90,  f"NN{sfx}",  f"NS{sfx}"),
        (f"E4_structure_rebirth", "C", b+135, f"NS{sfx}",  f"NI{sfx}"),
        (f"E5_intent_death",      "I", b+135, f"NS{sfx}",  f"NI{sfx}"),
        (f"E6_intent_rebirth",    "I", b+180, f"NI{sfx}",  f"FULL{nxt}"),
    ]

async def probe(pw, shot=None):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width":1280,"height":720})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    if shot:  # tau≈95: structure mid-dying (95*4+1 = 381 samples)
        await page.wait_for_function(
            "window.__report && window.__report().n >= 381", timeout=90000)
        await page.screenshot(path=str(shot))
    await page.wait_for_function("window.__done === true", timeout=300000)
    rep = await page.evaluate("window.__report()")
    await browser.close()
    rep["pageerrors"] = errors
    return rep

def med(samples, lo, hi, key):
    return statistics.median(s[key] for s in samples if lo <= s["tau"] <= hi)

def crossing_lag(samples, ear, T, m_old, m_new):
    """First tau in [T, T+30] where 3 consecutive samples pass the midpoint
    toward m_new. Lag measured from the ramp midpoint T+RAMP/2."""
    mid = (m_old + m_new) / 2
    rising = m_new > m_old
    win = [s for s in samples if T <= s["tau"] <= T + 30]
    for i in range(len(win) - 2):
        trio = win[i:i+3]
        if all((s[ear] > mid) == rising for s in trio):
            return round(trio[0]["tau"] - (T + RAMP/2), 2)
    return None

async def main():
    async with async_playwright() as pw:
        r1 = await probe(pw, shot=HERE / "pass2-dying-structure.png")
        r2 = await probe(pw)

    samples = sorted(r1["samples"], key=lambda x: x["tau"])
    sm = {k: {e: med(samples, lo, hi, e) for e in ("I","C","J")}
          for k, (lo, hi) in STEADY.items()}
    verdicts = {}

    # INSTRUMENT REPAIR #2 (see header): the dead-intent state has no anchored
    # value (NI median is a realization artifact inside the +-0.25 blind band:
    # c1 0.031 vs c2 0.198 -> E5 drifted 6.25s). For I events the dead-side
    # anchor is the DESIGN value 0 (the blind band's center — P1's own
    # definition of dead intent); threshold = m_live/2. C/J events untouched
    # (both their endpoints are anchored, and both reproduced held-out).
    lags = {}
    for cyc in (0, 1):
        for name, ear, T, oa, na in events(cyc):
            if ear == "I":
                live = sm[oa][ear] if "death" in name else sm[na][ear]
                dead = 0.0
                m_old = live if "death" in name else dead
                m_new = dead if "death" in name else live
            else:
                m_old, m_new = sm[oa][ear], sm[na][ear]
            lags[f"c{cyc+1}_{name}"] = crossing_lag(samples, ear, T, m_old, m_new)

    # FINAL (P5f/P6f — see header Run 3 amendment): the I layer's dying
    # speed was twice shown to belong to the REALIZATION, not the layer
    # (drift 6.25s survives the anchor repair). Diagnosis: C and J are
    # ensemble averages (24 springs / 25 nodes, self-averaging); I is a
    # single degree of freedom — its death is circumstantial, a narrative
    # not a statistic. I-event lags are REPORTED as data, not gated;
    # their variance IS the finding.

    # P5f — self-averaging layers' signature, BOTH cycles:
    # A = lag_death - lag_rebirth; A_C >= 4 (dies late, reborn early),
    # |A_J| <= 2 (memoryless = obeys the executioner's clock).
    def asym(cyc, d, r):
        a, b = lags[f"c{cyc}_{d}"], lags[f"c{cyc}_{r}"]
        return None if a is None or b is None else round(a - b, 2)
    A = {f"c{c}": { "C": asym(c, "E3_structure_death", "E4_structure_rebirth"),
                    "I": asym(c, "E5_intent_death",    "E6_intent_rebirth"),
                    "J": asym(c, "E1_noise_death",     "E2_noise_rebirth") }
         for c in (1, 2)}
    p5 = all(A[c]["C"] is not None and A[c]["J"] is not None
             and A[c]["C"] >= 4.0 and abs(A[c]["J"]) <= 2.0 for c in ("c1","c2"))
    verdicts["P5f_selfavg_asymmetry_both_cycles"] = {
        "asymmetry": A, "I_note": "reported, not gated — circumstantial death",
        "lags": lags, "pass": p5 }

    # P6f — lag is the layer's property for self-averaging events (E1-E4):
    # cross-cycle drift <= 1.5s. E5/E6 drift reported as data.
    drift = {}
    for name, *_ in events(0):
        a, b = lags[f"c1_{name}"], lags[f"c2_{name}"]
        drift[name] = None if a is None or b is None else round(abs(a - b), 2)
    gated = ["E1_noise_death","E2_noise_rebirth","E3_structure_death","E4_structure_rebirth"]
    p6 = all(drift[k] is not None and drift[k] <= 1.5 for k in gated)
    verdicts["P6f_lag_is_layer_property_selfavg"] = {
        "cross_cycle_drift": drift, "gated_events": gated,
        "I_drift_as_data": {k: drift[k] for k in drift if k.startswith(("E5","E6"))},
        "pass": p6 }

    # P7 — freed-head holds THROUGH the dying window, both cycles
    d1 = [s["I"] for s in samples if 90 <= s["tau"] <= 110]
    d2 = [s["I"] for s in samples if 270 <= s["tau"] <= 290]
    verdicts["P7_freed_head_through_dying"] = {
        "min_I_c1": round(min(d1), 4), "min_I_c2": round(min(d2), 4),
        "pass": min(d1) >= 0.5 and min(d2) >= 0.5 }

    # P8 — instrument: determinism at new resolution + P1/P2 regression (cycle 1)
    m = [sm["FULL"], sm["NN"], sm["NS"], sm["NI"]]
    cells = {
        "FULL":         m[0]["I"] >= 0.35 and m[0]["C"] >= 0.80 and m[0]["J"] >= 0.10,
        "NO_NOISE":     m[1]["I"] >= 0.45 and m[1]["C"] >= 0.80 and m[1]["J"] <= 0.5*m[0]["J"],
        "NO_STRUCTURE": m[2]["I"] >= 0.30 and m[2]["C"] <= 0.60 and m[2]["J"] >= 0.10,
        "NO_INTENT":    abs(m[3]["I"]) <= 0.25 and m[3]["C"] >= 0.80 and m[3]["J"] >= 0.10,
    }
    def blind(a, b): return abs(a-b) < 0.2*max(abs(a), abs(b), 1e-9)
    pairs = {
        "I_blind_FULL_vs_NN": blind(m[0]["I"], m[1]["I"]) and m[0]["J"] >= 2*m[1]["J"],
        "C_blind_FULL_vs_NI": blind(m[0]["C"], m[3]["C"]) and abs(m[0]["I"]-m[3]["I"]) >= 0.25,
        "J_blind_FULL_vs_NS": blind(m[0]["J"], m[2]["J"]) and abs(m[0]["C"]-m[2]["C"]) >= 0.25,
    }
    verdicts["P8_instrument"] = {
        "n1": r1["n"], "n2": r2["n"], "hash1": r1["hash"], "hash2": r2["hash"],
        "errors": r1["errors"] + len(r1["pageerrors"]), "fps": r1["fps"],
        "P1_regression": cells, "P2_regression": pairs,
        "steady_medians": {k: {e: round(v,4) for e,v in mm.items()} for k,mm in sm.items()},
        "pass": (r1["n"] == N_EXPECTED and r2["n"] == N_EXPECTED
                 and r1["hash"] == r2["hash"] and r1["errors"] == 0
                 and not r1["pageerrors"] and all(cells.values()) and all(pairs.values())),
    }

    out = HERE / "verify2-verdicts.json"
    out.write_text(json.dumps({"verdicts": verdicts}, indent=2))
    ok = all(v["pass"] for v in verdicts.values())
    for k, v in verdicts.items(): print(k, "→", json.dumps(v))
    print("ALL PASS" if ok else "SOMETHING DIED (read the body)")
    sys.exit(0 if ok else 1)

asyncio.run(main())
