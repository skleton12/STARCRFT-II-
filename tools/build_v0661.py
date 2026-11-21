#!/usr/bin/env python3
"""0.6.60 -> 0.6.61 (user 2026-11-21 "사령부 근처 2칸 이내에 소환되게, 건물이 있으면 조금 먼 데로, 광물 반대편으로").

Ally research buildings (Purifier Conclave 4x4, Dehaka's Den 3x3, maps 4-6) are placed right next to Raynor's
Command Center on the side away from the minerals: centre distance starts at 5 (CC half-width 2.5 + gap up to 2 +
building half-width), and steps out 1 at a time (up to 16) only when that spot is taken. Angles stay on the
far side (5-75 degrees off the away-from-minerals line, Conclave one side, Den the other). Placement search
radius 1; every found spot is re-checked to be at least 2 cells toward the away-from-minerals side. Mineral/geyser 5-cell keep-out, retry for 5 minutes - unchanged. Game not run.

Usage: python3 tools/build_v0661.py <0.6.60 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.60', b'version=0.6.61'
MAPS = ['TTychus01', 'TTosh01', 'THanson01']
OLD_FN = re.compile(rb'point gf_rm7Spot \(string kind, point c, fixed ang, fixed side\) \{.*?\r?\n\}\r?\n', re.S)
NEW_FN = b'''point gf_rm7Spot (string kind, point c, fixed ang, fixed side) {
    // 0.6.61: right next to the Command Center (gap up to 2), stepping out only when the spot is taken.
    // Every result is re-checked to stay on the side away from the minerals.
    fixed[6] off;
    point q;
    fixed d;
    int k;
    off[0] = 30.0; off[1] = 45.0; off[2] = 15.0; off[3] = 60.0; off[4] = 5.0; off[5] = 75.0;
    for (d = 5.0; d <= 16.0; d += 1.0) {
        for (k = 0; k < 6; k += 1) {
            q = UnitTypePlacementFromPoint(kind, 1, PointWithOffsetPolar(c, d, ang + side * off[k]), 1.0);
            if (q != null && !gf_rm7NearMineral(q)
                && (PointGetX(q) - PointGetX(c)) * Cos(ang) + (PointGetY(q) - PointGetY(c)) * Sin(ang) >= 2.0) {
                return q;
            }
        }
    }
    return null;
}
'''


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            k = f'{m}.SC2Map/mapscript.galaxy'
            s = files[k]
            nl = b'\r\n' if b'\r\n' in s else b'\n'
            s, n = OLD_FN.subn(NEW_FN.replace(b'\n', nl), s, count=1)
            assert n == 1, m
            files[k] = s; changed.add(k)
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
