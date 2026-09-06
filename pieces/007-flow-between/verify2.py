# 007 verification #2 — breathing pace (pass 2).
# Ephemeral verifier, house bloodline: P5-P7 written in index.html header
# BEFORE implementation. Checks P5 (dwell in the wave-birth window),
# P6 (period + determinism across two runs), P7 (no teleport steps).
# P3 remains field-deferred (the eye is the sensor).
#
# Protocol: two probe runs (TIME_SCALE=30). Run 1 supplies verdicts +
# judgment frame (screenshot inside the dwell, tau≈10, mid wave-birth).
# Run 2 supplies only its FNV hash for P6.

import asyncio, json, pathlib, sys
from playwright.async_api import async_playwright

HERE = pathlib.Path(__file__).parent
URL = (HERE / "index.html").as_uri() + "?probe=1"
WINDOW = 1 / 12          # s <= 0.0833: edge A first 1/K_MAX — the wave birth

async def probe(pw, shot=None):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width":1280,"height":720})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    if shot:
        await page.wait_for_function("window.__report && window.__report().samples.length >= 11", timeout=30000)
        await page.screenshot(path=str(shot))
    await page.wait_for_function("window.__done === true", timeout=60000)
    rep = await page.evaluate("window.__report()")
    await browser.close()
    rep["pageerrors"] = errors
    return rep

async def main():
    async with async_playwright() as pw:
        r1 = await probe(pw, shot=HERE / "pass2-wave-birth.png")
        r2 = await probe(pw)

    samples = sorted(r1["samples"], key=lambda x: x["tau"])
    outbound = [x for x in samples if x["tau"] < 90]

    verdicts = {}

    # P5 — dwell: integer-tau samples inside the birth window on the outbound half
    in_window = [x for x in outbound if x["s"] <= WINDOW]
    verdicts["P5_dwell"] = {
        "window_samples": len(in_window), "uniform_share": 7.5,
        "ratio": round(len(in_window) / 7.5, 2),
        "pass": len(in_window) >= 19,
    }

    # P6 — period preserved + determinism
    verdicts["P6_period_determinism"] = {
        "n_samples": r1["n"], "hash1": r1["hash"], "hash2": r2["hash"],
        "errors": r1["errors"] + len(r1["pageerrors"]), "fps": r1["fps"],
        # RUN AMENDMENTS (2026-09-07 03:4x, in order):
        # 1st run: verifier assumed 181; record had 180 — I "fixed" the
        #   verifier to 180 (first light also read 180). WRONG move, and
        # 2nd run exposed it: 177 samples + split hashes — a screenshot
        #   stall carried floor(tau) across several integers and the
        #   `sec !== lastSample` gate dropped the ones between. The count
        #   was NEVER deterministic; 180 was frame luck, 181 is the true
        #   complete schedule (secs 0..180 — sec 180 reachable once tau
        #   passes SWEEP). Piece repaired with a catch-up loop: sample the
        #   SCHEDULE, not the frame. Expectation restored to 181.
        "pass": r1["n"] == 181 and r1["hash"] == r2["hash"]
                and r1["errors"] == 0 and not r1["pageerrors"],
    }

    # P7 — no teleport: per-integer-tau steps bounded; real slowdown exists
    steps = [abs(samples[i+1]["s"] - samples[i]["s"]) for i in range(len(samples)-1)]
    # min-step check restricted to outbound interior (exclude the s-peak turn at tau=90)
    interior = [abs(outbound[i+1]["s"] - outbound[i]["s"]) for i in range(len(outbound)-1)]
    verdicts["P7_no_teleport"] = {
        "max_step": round(max(steps), 5), "min_step_outbound": round(min(interior), 5),
        "pass": max(steps) <= 0.04 and min(interior) <= 0.0045,
    }

    verdicts["P3"] = "still field-deferred (活人 pass, batched with 004/006)"

    out = HERE / "verify2-verdicts.json"
    out.write_text(json.dumps({"run1_n": r1["n"], "verdicts": verdicts}, indent=2))
    ok = all(v["pass"] for v in verdicts.values() if isinstance(v, dict))
    for k, v in verdicts.items(): print(k, "→", v)
    print("ALL PASS" if ok else "SOMETHING DIED (read the body)")
    sys.exit(0 if ok else 1)

asyncio.run(main())
