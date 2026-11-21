#!/usr/bin/env python3
"""0.6.41 -> 0.6.42: Legionnaire numbers by supply (user 2026-11-21 "파수병 인구수에 맞게 나오게 해줘, 너무 많이 나와서 걍 싹다 죽인당").

0.6.36 turned the Sentinel (ZealotPurifier, supply 2) into the much stronger Fenix Legionnaire (supply 3) but kept the
Sentinel counts. Legionnaire counts now keep the old Sentinel supply (count x 2/3), trial values:
- Missions 3·5·6 support groups: paid Legionnaires 3 -> 2, free Legionnaires 3 -> 2 (tier bonus unchanged).
- Mission 2 Purifier arrivals: 4+4 -> 3+3 Legionnaires, and the 20-unit army cap becomes a 40-supply cap
  (= 20 Sentinels' supply), so Legionnaires fill it at their real supply.
- Mission 1 start: 4 -> 3 Legionnaires.
Mission 4 warps by supply/cost already.

Usage: python3 tools/build_v0642.py <0.6.41 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.41', b'version=0.6.42'
Z = 'gf_{m}_SupAdd(p,"ZealotPurifier");\n'


def grp(m):
    zp = '        ' + Z.format(m=m)
    return [
        # paid part: 2 + 1 -> 1 + 1 (drop the 0.6.2 extra)
        (zp + zp + f'        gf_{m}_SupAdd(p,"AdeptFenix");\n        // 0.6.2: +2 per group (user 2026-10-28 "동맹 좀더 2~3명 추가").\n' + zp,
         zp + f'        gf_{m}_SupAdd(p,"AdeptFenix");\n        // 0.6.2: +2 per group (user 2026-10-28 "동맹 좀더 2~3명 추가").\n'
         + '        // 0.6.42: Legionnaire is supply 3 (was the supply-2 Sentinel) - one fewer.\n' + zp),
        # free part: 2 + 1 -> 1 + 1
        ('        // 0.6.28: +3 free per group (user 2026-11-14, trial).\n' + zp + zp,
         '        // 0.6.28: +3 free per group (user 2026-11-14, trial). 0.6.42: one Legionnaire fewer (supply 3).\n' + zp),
    ]


EDITS = {
    'TTosh01': grp('m5'),
    'THanson01': grp('m6'),
    'TRaynor03': [
        ('        for (k=0;k<3;k+=1) { gf_m3c_SupAdd(p,"ZealotPurifier"); }\n',
         '        // 0.6.42: Legionnaire is supply 3 (was the supply-2 Sentinel): 3 -> 2.\n        for (k=0;k<2;k+=1) { gf_m3c_SupAdd(p,"ZealotPurifier"); }\n'),
        ('        // 0.6.28: +3 free per group (user 2026-11-14, trial).\n        gf_m3c_SupAdd(p,"ZealotPurifier");\n        gf_m3c_SupAdd(p,"ZealotPurifier");\n',
         '        // 0.6.28: +3 free per group (user 2026-11-14, trial). 0.6.42: one Legionnaire fewer (supply 3).\n        gf_m3c_SupAdd(p,"ZealotPurifier");\n'),
    ],
    'TRaynor02': [
        ('        else if (i<2) { wanted=4; }\n', '        else if (i<2) { wanted=3; } // 0.6.42: Legionnaire supply 3 (was 4 Sentinels)\n'),
        ('        available=20-UnitGroupCount(gf_os_Army(8),c_unitCountAlive);\n',
         '        // 0.6.42: cap by supply (40 = 20 old Sentinels), counted in Legionnaire slots.\n        available=FloorI((40.0-gf_os_Supply(8))/3.0);\n'),
        ('UnitIsAlive(gv_os_pylon) && UnitGroupCount(gf_os_Army(8),c_unitCountAlive)<20) {\n                if (i==rounds)',
         'UnitIsAlive(gv_os_pylon) && gf_os_Supply(8)<40.0) {\n                if (i==rounds)'),
        ('!gv_os_warpBusy && UnitGroupCount(gf_os_Army(8),c_unitCountAlive)<20) {', '!gv_os_warpBusy && gf_os_Supply(8)<40.0) {'),
    ],
    'TRaynor01': [
        ('    UnitCreate(4, "ZealotPurifier", 0, gv_rm_PURIFIER,', '    // 0.6.42: 3 Legionnaires (supply 3 each; was 4 Sentinels).\n    UnitCreate(3, "ZealotPurifier", 0, gv_rm_PURIFIER,'),
    ],
}


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m, eds in EDITS.items():
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            for a, b in eds:
                assert t.count(a) == 1, (m, a[:70])
                t = t.replace(a, b)
            files[p] = t.replace('\n', nl).encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                changed = {'metadata.txt'} | {f'{m}.SC2Map/mapscript.galaxy' for m in EDITS}
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
