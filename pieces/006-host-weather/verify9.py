#!/usr/bin/env python3
"""
006 pass 9 — the closed ear (negative space made lawful). Predictions FIRST:

The gap this pass closes: the ear's gate is the browser's rAF throttle
(hidden tab -> no frames -> no epochs -> honest silence of the STRATA),
but the VOICE leaked through two doors: (a) live bed drone holds its last
chord forever when the tab hides mid-listen (the mouth stays open after
the ear closes); (b) a replay's final scheduled segment holds forever
when the record ends off-stage. Law: "it speaks as it listens" — when
the ear-window goes dark, the voice must go out. Slate (0.010) is a
listener's whisper; the closed ear is NOT slate — it is silence (0).

N1  gesture law unchanged: hide/show cycles with no gesture never create
    an AudioContext; epochs advance; zero errors.
N2  the live leak is closed: wake the voice, let founding land and the
    bed rise (gain > 0.004), simulate hidden -> the bed gain falls
    below 0.004, STATS.audio.earClosed == 1, hud reads 'ear closed'.
    Hidden window must span >= 4.5s (first run died at 2.2s: EPOCH_S=3,
    the window never crossed a commit boundary — the gate was never
    tested) so >= 1 epoch commits while hidden, proving the silencing
    is the instrument's own gate (!document.hidden in commitEpoch)
    holding through a live commit, not the browser's mercy.
N3  the ear re-opens before the mouth: back to visible, hud flips to
    'listening', bed stays quiet until the NEXT committed epoch
    re-voices it — gain climbs back above 0.006 within ~5s.
N4  the record player (REVISED after first run — an instrument-clock
    death in the prediction layer, not the piece: a 9-epoch strip at
    400 epochs/s is a 22ms record; it ends before any hand can hide it.
    Score time = listened time is the piece's own law — the record is
    short because the life lived is short, and there is no honest way
    to fast-forward an ear. The mid-flight persistence clause is a
    browser-clock property; it is DEFERRED TO THE FIELD, logged as
    observational only). Scored clauses: replay fires; when the reading
    ends while hidden the needle lifts into silence (scheduled bedOff:
    gain < 0.006 after end) and the voice does NOT return to the
    present (hud 'ear closed') until visibility + next commit.
N5  instrument integrity: after all cycles rebuildCheck.ok and
    stripCheck.ok hold, STATS.errors == 0, zero page errors; judgment
    frame pass9-closed-ear.png (hud showing 'ear closed' while the
    strata keep growing).
"""
import json, time
from pathlib import Path

HERE = Path(__file__).parent

VIS_INIT = """
window.__vh = false;
Object.defineProperty(document, 'hidden', { get: () => window.__vh, configurable: true });
Object.defineProperty(document, 'visibilityState', { get: () => window.__vh ? 'hidden' : 'visible', configurable: true });
"""

def set_hidden(pg, hidden):
    pg.evaluate(f"window.__vh = {'true' if hidden else 'false'}; document.dispatchEvent(new Event('visibilitychange'))")

def main():
    from playwright.sync_api import sync_playwright
    base = 'file://' + str(HERE / 'index.html')
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch()

        # --- N1: no gesture; hide/show creates no AC ---
        pg = b.new_page(viewport={'width': 1280, 'height': 800})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.add_init_script(VIS_INIT)
        pg.goto(base)
        pg.wait_for_function('STATS.epochs.length >= 2', timeout=120000)
        set_hidden(pg, True); time.sleep(1.0)
        set_hidden(pg, False); time.sleep(0.5)
        n1 = pg.evaluate("""() => ({
            ac: (AC === null ? 'null' : 'exists'),
            epochs: STATS.epochs.length, errors: STATS.errors.length })""")
        out['N1'] = {'ok': n1['ac'] == 'null' and n1['epochs'] >= 2 and n1['errors'] == 0 and not errs, **n1}

        # --- N2: live leak closed ---
        pg.wait_for_function('STATS.founding !== null', timeout=120000)
        pg.mouse.click(640, 400)               # wake (strip too young to replay)
        pg.wait_for_function("AC && AC.state === 'running'", timeout=15000)
        pg.wait_for_function('bedGain.gain.value > 0.004', timeout=30000)
        pre = pg.evaluate('STATS.epochs.length')
        set_hidden(pg, True)
        time.sleep(4.6)                        # must span >= 1 commit (EPOCH_S = 3)
        # judgment frame: ear closed, strata still growing
        pg.screenshot(path=str(HERE / 'pass9-closed-ear.png'))
        n2 = pg.evaluate("""() => ({
            gain: bedGain.gain.value, earClosed: STATS.audio.earClosed,
            hud: document.getElementById('voice').textContent,
            epochs: STATS.epochs.length })""")
        out['N2'] = {'ok': n2['gain'] < 0.004 and n2['earClosed'] == 1
                           and n2['hud'] == 'ear closed' and n2['epochs'] > pre,
                     'epochsDuringHidden': n2['epochs'] - pre, **n2}

        # --- N3: ear re-opens before the mouth ---
        set_hidden(pg, False)
        n3a = pg.evaluate("document.getElementById('voice').textContent")
        pg.wait_for_function('bedGain.gain.value > 0.006', timeout=15000)
        n3 = pg.evaluate("""() => ({ gain: bedGain.gain.value,
            hud: document.getElementById('voice').textContent })""")
        out['N3'] = {'ok': n3a == 'listening' and n3['gain'] > 0.006 and n3['hud'] == 'listening',
                     'hudOnReturn': n3a, **n3}

        # --- N4: the record player + needle lift ---
        pg.wait_for_function('epochIdx >= 9', timeout=120000)
        pg.mouse.click(640, 400)               # second gesture -> replay
        pg.wait_for_function('replay !== null', timeout=5000)
        rep = pg.evaluate("({ replays: STATS.audio.replays, dur: replay.dur })")
        set_hidden(pg, True)
        mid = pg.evaluate("replay !== null")   # observational only — a young strip is a 22ms record (field-deferred)
        pg.wait_for_function('replay === null', timeout=int(rep['dur'] * 1000) + 15000)
        n4 = pg.evaluate("""() => ({
            hud: document.getElementById('voice').textContent,
            replays: STATS.audio.replays })""")
        time.sleep(1.2)                        # let the scheduled needle-lift land
        n4['gainLater'] = pg.evaluate('bedGain.gain.value')
        out['N4'] = {'ok': rep['replays'] == 1 and n4['hud'] == 'ear closed'
                           and n4['gainLater'] < 0.006,
                     'midReplayPersists_observational': mid, **rep, **n4}

        # --- N5: integrity after all cycles ---
        set_hidden(pg, False)
        pg.wait_for_function('bedGain.gain.value > 0.006', timeout=15000)
        n5 = pg.evaluate("""() => ({
            rebuild: STATS.rebuildCheck(), strip: STATS.stripCheck(),
            errors: STATS.errors.length })""")
        out['N5'] = {'ok': n5['rebuild']['ok'] and n5['strip']['ok'] and n5['errors'] == 0 and not errs,
                     'pageErrors': errs, **{'rebuildOk': n5['rebuild']['ok'], 'stripOk': n5['strip']['ok'],
                     'errors': n5['errors']}}

        b.close()
    allok = all(v['ok'] for v in out.values())
    print(json.dumps(out, indent=2, default=str))
    print('ALL PASS' if allok else 'FAILURES PRESENT')
    (HERE / 'pass9-verdicts.json').write_text(json.dumps(out, indent=2, default=str))
    return 0 if allok else 1

if __name__ == '__main__':
    raise SystemExit(main())
