#!/usr/bin/env python3
"""0.6.67 -> 0.6.68 (user 2026-11-22 "재생속도를 올려줘" -> "3/6/9 0.5초 재생속도").

Maps 3-6, Inexhaustible Resources: regen tick every 0.5 s (was 1 s), +3 / +6 / +9 per field per tick by level
(= 6 / 12 / 18 per second, was 2 / 3 / 4). Caps (minerals 10000, gas 50000) and the 100 floor unchanged.
Tooltips updated. Game not run.

Usage: python3 tools/build_v0668.py <0.6.67 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO

OLD, NEW = b'version=0.6.67', b'version=0.6.68'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
SUBS = [('    gv_rmEternalQ[1] = 8; gv_rmEternalQ[2] = 12; gv_rmEternalQ[3] = 16;\n',
         '    // 0.6.68: per tick (0.5 s) +3 / +6 / +9 by level (quarters 12 / 24 / 36).\n'
         '    gv_rmEternalQ[1] = 12; gv_rmEternalQ[2] = 24; gv_rmEternalQ[3] = 36;\n'),
        ('    TriggerAddEventTimePeriodic(gt_rmEternal, 1.0, c_timeGame);\n',
         '    TriggerAddEventTimePeriodic(gt_rmEternal, 0.5, c_timeGame);\n')]
CAP = '(광물 최대 10000, 가스 최대 50000)'
CAP_EN = '(minerals up to 10000, vespene up to 50000)'
STR = {'Button/Tooltip/RM6_EternalRes': f'단계마다 사령부 근처 광물과 레이너 정제소 가스가 고갈되지 않고 다시 찹니다 {CAP}. 지대 하나당 0.5초마다 재생: 1단계 3, 2단계 6, 3단계 9 (최대 3단계). /// Each level: minerals near your Command Centers and vespene in your Refineries no longer run out and regenerate {CAP_EN}. Regeneration per field every 0.5 s: Level 1 3, Level 2 6, Level 3 9 (max 3 levels).'}
for n, r in ((1, 3), (2, 6), (3, 9)):
    STR[f'Behavior/Tooltip/RM6_EternalShow{n}'] = (f'이 근처 광물·가스는 고갈되지 않고 0.5초마다 {r}씩 다시 찹니다 {CAP}. '
                                                f'/// Resources here never run out and regrow {r} every 0.5 s {CAP_EN}.')


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'; t = raw.replace('\r\n', '\n')
            for a, b in SUBS:
                assert t.count(a) == 1, (m, a[:40]); t = t.replace(a, b)
            files[p] = t.replace('\n', nl).encode('utf-8'); changed.add(p)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], STR); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None and z.namelist() == prev.namelist()
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
