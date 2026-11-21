#!/usr/bin/env python3
"""0.6.57 -> 0.6.58 (user 2026-11-21 "무기명도 변경되지 않음, 무기 공격 아이콘이 이상해짐").

The 0.6.56 script that renamed/re-iconed the War Pig weapon (CatalogFieldValueSet Name/Icon on
KelmorianMinerGaussRifle) did not rename it (the UI shows the weapon's own string) and broke the attack icon.
Removed: the gt_rmB2 trigger and its start lines, and the unused Weapon/Name/RM6_B2LMG string. The weapon keeps its
original name and icon; B-2 shows as the research, upgrade and War Pig passive icon. Damage/cost effects unchanged.
Maps 3-6. Game not run.

Usage: python3 tools/build_v0658.py <0.6.57 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.6.57', b'version=0.6.58'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
FN = re.compile(rb'\r?\n// 0\.6\.56 \(user 2026-11-21\): B-2 High-Cal LMG[^\n]*\r?\ntrigger gt_rmB2;\r?\nbool gt_rmB2_Func .*?\r?\n}\r?\n', re.S)
INIT = re.compile(rb'    gt_rmB2 = TriggerCreate\("gt_rmB2_Func"\);\r?\n    TriggerAddEventTimePeriodic\(gt_rmB2, 1\.0, c_timeGame\);\r?\n')
KEY = rb'Weapon/Name/RM6_B2LMG='


def drop_key(raw):
    lines = raw.split(b'\n')
    out = [l for l in lines if not l.lstrip(b'\xef\xbb\xbf').startswith(KEY)]
    assert len(out) == len(lines) - 1
    return b'\n'.join(out)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            k = f'{m}.SC2Map/mapscript.galaxy'; s = files[k]
            s, a = FN.subn(b'\n', s, count=1); s, b = INIT.subn(b'', s, count=1)
            assert a == 1 and b == 1 and b'gt_rmB2' not in s, (m, a, b)
            files[k] = s; changed.add(k)
            ko = drop_key(files[f'{m}.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt'])
            V35.gate('kokr', ko)
            files[f'{m}.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt'] = ko
            changed.add(f'{m}.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt')
            for loc in V35.OTHER_LOCALES:
                k = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'
                files[k] = V35.other_locale(ko); changed.add(k)
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
