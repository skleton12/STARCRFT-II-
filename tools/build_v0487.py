#!/usr/bin/env python3
"""0.4.86 -> 0.4.87: 동맹 자원 분리 + 동맹 확장 기지(넥서스·원시 군락)·실제 채굴 (3·4번, 사용자 2026-10-24).

1) 자원 분리 (사용자 선택 A "나랑 동맹 자원을 따로"): 동맹→레이너 자원 사용 허용(c_allianceIdSpend)을 끈다.
   레이너는 동맹 돈을 쓰지 않는다. 동맹 일꾼으로 짓는 건물은 일꾼 주인(동맹)이 낸다(엔진 규칙, 게임 확인 필요).
2) 확장 기지 (사용자: "넥서스와 원시 군락 지을 수 있게, 저그 처리하면 거기다 짓고 싶음"):
   - 정화자 탐사정이 넥서스, 원시 일벌레가 원시 군락(DehakaDroneMorph Build3, 원작 건설 시간 100)을 동시에 1개까지 짓는다.
   - 기지가 한 번 완성되면 차원 관문·원시 감시자 상한 +2 (사용자 "한 번만", 기지가 부서져도 유지).
   - 진짜 채굴 (사용자 선택): 기지마다 채굴 일꾼(표식 RM_AllyMiner, 숨김)을 12초마다 1기씩 광물 50으로 최대 16기 만들고
     (시험값 ALLY_MINERS), 쉬는 채굴 일꾼은 기지 반경 12 안의 광물을 캔다. 가스 채굴은 없다.
   - 채굴한 광물의 50%는 레이너에게 간다 (사용자 "50%는 레이너에게"). 동맹 채굴량(MineralsCollected) 증가분의 절반을 옮긴다.
   - 기존 2초 고정 수입은 그대로. 채굴 일꾼은 프로비우스로 바꾸지 않는다.

Usage: python3 tools/build_v0487.py <0.4.86 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.86', b'version=0.4.87'
ALLY_MINERS = 16
FN = f'''
// 0.4.87: allied expansions (user 2026-10-24): one Nexus / Primal Hive each, real mining, half of mined minerals to Raynor.
const int gv_rmMinerMax = {ALLY_MINERS};
int gv_rmGateBonus;
int gv_rmWardenBonus;
int[16] gv_rmMinedLast;
fixed[16] gv_rmMinerNext;

unit gf_rmBase (int p, string kind) {{
    unitgroup g=UnitGroup(kind,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterUnderConstruction - 32))),1);
    if (UnitGroupCount(g,c_unitCountAlive)==0) {{ return null; }}
    return UnitGroupUnit(g,1);
}}

void gf_rmMiners (int p, unit base, string worker, string harvest) {{
    unitgroup g;
    unitgroup res;
    unit u;
    unit m;
    int i;
    int n;
    if (base==null) {{ return; }}
    m=null;
    res=UnitGroup(null,c_playerAny,RegionCircle(UnitGetPosition(base),12.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    i=UnitGroupCount(res,c_unitCountAll);
    for (;i>0;i-=1) {{
        u=UnitGroupUnit(res,i);
        if (StringContains(UnitGetType(u),"MineralField",c_stringAnywhere,c_stringNoCase) && UnitGetPropertyInt(u,c_unitPropResources,c_unitPropCurrent)>0) {{ m=u; }}
    }}
    n=0;
    g=UnitGroup(worker,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {{
        u=UnitGroupUnit(g,i);
        if (UnitHasBehavior2(u,"RM_AllyMiner")) {{
            n+=1;
            if (m!=null && UnitOrderCount(u)==0) {{ UnitIssueOrder(u,OrderTargetingUnit(AbilityCommand(harvest,0),m),c_orderQueueReplace); }}
        }}
    }}
    if (m==null || n>=gv_rmMinerMax || GameGetMissionTime()<gv_rmMinerNext[p] || PlayerGetPropertyInt(p,c_playerPropMinerals)<50) {{ return; }}
    PlayerModifyPropertyInt(p,c_playerPropMinerals,c_playerPropOperSubtract,50);
    UnitCreate(1,worker,0,p,UnitGetPosition(base),270.0);
    u=UnitLastCreated();
    UnitBehaviorAdd(u,"RM_AllyMiner",u,1);
    gv_rmMinerNext[p]=GameGetMissionTime()+12.0;
}}

void gf_rmShare (int p) {{
    int give;
    give=(PlayerGetPropertyInt(p,c_playerPropMineralsCollected)-gv_rmMinedLast[p])/2;
    if (give<=0) {{ return; }}
    PlayerModifyPropertyInt(1,c_playerPropMinerals,c_playerPropOperAdd,give);
    PlayerModifyPropertyInt(p,c_playerPropMinerals,c_playerPropOperSubtract,give);
    gv_rmMinedLast[p]+=give*2;
}}

void gf_rmAllyBases (int pp, int pz) {{
    unit nexus=gf_rmBase(pp,"Nexus");
    unit hive=gf_rmBase(pz,"DehakaHatchery");
    if (nexus!=null) {{ gv_rmGateBonus=2; }}
    if (hive!=null) {{ gv_rmWardenBonus=2; }}
    TechTreeAbilityAllow(pp,AbilityCommand("ProtossBuild",0),TechTreeUnitCount(pp,"Nexus",c_techCountQueuedOrBetter)<1);
    TechTreeAbilityAllow(pz,AbilityCommand("DehakaDroneMorph",2),TechTreeUnitCount(pz,"DehakaHatchery",c_techCountQueuedOrBetter)<1);
    gf_rmMiners(pp,nexus,"Probe","ProbeHarvest");
    gf_rmMiners(pz,hive,"DehakaDrone","DroneHarvest");
    gf_rmShare(pp);
    gf_rmShare(pz);
}}
'''
MAPS = {
    'TRaynor03': dict(pp=10, pz=11, tick='gt_m3_Tick_Func', pairs=[
        ('    gf_m3_Workers();\n    // Post limits', '    gf_m3_Workers();\n    gf_rmAllyBases(10,11);\n    // Post limits'),
        ('TechTreeUnitCount(11,"DehakaBarracks",c_techCountQueuedOrBetter)<4);', 'TechTreeUnitCount(11,"DehakaBarracks",c_techCountQueuedOrBetter)<4+gv_rmWardenBonus);'),
        ('TechTreeUnitCount(10,"WarpGate",c_techCountQueuedOrBetter)<3);', 'TechTreeUnitCount(10,"WarpGate",c_techCountQueuedOrBetter)<3+gv_rmGateBonus);'),
        ('    PlayerSetAlliance(10,c_allianceIdSpend,1,true);', '    PlayerSetAlliance(10,c_allianceIdSpend,1,false);'),
        ('    PlayerSetAlliance(11,c_allianceIdSpend,1,true);', '    PlayerSetAlliance(11,c_allianceIdSpend,1,false);'),
        ('    TechTreeUnitAllow(10,"Nexus",false);', '    TechTreeUnitAllow(10,"Nexus",true);\n    TechTreeUnitAllow(11,"DehakaHatchery",true);'),
    ]),
    'TTychus01': dict(pp=8, pz=9, tick='gt_m4_Tick_Func', pairs=[
        ('    gf_m4_Workers();\n    // Post limits', '    gf_m4_Workers();\n    gf_rmAllyBases(8,9);\n    // Post limits'),
        ('    TechTreeAbilityAllow(8,AbilityCommand("ProtossBuild",3),gates<3);', '    TechTreeAbilityAllow(8,AbilityCommand("ProtossBuild",3),gates<3+gv_rmGateBonus);'),
        ('TechTreeUnitCount(9,"DehakaBarracks",c_techCountQueuedOrBetter)<3);', 'TechTreeUnitCount(9,"DehakaBarracks",c_techCountQueuedOrBetter)<3+gv_rmWardenBonus);'),
        ('    PlayerSetAlliance(8,c_allianceIdSpend,1,true);', '    PlayerSetAlliance(8,c_allianceIdSpend,1,false);'),
        ('    PlayerSetAlliance(9,c_allianceIdSpend,1,true);', '    PlayerSetAlliance(9,c_allianceIdSpend,1,false);'),
        ('    TechTreeUnitAllow(8,"Nexus",false);', '    TechTreeUnitAllow(8,"Nexus",true);\n    TechTreeUnitAllow(9,"DehakaHatchery",true);'),
        ('if (p==8 && UnitGetType(u)=="Probe" && !UnitHasBehavior2(u,"FenixProbiusProbe")) {',
         'if (p==8 && UnitGetType(u)=="Probe" && !UnitHasBehavior2(u,"FenixProbiusProbe") && !UnitHasBehavior2(u,"RM_AllyMiner")) {'),
    ]),
}
MINER = '<CBehaviorBuff id="RM_AllyMiner"><BehaviorFlags index="Permanent" value="1" /><MaxStackCount value="1" /><InfoFlags index="Hidden" value="1" /></CBehaviorBuff>'
BUILD3 = '\n    <InfoArray index="Build3" Unit="DehakaHatchery" Time="100">\n      <Button DefaultButtonFace="DehakaHatchery" />\n    </InfoArray>'
LAYOUT = '<LayoutButtons Face="DehakaHatchery" Type="AbilCmd" AbilCmd="DehakaDroneMorph,Build3" Row="2" Column="2" />'


def append(t, extra):
    i = t.rindex('</Catalog>')
    return t[:i] + extra + t[i:]


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m, cfg in MAPS.items():
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            head = f'\nbool {cfg["tick"]} (bool testConds,bool runActions) {{'
            assert t.count(head) == 1 and 'gf_rmAllyBases' not in t
            t = t.replace(head, FN + head)
            for a, b in cfg['pairs']:
                assert t.count(a) == 1, (m, a)
                t = t.replace(a, b)
            files[s] = t.encode('utf-8'); changed.add(s)
            g = f'{m}.SC2Map/base.sc2data/gamedata/'
            files[g + 'behaviordata.xml'] = append(files[g + 'behaviordata.xml'].decode('utf-8'), MINER).encode('utf-8')
            a = files[g + 'abildata.xml'].decode('utf-8')
            mm = re.search(r'<CAbilBuild id="DehakaDroneMorph">.*?</CAbilBuild>', a, re.S)
            b = mm.group(0)
            assert 'Build3' not in b
            i = b.rindex('</CAbilBuild>')
            b = b[:i].rstrip() + BUILD3 + '\n  ' + b[i:]
            files[g + 'abildata.xml'] = (a[:mm.start()] + b + a[mm.end():]).encode('utf-8')
            u = files[g + 'unitdata.xml'].decode('utf-8')
            mm = re.search(r'<CUnit id="DehakaDrone"[^>]*>.*?</CUnit>', u, re.S)
            b = mm.group(0)
            anchor = '<LayoutButtons Face="DehakaNydusDestroyer" Type="AbilCmd" AbilCmd="DehakaDroneMorph,Build2" Row="2" Column="1" />'
            assert b.count(anchor) == 1
            b = b.replace(anchor, anchor + LAYOUT)
            files[g + 'unitdata.xml'] = (u[:mm.start()] + b + u[mm.end():]).encode('utf-8')
            changed |= {g + 'behaviordata.xml', g + 'abildata.xml', g + 'unitdata.xml'}
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
