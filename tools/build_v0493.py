#!/usr/bin/env python3
"""0.4.92 -> 0.4.93: 플레이어는 넥서스·원시 군락만, 기지가 서면 동맹이 스스로 (3·4번, 사용자 2026-10-24).

사용자: "그냥 넥서스랑 군락만 지을 수 있게, 지어지면 동맹이 알아서 컨트롤 — 건물 건설이랑 유닛 생성",
"기지 전엔 동맹 없음", "차원 관문에서 3번 소환 → 1번으로 제한".
- 기지 전: 동맹 일꾼(레이너 기지에 내려온 탐사정·원시 일벌레)으로 플레이어가 지을 수 있는 건 넥서스·원시 군락뿐이다
  (수정탑·관문·광자포·원시 감시자·원시 벌레 건설 명령을 막는다). 생산 건물이 없으니 동맹 병력도 없다.
- 기지가 한 번 완성되면(gv_rmBaseUp) 그 동맹의 일꾼은 모두 명령 불가 — 동맹이 조종한다. 혼합 선택에서도 내 일꾼으로 치지 않고,
  레이너→동맹 돈 공유도 그 동맹은 끈다(동맹 건설은 동맹 돈).
- 동맹 자동 건설: 10초마다 기지 근처에 부족한 것 하나 (0.4.89 방식, 기지 기준). 정화자 수정탑 → 관문 3 → 광자포 2,
  원시저그 원시 감시자 3(3번 4) → 원시 벌레 2. 쉬는 일꾼이 없으면 채굴 일꾼 하나를 쓴다. 수·간격 시험값.
  기지 완성 보너스(+2)는 동맹이 쓰지 않는다(상한 3, 3번 감시자 4).
- 차원 관문 충전 3 → 1: 한 번 소환하면 원작처럼 재사용 대기를 기다린다.
- 부관 안내 문구를 새 흐름으로 바꾸고, 기지 완성 때 안내를 띄운다.

Usage: python3 tools/build_v0493.py <0.4.92 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path
from build_v0464 import LOCALES, update_lines

OLD, NEW = b'version=0.4.92', b'version=0.4.93'
BUILD_EVERY, CANNONS, WURMS = 10.0, 2, 2  # 시험값
GLOBALS = '''// 0.4.93: an ally takes over its own workers, building and production once its Nexus / Primal Hive is up (user 2026-10-24).
bool[16] gv_rmBaseUp;

'''
FN = f'''
// 0.4.93: before its base the player may build only the Nexus / Primal Hive with ally workers; afterwards the ally builds itself.
fixed gv_rmBuildNext;
point[16] gv_rmBasePt;

unit gf_rmFreeWorker (int p, string worker) {{
    unitgroup g=UnitGroup(worker,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    int i=UnitGroupCount(g,c_unitCountAll);
    unit u;
    unit miner=null;
    for (;i>0;i-=1) {{
        u=UnitGroupUnit(g,i);
        if (UnitHasBehavior2(u,"RM_AllyMiner")) {{ miner=u; }}
        else if (UnitOrderCount(u)==0) {{ return u; }}
    }}
    return miner;
}}

bool gf_rmTryBuild (int p, string worker, string abil, int idx, string kind, point at, fixed r) {{
    unit w=gf_rmFreeWorker(p,worker);
    point spot;
    if (w==null) {{ return true; }}
    if (PlayerGetPropertyInt(p,c_playerPropMinerals)<UnitTypeGetCost(kind,c_unitCostMinerals)
        || PlayerGetPropertyInt(p,c_playerPropVespene)<UnitTypeGetCost(kind,c_unitCostVespene)) {{ return true; }}
    spot=UnitTypePlacementFromPoint(kind,p,at,r);
    if (spot==null) {{ return false; }}
    UnitIssueOrder(w,OrderTargetingPoint(AbilityCommand(abil,idx),spot),c_orderQueueReplace);
    return true;
}}

int gf_rmNear (int p, string kind, point at, fixed r) {{
    return UnitGroupCount(UnitGroup(kind,p,RegionCircle(at,r),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0),c_unitCountAlive);
}}

void gf_rmTakeOver (int p, string worker, string base, string msg) {{
    unitgroup g;
    unit hall=gf_rmBase(p,base);
    int i;
    if (!gv_rmBaseUp[p]) {{
        if (hall==null) {{ return; }}
        gv_rmBaseUp[p]=true;
        gv_rmBasePt[p]=UnitGetPosition(hall);
        UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal(msg));
    }}
    g=UnitGroup(worker,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {{ libNtve_gf_MakeUnitUncommandable(UnitGroupUnit(g,i),true); }}
}}

void gf_rmPhase (int pp, int pz, int capG, int capW) {{
    unitgroup py;
    point at;
    bool now=GameGetMissionTime()>=gv_rmBuildNext;
    gf_rmTakeOver(pp,"Probe","Nexus","rm/AllyBaseP");
    gf_rmTakeOver(pz,"DehakaDrone","DehakaHatchery","rm/AllyBaseZ");
    // Before the base: ally workers in the player's hands may build only the Nexus / Primal Hive.
    TechTreeAbilityAllow(pp,AbilityCommand("ProtossBuild",1),gv_rmBaseUp[pp]);
    TechTreeAbilityAllow(pp,AbilityCommand("ProtossBuild",7),gv_rmBaseUp[pp]);
    TechTreeAbilityAllow(pz,AbilityCommand("DehakaDroneMorph",1),gv_rmBaseUp[pz]);
    if (!gv_rmBaseUp[pp]) {{ TechTreeAbilityAllow(pp,AbilityCommand("ProtossBuild",3),false); }}
    if (!gv_rmBaseUp[pz]) {{ TechTreeAbilityAllow(pz,AbilityCommand("DehakaDroneMorph",0),false); }}
    if (!now) {{ return; }}
    gv_rmBuildNext=GameGetMissionTime()+{BUILD_EVERY};
    // Purifiers: Pylon -> Gateways up to capG -> {CANNONS} Photon Cannons, around their Nexus.
    if (gv_rmBaseUp[pp]) {{
        py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],12.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
        if (UnitGroupCount(py,c_unitCountAlive)==0) {{ gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",gv_rmBasePt[pp],10.0); }}
        else {{
            py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],12.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterUnderConstruction - 32))),0);
            if (UnitGroupCount(py,c_unitCountAlive)>0) {{
                at=UnitGetPosition(UnitGroupClosestToPoint(py,gv_rmBasePt[pp]));
                if (TechTreeUnitCount(pp,"Gateway",c_techCountQueuedOrBetter)+TechTreeUnitCount(pp,"WarpGate",c_techCountQueuedOrBetter)<capG) {{
                    if (!gf_rmTryBuild(pp,"Probe","ProtossBuild",3,"Gateway",at,6.0)) {{ gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",gv_rmBasePt[pp],14.0); }}
                }}
                else if (gf_rmNear(pp,"PhotonCannon",gv_rmBasePt[pp],14.0)<{CANNONS}) {{ gf_rmTryBuild(pp,"Probe","ProtossBuild",7,"PhotonCannon",at,6.0); }}
            }}
        }}
    }}
    // Primal Zerg: Primal Wardens up to capW -> {WURMS} Primal Wurms, around their Primal Hive.
    if (gv_rmBaseUp[pz]) {{
        if (TechTreeUnitCount(pz,"DehakaBarracks",c_techCountQueuedOrBetter)<capW) {{ gf_rmTryBuild(pz,"DehakaDrone","DehakaDroneMorph",0,"DehakaBarracks",gv_rmBasePt[pz],10.0); }}
        else if (gf_rmNear(pz,"DehakaNydusDestroyer",gv_rmBasePt[pz],14.0)<{WURMS}) {{ gf_rmTryBuild(pz,"DehakaDrone","DehakaDroneMorph",1,"DehakaNydusDestroyer",gv_rmBasePt[pz],10.0); }}
    }}
}}
'''
MAPS = {
    'TRaynor03': dict(tick='gt_m3_Tick_Func', threat='    gf_m3_FindThreat();\n', call='    gf_rmPhase(10,11,3,4);\n', p=10, extra=[]),
    'TTychus01': dict(tick='gt_m4_Tick_Func', threat='    gf_m4_FindThreat();\n', call='    gf_rmPhase(8,9,3,3);\n', p=8, extra=[
        ('&& !UnitHasBehavior2(u,"RM_AllyMiner");', '&& !UnitHasBehavior2(u,"RM_AllyMiner") && !gv_rmBaseUp[owner];')]),
}
SPEND = ('bool gf_rmBuilding (int p) {\n    unitgroup g=UnitGroup(null,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);\n'
         '    int i=UnitGroupCount(g,c_unitCountAll);\n    unit u;\n    string k;\n    string a;\n')
SPEND_NEW = SPEND + '    if (gv_rmBaseUp[p]) { return false; }\n'
STR = {
    'rm/AllyBaseP': '정화자 기지가 완성됐습니다. 이제 정화자가 스스로 건설하고 병력을 보냅니다. /// The Purifier base is up. The Purifiers now build and send forces on their own.',
    'rm/AllyBaseZ': '원시저그 기지가 완성됐습니다. 이제 원시저그가 스스로 건설하고 병력을 보냅니다. /// The Primal Zerg base is up. The Primal Zerg now build and send forces on their own.',
}
for _m in ('rm3', 'rm4'):
    STR[f'{_m}/Adj1'] = ('정화자와 원시저그가 일꾼을 보냈습니다. 동맹 일꾼으로 넥서스와 원시 군락을 지어 주십시오. /// '
                         'The Purifiers and Primal Zerg have sent workers. Use them to build a Nexus and a Primal Hive.')
    STR[f'{_m}/Adj2'] = ('기지가 완성되면 그 동맹이 일꾼을 맡아 스스로 건물을 짓고 병력을 보냅니다. 비용은 동맹 자원입니다. /// '
                         'Once a base is up, that ally takes its workers, builds on its own and sends forces. Costs come from ally resources.')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m, c in MAPS.items():
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            head = f'\nbool {c["tick"]} (bool testConds,bool runActions) {{'
            ping = 'bool gf_rmPingEnemy (point pt, int ally) {'
            assert t.count(head) == 1 and t.count(ping) == 1 and t.count(c['threat']) == 1 and t.count(SPEND) == 1 and 'gf_rmPhase' not in t
            t = t.replace(ping, GLOBALS + ping).replace(head, FN + head).replace(c['threat'], c['call'] + c['threat'])
            t = t.replace(SPEND, SPEND_NEW)
            # Warp Gates: 3 stored warp-ins -> 1 (user).
            n = 0
            for idx in ('Train1', 'Train2', 'Train6'):
                for f in ('CountMax', 'CountStart'):
                    a = f'"WarpGateTrain","InfoArray[{idx}].Charge.{f}",{c["p"]},"3");'
                    assert t.count(a) == 1, (m, a)
                    t = t.replace(a, a.replace(',"3");', ',"1");')); n += 1
            t = t.replace('// Purifier Warp Gates store 3 warp-ins', '// Purifier Warp Gates store 1 warp-in (0.4.93, was 3)')
            for a, b in c['extra']:
                assert t.count(a) == 1, (m, a)
                t = t.replace(a, b)
            files[s] = t.encode('utf-8'); changed.add(s)
            ad = f'{m}.SC2Map/base.sc2data/gamedata/abildata.xml'
            a = files[ad].decode('utf-8')
            mm = re.search(r'<CAbilWarpTrain id="WarpGateTrain"[^>]*>.*?</CAbilWarpTrain>', a, re.S)
            if mm:
                blk = mm.group(0).replace('<CountMax value="3" />', '<CountMax value="1" />').replace('<CountStart value="3" />', '<CountStart value="1" />')
                if blk != mm.group(0):
                    files[ad] = (a[:mm.start()] + blk + a[mm.end():]).encode('utf-8'); changed.add(ad)
            pre = 'rm3' if m == 'TRaynor03' else 'rm4'
            vals_ko = {k: v for k, v in STR.items() if not k.startswith(('rm3/', 'rm4/')) or k.startswith(pre)}
            for loc in ('kokr',) + LOCALES:
                p = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'
                vals = vals_ko if loc == 'kokr' else {k: v.split(' /// ', 1)[1] for k, v in vals_ko.items()}
                files[p] = update_lines(files[p], vals); changed.add(p)
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
