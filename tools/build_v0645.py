#!/usr/bin/env python3
"""0.6.44 -> 0.6.45: enemy Tech Reactors attached from the start (user 2026-11-21 "아니 짓는 거였음? 원래 부착되어 있는 거여야지").

Missions 1·2, Hard and up. The add-on build time (Tech Reactor Build3, Tech Lab Build1) is set to 1/16 s for the enemy
player only (per-player catalog value), and the add-on pass runs right at mission start instead of after 15 s, so every
enemy Barracks/Factory/Starport has its Tech Reactor at once; buildings that appear later (AI builds, the Hard+ extra
production base at 1:00) get theirs within 15 s. Raynor's add-on times are unchanged.

Usage: python3 tools/build_v0645.py <0.6.44 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.44', b'version=0.6.45'
MAPS = ('TRaynor01', 'TRaynor02')
A = '    TechTreeAbilityAllow(p, AbilityCommand("StarportAddOns", 2), true);\n'
A_NEW = A + '    // 0.6.45: add-ons appear at once for the enemy (per-player build time 1/16 s).\n' + ''.join(
    f'    CatalogFieldValueSet(c_gameCatalogAbil, "{b}AddOns", "InfoArray[{i}].Time", p, "0.0625");\n'
    for b in ('Barracks', 'Factory', 'Starport') for i in ('Build1', 'Build3'))
B = '        TriggerAddEventTimePeriodic(gt_rmAddon, 15.0, c_timeGame);\n'
B_NEW = B + '        TriggerExecute(gt_rmAddon, true, false);\n'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            for a, b in ((A, A_NEW), (B, B_NEW)):
                assert t.count(a) == 1, (m, a[:50]); t = t.replace(a, b)
            files[p] = t.replace('\n', nl).encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                changed = {'metadata.txt'} | {f'{m}.SC2Map/mapscript.galaxy' for m in MAPS}
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
