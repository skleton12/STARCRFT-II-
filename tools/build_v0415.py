#!/usr/bin/env python3
"""Build CCM 0.4.15 from 0.4.14: 정화자가 차원 관문에서 직접 소환 (사용자 2026-10-18 "소환 간격은 놔두고 동맹이 관문에서 소환").

- 0.4.14의 40초 묶음 간격과 '정화자 관문 생산 명령 막기'를 되돌린다 (막으면 동맹도 소환을 못 함).
- 정화자 차원 관문이 원작 WarpGateTrain으로 수정탑 동력장 안에 한 기씩 소환한다. 관문마다 원작 재사용 대기, 비용은 정화자 자원.
  광전사→정화자 파수병, 추적자→피닉스 사도, 파수기→동력기 (정화자 전용 연결 바꿈, 인공제어소 조건은 정화자만 없앰).
  순서: 파수병, 파수병, 사도, 동력기(2기 미만일 때) — 시험값. 동맹 병력 인구 100 상한 그대로.
- 플레이어가 정화자 관문을 누르지 못하게 관문·차원 관문을 '명령 불가'로 만든다 (스크립트 명령은 원작 스완 수송선처럼 통한다).

Usage: python3 tools/build_v0415.py <0.4.14 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.14', b'version=0.4.15'
M4 = 'TTychus01.SC2Map/mapscript.galaxy'

WARP = '''void gf_m4_Warp () {
    unitgroup gates;
    unitgroup pylons;
    unit gate;
    int n;
    int i;
    int k;
    int cmd;
    int tries;
    point at;
    // Purifier Warp Gates warp in themselves (WarpGateTrain, native cooldown and cost, user 2026-10-18).
    // Rotation (trial): Sentinel, Sentinel, Fenix Adept, Energizer while fewer than 2. Ally army supply cap 100.
    gates=UnitGroup("WarpGate",8,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
    pylons=UnitGroup("Pylon",8,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
    if (UnitGroupCount(pylons,c_unitCountAlive)==0) { return; }
    n=UnitGroupCount(gates,c_unitCountAll);
    for (i=1;i<=n;i+=1) {
        gate=UnitGroupUnit(gates,i);
        if (!UnitIsAlive(gate) || gf_m4_Food(8)+2.0>100.0) { continue; }
        k=ModI(gv_m4_turn8,4);
        if (k==3 && UnitGroupCount(UnitGroup("RM21_Energizer",8,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)>=2) { k=0; }
        if (k==3) { cmd=5; } else if (k==2) { cmd=1; } else { cmd=0; }
        for (tries=0;tries<4;tries+=1) {
            at=PointWithOffsetPolar(UnitGetPosition(UnitGroupRandomUnit(pylons,c_unitCountAlive)),RandomFixed(2.0,5.0),RandomFixed(0.0,360.0));
            if (UnitIssueOrder(gate,OrderTargetingPoint(AbilityCommand("WarpGateTrain",cmd),at),c_orderQueueReplace)) { gv_m4_turn8+=1; break; }
        }
    }
}'''
OLD_INIT = '''    // The player shares control of the Purifiers for the Probe; Purifier gates must not train for the player.
    for (ally=0;ally<8;ally+=1) {
        TechTreeAbilityAllow(8,AbilityCommand("GatewayTrain",ally),false);
        TechTreeAbilityAllow(8,AbilityCommand("WarpGateTrain",ally),false);
    }
'''
NEW_INIT = '''    // Purifier Warp Gates train Purifier units (ally-only link swaps; no Cybernetics Core needed for the ally).
    CatalogLinkReplace(8,c_gameCatalogUnit,"Sentry","RM21_Energizer");
    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[Train2].Button.Requirements",8,"");
    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[Train6].Button.Requirements",8,"");
    TechTreeUnitAllow(8,"ZealotPurifier",true);
    TechTreeUnitAllow(8,"AdeptFenix",true);
    TechTreeUnitAllow(8,"RM21_Energizer",true);
    TechTreeUnitAllow(8,"Zealot",true);
    TechTreeUnitAllow(8,"Stalker",true);
    TechTreeUnitAllow(8,"Sentry",true);
'''
GATES_OLD = '''    for (;i>0;i-=1) { UnitIssueOrder(UnitGroupUnit(g,i),Order(AbilityCommand("UpgradeToWarpGate",0)),c_orderQueueReplace); }
}'''
GATES_NEW = '''    for (;i>0;i-=1) { UnitIssueOrder(UnitGroupUnit(g,i),Order(AbilityCommand("UpgradeToWarpGate",0)),c_orderQueueReplace); }
    // The player shares control for the Probe but must not use Purifier gates (scripts still order them).
    g=UnitGroup("Gateway",8,RegionEntireMap(),UnitFilter(0,0,0,0),0);
    UnitGroupAddUnitGroup(g,UnitGroup("WarpGate",8,RegionEntireMap(),UnitFilter(0,0,0,0),0));
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) { libNtve_gf_MakeUnitUncommandable(UnitGroupUnit(g,i),true); }
}'''


def patch(t):
    i = t.index('void gf_m4_Warp () {'); j = t.index('\n}\n', i) + 2
    t = t[:i] + WARP + t[j:]
    for a, b in ((OLD_INIT, NEW_INIT), (GATES_OLD, GATES_NEW)):
        assert t.count(a) == 1, a[:50]
        t = t.replace(a, b)
    return t


def script(d):
    crlf = b'\r\n' in d
    t = patch(d.decode('utf-8').replace('\r\n', '\n'))
    return (t.replace('\n', '\r\n') if crlf else t).encode('utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    fix = {M4: script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), fix[info.filename](d) if info.filename in fix else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in fix: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    sup = HERE / 'data/mission04_support.galaxy'
    sup.write_text(patch(sup.read_text()))
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
