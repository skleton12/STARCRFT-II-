#!/usr/bin/env python3
"""0.4.90 -> 0.4.91: 레이너 자기 생산이 동맹 돈을 쓰지 않게 — 자원 공유를 필요할 때만 켬 (3·4번, 사용자 보고 2026-10-24).

사용자 보고: "내가 동맹 돈 씀" → 레이너 자기 유닛·건물에 동맹 돈이 빠진다. 원인: 동맹→레이너 자원 공유(c_allianceIdSpend)가
늘 켜져 있어 엔진이 레이너 돈이 모자랄 때 동맹 돈을 끌어다 쓴다. 공유를 끄면 동맹 일꾼으로 건물을 못 짓는다(0.4.87).
해결: 0.25초마다 공유를 다시 정한다. 켜는 때는 (1) 플레이어가 동맹 일꾼(탐사정·원시 일벌레, 채굴 일꾼 제외)을 선택하고 있을 때,
(2) 동맹 일꾼이 건설 명령(ProtossBuild·DehakaDroneMorph)을 들고 있을 때뿐이다. 그 밖에는 꺼서 레이너 생산은 레이너 돈만 쓴다.
0.4.90 정산(레이너가 낸 동맹 건물 값을 동맹 돈에서 돌려줌)은 그대로.

Usage: python3 tools/build_v0491.py <0.4.90 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.90', b'version=0.4.91'
FN = '''// 0.4.91: ally -> Raynor spending is on only while the player has an ally worker selected or an ally worker carries
// a build order (user 2026-10-24 "my own units used ally money"). Otherwise Raynor's own production uses only his money.
bool gf_rmBuilding (int p) {
    unitgroup g=UnitGroup(null,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    int i=UnitGroupCount(g,c_unitCountAll);
    unit u;
    string k;
    string a;
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        k=UnitGetType(u);
        if ((k=="Probe" || k=="DehakaDrone") && !UnitHasBehavior2(u,"RM_AllyMiner")) {
            if (UnitIsSelected(u,1)) { return true; }
            if (UnitOrderCount(u)>0) {
                a=AbilityCommandGetAbility(OrderGetAbilityCommand(UnitOrder(u,0)));
                if (a=="ProtossBuild" || a=="DehakaDroneMorph") { return true; }
            }
        }
    }
    return false;
}

bool gt_rmSpendGate_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    PlayerSetAlliance(gv_rmPayA,c_allianceIdSpend,1,gf_rmBuilding(gv_rmPayA));
    PlayerSetAlliance(gv_rmPayB,c_allianceIdSpend,1,gf_rmBuilding(gv_rmPayB));
    return true;
}

void gf_rmPayInit (int a, int b) {'''
MAPS = ['TRaynor03', 'TTychus01']
TAIL_OLD = '    TriggerAddEventUnitConstructProgress(t,null,c_unitProgressStageStart);\n}\n'
TAIL_NEW = ('    TriggerAddEventUnitConstructProgress(t,null,c_unitProgressStageStart);\n'
            '    t=TriggerCreate("gt_rmSpendGate_Func");\n'
            '    TriggerAddEventTimePeriodic(t,0.25,c_timeGame);\n'
            '    TriggerExecute(t,false,false);\n}\n')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m in MAPS:
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            head = 'void gf_rmPayInit (int a, int b) {'
            assert t.count(head) == 1 and t.count(TAIL_OLD) == 1 and 'gt_rmSpendGate_Func' not in t
            t = t.replace(head, FN).replace(TAIL_OLD, TAIL_NEW)
            files[s] = t.encode('utf-8'); changed.add(s)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
