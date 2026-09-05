# 007 verification #1 — first light (the triangle instrument).
# Ephemeral verifier, house bloodline: predictions written in index.html
# header BEFORE implementation. This checks P1 (path corners), P2
# (one-number blindness), P4 (determinism + zero errors). P3 is the eye's
# and stays field-deferred to the 活人 pass, honestly.
#
# Protocol: two probe runs (TIME_SCALE=30, 180 piece-seconds ≈ 6 real
# seconds each). Run 1 supplies verdicts + judgment frame (screenshot at
# the wave corner s≈0.5). Run 2 supplies only its FNV hash for P4.

# RUN-1 AMENDMENT (2026-09-06 03:5x, before run 2): P4 died of an
# instrument fault, not of the thesis: probe samples were read off the
# LIVE FRAME at the first rAF tick after each integer tau — rAF jitter
# entered the record, so two runs hashed differently. The mapping itself
# is a pure function of piece time; the probe was not. Repair (index.html):
# probe now re-derives (s,R,A) at exact integer tau via pure functions
# (rebuildCheck bloodline). Predictions unchanged, P4 re-armed.

import asyncio, json, pathlib, sys
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
URL = (HERE / "index.html").as_uri() + "?probe=1"

async def probe(pw, shot=None):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width":1280,"height":720})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    if shot:
        # wave corner s≈0.5 sits at tau≈45 (triangle: s hits 1 at tau=90)
        await page.wait_for_function("window.__report && window.__report().samples.length >= 46", timeout=30000)
        await page.screenshot(path=str(shot))
    await page.wait_for_function("window.__done === true", timeout=60000)
    rep = await page.evaluate("window.__report()")
    await browser.close()
    rep["pageerrors"] = errors
    return rep

async def main():
    async with async_playwright() as pw:
        r1 = await probe(pw, shot=HERE / "firstlight-wave-corner.png")
        r2 = await probe(pw)

    S = {x["tau"]: x for x in r1["samples"]}
    def near(tau): return S[min(S, key=lambda k: abs(k-tau))]

    corner_u = near(1)     # s≈0 (unison)
    corner_w = near(89)    # s≈0.5 (wave, end of edge A)
    corner_c = near(179)   # s≈1... triangle: s returns; s=1 is at tau=90? no:
    # triangle wave: s rises 0→1 over tau 0→90, falls 1→0 over 90→180.
    # So wave corner s=0.5 is at tau=45 and tau=135; crowd corner s=1 at tau=90.
    corner_u = near(1)
    corner_w = near(45)
    corner_c = near(90)

    verdicts = {}
    verdicts["P1_unison"] = {"R": corner_u["R"], "A": corner_u["A"],
                             "pass": corner_u["R"] > 0.95 and corner_u["A"] > 0.95}
    verdicts["P1_wave"]   = {"R": corner_w["R"], "A": corner_w["A"],
                             "pass": corner_w["R"] < 0.15 and corner_w["A"] > 0.95}
    verdicts["P1_crowd"]  = {"R": corner_c["R"], "A": corner_c["A"],
                             "pass": corner_c["R"] < 0.15 and corner_c["A"] < 0.35}
    edgeA = [x for x in r1["samples"] if x["tau"] <= 45]
    minA_on_edgeA = min(x["A"] for x in edgeA)
    r_span = (max(x["R"] for x in edgeA), min(x["R"] for x in edgeA))
    verdicts["P2_blindness"] = {"min_A_edgeA": minA_on_edgeA,
                                "R_span": r_span,
                                "pass": minA_on_edgeA > 0.99 and r_span[0] > 0.95 and r_span[1] < 0.15}
    verdicts["P4_determinism"] = {"hash1": r1["hash"], "hash2": r2["hash"],
                                  "errors": r1["errors"] + len(r1["pageerrors"]),
                                  "fps": r1["fps"],
                                  "pass": r1["hash"] == r2["hash"]
                                          and r1["errors"] == 0 and not r1["pageerrors"]}
    verdicts["P3"] = "field-deferred (the eye is the sensor — 活人 pass)"

    out = HERE / "verify1-verdicts.json"
    out.write_text(json.dumps({"run1_n": r1["n"], "verdicts": verdicts}, indent=2))
    ok = all(v["pass"] for k, v in verdicts.items() if isinstance(v, dict))
    for k, v in verdicts.items(): print(k, "→", v)
    print("ALL PASS" if ok else "SOMETHING DIED (read the body)")
    sys.exit(0 if ok else 1)

asyncio.run(main())
