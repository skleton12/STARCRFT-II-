#!/usr/bin/env python3
"""0.6.50 -> 0.6.51: mission 3 relic truck moved north (user 2026-11-21 "유물 들려 있는 트럭 좀 더 위에, 안 겹칠 정도로").

TRaynor03 objects: the FlatbedTruck carrying the artifact (Id 258) at (102.71, 37.62), right by Raynor's Command Center
and rich mineral line, moves north to (101.5, 43.5) — clear of the Engineering Bay (98.5, 40.5), the bullhorn lights
(104.5, 40.5) and the minerals. Nothing else in the map changes.

Usage: python3 tools/build_v0651.py <0.6.50 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.50', b'version=0.6.51'
P = 'TRaynor03.SC2Map/objects'
A = b'<ObjectUnit Id="258" Position="102.7053,37.6245,0"'
B = b'<ObjectUnit Id="258" Position="101.5,43.5,0"'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        assert files[P].count(A) == 1
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
