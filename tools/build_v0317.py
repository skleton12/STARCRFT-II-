#!/usr/bin/env python3
"""Build CCM 0.3.17 from 0.3.16: 3번 동맹이 실제로 지키며 싸우게 (CLAUDE.md 7-0 '2번부터 자동 전투').

사용자 보고 (2026-10-17): "동맹이 바보가 됐잖음".
원인 (코드 검토): 동맹 병력은 할 일이 없을 때 (65,47) 한 점으로 공격 이동만 하고 그 자리에 서 있었다.
레이너 본진·동맹 기지가 공격받아도 사거리 밖이면 반응하지 않았다.
수정 — 자동 전투:
  - 방어 구역(레이너 본진 언덕 (92,38) 반경 24, 서쪽 접근로 (65,47) 반경 12, 정화자 기지 (29,31) 반경 14,
    원시저그 기지 (104.5,45.5) 반경 12) 안에 적(2~5번)이 있으면, 레이너 본진에 가장 가까운 적에게
    동맹 병력 전체가 공격 이동 (4초마다 갱신, 이미 적 6칸 안에서 싸우는 유닛은 그대로).
  - 위협이 없으면 레이너 본진 언덕길 앞 (80,46)에 모여 대기.
  - 핑은 기존대로 30초 우선.
반경·지점·갱신 간격은 시험값.

Usage: python3 tools/build_v0317.py <0.3.16 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.16', b'version=0.3.17'
M3 = 'TRaynor03.SC2Map/'

ATTACK_OLD_START = 'void gf_m3_Attack (int p) {'
ATTACK_NEW = '''point gv_m3_threat;
bool gv_m3_hasThreat;
int gv_m3_threatTick;

void gf_m3_FindThreat () {
    unitgroup e;
    int p;
    // Enemy players 2-5 inside the areas the allies defend (trial radii).
    e=UnitGroupEmpty();
    for (p=2;p<=5;p+=1) {
        UnitGroupAddUnitGroup(e,UnitGroup(null,p,RegionCircle(Point(92.0,38.0),24.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0));
        UnitGroupAddUnitGroup(e,UnitGroup(null,p,RegionCircle(Point(65.0,47.0),12.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0));
        UnitGroupAddUnitGroup(e,UnitGroup(null,p,RegionCircle(Point(29.0,31.0),14.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0));
        UnitGroupAddUnitGroup(e,UnitGroup(null,p,RegionCircle(Point(104.5,45.5),12.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0));
    }
    gv_m3_hasThreat=(UnitGroupCount(e,c_unitCountAlive)>0);
    if (gv_m3_hasThreat) { gv_m3_threat=UnitGetPosition(UnitGroupClosestToPoint(e,Point(92.0,38.0))); }
}

void gf_m3_Attack (int p) {'''

BODY_OLD = '''    // Help defend the player's western approach instead of the mission 2 target.
    target=Point(65.0,47.0);
    if (gv_m3_clearing) { target=Point(35.5,31.0); }
    if (GameGetMissionTime()<gv_m3_pingUntil) { target=gv_m3_ping; }
    g=gf_m3_Army(p);
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (!UnitGroupHasUnit(gv_m3_pending,u) && UnitOrderCount(u)==0) {
            UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),target),c_orderQueueReplace);
        }
    }
}'''
BODY_NEW = '''    // Automatic combat (7-0): ping first, then the closest threat to Raynor's base, else wait at Raynor's ramp.
    g=gf_m3_Army(p);
    i=UnitGroupCount(g,c_unitCountAll);
    if (GameGetMissionTime()<gv_m3_pingUntil) {
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            if (!UnitGroupHasUnit(gv_m3_pending,u) && UnitOrderCount(u)==0) {
                UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),gv_m3_ping),c_orderQueueReplace);
            }
        }
        return;
    }
    if (gv_m3_hasThreat) {
        target=gv_m3_threat;
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            if (UnitGroupHasUnit(gv_m3_pending,u)) { continue; }
            if (UnitOrderCount(u)==0 || (gv_m3_threatTick==0 && DistanceBetweenPoints(UnitGetPosition(u),target)>6.0)) {
                UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),target),c_orderQueueReplace);
            }
        }
        return;
    }
    target=Point(80.0,46.0);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (!UnitGroupHasUnit(gv_m3_pending,u) && UnitOrderCount(u)==0 && DistanceBetweenPoints(UnitGetPosition(u),target)>5.0) {
            UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),target),c_orderQueueReplace);
        }
    }
}'''
TICK_OLD = '    gf_m3_Attack(10);\n    gf_m3_Attack(11);\n'
TICK_NEW = ('    gf_m3_FindThreat();\n    gf_m3_Attack(10);\n    gf_m3_Attack(11);\n'
            '    gv_m3_threatTick=ModI(gv_m3_threatTick+1,2);\n')


def script(data):
    text = data.decode('utf-8')
    for old, new in [(BODY_OLD, BODY_NEW), (ATTACK_OLD_START, ATTACK_NEW), (TICK_OLD, TICK_NEW)]:
        assert text.count(old) == 1, old[:60]
        text = text.replace(old, new, 1)
    return text.encode('utf-8')


FIX = {M3 + 'mapscript.galaxy': script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = prev.read(info.filename)
                    if info.filename in FIX: data = FIX[info.filename](data)
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path)
    a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
