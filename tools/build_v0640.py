#!/usr/bin/env python3
"""0.6.39 -> 0.6.40: Very Hard enemy production bases (user 2026-11-21 "2번 이후는 건물 건설할 수 있는 놈들이니 생산기지 추가…
아주 어려움을 엄청 어렵게", "그 후에도 적 병력이 중후반부터 많이 나올 수 있게", "ㅇㅇ").

Missions 2~6, Very Hard only. Trial values.
- 60 s after start, by the main town hall of up to 2 enemy players (players already given the 7-1 enemy buffs), the script
  places production buildings of that enemy's race (placement-tested, path-connected to Raynor's base):
  Terran Barracks ×2 + Factory, Zerg Hatchery + Roach Warren / Hydralisk Den, Protoss Pylon + Gateway ×2.
- From mission 5:00, every 50 s each living extra building sends units (types already used by that mission's waves) that
  attack-move to Raynor's main. Destroying the building stops it. At most 60 of these units alive at once.
- Mid/late game: count = base × wave ramp (0.7→1.4 over 24 min) × (1 + (minutes − 10)/10 after 10 min), capped ×2.5.

Usage: python3 tools/build_v0640.py <0.6.39 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.39', b'version=0.6.40'
FIRST, PERIOD, CAP, MAX_PLAYERS, ARMY_CAP = 300.0, 50.0, 2.5, 2, 60
HALLS = ('CommandCenter', 'OrbitalCommand', 'PlanetaryFortress', 'Hatchery', 'Lair', 'Hive', 'Nexus')
# per map: race -> [(building, [(unit, base count)])]
TERRAN = [('Barracks', [('Marine', 3), ('Medic', 1)]), ('Barracks', [('Marine', 3), ('Medic', 1)]), ('Factory', [('Hellion', 2)])]
PROTOSS = [('Pylon', []), ('Gateway', [('Zealot', 2), ('Stalker', 1)]), ('Gateway', [('Zealot', 2), ('Stalker', 1)])]
ROACH = [('Hatchery', [('Zergling', 4)]), ('RoachWarren', [('Roach', 2)])]
HYDRA = [('Hatchery', [('Zergling', 4)]), ('HydraliskDen', [('Hydralisk', 2)])]
MAPS = {
    'TRaynor02': {'Terr': TERRAN},
    'TRaynor03': {'Zerg': [('Hatchery', [('Zergling', 4), ('Baneling', 1)]), ('RoachWarren', [('Roach', 2)])]},
    'TTychus01': {'Zerg': HYDRA, 'Prot': PROTOSS},
    'TTosh01': {'Zerg': HYDRA},
    'THanson01': {'Zerg': ROACH},
}
ANCHOR = 'void gf_rmVHTerran (int p) {\n'


def block(table):
    place = ''
    for i, (race, blds) in enumerate(table.items()):
        place += ('    if' if i == 0 else '    else if') + f' (r=="{race}") {{\n' + ''.join(
            f'        if (gf_rmVHBaseBuild(p,"{b}",c)) {{ n += 1; }}\n' for b, _ in blds) + '    }\n'
    kinds = {}
    for blds in table.values():
        for b, units in blds:
            if units: kinds[b] = units
    spawn = ''.join(f'    if (k=="{b}") {{\n' + ''.join(f'        gf_rmVHBaseUnits(b,"{u}",{n},s);\n' for u, n in units) + '    }\n'
                    for b, units in kinds.items())
    halls = '||'.join(f't=="{h}"' for h in HALLS)
    return f'''// 0.6.40 (user 2026-11-21): Very Hard - extra enemy production buildings by enemy main bases; their units grow mid/late (trial).
const fixed gv_rmVHBaseFirst = {FIRST};
const fixed gv_rmVHBasePeriod = {PERIOD};
const fixed gv_rmVHBaseCap = {CAP};
const int gv_rmVHBaseMaxPlayers = {MAX_PLAYERS};
const int gv_rmVHBaseArmyCap = {ARMY_CAP};
unitgroup gv_rmVHBaseArmy;
bool[16] gv_rmVHBaseReg;
unitgroup gv_rmVHBaseBlds;
trigger gt_rmVHBase;

unit gf_rmVHHall (int p) {{
    unitgroup g = UnitGroup(null, p, RegionEntireMap(), UnitFilter((1 << c_targetFilterStructure), 0, 0, (1 << (c_targetFilterDead - 32))), 0);
    int i = UnitGroupCount(g, c_unitCountAll);
    unit u;
    string t;
    for ( ; i > 0 ; i -= 1) {{
        u = UnitGroupUnit(g, i);
        t = UnitGetType(u);
        if ({halls}) {{ return u; }}
    }}
    return null;
}}

point gf_rmVHTarget () {{
    unit u = gf_rmVHHall(1);
    point c = PlayerStartLocation(1);
    if (u != null) {{ c = UnitGetPosition(u); }}
    if (c == null) {{ return null; }}
    // A walkable spot next to Raynor's main (the hall centre itself is blocked).
    return UnitTypePlacementFromPoint("Marine", 1, c, 12.0);
}}

bool gf_rmVHBaseBuild (int p, string k, point c) {{
    point home = gf_rmVHTarget();
    point pt;
    int i;
    for (i = 0; i < 8; i += 1) {{
        pt = UnitTypePlacementFromPoint(k, p, PointWithOffsetPolar(c, 8.0 + IntToFixed(i), IntToFixed(i * 45 + RandomInt(0, 40))), 6.0);
        if (pt != null && PointPathingPassable(pt) && (home == null || PointPathingIsConnected(pt, home))) {{
            UnitCreate(1, k, c_unitCreateIgnorePlacement, p, pt, 270.0);
            if (k != "Pylon") {{ UnitGroupAddUnitGroup(gv_rmVHBaseBlds, UnitLastCreatedGroup()); }}
            return true;
        }}
    }}
    return false;
}}

int gf_rmVHBasePlace (int p, point c) {{
    string r = PlayerRace(p);
    int n = 0;
{place}    return n;
}}

void gf_rmVHBaseUnits (unit b, string k, int n, fixed s) {{
    int c = CeilingI(IntToFixed(n) * s);
    point home = gf_rmVHTarget();
    point pt = UnitTypePlacementFromPoint(k, UnitGetOwner(b), UnitGetPosition(b), 8.0);
    if (c <= 0 || pt == null || UnitGroupCount(gv_rmVHBaseArmy, c_unitCountAlive) >= gv_rmVHBaseArmyCap) {{ return; }}
    UnitCreate(c, k, 0, UnitGetOwner(b), pt, 270.0);
    UnitGroupAddUnitGroup(gv_rmVHBaseArmy, UnitLastCreatedGroup());
    if (home != null) {{
        UnitGroupIssueOrder(UnitLastCreatedGroup(), OrderTargetingPoint(AbilityCommand("attack", 0), home), c_orderQueueReplace);
    }}
}}

void gf_rmVHBaseSpawn (unit b, fixed s) {{
    string k = UnitGetType(b);
{spawn}}}

bool gt_rmVHBase_Func (bool testConds, bool runActions) {{
    int p;
    int i;
    int made = 0;
    unit u;
    fixed m;
    fixed s;
    if (!runActions) {{ return true; }}
    Wait(60.0, c_timeGame);
    for (p = 1; p <= 15; p += 1) {{
        if (gv_rmVHBaseReg[p] && made < gv_rmVHBaseMaxPlayers) {{
            u = gf_rmVHHall(p);
            if (u != null) {{ if (gf_rmVHBasePlace(p, UnitGetPosition(u)) > 0) {{ made += 1; }} }}
        }}
    }}
    while (GameGetMissionTime() < gv_rmVHBaseFirst) {{ Wait(5.0, c_timeGame); }}
    while (UnitGroupCount(gv_rmVHBaseBlds, c_unitCountAlive) > 0) {{
        m = GameGetMissionTime() / 60.0;
        s = gf_rmWaveRamp() * (1.0 + MaxF(0.0, m - 10.0) / 10.0);
        if (s > gv_rmVHBaseCap) {{ s = gv_rmVHBaseCap; }}
        for (i = UnitGroupCount(gv_rmVHBaseBlds, c_unitCountAll); i > 0; i -= 1) {{
            u = UnitGroupUnit(gv_rmVHBaseBlds, i);
            if (UnitIsAlive(u)) {{ gf_rmVHBaseSpawn(u, s); }}
        }}
        Wait(gv_rmVHBasePeriod, c_timeGame);
    }}
    return true;
}}

void gf_rmVHBaseReg (int p) {{
    if (libNtve_gf_DifficultyValueInt(0, 0, 0, 1) == 0 || gv_rmVHBaseReg[p]) {{ return; }}
    gv_rmVHBaseReg[p] = true;
    if (gt_rmVHBase == null) {{
        gv_rmVHBaseBlds = UnitGroupEmpty();
        gv_rmVHBaseArmy = UnitGroupEmpty();
        gt_rmVHBase = TriggerCreate("gt_rmVHBase_Func");
        TriggerExecute(gt_rmVHBase, false, false);
    }}
}}

'''


def once(t, a, b):
    assert t.count(a) == 1, a[:60]
    return t.replace(a, b)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m, table in MAPS.items():
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            assert t.index('fixed gf_rmWaveRamp ()') < t.index(ANCHOR)
            t = once(t, ANCHOR, block(table) + ANCHOR)
            for race in ('Terran', 'Zerg', 'Protoss'):
                a = f'void gf_rmVH{race} (int p) {{\n    gf_rmAIUp(p);\n'
                t = once(t, a, a + '    gf_rmVHBaseReg(p);\n')
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
