# 005 pass 23 companion — positional-identity checks (P74/P75).
# Reads run files only; no browser. Predictions in measure22.py /
# index.html header (written before the runs).
import json

def frets(fn):
    return json.load(open(fn))["final"]["score"]["frets"]

r80_36 = frets("run22-canon-g0.80.json")
r80_18 = frets("run19-tortoise.json")
r90_36 = frets("run21-threefifths.json")
r100_18 = frets("run22-canon-g1.00.json")
r100_06 = frets("run17-interregnum.json")

def match(a, b, tol=0.5):
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
def dark(fr): return [f for f in fr if not f["played"]]

print("=== counts ===")
for tag, fr in [("0.80@3600", r80_36), ("0.80@1800 run19", r80_18),
                ("0.90@3600 run21", r90_36), ("1.00@1800", r100_18),
                ("1.00@600 run17", r100_06)]:
    print(f"{tag}: frets {len(fr)} lit {len(lit(fr))} ({len(lit(fr))/len(fr):.1%}) dark {len(dark(fr))}")

print("\n=== P75 re-mint positional identity (same law, tol 0.01) ===")
for tag, a, b in [("0.80: run22 vs run19", r80_36, r80_18),
                  ("1.00: run22 vs run17", r100_18, r100_06)]:
    pairs = match(a, b, tol=0.01)
    print(f"{tag}: {len(pairs)}/{len(a)} exact-position matches")

print("\n=== P74 cross-law lit/dark agreement (0.80@3600 vs 0.90@3600, tol 0.5) ===")
pairs = match(r80_36, r90_36)
agree = sum(1 for fa, fb in pairs if fa["played"] == fb["played"])
dd = sum(1 for fa, fb in pairs if not fa["played"] and not fb["played"])
print(f"shared {len(pairs)}  agree {agree/len(pairs):.0%}  (dark-dark {dd})")

print("\n=== P74 same-law ratchet: run19 lit set lit again in run22 (fresh dice) ===")
pairs = match(lit(r80_18), r80_36, tol=0.01)
relit = sum(1 for fa, fb in pairs if fb["played"])
print(f"0.80: {relit}/{len(lit(r80_18))} of run19's lit frets lit in run22 ({relit/len(lit(r80_18)):.0%})")
pairs = match(lit(r100_06), r100_18, tol=0.01)
relit = sum(1 for fa, fb in pairs if fb["played"])
print(f"1.00: {relit}/{len(lit(r100_06))} of run17's lit frets lit in run22 ({relit/len(lit(r100_06)):.0%})")

print("\n=== P70-family dark nesting across window doubling (fresh dice) ===")
pairs = match(dark(r80_36), r80_18, tol=0.01)
dd = sum(1 for fa, fb in pairs if not fb["played"])
print(f"0.80: {dd}/{len(dark(r80_36))} of run22@3600 dark also dark in run19@1800 ({dd/len(dark(r80_36)):.0%})")
pairs = match(dark(r100_18), r100_06, tol=0.01)
dd = sum(1 for fa, fb in pairs if not fb["played"])
print(f"1.00: {dd}/{len(dark(r100_18))} of run22@1800 dark also dark in run17@600 ({dd/len(dark(r100_18)):.0%})")

print("\n=== residual dark anatomy (mean |phi|, mean x) ===")
for tag, fr in [("0.80@3600", r80_36), ("0.90@3600", r90_36), ("1.00@1800", r100_18)]:
    d = dark(fr)
    mp = sum(abs(f["phi"]) for f in d)/len(d)
    mx = sum(f["x"] for f in d)/len(d)
    l = lit(fr)
    lp = sum(abs(f["phi"]) for f in l)/len(l)
    print(f"{tag}: dark mean|phi| {mp:.2f} (lit {lp:.2f})  dark mean-x {mx:.2f}")
