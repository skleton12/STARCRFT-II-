#!/usr/bin/env python3
"""0.6.51 -> 0.6.52: mission 3 second gas geyser at Raynor's main (user 2026-11-21 "가스 추가해 달랬지").

TRaynor03 objects: a new RichVespeneGeyser (Id 1270, Resources 3465 = same as the existing main geyser Id 406) at
(102.5, 37.5), the spot the relic truck used to stand on (truck moved to (101.5, 43.5) in 0.6.51). Footprint x 101-104,
y 36-39 clears the Command Center, the rich minerals, the Engineering Bay and the bullhorn lights. Nothing else changes.

Usage: python3 tools/build_v0652.py <0.6.51 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.51', b'version=0.6.52'
P = 'TRaynor03.SC2Map/objects'
A = b'    <ObjectUnit Id="406" Position="93.5,26.5,0" Scale="1,1,1" UnitType="RichVespeneGeyser" Resources="3465" />\n'
B = A + b'    <ObjectUnit Id="1270" Position="102.5,37.5,0" Scale="1,1,1" UnitType="RichVespeneGeyser" Resources="3465" />\n'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        assert files[P].count(A) == 1 and b' Id="1270"' not in files[P]
        files[P] = files[P].replace(A, B)
        import xml.etree.ElementTree as E
        E.fromstring(files[P])
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
