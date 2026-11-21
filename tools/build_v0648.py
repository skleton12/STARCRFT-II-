#!/usr/bin/env python3
"""0.6.47 -> 0.6.48: Codex review fix for 0.6.47 add-on replacement (missions 1·2).

Plain Tech Labs/Reactors are replaced only in the first 30 s of the mission (the "originally attached" ones the user asked
about), so later passes never tear down an add-on mid-production, and a Tech Lab fallback is never removed and rebuilt in
a loop. Buildings without an add-on still get a Tech Reactor at any time.

Usage: python3 tools/build_v0648.py <0.6.47 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.47', b'version=0.6.48'
MAPS = ('TRaynor01', 'TRaynor02')
A = '                if ((k == "Barracks" || k == "Factory" || k == "Starport") && c != null\n'
B = ('                // 0.6.48: only at mission start (Codex review: no tear-down mid-production, no rebuild loop).\n'
     '                if ((k == "Barracks" || k == "Factory" || k == "Starport") && c != null && GameGetMissionTime() < 30.0\n')


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
            assert t.count(A) == 1, m
            files[p] = t.replace(A, B).replace('\n', nl).encode('utf-8')
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
