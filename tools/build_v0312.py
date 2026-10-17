#!/usr/bin/env python3
"""Build CCM 0.3.12 from 0.3.11 (3번 미션).

사용자 지적 (2026-10-17): "적군 강화는 왜 없으며", "원시 군락과 감시자는 왜 이리 빨리 지어져 있음".

1. 적 강화 (CLAUDE.md 7-1) — 3번 맵에 빠져 있었다 (1·2번은 있음).
   - 적 2~5번 주는 피해 100+값 %, 받는 피해 10000/(100+값) % — 쉬움 0, 보통 5, 어려움 15, 아주 어려움 35.
   - 최소 업그레이드: 저그 근접 공격·원거리 공격·지상 갑피 1단계 (테란 '보병 공격·방어 1'에 대응). 부족분만 채움.
     원본은 240초에 근접·원거리 공격을 무조건 +1 하므로, 그대로 두면 2단계로 겹친다. 원본이 그 시점에 주려던 단계
     (근접 1, 원거리 1 + 아주 어려움 1)까지만 채우도록 바꿨다.
   - 병력 증강 (시험값): 원본 공세 생성 함수 4개(드롭포드 저글링, 첫 땅굴 공세, 서·동 땅굴 증원)의 수량을 +50% (내림).
     원본에 나오는 적 종류만, 브리핑·승리 연출 생성은 그대로.
2. 원시 건물 즉시 완성 — 데하카 건물은 '건설 중' 상태를 쓰지 않아 진행률 조절이 먹지 않고 바로 완성됐다(코드 검토, 게임 미확인).
   → 원작처럼 일벌레가 고치(DehakaHatcheryBuild / DehakaBarracksBuild 모델)로 변태해 있다가, 시간이 다 되면 건물이 나온다.
   - 건설 시간을 원작 데이터 값으로: 원시 군락 100, 원시 감시자 60 (DehakaDroneMorph), 연결체 100, 수정탑 25, 관문 65,
     추출장 30 (Liberty ProtossBuild·저그 기본). 0.3.9~0.3.11의 40/30/16 시험값 폐기.
   - 추가 원시 감시자·추출장도 같은 방식.

Usage: python3 tools/build_v0312.py <0.3.11 zip> <new output zip>
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.3.11', b'version=0.3.12'
M3 = 'TRaynor03.SC2Map/'
GD = M3 + 'base.sc2data/gamedata/'

ENEMY = '''void gf_m3_EnemyRules () {
    int p;
    int lv_buff;
    // CLAUDE.md 7-1: difficulty buff (0/5/15/35) and minimum level-1 ground upgrades for enemy players 2-5.
    lv_buff=libNtve_gf_DifficultyValueInt(0,5,15,35);
    for (p=2;p<=5;p+=1) {
        PlayerModifyPropertyInt(p,c_playerPropDamageDealtPercent,c_playerPropOperSetTo,100+lv_buff);
        PlayerModifyPropertyInt(p,c_playerPropDamageTakenPercent,c_playerPropOperSetTo,10000/(100+lv_buff));
        TechTreeUpgradeAddLevel(p,"ZergMeleeWeaponsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"ZergMeleeWeaponsLevel1",c_techCountCompleteOnly)));
        TechTreeUpgradeAddLevel(p,"ZergMissileWeaponsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"ZergMissileWeaponsLevel1",c_techCountCompleteOnly)));
        TechTreeUpgradeAddLevel(p,"ZergGroundArmorsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"ZergGroundArmorsLevel1",c_techCountCompleteOnly)));
    }
}

bool gf_m3_Build (string kind,int p,point at,int seconds) {'''

BUILD_HEAD_OLD = 'bool gf_m3_Build (string kind,int p,point at,int seconds) {\n    unit b;\n    int elapsed;\n'
BUILD_HEAD_NEW = '''bool gf_m3_Build (string kind,int p,point at,int seconds) {
    unit b;
    int elapsed;
    actor cocoon;
    // Primal buildings: the drone becomes a cocoon, the building appears when the time is up (Dehaka style).
    if (kind=="DehakaHatchery" || kind=="DehakaBarracks") {
        cocoon=libNtve_gf_CreateModelAtPoint(kind+"Build",at);
        for (elapsed=0;elapsed<seconds;elapsed+=1) {
            if (gv_gameOver) { ActorSend(cocoon,"Destroy"); return false; }
            Wait(1.0,c_timeGame);
        }
        ActorSend(cocoon,"Destroy");
        UnitCreate(1,kind,0,p,at,270.0);
        if (kind=="DehakaHatchery") { gv_m3_hatchery=UnitLastCreated(); }
        return UnitIsAlive(UnitLastCreated());
    }
'''

UPG_OLD = ('        TechTreeUpgradeAddLevel(autoAC0A0760_var, "ZergMeleeWeaponsLevel1", 1);\n'
           '        TechTreeUpgradeAddLevel(autoAC0A0760_var, "ZergMissileWeaponsLevel1", 1);\n')
UPG_NEW = ('        // 0.3.12: fill up to the level the original grants here instead of stacking on the 7-1 minimum.\n'
           '        TechTreeUpgradeAddLevel(autoAC0A0760_var, "ZergMeleeWeaponsLevel1", MaxI(0, 1 - TechTreeUpgradeCount(autoAC0A0760_var, "ZergMeleeWeaponsLevel1", c_techCountCompleteOnly)));\n'
           '        TechTreeUpgradeAddLevel(autoAC0A0760_var, "ZergMissileWeaponsLevel1", MaxI(0, 1 + libNtve_gf_DifficultyValueInt(0, 0, 0, 1) - TechTreeUpgradeCount(autoAC0A0760_var, "ZergMissileWeaponsLevel1", c_techCountCompleteOnly)));\n')

WAVES = [  # +50% (trial) on original attack-wave spawns only
    ('    libNtve_gf_CreateUnitsAtPoint2(lp_quantity, "Zergling", 0, gv_pLAYER05_ZERG_NOAI, lp_zergSpawnPoint);',
     '    libNtve_gf_CreateUnitsAtPoint2(lp_quantity + lp_quantity / 2, "Zergling", 0, gv_pLAYER05_ZERG_NOAI, lp_zergSpawnPoint);'),
    ('    libNtve_gf_CreateUnitsAtPoint2(lp_quantity, lp_unitType, 0, gv_pLAYER03_ZERG, UnitGetPosition(gv_nydusWormP03));',
     '    libNtve_gf_CreateUnitsAtPoint2(lp_quantity + lp_quantity / 2, lp_unitType, 0, gv_pLAYER03_ZERG, UnitGetPosition(gv_nydusWormP03));'),
]
NYDUS_FUNCS = ['void gf_SpawnNydusUnitsP02West (', 'void gf_SpawnNydusUnitsP04East (']
NYDUS_OLD = '        UnitCreate(lp_qty, lp_unitType, 0, lp_player, UnitGetPosition(lp_nydus), libNtve_gf_RandomAngle());'
NYDUS_NEW = '        UnitCreate(lp_qty + lp_qty / 2, lp_unitType, 0, lp_player, UnitGetPosition(lp_nydus), libNtve_gf_RandomAngle());'

ARRIVE_OLD = '    Wait(12.0,c_timeGame);\n    if (gv_gameOver) { return true; }\n'
ARRIVE_NEW = '    Wait(12.0,c_timeGame);\n    if (gv_gameOver) { return true; }\n    gf_m3_EnemyRules();\n'

TAIL_START = '    // Workers come down first and build; troops only start once the production buildings are finished (trial times).\n'
TAIL_END = '    UIDisplayMessage(PlayerGroupAll(),c_messageAreaSubtitle,StringExternal("rm3/Ready"));\n    return true;\n}\n'
TAIL_NEW = '''    // Workers come down first and build, town halls first. Original build times (data seconds).
    for (i=0;i<5;i+=1) {
        started[i]=false;
        done[i]=false;
    }
    warped=false;
    dropped=false;
    PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSetTo,1200);
    PlayerModifyPropertyInt(10,c_playerPropVespene,c_playerPropOperSetTo,400);
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSetTo,1200);
    PlayerModifyPropertyInt(11,c_playerPropVespene,c_playerPropOperSetTo,400);
    UnitCreate(6,"Probe",0,10,Point(27.0,33.0),270.0);
    probes=UnitLastCreatedGroup();
    UnitCreate(6,"DehakaDrone",0,11,Point(36.0,31.0),270.0);
    drones=UnitLastCreatedGroup();
    site[0]=Point(27.0,34.0);
    site[1]=Point(42.5,29.5);
    site[2]=Point(37.5,25.5);
    site[3]=Point(28.5,29.5);
    site[4]=Point(30.5,34.5);
    dur[0]=25.0;
    dur[1]=100.0;
    dur[2]=60.0;
    dur[3]=100.0;
    dur[4]=65.0;
    UnitIssueOrder(UnitGroupUnit(probes,1),OrderTargetingPoint(AbilityCommand("move",0),site[3]),c_orderQueueReplace);
    UnitIssueOrder(UnitGroupUnit(drones,1),OrderTargetingPoint(AbilityCommand("move",0),site[1]),c_orderQueueReplace);
    UnitIssueOrder(UnitGroupUnit(drones,2),OrderTargetingPoint(AbilityCommand("move",0),site[2]),c_orderQueueReplace);
    Wait(3.0,c_timeGame);
    if (gv_gameOver) { return true; }
    PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSubtract,400);
    b[3]=gf_m3_Begin("Nexus",10,site[3]);
    st[3]=GameGetMissionTime();
    started[3]=true;
    // Primal Hive: the drone becomes a cocoon; the hive appears when the time is up.
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,450);
    UnitRemove(UnitGroupUnit(drones,1));
    fx[1]=libNtve_gf_CreateModelAtPoint("DehakaHatcheryBuild",site[1]);
    st[1]=GameGetMissionTime();
    started[1]=true;
    for (k=0;k<400;k+=1) {
        if (gv_gameOver) { return true; }
        for (i=0;i<5;i+=1) {
            if (!started[i] || done[i]) { continue; }
            if (i==1 || i==2) {
                if (GameGetMissionTime()-st[i]>=dur[i]) {
                    ActorSend(fx[i],"Destroy");
                    if (i==1) {
                        UnitCreate(1,"DehakaHatchery",0,11,site[1],270.0);
                        gv_m3_hatchery=UnitLastCreated();
                    }
                    else { UnitCreate(1,"DehakaBarracks",0,11,site[2],270.0); }
                    b[i]=UnitLastCreated();
                    done[i]=true;
                }
                continue;
            }
            if (!UnitIsAlive(b[i])) { done[i]=true; continue; }
            if (GameGetMissionTime()-st[i]>=dur[i]) {
                UnitSetProgressComplete(b[i],1,100);
                UnitSetProgressStage(b[i],1,c_unitProgressStageComplete);
                done[i]=true;
            }
            else { UnitSetProgressComplete(b[i],1,FixedToInt((GameGetMissionTime()-st[i])*100.0/dur[i])); }
        }
        // Nexus done: two probes build the Pylon and Gateway.
        if (done[3] && !started[0]) {
            UnitIssueOrder(UnitGroupUnit(probes,2),OrderTargetingPoint(AbilityCommand("move",0),site[0]),c_orderQueueReplace);
            UnitIssueOrder(UnitGroupUnit(probes,3),OrderTargetingPoint(AbilityCommand("move",0),site[4]),c_orderQueueReplace);
            PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSubtract,250);
            b[0]=gf_m3_Begin("Pylon",10,site[0]);
            st[0]=GameGetMissionTime();
            b[4]=gf_m3_Begin("Gateway",10,site[4]);
            st[4]=GameGetMissionTime();
            started[0]=true;
            started[4]=true;
        }
        // Primal Hive done: the waiting drone becomes the Primal Warden cocoon.
        if (done[1] && !started[2]) {
            PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,250);
            UnitRemove(UnitGroupUnit(drones,2));
            fx[2]=libNtve_gf_CreateModelAtPoint("DehakaBarracksBuild",site[2]);
            st[2]=GameGetMissionTime();
            started[2]=true;
        }
        if (done[4] && done[0] && !warped && UnitIsAlive(b[4]) && UnitIsAlive(b[0])) {
            warped=true;
            gv_m3_warpBusy=true;
            TriggerExecute(gt_m3_warp,false,false);
        }
        if (done[1] && done[2] && !dropped && UnitIsAlive(b[2])) {
            dropped=true;
            gv_m3_dropBusy=true;
            TriggerExecute(gt_m3_drop,false,false);
        }
        if (done[0] && done[1] && done[2] && done[3] && done[4]) { break; }
        Wait(1.0,c_timeGame);
    }
    gf_m3_AI(10,Point(28.5,29.5));
    gf_m3_AI(11,Point(42.5,29.5));
    gv_m3_ready=true;
    gv_m3_nextP=GameGetMissionTime()+90.0;
    gv_m3_nextZ=GameGetMissionTime()+90.0;
    UIDisplayMessage(PlayerGroupAll(),c_messageAreaSubtitle,StringExternal("rm3/Ready"));
    return true;
}
'''
DECL_OLD = '    bool warped;\n'
DECL_NEW = '    bool warped;\n    actor[5] fx;\n'

OTHER = [
    ('gf_m3_Build("Extractor",11,Point(35.5,28.5),20)', 'gf_m3_Build("Extractor",11,Point(35.5,28.5),30)'),
    ('gf_m3_Build("DehakaBarracks",11,Point(44.5,25.5),30)', 'gf_m3_Build("DehakaBarracks",11,Point(44.5,25.5),60)'),
]
COCOON_MODEL = ('<CModel id="DehakaHatcheryBuild" parent="PrimalZergBuildingBuild">'
                '<ScaleMax value="1.500000,1.500000,1.500000" /><ScaleMin value="1.500000,1.500000,1.500000" /></CModel>')


def script(data):
    text = data.decode('utf-8')
    for old, new in [('bool gf_m3_Build (string kind,int p,point at,int seconds) {', ENEMY)]:
        assert text.count(old) == 1; text = text.replace(old, new, 1)
    for old, new in [(BUILD_HEAD_OLD, BUILD_HEAD_NEW), (UPG_OLD, UPG_NEW), (ARRIVE_OLD, ARRIVE_NEW), (DECL_OLD, DECL_NEW)] + WAVES + OTHER:
        assert text.count(old) == 1, old[:70]
        text = text.replace(old, new, 1)
    for f in NYDUS_FUNCS:
        a = text.rindex(f); b = text.index("\n}\n", a)
        assert text[a:b].count(NYDUS_OLD) == 1, f
        text = text[:a] + text[a:b].replace(NYDUS_OLD, NYDUS_NEW) + text[b:]
    a = text.index(TAIL_START); b = text.index(TAIL_END, a)
    text = text[:a] + TAIL_NEW + text[b + len(TAIL_END):]
    return text.encode('utf-8')


def models(data):
    text = data.decode('utf-8')
    assert 'id="DehakaHatcheryBuild"' not in text and 'id="DehakaBarracksBuild"' in text and 'id="PrimalZergBuildingBuild"' in text
    out = text.replace('</Catalog>', COCOON_MODEL + '</Catalog>', 1).encode('utf-8')
    E.fromstring(out)
    return out


FIX = {M3 + 'mapscript.galaxy': script, GD + 'modeldata.xml': models, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
