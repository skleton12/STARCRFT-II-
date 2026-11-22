#!/usr/bin/env python3
"""0.6.75 -> 0.6.76 (user 2026-11-22 "5단계 이후부터 중간중간에 중장갑 강력 유닛을 넣어줘 불멸자라던가 거신 폭풍함 정찰기",
"자동시전 능력으로 공격하는 놈 플토쪽 그거 공격 안 함").

Maps 4-7 (TTychus01, TTosh01, THanson01, TTosh02), Purifier ally (player 8):
1. At lab tier 5, every other Purifier support call also brings one free heavy unit, in turn:
   Immortal -> Colossus -> Tempest -> Scout (trial). It is the first free unit, so it gets room under the 120 cap
   before the light tier units.
2. Disruptor: it has no real weapon - it attacks only by casting Purification Nova, and the ally AI only gets
   attack-move orders, so it never attacked. A 1-second script now casts Purification Nova for the ally's
   Disruptors at the nearest enemy ground unit within 9, when the ability is off cooldown and not already running.
Game not run.

Usage: python3 tools/build_v0676.py <0.6.75 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.75', b'version=0.6.76'
MAPS = {'TTychus01': 'm4', 'TTosh01': 'm5', 'THanson01': 'm6', 'TTosh02': 'm7'}
HEAVY = ['Immortal', 'ColossusPurifier', 'TempestPurifier', 'Scout']


def patch(s, pre):
    # 1. heavy unit at tier 5, every other Purifier call
    fill = f'void gf_{pre}_SupFill (int p) {{'
    i = s.index(fill)
    glob = (f'// 0.6.76: tier-5 heavy unit every other Purifier call (trial).\nint gv_{pre}_heavyN;\n\n')
    s = s[:i] + glob + s[i:]
    i = s.index(fill)
    paid = f'        gv_{pre}_supPaid[p]=gv_{pre}_supN[p];\n'
    j = s.index(paid, i); assert j - i < 2500 and s.index(f'    gv_{pre}_supPaid[p]=gv_{pre}_supN[p];\n', i) > j
    heavy = (f'        if (gv_{pre}_tier[p]>=5) {{\n'
             f'            if (ModI(gv_{pre}_heavyN+1,2)==1) {{\n'
             + ''.join(f'                if (ModI((gv_{pre}_heavyN+1)/2,4)=={k}) {{ gf_{pre}_SupAdd(p,"{u}"); }}\n' for k, u in enumerate(HEAVY))
             + '            }\n        }\n')
    s = s[:j] + paid + heavy + s[j + len(paid):]
    # the rotation moves on only when a tier-5 Purifier call is actually paid
    i = s.index(f'bool gf_{pre}_CallPay (int p) {{')
    end = f'        food+=gf_{pre}_UnitFood(gv_{pre}_supKind[p][i]);\n    }}\n    return true;\n}}\n'
    j = s.index(end, i); assert j - i < 2000
    s = s[:j] + end.replace('    return true;\n', f'    if (p==8 && gv_{pre}_tier[p]>=5) {{ gv_{pre}_heavyN+=1; }}\n    return true;\n') + s[j + len(end):]
    # 2. Disruptor nova for the ally
    nova = f'''// 0.6.76: ally Disruptors attack only through Purification Nova; cast it for them (every 1 s).
bool gt_{pre}_Nova_Func (bool testConds, bool runActions) {{
    unitgroup g=UnitGroup("Disruptor",8,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    unitgroup e;
    unit u;
    int i;
    for (i=UnitGroupCount(g,c_unitCountAll);i>0;i-=1) {{
        u=UnitGroupUnit(g,i);
        if (UnitOrderHasAbil(u,"PurificationNovaTargeted")) {{ continue; }}
        if (UnitAbilityGetCooldown(u,"PurificationNovaTargeted","Abil/PurificationNovaTargetted")>0.0) {{ continue; }}
        e=UnitGroupAlliance(8,c_unitAllianceEnemy,RegionCircle(UnitGetPosition(u),9.0),UnitFilter((1 << c_targetFilterGround),0,(1 << c_targetFilterStructure) | (1 << c_targetFilterMissile),(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))),0);
        if (UnitGroupCount(e,c_unitCountAlive)==0) {{ continue; }}
        UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("PurificationNovaTargeted",0),UnitGetPosition(UnitGroupClosestToPoint(e,UnitGetPosition(u)))),c_orderQueueReplace);
        // then keep fighting where it was going
        UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),UnitGetPosition(UnitGroupClosestToPoint(e,UnitGetPosition(u)))),c_orderQueueAddToEnd);
    }}
    return true;
}}

'''
    up = f'    gv_{pre}_callUp=true;\n'
    assert s.count(up) == 1 and f'gt_{pre}_Nova_Func' not in s
    k = s.rindex('\nvoid gf_', 0, s.index(up)) + 1  # the function that sets up the support buttons
    s = s[:k] + nova + s[k:]
    s = s.replace(up, up + f'    TriggerAddEventTimePeriodic(TriggerCreate("gt_{pre}_Nova_Func"),1.0,c_timeGame);\n')
    return s


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m, pre in MAPS.items():
            k = f'{m}.SC2Map/mapscript.galaxy'
            t = files[k].decode('utf-8'); crlf = '\r\n' in t
            t = patch(t.replace('\r\n', '\n'), pre)
            files[k] = (t.replace('\n', '\r\n') if crlf else t).encode('utf-8'); changed.add(k)
            u = files[f'{m}.SC2Map/base.sc2data/gamedata/abildata.xml'].decode('utf-8')
            assert 'id="PurificationNovaTargeted"' in u, m
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in prev.infolist():
                z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None and z.namelist() == prev.namelist()
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
