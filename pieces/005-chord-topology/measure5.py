# 005 measurement #5 — the invasion made visible. Ephemeral verifier.
# Question: measure4's sim found the piece's slowest story — ridge regime =
# voice A holding ~80% of the field, the capital relocated deep into B's
# homeland — but that variable lived only in the verifier. The invasion
# pass adds a per-node slow ledger (terr: EMA of claims, ~10 strikes to
# convert, tau=90s relaxation) rendered as a confidence-weighted wash whose
# cancellation IS the frontier, plus a HUD census bar. This file checks the
# display tells the truth.
#
# PREDICTIONS (written before running — 2026-08-06 02:0x):
#   P14 baseline slip (γ=1.00 Δ=0.10, 55s): the fast voice's advantage is
#       real but bounded — A share of confident nodes in [0.45, 0.68];
#       frontier (first sign change of column-mean terr, scanning A→B)
#       within R_LOC=2.4 of the sink (x=12.1). The homelands split at the
#       mouth, where 003/005 have always put the seam.
#   P15 ridge locked (γ=1.15 Δ=0, 55s): THE invasion renders — A share
#       >= 0.65 (sim said 80/20; the real run may be softer), frontier
#       x >= 14 (past the sink, into B's half). B's surviving confident
#       core huddles near home: meanX of B-confident nodes within 5 of
#       srcB.x. RISK: ridge traffic is thin (2 channels); if too few nodes
#       ever get struck, confident sets may be tiny — report sizes.
#   P16 mesh locked (γ=0.60 Δ=0, 55s): balance + churn — A share in
#       [0.35, 0.65] AND the contested fraction (|terr| < 0.30 among
#       touched |terr| > 0.02) >= 1.5x the ridge run's: interpenetration
#       keeps flipping claims, the EMA never settles, the dark band is
#       WIDE. Mesh doesn't split the field, it dissolves the border.
#   P17 harmlessness: terr is display-only — zero JS errors in all runs,
#       fps >= 100, and meetings within the known band for each regime
#       (baseline ~15-45, mesh ~50-100, ridge ~3-15 per 55s).
import asyncio, json
from playwright.async_api import async_playwright

BASE = "file:///Users/jie/Dev/substrate/pieces/005-chord-topology/index.html"
RUNS = [  # (label, gamma, detune, seconds)
    ("baseline", 1.00, 0.10, 55),
    ("ridge",    1.15, 0.00, 55),
    ("mesh",     0.60, 0.00, 55),
]

async def run_one(pw, label, g, det, secs):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(f"{BASE}?g={g:.2f}")
    await page.wait_for_function("window.STATS !== undefined")
    await page.evaluate(f"window.setDet({det})")
    await page.wait_for_timeout(2000)
    await page.evaluate("window.STATS.reset()")
    await page.wait_for_timeout(secs * 1000)
    out = await page.evaluate("""() => {
      const S = window.STATS, st = window.state(), G = window.G;
      const nodes = G.nodes.map(n => ({ x: +n.x.toFixed(2), terr: +n.terr.toFixed(3) }));
      return { meetings: S.meetings, conducts: S.conducts, formed: S.organsFormed,
               biomass: st.biomass, terr: st.terr, nodes,
               srcAx: G.nodes[G.srcA].x, srcBx: G.nodes[G.srcB].x,
               sinkX: G.nodes[G.sink].x,
               bar: document.getElementById('terr-bar').title };
    }""")
    fps = await page.evaluate("parseFloat(document.getElementById('fps').textContent) || -1")
    await page.screenshot(path=f"terr-{label}.png")
    await browser.close()
    out["errors"] = errors; out["fps"] = fps; out["label"] = label
    return out

def frontier_x(nodes):
    """First sign change of column-mean terr, scanning low->high x (A->B)."""
    cols = {}
    for n in nodes:
        if abs(n["terr"]) > 0.15:
            cols.setdefault(round(n["x"]), []).append(n["terr"])
    if not cols: return None
    xs = sorted(cols)
    means = [(x, sum(cols[x]) / len(cols[x])) for x in xs]
    prev = None
    for x, m in means:
        if prev is not None and prev[1] < 0 <= m:
            return (prev[0] + x) / 2
        prev = (x, m)
    # no crossing: field is one homeland — report the far edge of the wash
    return xs[-1] if means[-1][1] < 0 else xs[0]

def contested_frac(nodes):
    touched = [n for n in nodes if abs(n["terr"]) > 0.02]
    if not touched: return None
    return sum(1 for n in touched if abs(n["terr"]) < 0.30) / len(touched)

async def main():
    async with async_playwright() as pw:
        results = [await run_one(pw, *r) for r in RUNS]
    out = {}
    for r in results:
        lbl = r["label"]
        fx = frontier_x(r["nodes"])
        cf = contested_frac(r["nodes"])
        bconf = [n for n in r["nodes"] if n["terr"] > 0.15]
        bMeanX = sum(n["x"] for n in bconf) / len(bconf) if bconf else None
        out[lbl] = { "shareA": r["terr"]["shareA"], "A": r["terr"]["A"], "B": r["terr"]["B"],
                     "frontierX": fx, "contested": None if cf is None else round(cf, 3),
                     "bMeanX": None if bMeanX is None else round(bMeanX, 2),
                     "srcBx": r["srcBx"], "sinkX": r["sinkX"],
                     "meetings": r["meetings"], "conducts": r["conducts"],
                     "biomass": r["biomass"], "fps": r["fps"], "errors": r["errors"],
                     "bar": r["bar"] }
        print(lbl, json.dumps(out[lbl], ensure_ascii=False))

    b, ri, m = out["baseline"], out["ridge"], out["mesh"]
    verdicts = {
        "P14_share":    b["shareA"] is not None and 0.45 <= b["shareA"] <= 0.68,
        "P14_frontier": b["frontierX"] is not None and abs(b["frontierX"] - b["sinkX"]) <= 2.4,
        "P15_share":    ri["shareA"] is not None and ri["shareA"] >= 0.65,
        "P15_frontier": ri["frontierX"] is not None and ri["frontierX"] >= 14,
        "P15_bcore":    ri["bMeanX"] is None or abs(ri["bMeanX"] - ri["srcBx"]) <= 5,
        "P16_share":    m["shareA"] is not None and 0.35 <= m["shareA"] <= 0.65,
        "P16_churn":    m["contested"] is not None and ri["contested"] is not None
                        and m["contested"] >= 1.5 * ri["contested"],
        "P17_clean":    all(not r["errors"] and r["fps"] >= 100 for r in [b, ri, m]),
        "P17_meet":     15 <= b["meetings"] <= 45 and 50 <= m["meetings"] <= 100
                        and 3 <= ri["meetings"] <= 15,
    }
    for k, v in verdicts.items(): print(k, "PASS" if v else "FAIL")
    with open("run5-territory.json", "w") as f:
        json.dump(out, f, indent=1)

asyncio.run(main())
