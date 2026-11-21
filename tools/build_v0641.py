#!/usr/bin/env python3
"""0.6.40 -> 0.6.41: enemy Terran Tech Reactors on Hard and up (user 2026-11-21 "적 테란들에게 기술 반응로 같은거라도 넣어야 할듯",
range "어려움 이상").

Missions 1·2 (TRaynor01, TRaynor02), enemy Terran players that get the 7-1 buffs (Dominion; mission 2 also the patrol).
- They get the Liberty AI upgrade TechReactorAI (unlocks the AI add-on "Tech Reactor" = tech lab + reactor in one).
- Every 15 s each finished Barracks/Factory/Starport of theirs without an add-on is ordered once to build a Tech Reactor
  (the script hands over the 75/75 cost so the AI economy is not drained). Covers original buildings, ones the AI builds
  later and the 0.6.40 Very Hard production base.

Usage: python3 tools/build_v0641.py <0.6.40 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.40', b'version=0.6.41'
MAPS = ('TRaynor01', 'TRaynor02')
PERIOD = 15.0
ANCHOR = 'void gf_rmVHTerran (int p) {\n    gf_rmAIUp(p);\n'
BLOCK = f'''// 0.6.41 (user 2026-11-21): Hard and up - enemy Terran production buildings get Tech Reactors
// (Liberty AI add-on: tech lab + reactor). The script pays the 75/75 so the enemy economy is not drained.
bool[16] gv_rmAddonReg;
unitgroup gv_rmAddonTried;
trigger gt_rmAddon;

bool gt_rmAddon_Func (bool testConds, bool runActions) {{
    int p;
    int i;
    unit u;
    string k;
    unitgroup g;
    if (!runActions) {{ return true; }}
    for (p = 1; p <= 15; p += 1) {{
        if (gv_rmAddonReg[p]) {{
            g = UnitGroup(null, p, RegionEntireMap(), UnitFilter((1 << c_targetFilterStructure), 0, 0, (1 << (c_targetFilterDead - 32))), 0);
            for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {{
                u = UnitGroupUnit(g, i);
                k = UnitGetType(u);
                if ((k == "Barracks" || k == "Factory" || k == "Starport") && !UnitTestState(u, c_unitStateUnderConstruction)
                    && UnitAddOnChild(u, 0) == null && !UnitGroupHasUnit(gv_rmAddonTried, u)) {{
                    UnitGroupAdd(gv_rmAddonTried, u);
                    PlayerModifyPropertyInt(p, c_playerPropMinerals, c_playerPropOperAdd, 75);
                    PlayerModifyPropertyInt(p, c_playerPropVespene, c_playerPropOperAdd, 75);
                    UnitIssueOrder(u, Order(AbilityCommand(k + "AddOns", 2)), c_orderQueueAddToEnd);
                }}
            }}
        }}
    }}
    return true;
}}

void gf_rmAddonReg (int p) {{
    if (libNtve_gf_DifficultyValueInt(0, 0, 1, 1) == 0 || gv_rmAddonReg[p]) {{ return; }}
    gv_rmAddonReg[p] = true;
    if (TechTreeUpgradeCount(p, "TechReactorAI", c_techCountCompleteOnly) < 1) {{ TechTreeUpgradeAddLevel(p, "TechReactorAI", 1); }}
    if (gt_rmAddon == null) {{
        gv_rmAddonTried = UnitGroupEmpty();
        gt_rmAddon = TriggerCreate("gt_rmAddon_Func");
        TriggerAddEventTimePeriodic(gt_rmAddon, {PERIOD}, c_timeGame);
    }}
}}

'''


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
            assert t.count(ANCHOR) == 1, m
            t = t.replace(ANCHOR, BLOCK + ANCHOR + '    gf_rmAddonReg(p);\n')
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
