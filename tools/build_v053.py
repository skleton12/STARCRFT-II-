#!/usr/bin/env python3
"""0.5.2 -> 0.5.3: 레드스톤 동맹은 군사 건물 없이 30초마다 기지 근처로 병력 지원 (사용자 2026-10-27).

사용자: "동맹 걍 기지 근처에서 소환 및 낙하주머니 투하를 30초간 일어나게" → 선택 "30초마다 반복",
"지금 미션은 뭔가 지원만 필요" (군사 건물은 미션마다 필요한 곳에 따로 정할 예정).

- 5번(TTosh01)만: 동맹은 넥서스·원시 군락(플레이어가 지음)과 채굴만 한다. 수정탑·관문·광자포·원시 감시자·원시 벌레는
  짓지 않고 플레이어도 지을 수 없다 (gf_rmPhase 대신 기지 인수만).
- 기지가 서면 바로, 그 뒤 30초마다(시험값) 기지에서 광물 반대쪽 7칸 둘레에:
  정화자 = 차원 소환 연출로 파수병 2·피닉스 사도 1·동력기(2기 미만일 때) 1 + 해금된 정화자 유닛 1 (돌아가며),
  원시저그 = 낙하 주머니로 원시 저글링 4·바퀴 1·히드라 1 + 원시 숙주(공성 전차 해금)·울트라리스크(골리앗 해금).
  비용은 동맹 자원, 동맹 병력 인구 100 상한 유지. 돈·인구가 모자라면 될 때까지 기다린다. 자리는 높이 9.5 위(용암).
- 레드스톤 안내 문구(부관 2번째·기지 완성)를 이 방식으로 고친다.
- 3·4번 맵은 그대로.

Usage: python3 tools/build_v053.py <0.5.2 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.5.2', b'version=0.5.3'
M5 = 'TTosh01.SC2Map/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'

SUPPORT = r'''// 0.5.3: on Redstone the allies build no army structures (user 2026-10-27 "지금 미션은 지원만"). Once its base is up,
// every 30 s (trial) each ally sends a group next to that base: Purifiers warp in, Primal Zerg drop pods. Ally money, cap 100.
fixed[16] gv_m5_nextSup;
int gv_m5_supTurn;
int gv_m5_supP;
trigger gv_m5_supTrig;
string[16][12] gv_m5_supKind;
point[16][12] gv_m5_supAt;
int[16] gv_m5_supN;

void gf_m5_SupAdd (int p, string kind) {
    if (gv_m5_supN[p]>=12) { return; }
    gv_m5_supKind[p][gv_m5_supN[p]]=kind;
    gv_m5_supN[p]+=1;
}

void gf_m5_SupFill (int p) {
    string[9] extra;
    int n=0;
    int k;
    gv_m5_supN[p]=0;
    if (p==8) {
        gf_m5_SupAdd(p,"ZealotPurifier");
        gf_m5_SupAdd(p,"ZealotPurifier");
        gf_m5_SupAdd(p,"AdeptFenix");
        if (UnitGroupCount(UnitGroup("RM21_Energizer",8,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)<2) { gf_m5_SupAdd(p,"RM21_Energizer"); }
        // Raynor unlock -> Purifier unit (user table 2026-10-20); one unlocked kind per group, in turn.
        for (k=0;k<=8;k+=1) {
            if (gf_m5_Unl(k) || k==6) { extra[n]=gv_m5_supWarp[k]; n+=1; }
        }
        if (n>0) { gf_m5_SupAdd(p,extra[ModI(gv_m5_supTurn,n)]); }
        return;
    }
    for (k=0;k<4;k+=1) { gf_m5_SupAdd(p,"DehakaZerglingLevel2"); }
    gf_m5_SupAdd(p,"DehakaRoachLevel2");
    gf_m5_SupAdd(p,"DehakaHydraliskLevel2");
    if (gf_m5_Unl(2)) { gf_m5_SupAdd(p,"DehakaSwarmHost"); }
    if (gf_m5_Unl(3)) { gf_m5_SupAdd(p,"DehakaUltraliskLevel2"); }
}

void gf_m5_SupSpots (int p) {
    point c=PointWithOffsetPolar(gv_rmBasePt[p],7.0,AngleBetweenPoints(gv_rmBasePt[p],gf_rmAwayPt(p)));
    point h;
    point s;
    int i;
    int n=gv_m5_supN[p];
    if (WorldHeight(c_heightMapGround,c)<=9.5 || !PointPathingPassable(c)) {
        h=gf_m5_HighGround(c);
        if (h!=null) { c=h; }
    }
    for (i=0;i<n;i+=1) {
        s=PointWithOffsetPolar(c,2.0,IntToFixed(i*360/n));
        if (!PointPathingPassable(s)) { s=c; }
        gv_m5_supAt[p][i]=s;
    }
}

bool gt_m5_Sup_Func (bool testConds,bool runActions) {
    int p;
    int n;
    int i;
    string[12] kind;
    point[12] at;
    actor[12] fx;
    if (!runActions) { return true; }
    p=gv_m5_supP;
    n=gv_m5_supN[p];
    for (i=0;i<n;i+=1) {
        kind[i]=gv_m5_supKind[p][i];
        at[i]=gv_m5_supAt[p][i];
        if (p==8) {
            fx[i]=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",at[i]);
            ActorSend(fx[i],"AnimPlay Warp Birth NonLooping");
        }
        else if (ModI(i,2)==0) {
            fx[i]=libNtve_gf_CreateModelAtPoint("ZergDropPod",at[i]);
            ActorSend(fx[i],"AnimPlay Drop Birth NonLooping");
        }
    }
    if (p==8) { Wait(0.5,c_timeGame); } else { Wait(1.5,c_timeGame); }
    for (i=0;i<n;i+=1) {
        if (!gv_gameOver) { UnitCreate(1,kind[i],0,p,at[i],270.0); }
    }
    Wait(8.0,c_timeGame);
    for (i=0;i<n;i+=1) {
        if (fx[i]!=null) { ActorSend(fx[i],"Destroy"); }
    }
    return true;
}

void gf_m5_Support () {
    int p;
    int i;
    int m;
    int g;
    fixed food;
    if (gv_m5_supTrig==null) { gv_m5_supTrig=TriggerCreate("gt_m5_Sup_Func"); }
    for (p=8;p<=9;p+=1) {
        if (!gv_rmBaseUp[p] || GameGetMissionTime()<gv_m5_nextSup[p]) { continue; }
        gf_m5_SupFill(p);
        m=0;
        g=0;
        food=0.0;
        for (i=0;i<gv_m5_supN[p];i+=1) {
            m+=UnitTypeGetCost(gv_m5_supKind[p][i],c_unitCostMinerals);
            g+=UnitTypeGetCost(gv_m5_supKind[p][i],c_unitCostVespene);
            food+=gf_m5_UnitFood(gv_m5_supKind[p][i]);
        }
        // Wait until the ally can pay and has room under its army cap (checked every tick).
        if (gf_m5_Food(p)+food>100.0 || PlayerGetPropertyInt(p,c_playerPropMinerals)<m || PlayerGetPropertyInt(p,c_playerPropVespene)<g) { continue; }
        PlayerModifyPropertyInt(p,c_playerPropMinerals,c_playerPropOperSubtract,m);
        PlayerModifyPropertyInt(p,c_playerPropVespene,c_playerPropOperSubtract,g);
        gf_m5_SupSpots(p);
        if (p==8) { gv_m5_supTurn+=1; }
        gv_m5_nextSup[p]=GameGetMissionTime()+30.0;
        gv_m5_supP=p;
        TriggerExecute(gv_m5_supTrig,false,false);
    }
}

'''

WARP = ['StalkerPurifier', 'Immortal', 'ColossusPurifier', 'Disruptor', 'PhoenixPurifier', 'Scout',
        'SentryFenix', 'TempestPurifier', 'Carrier']
WARP_DECL = 'string[9] gv_m5_supWarp;\n'
WARP_INIT = ''.join(f'    gv_m5_supWarp[{i}]="{u}";\n' for i, u in enumerate(WARP))

SCRIPT = [
    ('bool gt_m5_Tick_Func (bool testConds,bool runActions) {\n',
     WARP_DECL + SUPPORT + 'bool gt_m5_Tick_Func (bool testConds,bool runActions) {\n'),
    ('    gf_m5_Produce();\n', '    gf_m5_Produce();\n    gf_m5_Support();\n'),
    ('    gates=TechTreeUnitCount(8,"Gateway",c_techCountQueuedOrBetter)+TechTreeUnitCount(8,"WarpGate",c_techCountQueuedOrBetter);\n'
     '    TechTreeAbilityAllow(8,AbilityCommand("ProtossBuild",3),gates<3+gv_rmGateBonus);\n'
     '    TechTreeAbilityAllow(9,AbilityCommand("DehakaDroneMorph",0),TechTreeUnitCount(9,"DehakaBarracks",c_techCountQueuedOrBetter)<3+gv_rmWardenBonus);\n'
     '    gf_rmPhase(8,9,3,3);\n',
     '    // 0.5.3: no ally army structures on Redstone; the base takes its workers and forces come from gf_m5_Support.\n'
     '    gf_rmTakeOver(8,"Probe","Nexus","rm/AllyBaseP");\n'
     '    gf_rmTakeOver(9,"DehakaDrone","DehakaHatchery","rm/AllyBaseZ");\n'
     '    TechTreeAbilityAllow(8,AbilityCommand("ProtossBuild",1),false);\n'
     '    TechTreeAbilityAllow(8,AbilityCommand("ProtossBuild",3),false);\n'
     '    TechTreeAbilityAllow(8,AbilityCommand("ProtossBuild",7),false);\n'
     '    TechTreeAbilityAllow(9,AbilityCommand("DehakaDroneMorph",0),false);\n'
     '    TechTreeAbilityAllow(9,AbilityCommand("DehakaDroneMorph",1),false);\n'),
    ('    gv_m5_eggUnit[0]="DehakaTrainEggZergling";\n', WARP_INIT + '    gv_m5_eggUnit[0]="DehakaTrainEggZergling";\n'),
]

STRINGS = {
    'rm4/Adj2': '기지가 완성되면 그 동맹이 일꾼을 맡아 자원을 캐고, 30초마다 기지 근처로 병력을 보냅니다. 비용은 동맹 자원입니다. '
                '/// Once a base is up, that ally takes its workers to mine and sends forces next to its base every 30 seconds. Costs come from ally resources.',
    'rm/AllyBaseP': '정화자 기지가 완성됐습니다. 이제 정화자가 30초마다 기지 근처로 병력을 차원 이동시킵니다. '
                    '/// The Purifier base is up. The Purifiers now warp in forces next to it every 30 seconds.',
    'rm/AllyBaseZ': '원시저그 기지가 완성됐습니다. 이제 원시저그가 30초마다 기지 근처로 병력을 투하합니다. '
                    '/// The Primal Zerg base is up. The Primal Zerg now drop forces next to it every 30 seconds.',
}


def sub1(t, a, b):
    assert t.count(a) == 1, (t.count(a), a[:80])
    return t.replace(a, b)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        s = M5 + 'mapscript.galaxy'
        t = files[s].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = t.replace('\r\n', '\n')
        for a, b in SCRIPT:
            t = sub1(t, a, b)
        files[s] = t.replace('\n', nl).encode('utf-8')
        ko = files[M5 + KO].decode('utf-8-sig')
        knl = '\r\n' if '\r\n' in ko else '\n'
        lines = ko.split(knl)
        for key, val in STRINGS.items():
            hit = [i for i, l in enumerate(lines) if l.startswith(key + '=')]
            assert len(hit) == 1, key
            lines[hit[0]] = f'{key}={val}'
        files[M5 + KO] = knl.join(lines).encode('utf-8')
        V35.gate('kokr', files[M5 + KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M5}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[M5 + KO])
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if not n.startswith(M5) and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
