#!/usr/bin/env python3
"""0.6.49 -> 0.6.50 (user 2026-11-21 "건물 뭉탱이로 있음, 좀 띄워 놓거나", "이상한 데 짓는", "배치가 광물 근처에 함",
"건설로봇도 추가해서 수리도 하게").

Enemy extra production buildings (Hard+, missions 2~6):
- Placed in a fan in FRONT of the enemy main (toward Raynor's base): 0°, ±35°, ±70°, rings 10 / 14 / 18 from the hall,
  one slot per building (no more clumping), the placement may only move 3 from the slot, and a slot within 6 of a
  mineral field or vespene geyser is skipped (no building in the mineral line).
Terran enemy (mission 2):
- With its production base it gets 4 extra SCVs at the main and AI repair is switched on (AISetDifficulty
  c_diffRepairDamage), so the AI repairs its buildings/bunkers.
All trial values.

Usage: python3 tools/build_v0650.py <0.6.49 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.49', b'version=0.6.50'
MAPS = ('TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
SCVS = 4
BUILD_RE = re.compile(r'bool gf_rmVHBaseBuild \(int p, string k, point c\) \{\n.*?\n\}\n', re.S)
BUILD_NEW = '''// 0.6.50 (user 2026-11-21): spread the buildings in a fan in front of the enemy main, away from minerals/gas.
int gv_rmVHBaseSlot;
fixed gf_rmVHFan (int j) {
    if (j == 1) { return 35.0; }
    if (j == 2) { return -35.0; }
    if (j == 3) { return 70.0; }
    if (j == 4) { return -70.0; }
    return 0.0;
}

bool gf_rmVHNearRes (point pt) {
    unitgroup g = UnitGroup(null, c_playerAny, RegionCircle(pt, 6.0), UnitFilter(0, 0, 0, 0), 0);
    int i = UnitGroupCount(g, c_unitCountAll);
    string t;
    for ( ; i > 0 ; i -= 1) {
        t = UnitGetType(UnitGroupUnit(g, i));
        if (StringContains(t, "Mineral", c_stringAnywhere, c_stringNoCase) || StringContains(t, "Vespene", c_stringAnywhere, c_stringNoCase)) { return true; }
    }
    return false;
}

bool gf_rmVHBaseBuild (int p, string k, point c) {
    point home = gf_rmVHTarget();
    point pt;
    point want;
    fixed face = 0.0;
    int i;
    int s;
    if (home != null) { face = AngleBetweenPoints(c, home); }
    for (i = 0; i < 15; i += 1) {
        s = gv_rmVHBaseSlot;
        gv_rmVHBaseSlot += 1;
        want = PointWithOffsetPolar(c, 10.0 + 4.0 * IntToFixed(ModI(s / 5, 3)), face + gf_rmVHFan(ModI(s, 5)));
        pt = UnitTypePlacementFromPoint(k, p, want, 3.0);
        if (pt != null && PointPathingPassable(pt) && DistanceBetweenPoints(pt, want) <= 3.0 && !gf_rmVHNearRes(pt)
            && (home == null || PointPathingIsConnected(pt, home))) {
            UnitCreate(1, k, c_unitCreateIgnorePlacement, p, pt, AngleBetweenPoints(pt, c));
            if (k != "Pylon") { UnitGroupAddUnitGroup(gv_rmVHBaseBlds, UnitLastCreatedGroup()); }
            return true;
        }
    }
    return false;
}
'''
TERR_OLD = '        gf_rmVHBunkers(p, c);\n'
TERR_NEW = TERR_OLD + (f'        // 0.6.50: extra SCVs and AI repair (user 2026-11-21 "건설로봇도 추가해서 수리도").\n'
                       f'        UnitCreate({SCVS}, "SCV", 0, p, UnitTypePlacementFromPoint("SCV", p, c, 8.0), 270.0);\n'
                       '        AISetDifficulty(p, c_diffRepairDamage, true);\n')


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
            t, n = BUILD_RE.subn(lambda _: BUILD_NEW, t)
            assert n == 1, m
            if m == 'TRaynor02':
                assert t.count(TERR_OLD) == 1; t = t.replace(TERR_OLD, TERR_NEW)
            files[p] = t.replace('\n', nl).encode('utf-8')
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
