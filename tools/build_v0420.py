#!/usr/bin/env python3
"""Build CCM 0.4.20 from 0.4.19: 3번 정화자도 차원 관문 (사용자 지시 2026-10-18 "수정탑 제한 때문에 3번에도 관문").

4번과 같은 방식 (tools/build_v0415.py·v0419.py):
  - 탐사정이 관문을 짓고(인공제어소·연결체 조건 없음) 완성되면 바로 차원 관문으로 바뀐다. 관문+차원 관문 최대 3.
  - 수정탑은 동력만 주므로 4개 제한을 없앤다.
  - 정화자 병력은 차원 관문이 원작 WarpGateTrain으로 수정탑 동력장 안에 소환 (파수병·파수병·사도·동력기(2기 미만), 시험값).
    소환 3회 충전, 재충전은 원작 재사용 시간. 비용은 정화자 자원.
  - 플레이어는 정화자 관문을 누를 수 없다 (명령 불가). 차원 관문도 정화자 외형.

Usage: python3 tools/build_v0420.py <0.4.19 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.19', b'version=0.4.20'
M3 = 'TRaynor03.SC2Map/'

P10_OLD = '''        if (p==10) {
            if (GameGetMissionTime()<gv_m3_nextMake10) { continue; }
            posts=UnitGroup("Pylon",10,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
            kind[0]="ZealotPurifier";
            kind[1]="ZealotPurifier";
            kind[2]="AdeptFenix";
            count=3;
            if (UnitGroupCount(UnitGroup("RM21_Energizer",10,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)<2) { kind[3]="RM21_Energizer"; count=4; }
        }'''
P10_NEW = '''        if (p==10) {
            // Purifier Warp Gates warp in themselves (0.4.20, same as mission 4).
            gf_m3_GateWarp();
            continue;
        }'''
GATEWARP = '''void gf_m3_GateWarp () {
    unitgroup gates;
    unitgroup pylons;
    unitgroup g;
    unit gate;
    int n;
    int i;
    int k;
    int cmd;
    int tries;
    point at;
    // Finished Gateways become Warp Gates; the player cannot use Purifier gates (scripts still order them).
    g=UnitGroup("Gateway",10,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
    n=UnitGroupCount(g,c_unitCountAll);
    for (i=1;i<=n;i+=1) { UnitIssueOrder(UnitGroupUnit(g,i),Order(AbilityCommand("UpgradeToWarpGate",0)),c_orderQueueReplace); }
    g=UnitGroup("Gateway",10,RegionEntireMap(),UnitFilter(0,0,0,0),0);
    UnitGroupAddUnitGroup(g,UnitGroup("WarpGate",10,RegionEntireMap(),UnitFilter(0,0,0,0),0));
    n=UnitGroupCount(g,c_unitCountAll);
    for (i=1;i<=n;i+=1) { libNtve_gf_MakeUnitUncommandable(UnitGroupUnit(g,i),true); }
    // Warp-in rotation (trial): Sentinel, Sentinel, Fenix Adept, Energizer while fewer than 2. Ally army supply cap 100.
    gates=UnitGroup("WarpGate",10,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
    pylons=UnitGroup("Pylon",10,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
    if (UnitGroupCount(pylons,c_unitCountAlive)==0) { return; }
    n=UnitGroupCount(gates,c_unitCountAll);
    for (i=1;i<=n;i+=1) {
        gate=UnitGroupUnit(gates,i);
        if (!UnitIsAlive(gate) || gf_m3_Food(10)+2.0>100.0) { continue; }
        k=ModI(gv_m3_turn10,4);
        if (k==3 && UnitGroupCount(UnitGroup("RM21_Energizer",10,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)>=2) { k=0; }
        if (k==3) { cmd=5; } else if (k==2) { cmd=1; } else { cmd=0; }
        for (tries=0;tries<4;tries+=1) {
            at=PointWithOffsetPolar(UnitGetPosition(UnitGroupRandomUnit(pylons,c_unitCountAlive)),RandomFixed(2.0,5.0),RandomFixed(0.0,360.0));
            if (UnitIssueOrder(gate,OrderTargetingPoint(AbilityCommand("WarpGateTrain",cmd),at),c_orderQueueReplace)) { gv_m3_turn10+=1; break; }
        }
    }
}

'''
LIMIT_OLD = 'TechTreeAbilityAllow(10,AbilityCommand("ProtossBuild",1),TechTreeUnitCount(10,"Pylon",c_techCountQueuedOrBetter)<4);'
LIMIT_NEW = ('TechTreeAbilityAllow(10,AbilityCommand("ProtossBuild",3),'
             'TechTreeUnitCount(10,"Gateway",c_techCountQueuedOrBetter)+TechTreeUnitCount(10,"WarpGate",c_techCountQueuedOrBetter)<3);')
INIT_OLD = '    TechTreeUnitAllow(10,"Gateway",false);\n'
INIT_NEW = '''    TechTreeUnitAllow(10,"Gateway",true);
    TechTreeUnitAllow(10,"WarpGate",true);
    TechTreeUpgradeAddLevel(10,"WarpGateResearch",1);
    CatalogFieldValueSet(c_gameCatalogAbil,"ProtossBuild","InfoArray[Build4].Button.Requirements",10,"");
    CatalogFieldValueSet(c_gameCatalogAbil,"ProtossBuild","InfoArray[Build4].Button.State",10,"Available");
    CatalogFieldValueSet(c_gameCatalogAbil,"UpgradeToWarpGate","CmdButtonArray[Execute].Requirements",10,"");
    CatalogLinkReplace(10,c_gameCatalogUnit,"Sentry","RM21_Energizer");
    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[Train2].Button.Requirements",10,"");
    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[Train6].Button.Requirements",10,"");
    TechTreeUnitAllow(10,"ZealotPurifier",true);
    TechTreeUnitAllow(10,"AdeptFenix",true);
    TechTreeUnitAllow(10,"RM21_Energizer",true);
    TechTreeUnitAllow(10,"Zealot",true);
    TechTreeUnitAllow(10,"Stalker",true);
    TechTreeUnitAllow(10,"Sentry",true);
    // Purifier Warp Gates store 3 warp-ins; recharge uses the original cooldown times.
''' + ''.join(
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.Link",10,"RM4_WarpGate");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.CountMax",10,"3");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.CountStart",10,"3");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.CountUse",10,"1");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.TimeUse",10,"{s}");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Cooldown.TimeUse",10,"0");\n'
    for t, s in (('Train1', 23), ('Train2', 32), ('Train6', 32)))
ADJ2 = ('rm3/Adj2=탐사정은 수정탑·관문(차원 관문으로 바뀜, 최대 3)·광자포를, 원시 일벌레는 원시 감시자와 원시 벌레를 짓습니다. '
        '동맹은 그 건물에서 자기 자원으로 병력을 보냅니다. /// The Probe builds Pylons, Gateways (become Warp Gates, max 3) and Photon Cannons; '
        'Primal Drones build Primal Wardens and Primal Wurms. The allies send forces from them with their own resources.')
SKIN = b'<CActorUnit id="WarpGate"><On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap Gateway_Purifier_COOP" /></CActorUnit>'


def script(d):
    crlf = b'\r\n' in d
    t = d.decode('utf-8').replace('\r\n', '\n')
    for a, b in ((P10_OLD, P10_NEW), (LIMIT_OLD, LIMIT_NEW), (INIT_OLD, INIT_NEW)):
        assert t.count(a) == 1, a[:60]
        t = t.replace(a, b)
    anchor = 'void gf_m3_Produce () {'
    assert t.count(anchor) == 1
    t = t.replace(anchor, GATEWARP + anchor)
    return (t.replace('\n', '\r\n') if crlf else t).encode('utf-8')


def actors(d):
    assert b'id="WarpGate"' not in d
    end = d.rindex(b'</Catalog>')
    return d[:end] + SKIN + d[end:]


def build(source, output):
    import sys; sys.path.insert(0, str(Path(__file__).resolve().parent)); import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        files[M3 + 'mapscript.galaxy'] = script(files[M3 + 'mapscript.galaxy'])
        files[M3 + 'base.sc2data/gamedata/actordata.xml'] = actors(files[M3 + 'base.sc2data/gamedata/actordata.xml'])
        ko = M3 + 'kokr.sc2data/localizeddata/gamestrings.txt'
        text = files[ko].decode('utf-8'); nl = '\r\n' if '\r\n' in text else '\n'
        lines = [ADJ2 if l.startswith('rm3/Adj2=') else l for l in text.split(nl)]
        assert ADJ2 in lines
        files[ko] = nl.join(lines).encode('utf-8')
        V35.gate('kokr', files[ko])
        changed = {'metadata.txt', M3 + 'mapscript.galaxy', M3 + 'base.sc2data/gamedata/actordata.xml', ko}
        for loc in V35.OTHER_LOCALES:
            k = f'{M3}{loc}.sc2data/localizeddata/gamestrings.txt'; files[k] = V35.other_locale(files[ko]); changed.add(k)
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
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
