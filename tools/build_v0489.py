#!/usr/bin/env python3
"""0.4.88 -> 0.4.89: 동맹 자동 건설 — 자날 'WOL with allies' 방식 (3·4번, 사용자 2026-10-24).

사용자: "동맹 자원으로 짓기", "자동 건설", "부족한 것부터", "드라이브의 자날 동맹 모드처럼".
드라이브의 WOL with allies(Ylvae) 확인 결과: 핑은 공격만, 건설은 지도에 정해 둔 동맹 기지 자리에서 AI가 스스로 짓고
부서지면 다시 짓는다(AI bully). 사용자 선택: "자날 방식 그대로", 동맹 돈은 "지금처럼 동맹 수입대로"(무한 보충 안 함).

- 핑은 지금처럼 공격(0.4.86 유지).
- 동맹마다 기지 자리(일꾼이 내리는 곳, 시험값) 근처에 부족한 건물부터 하나씩 짓는다. 10초마다 한 번(시험값).
  정화자: 수정탑(기지 자리 반경 8 안에 없으면) → 관문(상한까지) → 광자포 2개(시험값).
  원시저그: 원시 감시자(상한까지) → 원시 벌레 2개(시험값).
- 짓는 일꾼은 쉬고 있는 동맹 일꾼(채굴 일꾼 제외)만 쓴다 — 플레이어가 명령 중인 일꾼은 건드리지 않는다.
- 비용은 동맹 자원(일꾼 주인). 돈이 모자라면 기다린다. 부서지면 개수가 줄어 다시 짓는다.
- 플레이어가 동맹 일꾼으로 직접 짓는 기존 방식·확장 기지·상한은 그대로.

Usage: python3 tools/build_v0489.py <0.4.88 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.88', b'version=0.4.89'
BUILD_EVERY = 10.0   # 시험값
CANNONS = 2          # 시험값
WURMS = 2            # 시험값
FN = f'''
// 0.4.89: ally auto-build like the "WOL with allies" mod (user 2026-10-24): pings stay attack-only; each ally builds its
// most needed structure at its own base spot and rebuilds losses, paid with ally money. Spots and counts are trial values.
fixed gv_rmBuildNext;

unit gf_rmIdleWorker (int p, string worker) {{
    unitgroup g=UnitGroup(worker,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    int i=UnitGroupCount(g,c_unitCountAll);
    unit u;
    for (;i>0;i-=1) {{
        u=UnitGroupUnit(g,i);
        if (!UnitHasBehavior2(u,"RM_AllyMiner") && UnitOrderCount(u)==0) {{ return u; }}
    }}
    return null;
}}

int gf_rmNear (int p, string kind, point at, fixed r) {{
    return UnitGroupCount(UnitGroup(kind,p,RegionCircle(at,r),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0),c_unitCountAlive);
}}

bool gf_rmTryBuild (int p, string worker, string abil, int idx, string kind, point at, fixed r) {{
    unit w=gf_rmIdleWorker(p,worker);
    point spot;
    if (w==null) {{ return true; }}
    if (PlayerGetPropertyInt(p,c_playerPropMinerals)<UnitTypeGetCost(kind,c_unitCostMinerals)
        || PlayerGetPropertyInt(p,c_playerPropVespene)<UnitTypeGetCost(kind,c_unitCostVespene)) {{ return true; }}
    spot=UnitTypePlacementFromPoint(kind,p,at,r);
    if (spot==null) {{ return false; }}
    UnitIssueOrder(w,OrderTargetingPoint(AbilityCommand(abil,idx),spot),c_orderQueueReplace);
    return true;
}}

void gf_rmAutoBuild (int pp, int pz, point sp, point sz, int capG, int capW) {{
    unitgroup py;
    point at;
    if (GameGetMissionTime()<gv_rmBuildNext) {{ return; }}
    gv_rmBuildNext=GameGetMissionTime()+{BUILD_EVERY};
    // Purifiers: Pylon -> Gateways up to the cap -> {CANNONS} Photon Cannons.
    py=UnitGroup("Pylon",pp,RegionCircle(sp,8.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    if (UnitGroupCount(py,c_unitCountAlive)==0) {{ gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",sp,8.0); }}
    else {{
        py=UnitGroup("Pylon",pp,RegionCircle(sp,8.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterUnderConstruction - 32))),0);
        if (UnitGroupCount(py,c_unitCountAlive)>0) {{
            at=UnitGetPosition(UnitGroupClosestToPoint(py,sp));
            if (TechTreeUnitCount(pp,"Gateway",c_techCountQueuedOrBetter)+TechTreeUnitCount(pp,"WarpGate",c_techCountQueuedOrBetter)<capG+gv_rmGateBonus) {{
                if (!gf_rmTryBuild(pp,"Probe","ProtossBuild",3,"Gateway",at,6.0)) {{ gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",sp,12.0); }}
            }}
            else if (gf_rmNear(pp,"PhotonCannon",sp,12.0)<{CANNONS}) {{ gf_rmTryBuild(pp,"Probe","ProtossBuild",7,"PhotonCannon",at,6.0); }}
        }}
    }}
    // Primal Zerg: Primal Wardens up to the cap -> {WURMS} Primal Wurms.
    if (TechTreeUnitCount(pz,"DehakaBarracks",c_techCountQueuedOrBetter)<capW+gv_rmWardenBonus) {{ gf_rmTryBuild(pz,"DehakaDrone","DehakaDroneMorph",0,"DehakaBarracks",sz,10.0); }}
    else if (gf_rmNear(pz,"DehakaNydusDestroyer",sz,14.0)<{WURMS}) {{ gf_rmTryBuild(pz,"DehakaDrone","DehakaDroneMorph",1,"DehakaNydusDestroyer",sz,10.0); }}
}}
'''
MAPS = {
    'TRaynor03': ('gt_m3_Tick_Func', '    gf_rmAllyBases(10,11);\n',
                  '    gf_rmAutoBuild(10,11,Point(93.0,44.0),Point(100.0,44.0),3,4);\n'),
    'TTychus01': ('gt_m4_Tick_Func', '    gf_rmAllyBases(8,9);\n',
                  '    gf_rmAutoBuild(8,9,Point(64.0,26.0),Point(67.0,27.0),3,3);\n'),
}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m, (tick, anchor, call) in MAPS.items():
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            head = f'\nbool {tick} (bool testConds,bool runActions) {{'
            assert t.count(head) == 1 and t.count(anchor) == 1 and 'gf_rmAutoBuild' not in t
            t = t.replace(head, FN + head).replace(anchor, anchor + call)
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
