#!/usr/bin/env python3
"""0.6.56 -> 0.6.57 (user 2026-11-21 "경기관총 아이콘 그 푸르딩딩한 걸로"): B-2 High-Cal LMG icon ->
co-op Mengsk "Equip B-2 High-Cal LMG" icon btn-upgrade-mengsk-trooper-plasmarifle.dds (research button, passive,
upgrade and the weapon icon set by script), maps 3-6. Nothing else changes. Game not run.

Usage: python3 tools/build_v0657.py <0.6.56 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.56', b'version=0.6.57'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
A = b'btn-upgrade-terran-weaponrefit.dds'
B = b'btn-upgrade-mengsk-trooper-plasmarifle.dds'
COUNTS = {'buttondata.xml': 2, 'upgradedata.xml': 1}


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            for fn, n in COUNTS.items():
                k = f'{m}.SC2Map/base.sc2data/gamedata/{fn}'
                assert files[k].count(A) == n, (k, files[k].count(A))
                files[k] = files[k].replace(A, B); changed.add(k)
            k = f'{m}.SC2Map/mapscript.galaxy'
            assert files[k].count(A) == 1, k
            files[k] = files[k].replace(A, B); changed.add(k)
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
