# 005 pass 22 companion — archival dark-fret maps (P68).
# Reads the five existing run files; no browser. Predictions in
# measure21.py / index.html header (written before this ran).
import json

RUNS = [
    ("g1.00@600",  "run17-interregnum.json"),
    ("g0.95@1800", "run20-dose-g0.95.json"),
    ("g0.90@1800", "run20-dose-g0.90.json"),
    ("g0.80@1800", "run19-tortoise.json"),
    ("g0.80@600",  "run18-amplitude.json"),
]

def load(fn):
    return json.load(open(fn))["final"]["score"]["frets"]

def stats(frets):
    dark = [f for f in frets if not f["played"]]
    lit  = [f for f in frets if f["played"]]
    mx = lambda a: sum(f["x"] for f in a)/len(a) if a else None
    mp = lambda a: sum(abs(f["phi"]) for f in a)/len(a) if a else None
    return dark, lit, mx(dark), mx(lit), mp(dark), mp(lit)

print("=== spatial stats (dark vs lit) ===")
data = {}
for tag, fn in RUNS:
    fr = load(fn)
    dark, lit, dx, lx, dp, lp = stats(fr)
    data[tag] = fr
    print(f"{tag}: frets {len(fr)} dark {len(dark)} ({len(dark)/len(fr):.0%})  "
          f"mean-x dark {dx:.2f} vs lit {lx:.2f}  mean|phi| dark {dp:.2f} vs lit {lp:.2f}")

print("\n=== dark fraction by |phi| bin (pooled per run) ===")
for tag, _ in RUNS:
    fr = data[tag]
    row = []
    for lo, hi in [(0,1.5),(1.5,3),(3,5),(5,99)]:
        b = [f for f in fr if lo <= abs(f["phi"]) < hi]
        row.append(f"|phi| {lo}-{hi if hi<99 else '+'}: " +
                   (f"{sum(1 for f in b if not f['played'])/len(b):.0%} of {len(b)}" if b else "-"))
    print(tag, " | ".join(row))

print("\n=== dark fraction by x band ===")
for tag, _ in RUNS:
    fr = data[tag]
    row = []
    for lo, hi, name in [(0,4,'deep-west'),(4,5.25,'deep-band'),(5.25,9.5,'mid-west'),(9.5,99,'east')]:
        b = [f for f in fr if lo <= f["x"] < hi]
        row.append(f"{name}: " +
                   (f"{sum(1 for f in b if not f['played'])/len(b):.0%} of {len(b)}" if b else "-"))
    print(tag, " | ".join(row))

def match(a, b, tol=0.5):
    pairs = []
    used = set()
    for fa in a:
        best, bd = None, tol
        for i, fb in enumerate(b):
            if i in used: continue
            d = max(abs(fa["x"]-fb["x"]), abs(fa["y"]-fb["y"]))
            if d < bd: best, bd = i, d
        if best is not None:
            used.add(best); pairs.append((fa, b[best]))
    return pairs

print("\n=== cross-run agreement on spatially shared frets (tol 0.5) ===")
for ta, tb in [("g0.90@1800","g0.95@1800"), ("g0.90@1800","g0.80@1800"),
               ("g0.95@1800","g1.00@600"), ("g0.80@1800","g0.80@600")]:
    pairs = match(data[ta], data[tb])
    agree = sum(1 for fa, fb in pairs if fa["played"] == fb["played"])
    dd = sum(1 for fa, fb in pairs if not fa["played"] and not fb["played"])
    print(f"{ta} vs {tb}: shared {len(pairs)}  agree {agree/len(pairs):.0%}  (dark-dark {dd})")
