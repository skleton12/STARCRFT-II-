#!/usr/bin/env python3
"""Build CCM 0.3.27 from 0.3.26: 동맹 병력을 묶음으로 소환 (3번 미션).

사용자 의견 (2026-10-17): "소환이 한 번에 한 기씩이라 별로, 여러 명 소환되면 좋겠다".
0.3.24~0.3.26은 거점마다 8초에 1기씩 만들었다. 이제 한 번에 묶음으로 나온다 (모두 시험값).
  - 정화자 수정탑 1기당: 파수병 2 + 피닉스 사도 1, 동력기가 2기 미만이면 동력기 1 추가.
    수정탑 둘레에 소환 연출과 함께 동시에 나타난다. 광물 300·가스 40 (동력기 포함 시 350·140).
  - 원시 감시자 1기당: 원시 저글링 4 + 바퀴 1 + 히드라 1, 두 번에 한 번 라바사우르스 1 추가.
    감시자 둘레에 동시에 나타난다. 광물 375·가스 75 (라바사우르스 포함 시 525·125).
  - 묶음 전체 비용이 모이고 인구(동맹마다 100)에 여유가 있을 때만 나온다. 다음 묶음은 20초 / 거점 수 뒤.
  - 비용은 유닛 데이터 값. 수입(2초마다 광물 25·가스 8)과 시작 자원은 그대로다.
  - 소환 연출 모델은 다음 2초 주기에 지운다 (전에는 남아 있었다).

Usage: python3 tools/build_v0327.py <0.3.26 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.26', b'version=0.3.27'
SCRIPT = 'TRaynor03.SC2Map/mapscript.galaxy'

PRODUCE = '''actor[8] gv_m3_fx;
int gv_m3_fxN;

void gf_m3_Produce () {
    unitgroup posts;
    unit post;
    int n;
    int k;
    int count;
    int m;
    int g;
    int p;
    fixed food;
    point at;
    string[8] kind;
    // Warp-in effects from the previous tick (2 s ago) are removed now.
    for (k=0;k<gv_m3_fxN;k+=1) { ActorSend(gv_m3_fx[k],"Destroy"); }
    gv_m3_fxN=0;
    // Income (trial): 25 minerals / 8 gas per 2 s tick for each ally.
    PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperAdd,25);
    PlayerModifyPropertyInt(10,c_playerPropVespene,c_playerPropOperAdd,8);
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperAdd,25);
    PlayerModifyPropertyInt(11,c_playerPropVespene,c_playerPropOperAdd,8);
    // Ally armies stay AI-only: their unit types are Uncommandable (selectable, but the player cannot order them).
    // Waves (user 2026-10-17, trial): one group per post when the whole group is affordable; next wave 20 s / posts.
    for (p=10;p<=11;p+=1) {
        if (p==10) {
            if (GameGetMissionTime()<gv_m3_nextMake10) { continue; }
            posts=UnitGroup("Pylon",10,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
            kind[0]="ZealotPurifier";
            kind[1]="ZealotPurifier";
            kind[2]="AdeptFenix";
            count=3;
            if (UnitGroupCount(UnitGroup("RM21_Energizer",10,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)<2) { kind[3]="RM21_Energizer"; count=4; }
        }
        else {
            if (GameGetMissionTime()<gv_m3_nextMake11) { continue; }
            posts=UnitGroup("DehakaBarracks",11,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
            for (k=0;k<4;k+=1) { kind[k]="DehakaZerglingLevel2"; }
            kind[4]="DehakaRoachLevel2";
            kind[5]="DehakaHydraliskLevel2";
            count=6;
            if (ModI(gv_m3_turn11,2)==1) { kind[6]="DehakaRavasaur"; count=7; }
        }
        n=UnitGroupCount(posts,c_unitCountAlive);
        if (n==0) { continue; }
        m=0;
        g=0;
        food=0.0;
        for (k=0;k<count;k+=1) {
            m+=UnitTypeGetCost(kind[k],c_unitCostMinerals);
            g+=UnitTypeGetCost(kind[k],c_unitCostVespene);
            food+=gf_m3_UnitFood(kind[k]);
        }
        if (gf_m3_Food(p)+food>100.0 || PlayerGetPropertyInt(p,c_playerPropMinerals)<m || PlayerGetPropertyInt(p,c_playerPropVespene)<g) { continue; }
        PlayerModifyPropertyInt(p,c_playerPropMinerals,c_playerPropOperSubtract,m);
        PlayerModifyPropertyInt(p,c_playerPropVespene,c_playerPropOperSubtract,g);
        if (p==10) { post=UnitGroupUnit(posts,ModI(gv_m3_turn10,n)+1); }
        else { post=UnitGroupUnit(posts,ModI(gv_m3_turn11,n)+1); }
        for (k=0;k<count;k+=1) {
            at=PointWithOffsetPolar(UnitGetPosition(post),2.5,IntToFixed(k*360/count));
            if (p==10) {
                gv_m3_fx[gv_m3_fxN]=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",at);
                ActorSend(gv_m3_fx[gv_m3_fxN],"AnimPlay Warp Birth NonLooping");
                gv_m3_fxN+=1;
            }
            UnitCreate(1,kind[k],0,p,at,270.0);
        }
        if (p==10) {
            gv_m3_turn10+=1;
            gv_m3_nextMake10=GameGetMissionTime()+20.0/IntToFixed(n);
        }
        else {
            gv_m3_turn11+=1;
            gv_m3_nextMake11=GameGetMissionTime()+20.0/IntToFixed(n);
        }
    }
}

'''


def script(data):
    text = data.decode('utf-8')
    a = text.index('void gf_m3_Produce () {')
    b = text.index('void gf_m3_GuardWarp () {', a)
    text = text[:a] + PRODUCE + text[b:]
    return text.encode('utf-8')


FIX = {SCRIPT: script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
