#!/usr/bin/env python3
"""006 pass 3 — the persistence ear (embrace-the-silence branch).

Question: pass 2 proved the workday's amplitude lives BELOW the timer quantum
(every hour rel-p95 = 1.031 = one 0.1ms tick on a 3.2ms task). But D1's autopsy
showed crawl windows carried 5-6 CONSECUTIVE epochs above threshold while window
means stayed ~1.005. Hypothesis: at this sensor, weather is not amplitude — it
is PERSISTENCE. A sub-quantum signal cannot lift the median, but it CAN bias
which side of the quantum boundary consecutive epochs land on (the timer's
quantization + scheduler jitter act as natural dither).

PREDICTIONS — written 2026-08-30 00:35, BEFORE running (charter discipline):

P1 (whispers beat chance): under an iid Bernoulli null with the observed
   p(up), expected max run ~ log(N)/log(1/p). The observed max up-run in the
   steady-state workday will exceed the null's 99th percentile (Monte Carlo,
   10k trials). If it doesn't, the persistence ear is stillborn and the
   silence really is total.

P2 (whispers have a schedule): the top-10 longest up-runs will cluster in
   known host-event windows (crawl batches 08/14/20h ±30min, nightly
   automation 22:00-23:00) rather than uniformly. Bar: >=5 of top-10 inside
   event windows, where event windows cover <20% of the steady-state day.

P3 (persistence separates what amplitude cannot): an hourly persistence
   statistic (longest run per hour, or runs>=4 per hour) will vary across
   hours by >=3x even though hourly rel-p95 is constant at 1.031. The day
   becomes legible through run structure alone.

Baseline discipline (instance-1/2 lesson, now implemented): founding is
IDENTITY (birth certificate), not the ruler. All analysis here uses the
steady-state day median as baseline — the piece itself will grow the same
split (slow local baseline for judging, founding for identity) if P1-P2 pass.
"""
import json, math, random, datetime

TZ = datetime.timezone(datetime.timedelta(hours=8))
d = json.load(open('run2-workday.json'))
eps = d['epochs']
t0 = 1787938259.335354  # listener start (day-ambient.jsonl line 1)

# --- steady state: drop birth hour (GC youth, epoch warmup — pass 2 D4) ---
ss = [e for e in eps if e['t'] > 3600 and e['bench'] is not None]
N = len(ss)
benches = sorted(e['bench'] for e in ss)
med = benches[N // 2]
p_up = sum(1 for e in ss if e['bench'] > med) / N
print(f"steady-state epochs: {N}, median bench: {med:.4f} ms, p(up)={p_up:.4f}")

# --- run extraction ---
def runs_of_ups(seq):
    out, cur, start = [], 0, None
    for idx, up in enumerate(seq):
        if up:
            if cur == 0: start = idx
            cur += 1
        else:
            if cur: out.append((start, cur))
            cur = 0
    if cur: out.append((start, cur))
    return out

ups = [e['bench'] > med for e in ss]
runs = runs_of_ups(ups)
runs_sorted = sorted(runs, key=lambda r: -r[1])
max_run = runs_sorted[0][1]
print(f"runs: {len(runs)}, max up-run: {max_run}")

# --- P1: Monte Carlo null ---
rng = random.Random(6)  # piece number as seed — no wall-clock entropy
TRIALS = 10000
null_max = []
for _ in range(TRIALS):
    m = c = 0
    for _ in range(N):
        if rng.random() < p_up:
            c += 1
            if c > m: m = c
        else:
            c = 0
    null_max.append(m)
null_max.sort()
p99 = null_max[int(TRIALS * 0.99)]
exceed = sum(1 for m in null_max if m >= max_run) / TRIALS
exp_max = math.log(N) / math.log(1 / p_up) if p_up > 0 else 0
print(f"P1: null expected max ~{exp_max:.1f}, null p99={p99}, observed={max_run}, "
      f"P(null>=obs)={exceed:.4f} -> {'PASS' if max_run > p99 else 'DIE'}")

# --- P2: where do the long runs live? ---
def hour_of(e):
    return datetime.datetime.fromtimestamp(t0 + e['t'], TZ).hour + \
           datetime.datetime.fromtimestamp(t0 + e['t'], TZ).minute / 60

def in_event_window(h):
    for c in (8.0, 14.0, 20.0):           # crawl batches ±30min
        if abs(h - c) <= 0.5: return True
    if 22.0 <= h <= 23.0: return True      # nightly automation
    return False

print("\nP2: top-10 longest up-runs:")
hits = 0
for start, length in runs_sorted[:10]:
    e = ss[start]
    dt = datetime.datetime.fromtimestamp(t0 + e['t'], TZ)
    hit = in_event_window(hour_of(e))
    hits += hit
    mean_ratio = sum(ss[start+k]['bench'] for k in range(length)) / length / med
    print(f"  len={length:3d}  {dt.strftime('%H:%M:%S')}  mean_rel={mean_ratio:.3f}  "
          f"{'EVENT' if hit else 'quiet'}")
# coverage of event windows in steady-state day
cov = sum(1 for e in ss if in_event_window(hour_of(e))) / N
print(f"P2: {hits}/10 in event windows (coverage={cov:.1%}) -> "
      f"{'PASS' if hits >= 5 else 'DIE'}")

# --- P3: hourly persistence vs the flat amplitude table ---
print("\nP3: hourly persistence (max run / runs>=4) vs flat rel-p95:")
by_hour = {}
for start, length in runs:
    h = int(hour_of(ss[start]))
    m, c = by_hour.get(h, (0, 0))
    by_hour[h] = (max(m, length), c + (length >= 4))
vals = [v[0] for v in by_hour.values()]
for h in sorted(by_hour):
    m, c = by_hour[h]
    bar = '#' * m
    print(f"  {h:02d}h  maxrun={m:3d}  runs>=4: {c:3d}  {bar}")
spread = max(vals) / max(1, min(vals))
print(f"P3: hourly max-run spread = {spread:.1f}x -> {'PASS' if spread >= 3 else 'DIE'}")
