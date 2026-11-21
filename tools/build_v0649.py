#!/usr/bin/env python3
"""0.6.48 -> 0.6.49: mission 2 Hellion upgrades (user 2026-11-21 "화염차 왜 공방 2/2냐").

On Very Hard the original mission gives the Dominion vehicle weapons/armor 1 at start, and the mod's Very Hard +1
(0.6.13, still on the vehicle lines) pushed it to 2/2 at 10 s. 0.6.15 had already removed the mod-given levels from
mission 2 for infantry ("적 공방업 1단계 너프"); the vehicle lines were missed. They are removed now, so mission 2
vehicles keep only the original mission's levels (Very Hard 1/1 at start, original 2/2 later at its timer).

Usage: python3 tools/build_v0649.py <0.6.48 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.48', b'version=0.6.49'
P = 'TRaynor02.SC2Map/mapscript.galaxy'
A = '    gf_rmVHAdd(p,"TerranVehicleWeaponsLevel");\n    gf_rmVHAdd(p,"TerranVehicleArmorsLevel");\n}\n'
B = '    // 0.6.49: no mod Very Hard +1 on vehicles in mission 2 (0.6.15 rule; user 2026-11-21 "화염차 왜 공방 2/2").\n}\n'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        raw = files[P].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
        t = raw.replace('\r\n', '\n')
        assert t.count(A) == 1
        files[P] = t.replace(A, B).replace('\n', nl).encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in ('metadata.txt', P): assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
