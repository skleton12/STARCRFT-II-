#!/usr/bin/env python3
"""Build CCM 0.3.9 from 0.3.8 (3번 미션).

사용자 보고·지시 (2026-10-17):
1. "일부 지역 저그 처리 안 됨" — 광선 경로(y 23~38)가 고원 북쪽(y 41~47, x 19~30: 가시 촉수·포자 촉수·저글링 등)에
   닿지 않았고, 남은 적 추적도 (35.5,31) 반경 14만 봤다.
   → 5줄(y 23·28·33·38·43)로 늘리고, 남은 적 추적 범위를 고원 전체(사각형 x17~50, y19~47 중 기지 터와 같은 높이)로, 최대 30초.
2. "유닛이 이상한 곳에 소환됨" — 원시저그 투하·일벌레가 0.3.7에서 옮긴 군락 북쪽 광물 줄 위(40~46,35~39)에 나왔다.
   → 투하 (32~36.5, 33~37) 두 기지 사이 빈터, 드롭포드 (34,35), 일벌레 (36,31), 탐사정 (27,33), 정화자 소환 (27~33, 38~41).
3. "건물 건설 위치 수정" — 관문 (23.5,35.5)은 적 부화장 자리 → 연결체 북쪽 (30.5,34.5). 원시 감시자 (38.5,26.5) → (37.5,25.5).
4. "일꾼 내려오면 건물부터 건설" — 일꾼이 먼저 와서 각 터로 가 건물을 짓고, 병력은 생산 건물이 완성된 뒤 나온다.
   정화자: 탐사정이 수정탑(16초) → 완성 후 연결체(40)·관문(30) 동시. 관문 완성 시 첫 소환 시작.
   원시저그: 원시 일벌레가 군락(40)·감시자(30) 터로 가서 변태(일벌레 소모, 데하카 방식). 둘 다 완성 시 첫 투하.
   건설비는 각 동맹 자원에서 냄 (수정탑 100, 연결체 400, 관문 150 / 군락 450, 감시자 250). 시작 자원 1200/400.
   0.3.6의 "첫 병력이 남은 적 정리 후 건설" 단계는 병력이 나중에 오므로 빼고, 광선 추적이 맡는다.
수치·시간·위치는 시험값.

Usage: python3 tools/build_v039.py <0.3.8 zip> <new output zip>
"""
import argparse
import copy
import sys
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.8', b'version=0.3.9'
M3 = 'TRaynor03.SC2Map/'

SITE_FUNC = '''unitgroup gf_m3_SiteEnemies () {
    unitgroup all;
    unitgroup g;
    unit u;
    int p;
    int i;
    int lv;
    // Enemy players 2-5 anywhere on the allies' plateau (same cliff level as the site centre).
    all=UnitGroupEmpty();
    lv=CliffLevel(Point(35.5,31.0));
    for (p=2;p<=5;p+=1) {
        g=UnitGroup(null,p,RegionRect(17.0,19.0,50.0,47.0),UnitFilter(0,0,0,0),0);
        i=UnitGroupCount(g,c_unitCountAll);
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            if (UnitIsAlive(u) && CliffLevel(UnitGetPosition(u))==lv) { UnitGroupAdd(all,u); }
        }
    }
    return all;
}

unit gf_m3_Begin (string kind,int p,point at) {
    unit b;
    UnitCreate(1,kind,c_unitCreateConstruct,p,at,270.0);
    b=UnitLastCreated();
    if (kind=="Pylon") { gv_m3_pylon=b; }
    if (kind=="Nexus") { gv_m3_nexus=b; }
    if (kind=="DehakaHatchery") { gv_m3_hatchery=b; }
    return b;
}

void gf_m3_Burn (point at) {'''

