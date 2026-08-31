#!/usr/bin/env python3
"""006 run 4 verdicts — the third workday (live memory strip).

Predictions M1-M4 written 2026-08-31 02:3x in day-ambient3.py, BEFORE launch.
This script only judges. Monday host schedule: crawl batches 08/14/20 +
hourly crawlScan + 22:00 nightly automation; NO Sunday organs.
"""
import json, datetime

TZ = datetime.timezone(datetime.timedelta(hours=8))
d = json.load(open('run4-workday-strip.json'))
eps = [e for e in d['epochs'] if e['bench'] is not None]
t0 = None
with open('day-ambient3.jsonl') as f:
    for line in f:
        j = json.loads(line)
        if j.get('event') == 'start':
            t0 = j['t']; break
N = len(eps)
print(f"run 4: {N} epochs, t0={t0}")

# --- M1: the score fills ---
sw = d['stripWritten']
m1 = sw == len(d['epochs'])
print(f"M1: stripWritten={sw} vs epochs={len(d['epochs'])}, "
      f"fill extent={sw/28800:.1%} of the day-score -> {'PASS' if m1 else 'DIE'}")

# --- strong marks + wall-clock hours ---
def hour_min(e):
    dt = datetime.datetime.fromtimestamp(t0 + e['t'], TZ)
    return dt.hour, dt.minute, dt

strong = [e for e in eps if (e.get('pulse') or 0) >= 0.5]
print(f"strong marks: {len(strong)} ({len(strong)/N:.1%} of epochs)")

# steady-state top-of-hours: exclude birth+fill era (~first 40 min: founding
# + MIN_FILL + rolling-median youth ~2h per run-3 youth-deafness — use the
# measured maturation: organ hears from ~2h after launch)
launch_dt = datetime.datetime.fromtimestamp(t0, TZ)
mature_t = 7200  # youth-deafness ~2h (run 3 quantified)
hours_seen = sorted(set(datetime.datetime.fromtimestamp(t0 + e['t'], TZ).hour
                        for e in eps if e['t'] > mature_t))
# top-of-hour catch: strong mark landing 0-3 min after the hour
caught = set()
for e in strong:
    h, m, _ = hour_min(e)
    if m <= 3:
        caught.add(h)
steady = [h for h in hours_seen]
m2_rate = len([h for h in steady if h in caught]) / len(steady) if steady else 0
m2 = m2_rate >= 0.9
print(f"M2: steady-state hours={steady}")
print(f"    caught at top-of-hour={sorted(caught)}")
print(f"    catch rate={m2_rate:.0%} (bar 90%) -> {'PASS' if m2 else 'DIE'}")

# --- M3: Monday physiology — no duration bar > 5 min (100 epochs) ---
clusters = []
for e in strong:
    if clusters and e['i'] - clusters[-1][-1]['i'] <= 40:
        clusters[-1].append(e)
    else:
        clusters.append([e])
extents = [(c[0]['i'], c[-1]['i'] - c[0]['i'] + 1,
            hour_min(c[0])[2].strftime('%H:%M:%S')) for c in clusters]
long_bars = [x for x in extents if x[1] > 100]
m3 = len(long_bars) == 0
print(f"M3: {len(clusters)} clusters; extents (epochs): "
      f"{sorted(set(x[1] for x in extents))}")
for start_i, ext, ts in extents:
    if ext > 60:
        print(f"    long-ish: start i={start_i} at {ts}, {ext} epochs (~{ext*3}s)")
print(f"M3: bars >100 epochs (5min): {len(long_bars)} -> "
      f"{'PASS' if m3 else 'DIE (unscheduled long organ = finding)'}")

# --- M4: instrument ---
sc = d['stripCheck']; rc = d['rebuildCheck']
m4 = (not d['harness_errors'] and not d['pageerrors']
      and sc and sc['ok'] and rc and rc['ok'])
print(f"M4: errors={len(d['harness_errors'])}/{len(d['pageerrors'])}, "
      f"stripCheck={sc}, rebuildCheck ok={rc['ok']} -> {'PASS' if m4 else 'DIE'}")

print("\nverdict:", "ALL PASS" if all([m1, m2, m3, m4]) else "DEATHS ABOVE — autopsy them")
