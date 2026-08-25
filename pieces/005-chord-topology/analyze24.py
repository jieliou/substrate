# 005 pass 25 companion — cross-branch canon + instrument checks (P83/P84).
# Reads run files only; no browser. Predictions in measure24.py header.
import json

def frets(fn):
    return json.load(open(fn))["final"]["score"]["frets"]

r24 = frets("run24-hearth.json")        # clean east 1.00@1800 (tonight)
rB  = frets("run22-canon-g1.00.json")   # loaded west 1.00@1800
r17 = frets("run17-interregnum.json")   # east 1.00@600

def match(a, b, tol=0.01):
    pairs, used = [], set()
    for fa in a:
        best, bd = None, tol
        for i, fb in enumerate(b):
            if i in used: continue
            d = max(abs(fa["x"]-fb["x"]), abs(fa["y"]-fb["y"]))
            if d < bd: best, bd = i, d
        if best is not None:
            used.add(best); pairs.append((fa, b[best]))
    return pairs

def lit(fr): return [f for f in fr if f["played"]]

print("=== P84 re-mint positional identity (tol 0.01) ===")
pairs = match(r24, rB)
print("run24 vs run22-B: %d/%d exact-position" % (len(pairs), len(r24)))

print("\n=== P83 cross-branch lit agreement at equal age (1800) ===")
agree = sum(1 for fa, fb in pairs if fa["played"] == fb["played"])
print("shared %d  lit/dark agree %d (%.0f%%)" % (len(pairs), agree, 100.0*agree/len(pairs)))
only24 = [(fa["x"], fa["y"]) for fa, fb in pairs if fa["played"] and not fb["played"]]
onlyB  = [(fa["x"], fa["y"]) for fa, fb in pairs if fb["played"] and not fa["played"]]
print("lit only in run24 (clean):", [("%.2f,%.2f" % p) for p in only24])
print("lit only in run22-B (loaded):", [("%.2f,%.2f" % p) for p in onlyB])

print("\n=== P83 ratchet: run17 lit set relit in run24 ===")
pairs17 = match(lit(r17), r24, tol=0.01)
relit = sum(1 for fa, fb in pairs17 if fb["played"])
print("%d/%d relit (%.0f%%)" % (relit, len(lit(r17)), 100.0*relit/len(lit(r17))))