TAIL_START = '    // Workers arrive, then the actual construction states are progressed.\n'
TAIL_END = '    UIDisplayMessage(PlayerGroupAll(),c_messageAreaSubtitle,StringExternal("rm3/Ready"));\n    return true;\n}\n'
TAIL_NEW = '''    // Workers come down first and build; troops only start once the production buildings are finished (trial times).
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
    UnitIssueOrder(UnitGroupUnit(probes,1),OrderTargetingPoint(AbilityCommand("move",0),site[0]),c_orderQueueReplace);
    UnitIssueOrder(UnitGroupUnit(drones,1),OrderTargetingPoint(AbilityCommand("move",0),site[1]),c_orderQueueReplace);
    UnitIssueOrder(UnitGroupUnit(drones,2),OrderTargetingPoint(AbilityCommand("move",0),site[2]),c_orderQueueReplace);
    Wait(3.0,c_timeGame);
    if (gv_gameOver) { return true; }
    dur[0]=16.0;
    dur[1]=40.0;
    dur[2]=30.0;
    dur[3]=40.0;
    dur[4]=30.0;
    PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSubtract,100);
    b[0]=gf_m3_Begin("Pylon",10,site[0]);
    st[0]=GameGetMissionTime();
    // Primal drones morph into the buildings (Dehaka style: the drone is used up).
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,700);
    UnitRemove(UnitGroupUnit(drones,2));
    UnitRemove(UnitGroupUnit(drones,1));
    b[1]=gf_m3_Begin("DehakaHatchery",11,site[1]);
    st[1]=GameGetMissionTime();
    b[2]=gf_m3_Begin("DehakaBarracks",11,site[2]);
    st[2]=GameGetMissionTime();
    started[0]=true;
    started[1]=true;
    started[2]=true;
    for (k=0;k<200;k+=1) {
        if (gv_gameOver) { return true; }
        for (i=0;i<5;i+=1) {
            if (!started[i] || done[i]) { continue; }
            if (!UnitIsAlive(b[i])) { done[i]=true; continue; }
            if (GameGetMissionTime()-st[i]>=dur[i]) {
                UnitSetProgressComplete(b[i],1,100);
                UnitSetProgressStage(b[i],1,c_unitProgressStageComplete);
                done[i]=true;
            }
            else { UnitSetProgressComplete(b[i],1,FixedToInt((GameGetMissionTime()-st[i])*100.0/dur[i])); }
        }
        // Pylon done: two probes build the Nexus and Gateway.
        if (done[0] && !started[3]) {
            UnitIssueOrder(UnitGroupUnit(probes,2),OrderTargetingPoint(AbilityCommand("move",0),site[3]),c_orderQueueReplace);
            UnitIssueOrder(UnitGroupUnit(probes,3),OrderTargetingPoint(AbilityCommand("move",0),site[4]),c_orderQueueReplace);
            PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSubtract,550);
            b[3]=gf_m3_Begin("Nexus",10,site[3]);
            st[3]=GameGetMissionTime();
            b[4]=gf_m3_Begin("Gateway",10,site[4]);
            st[4]=GameGetMissionTime();
            started[3]=true;
            started[4]=true;
        }
        // Production buildings finished: first warp-in / drop.
        if (done[4] && !warped && UnitIsAlive(b[4])) {
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
DECL_OLD = '    unitgroup left;\n'
DECL_NEW = ('    unitgroup left;\n    unitgroup probes;\n    unitgroup drones;\n    unit[5] b;\n    point[5] site;\n'
            '    fixed[5] st;\n    fixed[5] dur;\n    bool[5] started;\n    bool[5] done;\n    bool warped;\n    bool dropped;\n')

EDITS = [
    ('void gf_m3_Burn (point at) {', SITE_FUNC),
    ('    for (row=0;row<4;row+=1) {', '    for (row=0;row<5;row+=1) {'),
    ('        for (k=1;k<=5 && row<3;k+=1) {', '        for (k=1;k<=5 && row<4;k+=1) {'),
    ('    for (k=0;k<80 && !gv_gameOver;k+=1) {\n        left=UnitGroupEmpty();\n'
     '        for (p=2;p<=5;p+=1) { UnitGroupAddUnitGroup(left,UnitGroup(null,p,RegionCircle(Point(35.5,31.0),14.0),UnitFilter(0,0,0,0),0)); }\n',
     '    for (k=0;k<120 && !gv_gameOver;k+=1) {\n        left=gf_m3_SiteEnemies();\n'),
    ('    // Anything left at the site: the beam goes to it and burns it (up to 20 s, trial).\n',
     '    // Anything left on the plateau: the beam goes to it and burns it (up to 30 s, trial).\n'),
    (DECL_OLD, DECL_NEW),
    ('            at[k]=Point(27.0+2.0*k,36.0+i);', '            at[k]=Point(27.0+2.0*k,38.0+i);'),
    ('pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(43.0,36.0));', 'pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(34.0,35.0));'),
    ('UnitCreate(1,kind,0,11,Point(40.0+2.0*(i%4),35.0+2.0*(i/4)),0.0);', 'UnitCreate(1,kind,0,11,Point(32.0+1.5*(i%4),33.0+2.0*(i/4)),0.0);'),
    ('    PlayerModifyPropertyInt(p,c_playerPropMinerals,c_playerPropOperSetTo,1200);\n    PlayerModifyPropertyInt(p,c_playerPropVespene,c_playerPropOperSetTo,400);\n}', '}'),
]


def script(data):
    text = data.decode('utf-8')
    for old, new in EDITS:
        assert text.count(old) == 1, old[:60]
        text = text.replace(old, new, 1)
    a = text.index(TAIL_START); b = text.index(TAIL_END, a)
    text = text[:a] + TAIL_NEW + text[b + len(TAIL_END):]
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
