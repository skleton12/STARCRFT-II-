#!/usr/bin/env python3
"""0.6.43 -> 0.6.44 (user 2026-11-21 "적용만 되고 맵에 없잖아", "적 기지 근방에 건물 더 추가하라니까", "벙커도 더 짓게 해 아군 기지 근처까지").

1. Tech Reactor fix (missions 1·2, Hard and up). 0.6.41 issued the add-on order with no target, so nothing was built.
   Now: allow the add-on units/commands for the enemy, order Build3 (Tech Reactor) targeting the building's own position
   (how add-on orders are given), fall back to the untargeted order, then to a Tech Lab; refund the 75/75 if every order
   fails and retry next time (15 s).
2. Enemy production bases (0.6.40) now from Hard (was Very Hard only); Very Hard places the set twice.
3. Mission 2 (Terran enemy): with the base set, 4 bunkers with 4 marines each are placed on the line from the enemy main to
   Raynor's main (30·45·60·75 % of the way, placement- and path-checked) — reaching near Raynor's base.
All counts trial values.

Usage: python3 tools/build_v0644.py <0.6.43 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.43', b'version=0.6.44'
BASE_MAPS = ('TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
ADDON_MAPS = ('TRaynor01', 'TRaynor02')
BUNKERS, BUNKER_MARINES = 4, 4

ADDON_OLD = '''                    UnitGroupAdd(gv_rmAddonTried, u);
                    PlayerModifyPropertyInt(p, c_playerPropMinerals, c_playerPropOperAdd, 75);
                    PlayerModifyPropertyInt(p, c_playerPropVespene, c_playerPropOperAdd, 75);
                    UnitIssueOrder(u, Order(AbilityCommand(k + "AddOns", 2)), c_orderQueueAddToEnd);
'''
ADDON_NEW = '''                    // 0.6.44: add-on orders target the building's own position; fall back, refund if all fail.
                    PlayerModifyPropertyInt(p, c_playerPropMinerals, c_playerPropOperAdd, 75);
                    PlayerModifyPropertyInt(p, c_playerPropVespene, c_playerPropOperAdd, 75);
                    if (UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand(k + "AddOns", 2), UnitGetPosition(u)), c_orderQueueAddToEnd)
                        || UnitIssueOrder(u, Order(AbilityCommand(k + "AddOns", 2)), c_orderQueueAddToEnd)
                        || UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand(k + "AddOns", 0), UnitGetPosition(u)), c_orderQueueAddToEnd)) {
                        UnitGroupAdd(gv_rmAddonTried, u);
                    }
                    else {
                        PlayerModifyPropertyInt(p, c_playerPropMinerals, c_playerPropOperSubtract, 75);
                        PlayerModifyPropertyInt(p, c_playerPropVespene, c_playerPropOperSubtract, 75);
                    }
'''
ALLOW_OLD = '    if (TechTreeUpgradeCount(p, "TechReactorAI", c_techCountCompleteOnly) < 1) { TechTreeUpgradeAddLevel(p, "TechReactorAI", 1); }\n'
ALLOW_NEW = ALLOW_OLD + ''.join(
    f'    TechTreeUnitAllow(p, "{b}TechReactor", true);\n    TechTreeUnitAllow(p, "{b}TechLab", true);\n'
    f'    TechTreeAbilityAllow(p, AbilityCommand("{b}AddOns", 0), true);\n    TechTreeAbilityAllow(p, AbilityCommand("{b}AddOns", 2), true);\n'
    for b in ('Barracks', 'Factory', 'Starport'))

DIFF_OLD = '    if (libNtve_gf_DifficultyValueInt(0, 0, 0, 1) == 0 || gv_rmVHBaseReg[p]) { return; }\n'
DIFF_NEW = '    // 0.6.44: from Hard (was Very Hard only).\n    if (libNtve_gf_DifficultyValueInt(0, 0, 1, 1) == 0 || gv_rmVHBaseReg[p]) { return; }\n'
PLACE_OLD = '            if (u != null) { if (gf_rmVHBasePlace(p, UnitGetPosition(u)) > 0) { made += 1; } }\n'
PLACE_NEW = ('            if (u != null) {\n'
             '                if (gf_rmVHBasePlace(p, UnitGetPosition(u)) > 0) { made += 1; }\n'
             '                // 0.6.44: Very Hard places the set twice.\n'
             '                if (libNtve_gf_DifficultyValueInt(0, 0, 0, 1) == 1) { gf_rmVHBasePlace(p, UnitGetPosition(u)); }\n'
             '            }\n')
BUNK_ANCHOR = 'int gf_rmVHBasePlace (int p, point c) {\n'
BUNK_FN = f'''// 0.6.44 (user 2026-11-21): Terran enemies also get bunkers (with marines) out toward Raynor's base (trial).
const int gv_rmVHBunkers = {BUNKERS};
void gf_rmVHBunkers (int p, point c) {{
    point home = gf_rmVHTarget();
    point pt;
    int i;
    fixed f;
    unitgroup g;
    if (home == null) {{ return; }}
    for (i = 1; i <= gv_rmVHBunkers; i += 1) {{
        f = 0.15 + 0.6 * IntToFixed(i) / IntToFixed(gv_rmVHBunkers);
        pt = Point(PointGetX(c) + (PointGetX(home) - PointGetX(c)) * f, PointGetY(c) + (PointGetY(home) - PointGetY(c)) * f);
        pt = UnitTypePlacementFromPoint("Bunker", p, pt, 8.0);
        if (pt != null && PointPathingPassable(pt) && PointPathingIsConnected(pt, home)) {{
            g = UnitCreate(1, "Bunker", c_unitCreateIgnorePlacement, p, pt, 270.0);
            if (UnitGroupCount(g, c_unitCountAll) > 0) {{ UnitCargoCreate(UnitGroupUnit(g, 1), "Marine", {BUNKER_MARINES}); }}
        }}
    }}
}}

'''
TERR_OLD = '        if (gf_rmVHBaseBuild(p,"Factory",c)) { n += 1; }\n'
TERR_NEW = TERR_OLD + '        gf_rmVHBunkers(p, c);\n'


def once(t, a, b, m):
    assert t.count(a) == 1, (m, a[:60])
    return t.replace(a, b)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in sorted(set(BASE_MAPS) | set(ADDON_MAPS)):
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            if m in ADDON_MAPS:
                t = once(t, ADDON_OLD, ADDON_NEW, m)
                t = once(t, ALLOW_OLD, ALLOW_NEW, m)
            if m in BASE_MAPS:
                t = once(t, DIFF_OLD, DIFF_NEW, m)
                t = once(t, PLACE_OLD, PLACE_NEW, m)
                if m == 'TRaynor02':
                    t = once(t, BUNK_ANCHOR, BUNK_FN + BUNK_ANCHOR, m)
                    t = once(t, TERR_OLD, TERR_NEW, m)
            files[p] = t.replace('\n', nl).encode('utf-8')
            changed.add(p)
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
    x = a.parse_args(); build(x.source, x.output)
