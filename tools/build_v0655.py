#!/usr/bin/env python3
"""0.6.54 -> 0.6.55 (user 2026-11-21 "후반에 팍 몰려오니 못 막는다", chose "1번꺼 2배 상단 50으로").

Extra enemy production bases (0.6.40/0.6.44, maps 2-6, Hard and up): their late growth cap 2.5 -> 2.0 and the
cap on units alive from them at once 60 -> 50 (trial values). A batch is clamped to the room left under the cap (Codex review). Original attack waves and the wave time ramp unchanged.

Usage: python3 tools/build_v0655.py <0.6.54 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.54', b'version=0.6.55'
MAPS = ['TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
EDITS = [(b'const fixed gv_rmVHBaseCap = 2.5;', b'const fixed gv_rmVHBaseCap = 2.0; // 0.6.55 (was 2.5)'),
         (b'const int gv_rmVHBaseArmyCap = 60;', b'const int gv_rmVHBaseArmyCap = 50; // 0.6.55 (was 60)'),
         # Codex review: the alive check ran before a whole batch, so 49 + 6 could reach 55. Clamp to what is left.
         (b'    if (c <= 0 || pt == null || UnitGroupCount(gv_rmVHBaseArmy, c_unitCountAlive) >= gv_rmVHBaseArmyCap) { return; }',
          b'    if (c > gv_rmVHBaseArmyCap - UnitGroupCount(gv_rmVHBaseArmy, c_unitCountAlive)) { c = gv_rmVHBaseArmyCap - UnitGroupCount(gv_rmVHBaseArmy, c_unitCountAlive); } '
          b'    if (c <= 0 || pt == null) { return; }')]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            k = m + '.SC2Map/mapscript.galaxy'; s = files[k]
            for a, b in EDITS:
                assert s.count(a) == 1, (m, a)
                s = s.replace(a, b)
            files[k] = s; changed.add(k)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
