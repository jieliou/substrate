#!/usr/bin/env python3
"""
006 pass 8 — reading key (legibility prototype). Predictions FIRST:

K1  default load: legend CLOSED (no .cap visible), short title present,
    keyhint present, zero page errors, epochs advance (ear unaffected).
K2  ?key=1: legend OPEN on load — 4 captions + fulltext visible.
K3  the key is not an invitation: clicking [?] toggles the legend but
    does NOT wake the voice (AC stays null, replays 0).
K4  '?' keypress toggles legend; a plain pointerdown elsewhere still
    wakes the voice (the existing gesture law is unchanged).
K5  screenshot with legend open lands as pass8-key.png (record frame).
"""
import json, sys, time
from pathlib import Path

HERE = Path(__file__).parent

def main():
    from playwright.sync_api import sync_playwright
    base = 'file://' + str(HERE / 'index.html')
    out = {}
    with sync_playwright() as p:
        b = p.chromium.launch()

        # --- K1 + K3 + K4 on default load ---
        pg = b.new_page(viewport={'width': 1280, 'height': 800})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(base)
        pg.wait_for_function('STATS.epochs.length >= 2', timeout=120000)
        k1 = pg.evaluate("""() => ({
            capsVisible: [...document.querySelectorAll('.cap')].filter(c => c.checkVisibility()).length,
            keyOn: document.body.classList.contains('key-on'),
            hint: !!document.getElementById('keyhint'),
            fulltextShown: document.getElementById('fulltext').offsetParent !== null,
            epochs: STATS.epochs.length, errors: STATS.errors.length })""")
        out['K1'] = {'ok': (k1['capsVisible'] == 0 and not k1['keyOn'] and k1['hint']
                            and not k1['fulltextShown'] and k1['epochs'] >= 2
                            and k1['errors'] == 0 and not errs), **k1}

        # K3 — click the hint: legend opens, voice stays asleep
        pg.click('#keyhint')
        time.sleep(0.3)
        k3 = pg.evaluate("""() => ({
            keyOn: document.body.classList.contains('key-on'),
            caps: [...document.querySelectorAll('.cap')].filter(c => c.checkVisibility()).length,
            ac: (typeof AC !== 'undefined') ? (AC === null ? 'null' : 'exists') : 'undefined',
            replays: STATS.audio.replays })""")
        out['K3'] = {'ok': (k3['keyOn'] and k3['caps'] == 4 and k3['ac'] == 'null'
                            and k3['replays'] == 0), **k3}

        # K4a — '?' toggles it back closed
        pg.keyboard.press('?')
        time.sleep(0.2)
        k4a = pg.evaluate("() => document.body.classList.contains('key-on')")
        # K4b — plain pointerdown on canvas still wakes the voice
        pg.mouse.click(640, 400)
        time.sleep(0.5)
        k4b = pg.evaluate("""() => ({
            ac: (typeof AC !== 'undefined') ? (AC === null ? 'null' : 'exists') : 'undefined',
            state: STATS.audio.state })""")
        out['K4'] = {'ok': (k4a is False and k4b['ac'] == 'exists'), 'toggledOff': not k4a, **k4b}
        pg.close()

        # --- K2 + K5 on ?key=1 ---
        pg2 = b.new_page(viewport={'width': 1280, 'height': 800})
        errs2 = []
        pg2.on('pageerror', lambda e: errs2.append(str(e)))
        pg2.goto(base + '?key=1')
        pg2.wait_for_function('STATS.epochs.length >= 2', timeout=120000)
        k2 = pg2.evaluate("""() => ({
            keyOn: document.body.classList.contains('key-on'),
            caps: [...document.querySelectorAll('.cap')].filter(c => c.checkVisibility()).length,
            fulltextShown: document.getElementById('fulltext').offsetParent !== null,
            errors: STATS.errors.length })""")
        out['K2'] = {'ok': (k2['keyOn'] and k2['caps'] == 4 and k2['fulltextShown']
                            and k2['errors'] == 0 and not errs2), **k2}
        pg2.screenshot(path=str(HERE / 'pass8-key.png'))
        out['K5'] = {'ok': (HERE / 'pass8-key.png').exists()}
        b.close()

    for k in ('K1', 'K2', 'K3', 'K4', 'K5'):
        print(k, 'PASS' if out[k]['ok'] else 'FAIL', json.dumps({x: y for x, y in out[k].items() if x != 'ok'}))
    ok = all(out[k]['ok'] for k in out)
    (HERE / 'pass8-verdicts.json').write_text(json.dumps(out, indent=2))
    print('ALL PASS' if ok else 'FAILURES PRESENT')
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(main())
