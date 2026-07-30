# 004 fifth pass — AT WHOSE TEMPO does the lock stand?
#
# The fourth pass established WHAT lock is here: a standing sawtooth. The
# phases still drift apart between beats; every kick hauls them back. The
# negotiation never stops, it only stops losing ground.
#
# So the next question is not whether they agree but on whose terms. Two
# oscillators with different natural periods (A: 2.4s, B: 2.4*(1+D)) lock
# to ONE common period. Where does it land — at A's tempo, at B's, or
# between? And who paid: which voice absorbed more phase correction?
#
# The coupling here is not symmetric by construction. The ear is the WEB:
# you hear when a rival's front strikes a node YOU own. So the size of
# your territory is the size of your ear. More territory = more hearing =
# more being corrected. If that chain holds, the piece contains a small
# inversion worth saying out loud: the one who listens most is the one
# who moves most, and the bigger voice concedes the tempo.
#
# PREDICTIONS (written 2026-07-31 03:4x, BEFORE running):
#   PG  At lock (gamma=1.6, sign=-1, K=6, D=0.10) the realised periods of
#       A and B are equal to within 1% — this is the definition check; if
#       it fails, "lock" was a drift-rate artifact and everything below is
#       void.
#   PH  The common period lands BETWEEN 2.4 and 2.64 (neither voice simply
#       wins). Nontrivial: it could also sit outside the interval, because
#       the kicks are not a mean-field average but arrivals filtered
#       through terrain.
#   PI  ASYMMETRY: hear counts differ by >20% between voices, and the
#       voice that hears more carries the larger |kick| total — i.e. the
#       ear is unequal, and being heard-at costs you your tempo. Direction
#       NOT predicted (I do not know which of A/B holds more territory at
#       gamma=1.6 with D=0.10); honest uncertainty, per craft rule 8.
#   PJ  The signed kick sums have OPPOSITE signs (one voice is being
#       retarded on average, the other advanced) — that is what holding a
#       fixed phase offset requires. Their magnitudes need not match: the
#       difference is exactly the frequency gap being paid off, per beat.
#   PK  Deaf control (K=0): kick sums = 0, hear counts = 0, realised
#       periods = natural (2.4 / 2.64), fire counts in ratio 1.10.
#
# Runs: deaf control, partial (K=4), lock (K=6), and lock at the OTHER
# detune (D=0.05) to see whether the concession scales with the gap.
import asyncio, json
from playwright.async_api import async_playwright

URL = "file:///Users/jie/Dev/substrate/pieces/004-coupled-metronomes/index.html"
RUNS = [  # (gamma, detune, K, sign, seconds)
    (1.6, 0.10, 0.0, -1, 40),
    (1.6, 0.10, 4.0, -1, 40),
    (1.6, 0.10, 6.0, -1, 40),
    (1.6, 0.05, 6.0, -1, 40),
]

async def run_one(pw, gam, det, k, sign, secs):
    browser = await pw.chromium.launch(args=["--enable-unsafe-swiftshader"])
    page = await browser.new_page(viewport={"width": 1280, "height": 800})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.goto(URL)
    await page.wait_for_function("window.STATS !== undefined")
    await page.evaluate(f"window.setGamma({gam}); window.setDet({det}); window.setK({k}); window.setSign({sign});")
    await page.wait_for_timeout(6000)
    await page.evaluate("window.STATS.reset()")
    await page.wait_for_timeout(secs * 1000)
    out = await page.evaluate("""() => {
      const S = window.STATS;
      const per = (n, t0, t1) => (n > 2 && t1 > t0) ? (t1 - t0) / (n - 1) : null;
      const u = S.psiU, t = S.psiT, n = u.length;
      const rate = n > 4 ? (u[n-1] - u[0]) / (t[n-1] - t[0]) : null;
      // territory census: who owns how many claimed nodes right now
      let ownA = 0, ownB = 0;
      for (const nd of window.G.nodes) { if (nd.owner === 0) ownA++; else if (nd.owner === 1) ownB++; }
      const r = x => x === null ? null : +x.toFixed(4);
      return {
        perA: r(per(S.fireA, S.tA0, S.tA1)), perB: r(per(S.fireB, S.tB0, S.tB1)),
        fireA: S.fireA, fireB: S.fireB,
        hearA: S.hearA, hearB: S.hearB,
        kickSumA: r(S.kickSumA), kickSumB: r(S.kickSumB),
        kickAbsA: r(S.kickAbsA), kickAbsB: r(S.kickAbsB),
        ownA, ownB, meetings: S.meetings, shadows: S.shadows,
        driftRate: r(rate)
      };
    }""")
    await browser.close()
    out.update({"gamma": gam, "det": det, "K": k, "sign": sign, "jsErrors": errors})
    return out

async def main():
    async with async_playwright() as pw:
        for gam, det, k, sign, secs in RUNS:
            print(json.dumps(await run_one(pw, gam, det, k, sign, secs)), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
