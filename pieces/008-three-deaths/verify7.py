# 008 verification #7 — the source of the residue (pass 7).
# House bloodline: P24 written in index.html header BEFORE this file ran.
#
# Pass 6 left F_NOSOC at a weak, cycle-variable residue (0.048 c1 / 0.150 c2
# across worlds): the force channel quiets 3-9x at the cut but not to zero.
# Two suspects for what still correlates two UNBONDED tails: chain-drag
# common-mode (both heads chase the same clock, reaching the tails down the
# chains) vs containment-orbit (identical enclosures at a similar rate).
# Falsifier (probe door #3, ?freeze=1): pin worm B's head at home and stop
# its chase. If the residue is the shared clock, freezing one head kills
# half+ of it; if it is a shared cage, the residue survives.

import asyncio, json, pathlib, statistics
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
SEEDS = list(range(1, 13))
BASE_SEED = 7
N_EXPECTED = 1921
EARS = ("I", "C", "J", "S", "F")

STEADY = {
    "FULL":  (20, 44),   "NI":  (155, 179), "NOSOC": (200, 224),
    "FULL2": (245, 269), "NI2": (380, 404), "NOSOC2": (425, 449),
}

def med(samples, lo, hi, key):
    return statistics.median(s[key] for s in samples if lo <= s["tau"] <= hi)

async def probe(pw, seed, freeze):
    q = f"?probe=1&seed={seed}" + ("&freeze=1" if freeze else "")
    url = (HERE / "index.html").as_uri() + q
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

def steady_medians(rep):
    s = sorted(rep["samples"], key=lambda x: x["tau"])
    return {k: {e: med(s, lo, hi, e) for e in EARS} for k, (lo, hi) in STEADY.items()}

async def main():
    async with async_playwright() as pw:
        free0, free1 = {}, {}
        for s in SEEDS:
            free0[s] = await probe(pw, s, False)
            free1[s] = await probe(pw, s, True)
            print(f"world {s}: free0 hash={free0[s]['hash']} n={free0[s]['n']} | "
                  f"free1 hash={free1[s]['hash']} n={free1[s]['n']}", flush=True)
        rep0b = await probe(pw, BASE_SEED, False)   # determinism repeats
        rep1b = await probe(pw, BASE_SEED, True)

    sm0 = {s: steady_medians(free0[s]) for s in SEEDS}
    sm1 = {s: steady_medians(free1[s]) for s in SEEDS}

    def mow(sm, act, ear):
        return round(statistics.median(sm[s][act][ear] for s in SEEDS), 4)

    verdicts = {}

    # P24a — the freeze is live (worm A chases alone)
    i_full_0 = mow(sm0, "FULL", "I")
    i_full_1 = mow(sm1, "FULL", "I")
    p24a = i_full_1 <= 0.6 * i_full_0
    verdicts["P24a_freeze_is_live"] = {
        "FULL_I_free0": i_full_0, "FULL_I_free1": i_full_1,
        "ratio": round(i_full_1 / i_full_0, 3) if i_full_0 else None,
        "pass": p24a }

    # P24b — residue source discriminator (drop fraction on higher-residue cyc)
    def drop(act):
        f0, f1 = mow(sm0, act, "F"), mow(sm1, act, "F")
        d = round((f0 - f1) / f0, 3) if f0 > 1e-6 else None
        return f0, f1, d
    n1_f0, n1_f1, D1 = drop("NOSOC")
    n2_f0, n2_f1, D2 = drop("NOSOC2")
    # c2 is the higher-residue cycle in pass 6 (0.150 vs 0.048) — primary axis
    primary = "c2" if n2_f0 >= n1_f0 else "c1"
    Dp = D2 if primary == "c2" else D1
    def classify(d):
        if d is None: return "undefined"
        if d >= 0.5: return "chain-drag"
        if d <= 0.2: return "enclosure"
        return "gray"
    verdicts["P24b_residue_source"] = {
        "NOSOC_c1_F": (n1_f0, n1_f1), "drop_c1": D1,
        "NOSOC_c2_F": (n2_f0, n2_f1), "drop_c2": D2,
        "primary_cycle": primary, "primary_drop": Dp,
        "verdict": classify(Dp),
        "verdict_c1": classify(D1), "verdict_c2": classify(D2),
        "pass": classify(Dp) in ("chain-drag", "enclosure") }  # gray = not resolved

    # P24c — bond-coupling control (data, not gate): FULL F barely dented
    ff0, ff1, Df = drop("FULL")
    verdicts["P24c_bond_coupling_control"] = {
        "FULL_F_free0": ff0, "FULL_F_free1": ff1, "drop": Df,
        "note": "bond couples tails directly; freeze should barely dent bonded-act F",
        "pass": True }  # reported, not gated

    # P24d — instrument
    h0 = [free0[s]["hash"] for s in SEEDS]
    h1 = [free1[s]["hash"] for s in SEEDS]
    all_runs = list(free0.values()) + list(free1.values()) + [rep0b, rep1b]
    instrument = (
        rep0b["hash"] == free0[BASE_SEED]["hash"]
        and rep1b["hash"] == free1[BASE_SEED]["hash"]
        and len(set(h1)) == len(h1)
        and all(free0[s]["hash"] != free1[s]["hash"] for s in SEEDS)  # freeze changes physics
        and all(r["n"] == N_EXPECTED for r in all_runs)
        and all(r["errors"] == 0 and not r["pageerrors"] for r in all_runs))
    verdicts["P24d_instrument"] = {
        "unfrozen_repeat_match": rep0b["hash"] == free0[BASE_SEED]["hash"],
        "frozen_repeat_match": rep1b["hash"] == free1[BASE_SEED]["hash"],
        "distinct_frozen_hashes": len(set(h1)),
        "freeze_changes_all": all(free0[s]["hash"] != free1[s]["hash"] for s in SEEDS),
        "n_ok": all(r["n"] == N_EXPECTED for r in all_runs),
        "zero_errors": all(r["errors"] == 0 and not r["pageerrors"] for r in all_runs),
        "pass": instrument }

    gated = ("P24a_freeze_is_live", "P24b_residue_source", "P24d_instrument")
    ok = all(verdicts[k]["pass"] for k in gated)

    out = HERE / "verify7-verdicts.json"
    out.write_text(json.dumps({
        "verdicts": verdicts,
        "steady_seed7_free0": {k: {e: round(v, 4) for e, v in sm0[BASE_SEED][k].items()} for k in STEADY},
        "steady_seed7_free1": {k: {e: round(v, 4) for e, v in sm1[BASE_SEED][k].items()} for k in STEADY},
    }, indent=2))
    for k, v in verdicts.items():
        print(k, "→", json.dumps(v))
    print("ALL PASS" if ok else "SOME FAIL", "— verdicts in", out.name)

asyncio.run(main())
