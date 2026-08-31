#!/usr/bin/env python3
"""006 pass 7 — the voice. Verifier for the sound organ.

PREDICTIONS (written before first run, craft rule 8):

S1  SCORE PURITY — scoreOf is a pure function of the strip's memory,
    mirrored here float-for-float (pass-3 equivalence convention).
    Injecting the recorded fourth-workday (run4-workday-strip.json,
    23,678 epochs) through replayStrip and calling scoreOf(0, N) in the
    same atomic evaluate reproduces this mirror EXACTLY: same seg count,
    same note count, and per-note slot / len / f32 strength identity.
    (Design-time scoping saw 486 beads merge to 26 notes and 772 regime
    changes; the falsifiable claim is exact JS<->python equivalence.)
    Falsifier: any count or field mismatch — the voice would be singing
    a different day than the strip remembers.

S2  CROWD-DEAFNESS IS AUDIBLE — run 4's M2 (missed hours = the host's
    loudest hours) must survive into the score. Binning the day into
    score-hours (1200 epochs), the 6 loudest hours (by fraction of
    working+ epochs) carry strictly fewer bell onsets than the 6
    quietest hours. Falsifier: bells distribute evenly — masking would
    be visible in the strip but inaudible in the voice.

S3  DURATION SURVIVES AS SUSTAIN — merged note lengths discriminate:
    max(len) / median(len) >= 5, and at least one note is a held note
    (len/400 s > 0.15 s, the envelope's hold branch). The landlord's
    walk should be the longest note of the day. Falsifier: merging
    collapses durations or no note reaches the hold branch.

S4  THE VOICE DOES NOT SPEAK UNINVITED — after 60+ s of listening with
    no gesture: AC === null, STATS.audio.state 'none', zero bells, zero
    replays. Then ONE trusted click: AudioContext exists and reaches
    'running', replays === 1, and lastScore.notes equals S1's note
    count (the click reads the whole remembered day, head advanced to
    N). Falsifier: audio exists pre-gesture (dishonest), or the click
    fails to wake the voice (headless gesture law — an instrument
    finding to record either way).

S5  INSTRUMENT — with the audio graph live and a full-day replay
    scheduled (26 notes + ~770 bed automations): zero JS errors,
    fps >= 50 (swiftshader baseline 92-96), rebuildCheck.ok and
    stripCheck.ok still true (the new organ broke no old organ).
"""
import json, struct, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).parent
DAY = json.loads((HERE / 'run4-workday-strip.json').read_text())['epochs']
N = len(DAY)
RATE = 400

def f32(x):
    return struct.unpack('f', struct.pack('f', x))[0]

def mirror_score(epochs, n):
    """Float-for-float mirror of scoreOf(0, n) over replayStrip-injected data."""
    segs, notes = [], []
    cur, open_ = None, None
    for s in range(n):
        r = epochs[s]['regime']
        if r != cur:
            segs.append({'slot': s, 't': s / RATE, 'regime': r})
            cur = r
        p = f32(epochs[s].get('pulse') or 0.0)
        if p >= 0.5:
            if open_ is not None:
                open_['len'] += 1
                if p > open_['strength']:
                    open_['strength'] = p
            else:
                open_ = {'slot': s, 't': s / RATE, 'len': 1, 'strength': p}
                notes.append(open_)
        else:
            open_ = None
    return segs, notes

M_SEGS, M_NOTES = mirror_score(DAY, N)

JS = r"""
async () => {
  const day = window.__DAY__;
  const rep = STATS.replayStrip(day);
  const sc = STATS.scoreOf(0, day.length);
  epochIdx = day.length;   // advance the head so the next gesture reads the whole remembered day
  return {
    rep: { ticks: rep.ticks, beads: rep.beads, hash: rep.hash },
    segs: sc.segs, notes: sc.notes,
  };
}
"""

