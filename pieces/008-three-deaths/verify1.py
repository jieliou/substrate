# 008 verification #1 — first light.
# Ephemeral verifier, house bloodline: P1/P2/P4 written in index.html header
# BEFORE implementation. P3 stays field-deferred (the eye is the sensor).
#
# Protocol: two probe runs (TIME_SCALE=30). Run 1 supplies verdicts +
# judgment frame (screenshot inside NO-STRUCTURE, tau≈110 — the dust death).
# Run 2 supplies only its FNV hash for P4.

import asyncio, json, pathlib, statistics, sys
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
URL = (HERE / "index.html").as_uri() + "?probe=1"
ACT_LEN = 45
WINDOW = (15, 44)          # steady window inside each act (skip ramp+settle)

async def probe(pw, shot=None):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width":1280,"height":720})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    if shot:
        await page.wait_for_function(
            "window.__report && window.__report().n >= 111", timeout=60000)
        await page.screenshot(path=str(shot))
    await page.wait_for_function("window.__done === true", timeout=120000)
    rep = await page.evaluate("window.__report()")
    await browser.close()
    rep["pageerrors"] = errors
    return rep

def medians(samples, act):
    lo, hi = act*ACT_LEN + WINDOW[0], act*ACT_LEN + WINDOW[1]
    w = [s for s in samples if lo <= s["tau"] <= hi]
    return { k: statistics.median(s[k] for s in w) for k in ("I","C","J") }

async def main():
    async with async_playwright() as pw:
        r1 = await probe(pw, shot=HERE / "firstlight-dust-death.png")
        r2 = await probe(pw)

    samples = sorted(r1["samples"], key=lambda x: x["tau"])
    m = [medians(samples, a) for a in range(4)]   # FULL, NN, NS, NI
    verdicts = {}

    # P1 — four cells
    # AMENDMENT (run 1, 2026-09-08): J ear moved to tail + fixed V0 — the
    # head-ear heard wiggle-to-glide ratio (all layers at once): NO-INTENT
    # denominator inflation (J 0.57 > FULL 0.24) + NO-STRUCTURE drag-channel
    # eavesdrop (ΔJ 0.0817). NN cell now ratio-form (the ear is relative);
    # other cells unchanged. Instrument repaired, thresholds NOT bent to
    # readings (007 verifier-appeasement lesson).
    cells = {
        "FULL":         m[0]["I"] >= 0.35 and m[0]["C"] >= 0.80 and m[0]["J"] >= 0.10,
        "NO_NOISE":     m[1]["I"] >= 0.45 and m[1]["C"] >= 0.80 and m[1]["J"] <= 0.5*m[0]["J"],
        "NO_STRUCTURE": m[2]["I"] >= 0.30 and m[2]["C"] <= 0.60 and m[2]["J"] >= 0.10,
        "NO_INTENT":    abs(m[3]["I"]) <= 0.25 and m[3]["C"] >= 0.80 and m[3]["J"] >= 0.10,
    }
    verdicts["P1_four_cells"] = {
        "medians": [{k: round(v,4) for k,v in mm.items()} for mm in m],
        "cells": cells, "pass": all(cells.values()),
    }

    # P2 — single-ear blindness. AMENDMENT (run 1): blind criterion is now
    # relative (|Δ| < 0.2 × max of the pair) — J's magnitude scale changed
    # with the ear repair, absolute 0.08 was head-ear-specific.
    def blind(a, b): return abs(a-b) < 0.2*max(abs(a), abs(b), 1e-9)
    pairs = {
        "I_blind_FULL_vs_NN": {
            "blind_delta": abs(m[0]["I"]-m[1]["I"]),
            "separator": "J ratio", "sep_value": (m[0]["J"] / m[1]["J"]) if m[1]["J"] > 0 else float("inf"),
            "pass": blind(m[0]["I"], m[1]["I"]) and m[0]["J"] >= 2*m[1]["J"],
        },
        "C_blind_FULL_vs_NI": {
            "blind_delta": abs(m[0]["C"]-m[3]["C"]),
            "separator": "I delta", "sep_value": abs(m[0]["I"]-m[3]["I"]),
            "pass": blind(m[0]["C"], m[3]["C"]) and abs(m[0]["I"]-m[3]["I"]) >= 0.25,
        },
        "J_blind_FULL_vs_NS": {
            "blind_delta": abs(m[0]["J"]-m[2]["J"]),
            "separator": "C delta", "sep_value": abs(m[0]["C"]-m[2]["C"]),
            "pass": blind(m[0]["J"], m[2]["J"]) and abs(m[0]["C"]-m[2]["C"]) >= 0.25,
        },
    }
    for v in pairs.values():
        for k in ("blind_delta","sep_value"):
            v[k] = round(v[k], 4) if v[k] != float("inf") else "inf"
    verdicts["P2_blindness"] = { "pairs": pairs, "pass": all(p["pass"] for p in pairs.values()) }

    # P4 — determinism of a STATEFUL piece: step the schedule, not the frame
    verdicts["P4_determinism"] = {
        "n_samples": r1["n"], "hash1": r1["hash"], "hash2": r2["hash"],
        "errors": r1["errors"] + len(r1["pageerrors"]), "fps": r1["fps"],
        "pass": r1["n"] == 181 and r1["hash"] == r2["hash"]
                and r1["errors"] == 0 and not r1["pageerrors"],
    }

    verdicts["P3"] = "field-deferred (which death is most dead — the eye judges, 活人 pass)"

    out = HERE / "verify1-verdicts.json"
    out.write_text(json.dumps({"run1_n": r1["n"], "verdicts": verdicts}, indent=2))
    ok = all(v["pass"] for v in verdicts.values() if isinstance(v, dict))
    for k, v in verdicts.items(): print(k, "→", json.dumps(v) if isinstance(v,dict) else v)
    print("ALL PASS" if ok else "SOMETHING DIED (read the body)")
    sys.exit(0 if ok else 1)

asyncio.run(main())
