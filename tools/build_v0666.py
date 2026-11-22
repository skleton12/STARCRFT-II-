#!/usr/bin/env python3
"""0.6.65 -> 0.6.66 (user 2026-11-22 "대지파괴포 왜 자동공격 않해").

Maps 4-6: the Earthsplitter artillery weapon (ArtilleryMengskBombardment) kept the co-op acquire filters
"-;Ally,Neutral,Enemy" - it never picks targets by itself (in co-op the panel script fires it). Change acquire and
acquire-scan filters to exclude only own/ally/neutral ("-;Player,Ally,Neutral") and scan its full range, so it
auto-attacks enemies in range like a normal defense. Range, period, damage unchanged. Game not run.

Usage: python3 tools/build_v0666.py <0.6.65 zip> <new output zip>
"""
import argparse, copy, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.6.65', b'version=0.6.66'
MAPS = ['TTychus01', 'TTosh01', 'THanson01']
SUBS = [(b'<AcquireFilters value="-;Ally,Neutral,Enemy" />', b'<AcquireFilters value="-;Player,Ally,Neutral" />'),
        (b'<AcquireScanFilters value="-;Ally,Neutral,Enemy" />', b'<AcquireScanFilters value="-;Player,Ally,Neutral" />'),
        (b'<MinScanRange value="0" />', b'<MinScanRange value="20" />')]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            k = f'{m}.SC2Map/base.sc2data/gamedata/weapondata.xml'
            t = files[k]
            s = t.index(b'<CWeaponLegacy id="ArtilleryMengskBombardment">'); e = t.index(b'</CWeaponLegacy>', s)
            seg = t[s:e]
            for a, b in SUBS:
                assert seg.count(a) == 1, (m, a); seg = seg.replace(a, b)
            files[k] = t[:s] + seg + t[e:]; E.fromstring(files[k]); changed.add(k)
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