def main():
    from playwright.sync_api import sync_playwright
    url = 'file://' + str(HERE / 'index.html')
    out = {'S1': None, 'S2': None, 'S3': None, 'S4': None, 'S5': None}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1280, 'height': 800})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(url)
        # let the ear live a while un-touched
        pg.wait_for_function('STATS.epochs.length >= 20', timeout=120000)
        pre = pg.evaluate("""() => ({
          ac: (typeof AC !== 'undefined') ? (AC === null ? 'null' : 'exists') : 'undefined',
          audio: STATS.audio, errors: STATS.errors.length })""")
        s4a = pre['ac'] == 'null' and pre['audio']['state'] == 'none' \
              and pre['audio']['bellsLive'] == 0 and pre['audio']['replays'] == 0
        # inject the recorded day + read the score atomically
        pg.evaluate('day => { window.__DAY__ = day; }', DAY)
        r = pg.evaluate(JS)
        segs, notes = r['segs'], r['notes']
        s1 = (len(segs) == len(M_SEGS) and len(notes) == len(M_NOTES)
              and all(a['slot'] == b_['slot'] and a['regime'] == b_['regime'] and a['t'] == b_['t']
                      for a, b_ in zip(segs, M_SEGS))
              and all(a['slot'] == b_['slot'] and a['len'] == b_['len'] and a['t'] == b_['t']
                      and f32(a['strength']) == b_['strength']
                      for a, b_ in zip(notes, M_NOTES)))
        out['S1'] = {'ok': s1, 'segs': (len(segs), len(M_SEGS)), 'notes': (len(notes), len(M_NOTES)),
                     'beads': r['rep']['beads']}
        # S2 — hour bins
        HOUR = 1200
        hours = []
        for h in range((N + HOUR - 1) // HOUR):
            lo, hi = h * HOUR, min(N, (h + 1) * HOUR)
            loud = sum(1 for s in range(lo, hi) if DAY[s]['regime'] >= 2) / (hi - lo)
            onsets = sum(1 for n_ in notes if lo <= n_['slot'] < hi)
            hours.append({'h': h, 'loud': loud, 'onsets': onsets})
        by_loud = sorted(hours, key=lambda x: -x['loud'])
        loud6 = sum(x['onsets'] for x in by_loud[:6])
        quiet6 = sum(x['onsets'] for x in by_loud[-6:])
        out['S2'] = {'ok': loud6 < quiet6, 'loud6': loud6, 'quiet6': quiet6,
                     'loud_hours': [(x['h'], round(x['loud'], 2), x['onsets']) for x in by_loud[:6]],
                     'quiet_hours': [(x['h'], round(x['loud'], 2), x['onsets']) for x in by_loud[-6:]]}
        # S3 — durations
        lens = sorted(n_['len'] for n_ in notes)
        med = lens[len(lens) // 2]
        held = [n_ for n_ in notes if n_['len'] / RATE > 0.15]
        out['S3'] = {'ok': lens[-1] / med >= 5 and len(held) >= 1,
                     'max': lens[-1], 'median': med, 'ratio': round(lens[-1] / med, 1),
                     'held_notes': [(n_['slot'], n_['len']) for n_ in held]}
        # S4 — the gesture
        pg.mouse.click(640, 400)
        time.sleep(1.0)
        post = pg.evaluate("""() => ({
          ac: AC === null ? 'null' : AC.state, audio: STATS.audio })""")
        s4b = post['ac'] == 'running' and post['audio']['replays'] == 1 \
              and post['audio']['lastScore'] and post['audio']['lastScore']['notes'] == len(M_NOTES)
        out['S4'] = {'ok': s4a and s4b, 'pre': pre, 'post': post}
        # playhead frame mid-replay
        time.sleep(4.0)
        pg.screenshot(path=str(HERE / 'pass7-replay.png'), type='jpeg', quality=70)
        # S5 — instrument with graph live
        time.sleep(4.0)
        s5 = pg.evaluate("""() => ({
          errors: STATS.errors, fps: STATS.fps,
          rebuild: STATS.rebuildCheck(), strip: STATS.stripCheck() })""")
        out['S5'] = {'ok': len(s5['errors']) == 0 and len(errs) == 0 and s5['fps'] >= 50
                            and s5['rebuild']['ok'] and s5['strip']['ok'],
                     'fps': round(s5['fps'], 1), 'errors': s5['errors'] + errs,
                     'rebuild': s5['rebuild']['ok'], 'strip': s5['strip']['ok']}
        b.close()
    (HERE / 'pass7-verdicts.json').write_text(json.dumps(out, indent=2))
    for k, v in out.items():
        print(k, 'PASS' if v and v.get('ok') else 'FAIL', json.dumps({kk: vv for kk, vv in v.items() if kk != 'ok'})[:300])
    sys.exit(0 if all(v and v.get('ok') for v in out.values()) else 1)

if __name__ == '__main__':
    main()
