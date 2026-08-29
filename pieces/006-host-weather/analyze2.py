# 006 analysis #2 — the first workday, verdicts on D1-D4.
# Ephemeral verifier over run2-workday.json (instance 2, born 02:36 quiet
# valley — founding still launch-contaminated at 4.80ms, so ambient reads
# ~0.67-0.72x; regime bands rarely fire upward. Analysis therefore uses
# RAW ratio relative to the day's own median (the honest re-baseline the
# 03:30 beat predicted would be needed), with the founding-anchored regime
# labels reported alongside for the record.
# PREDICTIONS (from day-ambient.py header, written 01:35 before the run):
#   D1 crawl batches (08/14/20 +-20min) are the loudest regular weather —
#      sustained lift >= 3 consecutive epochs.
#   D2 heartbeats visible but small — brief flickers near beat times.
#   D3 quietest hours 03:00-06:00.
#   D4 GC heartbeat persists all day, self-signed by frame-sd co-burst.
import json, datetime, statistics as st

D = json.load(open("run2-workday.json"))
epochs = [e for e in D["epochs"] if e.get("ratio") is not None]
# wall-clock anchor: instance-2 start event in day-ambient.jsonl
start_t = None
for line in open("day-ambient.jsonl"):
    o = json.loads(line)
    if o.get("event") == "start":
        start_t = o["t"]          # last start wins (instance 2)
t0 = start_t - epochs[0]["t"] + 3  # page epoch t is page-relative
TZ = datetime.timezone(datetime.timedelta(hours=8))
def wall(e): return datetime.datetime.fromtimestamp(t0 + e["t"], TZ)

med = st.median(e["ratio"] for e in epochs)
for e in epochs:
    e["rel"] = e["ratio"] / med
    e["hr"] = wall(e).hour + wall(e).minute / 60

print(f"epochs {len(epochs)}  day-median ratio {med:.3f} (founding-anchored)")
print(f"span {wall(epochs[0]):%H:%M} - {wall(epochs[-1]):%H:%M}")

# hourly profile
print("\nhour  n     rel-mean  rel-p95  sd-mean  spikes(rel>1.5)")
by_hr = {}
for e in epochs: by_hr.setdefault(int(e["hr"]), []).append(e)
for h in sorted(by_hr):
    es = by_hr[h]
    rels = [e["rel"] for e in es]
    print(f"{h:02d}    {len(es):4d}  {st.mean(rels):7.3f}  "
          f"{sorted(rels)[int(len(rels)*0.95)]:7.3f}  "
          f"{st.mean(e['sd'] for e in es):6.2f}  "
          f"{sum(1 for r in rels if r > 1.5):3d}")

def window(h0, m0, mins):
    lo = h0 + m0/60; hi = lo + mins/60
    return [e for e in epochs if lo <= e["hr"] < hi]

# D1 crawl batches: sustained lift = >=3 consecutive epochs rel>1.15
def sustained(es, thr=1.15, k=3):
    run = best = 0
    for e in es:
        run = run + 1 if e["rel"] > thr else 0
        best = max(best, run)
    return best
print("\nD1 crawl windows (07:40-08:40 / 13:40-14:40 / 19:40-20:40):")
d1 = []
for h in (7, 13, 19):
    es = window(h, 40, 60)
    s = sustained(es)
    m = st.mean(e["rel"] for e in es) if es else 0
    d1.append(s >= 3)
    print(f"  {h+1:02d}:00 batch  n={len(es)}  rel-mean {m:.3f}  longest-run(>1.15) {s}")
print("  D1 ->", "PASS" if all(d1) else f"PARTIAL/FAIL {d1}")

# D2 heartbeat flickers: compare rel in :28-:38 windows vs :45-:55 (control)
beat_es, ctrl_es = [], []
for e in epochs:
    mn = (e["hr"] % 1) * 60
    if 28 <= mn < 38: beat_es.append(e["rel"])
    elif 45 <= mn < 55: ctrl_es.append(e["rel"])
print(f"\nD2 beat-window rel-mean {st.mean(beat_es):.3f} vs control {st.mean(ctrl_es):.3f}"
      f"  (n {len(beat_es)}/{len(ctrl_es)})")
print("  D2 ->", "PASS (visible)" if st.mean(beat_es) > st.mean(ctrl_es) * 1.02 else "FAIL/invisible")

# D3 quietest hours
hr_means = {h: st.mean(e["rel"] for e in by_hr[h]) for h in by_hr}
quiet3 = sorted(hr_means, key=hr_means.get)[:3]
print(f"\nD3 quietest 3 hours by rel-mean: {sorted(quiet3)}  -> "
      + ("PASS" if all(3 <= h < 6 for h in quiet3) else "check"))

# D4 GC heartbeat: spikes rel>1.5 — frame-sd co-burst? spread across the day?
spikes = [e for e in epochs if e["rel"] > 1.5]
if spikes:
    sd_all = st.mean(e["sd"] for e in epochs)
    sd_spk = st.mean(e["sd"] for e in spikes)
    hrs = sorted({int(e["hr"]) for e in spikes})
    print(f"\nD4 spikes(rel>1.5): {len(spikes)}  sd@spike {sd_spk:.2f} vs day {sd_all:.2f}"
          f"  hours-touched {len(hrs)}/{len(by_hr)}")
    print("  D4 ->", "PASS" if sd_spk > sd_all * 1.3 and len(hrs) >= len(by_hr)//2 else "check")
else:
    print("\nD4 no spikes above 1.5 — FAIL (GC invisible at this M?)")

# regime record (founding-anchored, for honesty)
from collections import Counter
print("\nfounding-anchored regimes:", dict(Counter(e["regime"] for e in epochs)))
